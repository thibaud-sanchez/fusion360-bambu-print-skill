#!/usr/bin/env python3
"""Read-only checks of saved Bambu 3MF projects and annotated text G-code.

Python 3.10+, standard library only. See references/printcheck.md for the
expectation format and deliberate limits. Never slices, modifies, or prints.
"""
from __future__ import annotations

import argparse
from array import array
from collections import Counter, defaultdict
from contextlib import contextmanager
import hashlib
import html
import io
import json
import math
from pathlib import Path
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

VERSION = "1.0.0"
IDENTITY = (1., 0., 0., 0., 1., 0., 0., 0., 1., 0., 0., 0.)
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)"
WORD = re.compile(r"([A-Za-z])\s*(" + NUMBER + r")")


def finite(values):
    result = tuple(float(v) for v in values)
    if not all(math.isfinite(v) for v in result):
        raise ValueError("Non-finite numeric input")
    return result


def matrix(text=None):
    value = finite(text.split()) if text else IDENTITY
    if len(value) != 12:
        raise ValueError("A 3MF transform must contain 12 numbers")
    return value


def point(v, m):
    # 3MF row vectors: [x y z 1] * M, translation at indices 9..11.
    return tuple(sum(v[j] * m[3*j+i] for j in range(3)) + m[9+i] for i in range(3))


def compose(a, b):
    """Local transform a followed by parent transform b."""
    return tuple(sum(a[3*r+k] * b[3*k+c] for k in range(3))
                 for r in range(3) for c in range(3)) + point(a[9:12], b)


def extend(bounds, p):
    for i, v in enumerate(p):
        bounds[i] = min(bounds[i], v)
        bounds[i+3] = max(bounds[i+3], v)


def empty_bounds():
    return [math.inf] * 3 + [-math.inf] * 3


def tag(node):
    return node.tag.rsplit("}", 1)[-1]


def metadata(node):
    return {m.get("key"): m.get("value", "") for m in node.findall("metadata") if m.get("key")}


def member_path(base, target):
    path = posixpath.normpath(target.lstrip("/") if target.startswith("/")
                             else posixpath.join(posixpath.dirname(base), target))
    if path.startswith("../") or ":" in path:
        raise ValueError("External or escaping package references are unsupported")
    return path


class Report:
    def __init__(self, source):
        self.data = {"tool": "printcheck", "version": VERSION, "source": str(source),
                     "findings": [], "checks": [], "limits": [
                         "No mechanical, adhesion, sag, fit or durability validation.",
                         "No mesh topology, unsupported-island or toolhead-collision analysis."]}
        self.seen = set()

    def add(self, severity, code, message, **context):
        # Deduplicate parser problems, bound evidence for large G-code inputs.
        key = (severity, code, json.dumps(context, sort_keys=True))
        if key not in self.seen:
            self.seen.add(key)
            self.data["findings"].append(dict(severity=severity, code=code, message=message, **context))

    def finish(self):
        counts = Counter(f["severity"] for f in self.data["findings"])
        self.data["status"] = "fail" if counts["error"] else "incomplete" if counts["incomplete"] else "pass"
        self.data["counts"] = dict(counts)
        return 1 if counts["error"] else 2 if counts["incomplete"] else 0


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expect_file(path):
    if not path:
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {"schema_version", "scope", "parts", "plates", "settings", "bed_mm",
               "max_height_mm", "tolerance_mm", "require_gcode", "protected_regions", "gcode_sha256"}
    if not isinstance(value, dict) or set(value) - allowed or value.get("schema_version") != 1:
        raise ValueError("Expected schema_version=1 and only documented expectation keys")
    if value.get("scope") not in ("complete", "replacements"):
        raise ValueError("scope must be complete or replacements")
    if not isinstance(value.get("parts"), list) or not value["parts"]:
        raise ValueError("parts must be a nonempty list of expected print-object IDs")
    ids = set()
    for part in value["parts"]:
        if set(part) - {"id", "name", "quantity", "dimensions_mm", "height_mm", "mesh_z_direction", "linear_transform", "settings"}:
            raise ValueError("Unknown expected part field")
        pid = part.get("id")
        if not isinstance(pid, str) or not pid or pid in ids:
            raise ValueError("Each part needs a unique nonempty id")
        ids.add(pid)
        q = part.get("quantity", 1)
        if type(q) is not int or q < 1:
            raise ValueError("Part quantity must be a positive integer")
        for key, size in [("dimensions_mm", 3), ("linear_transform", 9)]:
            if key in part and (len(part[key]) != size or not all(math.isfinite(float(x)) for x in part[key])):
                raise ValueError(f"Invalid {key}")
        if "height_mm" in part and (not math.isfinite(float(part["height_mm"])) or part["height_mm"] <= 0):
            raise ValueError("height_mm must be positive and finite")
        if "mesh_z_direction" in part:
            direction = finite(part["mesh_z_direction"])
            if len(direction) != 3 or abs(math.sqrt(sum(v*v for v in direction))-1) > 1e-5:
                raise ValueError("mesh_z_direction must be a unit vector with 3 numbers")
        if "settings" in part and not isinstance(part["settings"], dict):
            raise ValueError("Part settings must be an object")
    if "settings" in value and not isinstance(value["settings"], dict):
        raise ValueError("settings must be an object")
    for key in ("plates",):
        if key in value and (type(value[key]) is not int or value[key] < 1):
            raise ValueError(f"{key} must be a positive integer")
    for key in ("tolerance_mm", "max_height_mm"):
        if key in value and (not math.isfinite(float(value[key])) or value[key] <= 0):
            raise ValueError(f"{key} must be positive and finite")
    if "require_gcode" in value and type(value["require_gcode"]) is not bool:
        raise ValueError("require_gcode must be boolean")
    if "gcode_sha256" in value and not re.fullmatch(r"[0-9a-f]{64}", value["gcode_sha256"]):
        raise ValueError("gcode_sha256 must be a lowercase SHA-256 hex digest")
    if "bed_mm" in value:
        b = finite(value["bed_mm"])
        if len(b) != 4 or b[0] >= b[2] or b[1] >= b[3]:
            raise ValueError("bed_mm must be [xmin,ymin,xmax,ymax]")
    if not isinstance(value.get("protected_regions", []), list):
        raise ValueError("protected_regions must be a list")
    region_ids = set()
    for region in value.get("protected_regions", []):
        if set(region) - {"id", "bounds_mm", "features", "frame", "plate"}:
            raise ValueError("Unknown protected-region field")
        b = finite(region["bounds_mm"])
        if len(b) != 6 or any(b[i] >= b[i+3] for i in range(3)):
            raise ValueError("Region bounds must be [xmin,ymin,zmin,xmax,ymax,zmax]")
        if region.get("frame") != "plate" or region.get("plate", 1) != 1:
            raise ValueError("V1 protected regions require frame=plate and plate=1")
        if not region.get("id") or not isinstance(region.get("features"), list) or not region["features"] or not all(isinstance(x, str) and x for x in region["features"]):
            raise ValueError("Regions need id and a nonempty features list")
        if region["id"] in region_ids:
            raise ValueError("Protected-region IDs must be unique")
        region_ids.add(region["id"])
    return value


class Package:
    """Stream mesh XML; retain only vertex coordinates and component references."""
    def __init__(self, archive):
        self.z = archive
        self.models = {}

    def load(self, path):
        if path in self.models:
            return self.models[path]
        resources, items, stack, namespaces = {}, [], [], {}
        current = None
        with self.z.open(path) as stream:
            for event, node in ET.iterparse(stream, events=("start", "end", "start-ns")):
                if event == "start-ns":
                    namespaces[node[0]] = node[1]
                    continue
                kind = tag(node)
                if event == "start":
                    stack.append(node)
                    if kind == "model" and node.get("unit", "millimeter") != "millimeter":
                        raise NotImplementedError("Only millimeter 3MF models are supported in V1")
                    if kind == "model":
                        for prefix in node.get("requiredextensions", "").split():
                            if namespaces.get(prefix) != "http://schemas.microsoft.com/3dmanufacturing/production/2015/06":
                                raise NotImplementedError(f"Unsupported required 3MF extension: {prefix}")
                    if kind == "object":
                        if node.attrib["id"] in resources:
                            raise ValueError("Duplicate 3MF resource ID")
                        current = {"vertices": array("d"), "triangles": 0, "components": [], "name": node.get("name", "")}
                        resources[node.attrib["id"]] = current
                    continue
                if kind == "vertex":
                    current["vertices"].extend(finite(node.attrib[k] for k in "xyz"))
                elif kind == "triangle":
                    current["triangles"] += 1
                elif kind == "component":
                    target = next((v for k, v in node.attrib.items() if k.endswith("}path")), None)
                    current["components"].append((member_path(path, target) if target else path,
                                                  node.attrib["objectid"], matrix(node.get("transform"))))
                elif kind == "item" and len(stack) > 1 and tag(stack[-2]) == "build":
                    items.append((node.attrib["objectid"], matrix(node.get("transform")),
                                  node.get("printable", "1") not in ("0", "false")))
                if kind == "object":
                    current = None
                stack.pop()
                if stack:
                    stack[-1].remove(node)
                node.clear()
        self.models[path] = (resources, items)
        return resources, items

    def geometry(self, path, oid, transform, excluded=frozenset(), trail=()):
        key = (path, oid)
        if key in trail:
            raise ValueError("Cyclic 3MF component graph")
        obj = self.load(path)[0][oid]
        if obj["vertices"]:
            if not obj["triangles"]:
                raise ValueError("Mesh has vertices but no triangles")
            yield obj["vertices"], transform
        for child_path, cid, local in obj["components"]:
            if cid not in excluded:
                yield from self.geometry(child_path, cid, compose(local, transform), excluded, trail + (key,))


def compare_settings(actual, expected, report, label):
    for key, value in expected.items():
        got = actual.get(key)
        if got is None:
            report.add("incomplete", "setting_unavailable", "Requested setting is not available in the saved configuration", target=label, parameter=key)
            continue
        # String/number serialization differs; preserve list and boolean semantics.
        if got != value and str(got) != str(value):
            report.add("error", "setting_mismatch", "Saved setting differs from expectation",
                       target=label, parameter=key, expected=value, actual=got)


def inspect_project(path, expect, report):
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Ambiguous duplicate ZIP entries")
        try:
            rels = ET.fromstring(archive.read("_rels/.rels"))
            roots = [n.get("Target") for n in rels if n.get("Type", "").endswith("/3dmodel")]
            root = member_path("", roots[0]) if len(roots) == 1 else "3D/3dmodel.model"
        except KeyError:
            root = "3D/3dmodel.model"
        config = json.loads(archive.read("Metadata/project_settings.config")) if "Metadata/project_settings.config" in archive.namelist() else {}
        settings = ET.fromstring(archive.read("Metadata/model_settings.config")) if "Metadata/model_settings.config" in archive.namelist() else ET.Element("config")
        objects = {o.attrib["id"]: o for o in settings.findall("object")}
        plates = settings.findall("plate")
        mapping = {}
        for plate_index, plate in enumerate(plates, 1):
            for instance in plate.findall("model_instance"):
                m = metadata(instance)
                key = (m.get("object_id"), int(m.get("instance_id", "0")))
                if key in mapping:
                    raise ValueError("An instance belongs to multiple plates")
                mapping[key] = plate_index
        report.data["project"] = {"plates": len(plates) if plates else None,
                                  "printer": config.get("printer_model"), "objects": []}
        if expect.get("plates") is not None and not plates:
            report.add("incomplete", "plates_unknown", "No supported Bambu plate metadata")
        elif expect.get("plates") is not None and len(plates) != expect["plates"]:
            report.add("error", "plate_count", "Unexpected plate count", expected=expect["plates"], actual=len(plates))
        if len(plates) > 1:
            report.add("incomplete", "multiple_plate_frames", "V1 does not resolve multi-plate spatial origins; inventory and settings still checked")
        package = Package(archive)
        resources, items = package.load(root)
        instance_counts = Counter()
        found = Counter()
        tol = expect.get("tolerance_mm", .05)
        for oid, transform, printable in items:
            instance = instance_counts[oid]
            instance_counts[oid] += 1
            if not printable:
                continue
            node = objects.get(oid, ET.Element("object"))
            saved = metadata(node)
            name = saved.get("name") or resources[oid]["name"] or f"object_{oid}"
            plate = mapping.get((oid, instance))
            candidates = [p for p in expect.get("parts", []) if
                          (p.get("name") == name if "name" in p else re.match(re.escape(p["id"]) + r"(?=$|[^A-Za-z0-9])", name))]
            expected = candidates[0] if len(candidates) == 1 else None
            if expect.get("parts") and not expected:
                report.add("error", "unexpected_object", "Object has no unique expected ID match", name=name, object_id=oid, instance=instance)
            if expected:
                found[expected["id"]] += 1
            parts = node.findall("part")
            excluded = {p.attrib["id"] for p in parts if p.get("subtype", "normal_part") != "normal_part"}
            bounds, leaves = empty_bounds(), []
            for vertices, combined in package.geometry(root, oid, transform, excluded):
                leaves.append(combined[:9])
                for i in range(0, len(vertices), 3):
                    extend(bounds, point(vertices[i:i+3], combined))
            if not leaves:
                report.add("error", "empty_object", "No printable mesh vertices", name=name)
                continue
            dims = [bounds[i+3] - bounds[i] for i in range(3)]
            row = {"id": expected["id"] if expected else None, "name": name, "object_id": oid,
                   "instance": instance, "plate": plate, "bounds_mm": bounds, "dimensions_mm": dims,
                   "mesh_leaves": len(leaves), "linear_transforms": leaves}
            report.data["project"]["objects"].append(row)
            if plates and plate is None:
                report.add("incomplete", "unassigned_instance", "Printable instance has no plate mapping", name=name, instance=instance)
            if expected:
                if "dimensions_mm" in expected and any(abs(a-b) > tol for a, b in zip(dims, expected["dimensions_mm"])):
                    report.add("error", "dimensions_mismatch", "Saved oriented dimensions differ", name=name, actual=dims, expected=expected["dimensions_mm"])
                if "height_mm" in expected and abs(dims[2]-expected["height_mm"]) > tol:
                    report.add("error", "height_mismatch", "Saved build height differs", name=name, actual=dims[2], expected=expected["height_mm"])
                if "mesh_z_direction" in expected:
                    for m in leaves:
                        size = math.sqrt(sum(v*v for v in m[6:9]))
                        if size < 1e-12 or any(abs(m[6+i]/size-v) > 1e-5 for i, v in enumerate(expected["mesh_z_direction"])):
                            report.add("error", "orientation_mismatch", "Embedded mesh Z direction differs; yaw alone is allowed", name=name)
                if "linear_transform" in expected and any(any(abs(a-b) > 1e-5 for a, b in zip(m, expected["linear_transform"])) for m in leaves):
                    report.add("error", "orientation_mismatch", "Saved mesh-to-build linear transform differs", name=name)
                effective = dict(config)
                if plate is not None:
                    effective.update(metadata(plates[plate-1]))
                effective.update(saved)
                wanted = expected.get("settings", {})
                compare_settings(effective, wanted, report, name)
                for part in parts:
                    pmeta = metadata(part)
                    for key in wanted:
                        if key in pmeta and str(pmeta[key]) != str(effective.get(key)):
                            report.add("incomplete", "part_override", "A per-part override needs separate review", name=name, parameter=key, actual=pmeta[key])
            if len(plates) == 1 and plate == 1:
                bed_check(bounds, expect, report, name)
        if expect.get("parts"):
            for part in expect["parts"]:
                if found[part["id"]] != part.get("quantity", 1):
                    report.add("error", "part_quantity", "Unexpected printable instance quantity", part=part["id"], expected=part.get("quantity", 1), actual=found[part["id"]])
            report.data["checks"].append("expected_print_objects_and_quantities")
        else:
            report.add("incomplete", "expectations_missing", "Inventory only: no independent expected part list supplied")
        compare_settings(config, expect.get("settings", {}), report, "project")
        for plate in plates:
            for key in expect.get("settings", {}):
                if key in metadata(plate) and str(metadata(plate)[key]) != str(config.get(key)):
                    report.add("incomplete", "plate_override", "Project setting has a different plate override", parameter=key)
        embedded = sorted(n for n in archive.namelist() if re.fullmatch(r"Metadata/plate_\d+\.gcode", n))
        report.data["project"]["embedded_gcode"] = embedded
        report.data["checks"].append("saved_mesh_geometry_and_requested_settings")
        return embedded


def bed_check(bounds, expect, report, target):
    tol = expect.get("tolerance_mm", .05)
    bed = expect.get("bed_mm")
    if bed and (bounds[0] < bed[0]-tol or bounds[1] < bed[1]-tol or
                bounds[3] > bed[2]+tol or bounds[4] > bed[3]+tol):
        report.add("error", "outside_bed", "Geometry/path envelope exceeds the expected rectangular bed", target=target, bounds_mm=bounds)
    if bounds[2] < -tol or ("max_height_mm" in expect and bounds[5] > expect["max_height_mm"]+tol):
        report.add("error", "outside_height", "Geometry/path envelope exceeds allowed Z", target=target, bounds_mm=bounds)


def arc_points(start, end, args, clockwise, absolute_center, tolerance):
    if abs(start[2]-end[2]) > 1e-6:
        raise NotImplementedError("Helical arcs are not supported")
    if "R" in args:
        radius = abs(args["R"])
        dx, dy = end[0]-start[0], end[1]-start[1]
        chord = math.hypot(dx, dy)
        if chord < 1e-9 or chord > 2*radius+1e-7:
            raise ValueError("Invalid radius-form arc")
        side = (-1 if clockwise else 1) * (-1 if args["R"] < 0 else 1)
        offset = side * math.sqrt(max(0, radius*radius - chord*chord/4))
        cx, cy = (start[0]+end[0])/2 - dy/chord*offset, (start[1]+end[1])/2 + dx/chord*offset
    else:
        if "I" not in args and "J" not in args:
            raise ValueError("Arc is missing its center")
        cx = args.get("I", start[0]) if absolute_center else start[0]+args.get("I", 0)
        cy = args.get("J", start[1]) if absolute_center else start[1]+args.get("J", 0)
        radius = math.hypot(start[0]-cx, start[1]-cy)
        if radius <= 1e-9 or abs(math.hypot(end[0]-cx, end[1]-cy)-radius) > max(.02, radius*1e-3):
            raise ValueError("Inconsistent arc radii")
    a, b = math.atan2(start[1]-cy, start[0]-cx), math.atan2(end[1]-cy, end[0]-cx)
    sweep = -((a-b) % math.tau) if clockwise else (b-a) % math.tau
    if abs(sweep) < 1e-10:
        sweep = -math.tau if clockwise else math.tau
    angle = 2*math.acos(max(-1., min(1., 1-tolerance/radius)))
    steps = max(1, math.ceil(abs(sweep)/max(angle, 1e-6)))
    if steps > 100000:
        raise ValueError("Arc exceeds subdivision limit")
    return [start] + [(cx+radius*math.cos(a+sweep*i/steps), cy+radius*math.sin(a+sweep*i/steps), start[2]) for i in range(1, steps)] + [end]


def segments(stream, report, arc_tolerance=.02):
    """Yield deposited paths only after slicer feature annotations (not purge)."""
    xyz, e, absolute, relative_e = (0., 0., 0.), 0., True, False
    feature, width, height, plane, absolute_center = "Custom", None, None, "G17", False
    annotated = False
    unknown = Counter()
    for line_number, raw in enumerate(stream, 1):
        line = raw.strip()
        if line.startswith(("; FEATURE:", ";TYPE:")):
            feature = line.split(":", 1)[1].strip()
            annotated = True
        if line.startswith(("; LINE_WIDTH:", ";WIDTH:")):
            width = float(line.split(":", 1)[1])
        if line.startswith(("; LAYER_HEIGHT:", ";HEIGHT:")):
            height = float(line.split(":", 1)[1])
        if width is not None and (not math.isfinite(width) or width <= 0):
            raise ValueError("Invalid annotated extrusion width")
        if height is not None and (not math.isfinite(height) or height <= 0):
            raise ValueError("Invalid annotated layer height")
        code = re.sub(r"\([^)]*\)", "", line.split(";", 1)[0]).strip()
        if not code:
            continue
        code = re.sub(r"^N\d+\s*", "", code, flags=re.I)
        code = re.sub(r"\*\d+\s*$", "", code)
        words = WORD.findall(code)
        if not words:
            continue
        command = words[0][0].upper() + words[0][1]
        args = {k.upper(): float(v) for k, v in words[1:]}
        if not all(math.isfinite(x) for x in args.values()):
            raise ValueError("Non-finite G-code coordinate")
        if command == "G90": absolute = True
        elif command == "G91": absolute = False
        elif command == "M82": relative_e = False
        elif command == "M83": relative_e = True
        elif command == "G90.1": absolute_center = True
        elif command == "G91.1": absolute_center = False
        elif command in ("G17", "G18", "G19"): plane = command
        elif command == "G20": raise NotImplementedError("Inch G-code is unsupported in V1")
        elif command == "G92":
            if any(k in args for k in "XYZ"):
                unknown["G92 XYZ coordinate reset"] += 1
            xyz = tuple(args.get(k, xyz[i]) for i, k in enumerate("XYZ"))
            e = args.get("E", e)
        elif command == "G28":
            if annotated and feature.lower() != "custom": unknown[command] += 1
            xyz = tuple(0. if not args or k in args else xyz[i] for i, k in enumerate("XYZ"))
        elif command in ("G0", "G00", "G1", "G01", "G2", "G02", "G3", "G03"):
            if WORD.sub("", code).strip() or len(args) != len(words)-1:
                unknown["Malformed or ambiguous motion words"] += 1
            end = tuple(args.get(k, xyz[i]) if absolute else xyz[i]+args.get(k, 0.) for i, k in enumerate("XYZ"))
            extrusion = args.get("E", 0.) if relative_e else args.get("E", e)-e
            e = e+args["E"] if relative_e and "E" in args else args.get("E", e)
            arc = command in ("G2", "G02", "G3", "G03")
            if annotated and feature.lower() != "custom" and extrusion > 1e-8 and (arc or math.dist(xyz, end) > 1e-8):
                try:
                    if arc and plane != "G17":
                        raise NotImplementedError("Only XY-plane arcs are supported")
                    pts = arc_points(xyz, end, args, command in ("G2", "G02"), absolute_center, arc_tolerance) if arc else [xyz, end]
                    for a, b in zip(pts, pts[1:]):
                        yield a, b, feature, width, height, line_number, arc
                except (ValueError, NotImplementedError) as exc:
                    unknown[str(exc)] += 1
            xyz = end
        elif command.startswith("G") and command not in ("G4", "G04", "G21"):
            # Unknown coordinate-changing modes must not silently pass.
            unknown[command] += 1
    if not annotated:
        report.add("incomplete", "feature_annotations_missing", "No supported slicer feature annotations; deposited paths cannot be classified")
    if unknown:
        report.add("incomplete", "unsupported_gcode", "Some commands/arcs were not interpreted; path checks are incomplete", commands=dict(unknown))


def intersects(a, b, bounds):
    lo, hi = 0., 1.
    for i in range(3):
        d = b[i]-a[i]
        if abs(d) < 1e-12:
            if not bounds[i] <= a[i] <= bounds[i+3]: return False
        else:
            t0, t1 = sorted(((bounds[i]-a[i])/d, (bounds[i+3]-a[i])/d))
            lo, hi = max(lo, t0), min(hi, t1)
            if lo > hi: return False
    return True


def inspect_paths(stream, expect, report, source, selected_z=None):
    bounds, counts, layers, drawn = empty_bounds(), Counter(), set(), []
    regions = expect.get("protected_regions", [])
    hits, covered = Counter(), Counter()
    examples = defaultdict(list)
    missing_width, missing_height = False, False
    for a, b, feature, width, height, line, arc in segments(stream, report):
        counts[feature] += 1
        layers.add(round(b[2], 5))
        radius = (width or 0.)/2 + (.02 if arc else 0.)
        missing_width |= width is None
        missing_height |= height is None
        bottom = height or 0.
        for p in (a, b):
            extend(bounds, (p[0]-radius, p[1]-radius, p[2]-bottom))
            extend(bounds, (p[0]+radius, p[1]+radius, p[2]))
        for region in regions:
            rb = region["bounds_mm"]
            # Require some model path in the region's XY/Z neighborhood to catch
            # a region accidentally defined in CAD rather than plate coordinates.
            neighborhood = [rb[i]-5 for i in range(3)] + [rb[i+3]+5 for i in range(3)]
            if "support" not in feature.lower() and intersects(a, b, neighborhood):
                covered[region["id"]] += 1
            if any(s.lower() in feature.lower() for s in region["features"]):
                expanded = [rb[0]-radius, rb[1]-radius, rb[2], rb[3]+radius, rb[4]+radius, rb[5]+bottom]
                if intersects(a, b, expanded):
                    hits[region["id"]] += 1
                    if len(examples[region["id"]]) < 3:
                        examples[region["id"]].append({"line": line, "z_mm": b[2], "feature": feature})
        if selected_z is not None and abs(b[2]-selected_z) <= .001:
            drawn.append((a, b, feature, width or .4))
    summary = {"source": source, "deposited_segments": sum(counts.values()), "features": dict(counts),
               "z_planes": len(layers), "bead_envelope_bounds_mm": bounds if counts else None,
               "arc_chord_error_mm": .02}
    report.data.setdefault("gcode", []).append(summary)
    if not counts:
        report.add("incomplete", "no_deposited_paths", "No classified deposition paths were found", source=source)
    else:
        bed_check(bounds, expect, report, source)
    if missing_width:
        report.add("incomplete", "width_unknown", "Some bead widths are unknown; reported envelope is partial", source=source)
    if missing_height and regions:
        report.add("incomplete", "height_unknown", "Some bead heights are unknown; protected-volume check is partial", source=source)
    for region in regions:
        rid = region["id"]
        if hits[rid]:
            report.add("error", "protected_region_hit", "Deposited bead envelope intersects a protected region", region=rid, segments=hits[rid], examples=examples[rid])
        elif not covered[rid]:
            report.add("incomplete", "region_unlocated", "No model paths near the protected region; verify its plate coordinates", region=rid)
    report.data["checks"].append("annotated_deposition_envelope_and_requested_regions")
    return drawn


@contextmanager
def text_gcode(path, member=None):
    if member:
        with zipfile.ZipFile(path) as archive, archive.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8") as stream:
            yield stream
    else:
        with Path(path).open(encoding="utf-8") as stream:
            yield stream


def draw_svg(segments_, z, output):
    if not segments_:
        raise ValueError("No deposited paths at the requested Z; use an actual path height")
    xs = [p[0] for a, b, _, _ in segments_ for p in (a, b)]
    ys = [p[1] for a, b, _, _ in segments_ for p in (a, b)]
    x0, y0, x1, y1 = min(xs)-2, min(ys)-2, max(xs)+2, max(ys)+2
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}">',
             f'<title>Actual deposited paths at Z={z:g} mm</title>',
             f'<g transform="translate(0 {y0+y1}) scale(1 -1)" fill="none" stroke-linecap="round">']
    for a, b, feature, width in segments_:
        color = "#d26b22" if "support" in feature.lower() else "#24588a"
        lines.append(f'<path d="M{a[0]:.4f},{a[1]:.4f} L{b[0]:.4f},{b[1]:.4f}" stroke="{color}" stroke-width="{width:g}"><title>{html.escape(feature)}</title></path>')
    lines.append('</g></svg>')
    Path(output).write_text("\n".join(lines), encoding="utf-8")


def emit(report, args):
    status = report.finish()
    if args.report:
        try:
            Path(args.report).write_text(json.dumps(report.data, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        except OSError as exc:
            report.add("incomplete", "report_write_error", str(exc))
            status = report.finish()
    if args.json:
        result = report.data
    else:
        result = {k: report.data[k] for k in ("tool", "version", "status", "counts")}
        result["findings"] = report.data["findings"][:12]
        result["findings_omitted"] = max(0, len(report.data["findings"])-12)
        result["report"] = str(args.report) if args.report else None
        if "project" in report.data:
            result["objects"] = len(report.data["project"]["objects"])
            result["plates"] = report.data["project"]["plates"]
        result["gcode_files"] = len(report.data.get("gcode", []))
    print(json.dumps(result, allow_nan=False))
    return status


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    subs = parser.add_subparsers(dest="command", required=True)
    check = subs.add_parser("check", help="Check a saved 3MF or annotated text G-code")
    layers = subs.add_parser("layers", help="Draw actual paths at one Z height as SVG")
    for p in (check, layers):
        p.add_argument("source", type=Path)
        p.add_argument("--json", action="store_true", help="Print full JSON instead of a bounded summary")
        p.add_argument("--report", type=Path, help="Write full JSON report")
    check.add_argument("--expect", type=Path)
    check.add_argument("--gcode", type=Path, help="Explicit external G-code; never auto-discovers neighboring files")
    layers.add_argument("--z", type=float, required=True)
    layers.add_argument("--output", type=Path, required=True)
    layers.add_argument("--member", help="G-code member path inside a 3MF")
    args = parser.parse_args(argv)
    report = Report(args.source)
    try:
        # Prevent report/SVG paths from overwriting any input or each other.
        inputs = {args.source.resolve()}
        for name in ("expect", "gcode"):
            if getattr(args, name, None): inputs.add(getattr(args, name).resolve())
        outputs = [p.resolve() for p in (args.report, getattr(args, "output", None)) if p]
        if inputs.intersection(outputs) or len(set(outputs)) != len(outputs):
            args.report = None
            raise ValueError("Output paths must be distinct from all inputs and each other")
        report.data["source_sha256"] = sha256(args.source)
        if args.command == "layers":
            if not math.isfinite(args.z): raise ValueError("Z must be finite")
            if args.source.suffix.lower() == ".3mf" and not args.member:
                raise ValueError("Use --member for a G-code file embedded in a 3MF")
            with text_gcode(args.source, args.member) as stream:
                drawn = inspect_paths(stream, {}, report, str(args.source), selected_z=args.z)
            draw_svg(drawn, args.z, args.output)
            report.data["svg"] = str(args.output)
        else:
            expect = expect_file(args.expect)
            if args.expect:
                report.data["expectation_sha256"] = sha256(args.expect)
                report.data["scope"] = expect["scope"]
            is_project = args.source.suffix.lower() == ".3mf"
            embedded = inspect_project(args.source, expect, report) if is_project else []
            if not is_project:
                if expect.get("parts") or expect.get("settings") or expect.get("plates"):
                    report.add("incomplete", "project_checks_unavailable", "G-code alone cannot verify requested project inventory, orientation or settings")
                with text_gcode(args.source) as stream:
                    inspect_paths(stream, expect, report, str(args.source))
            elif args.gcode:
                digest = sha256(args.gcode)
                report.data["external_gcode_sha256"] = digest
                if digest != expect.get("gcode_sha256"):
                    report.add("incomplete", "external_gcode_unbound", "External G-code is not pinned by the expectation; do not assume it matches this project")
                report.data["limits"].append("A pinned external G-code hash records selection, not proof of slicing provenance.")
                with text_gcode(args.gcode) as stream:
                    inspect_paths(stream, expect, report, str(args.gcode))
            elif len(embedded) == 1:
                with text_gcode(args.source, embedded[0]) as stream:
                    inspect_paths(stream, expect, report, embedded[0])
            elif len(embedded) > 1:
                report.add("incomplete", "multiple_gcode_plates", "V1 spatial G-code checks require one explicitly selected plate")
            elif expect.get("require_gcode") or expect.get("protected_regions") or expect.get("bed_mm"):
                report.add("incomplete", "gcode_missing", "No embedded G-code: supports/brim/path coverage cannot be checked")
    except NotImplementedError as exc:
        report.add("incomplete", "unsupported_input", str(exc))
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError, ET.ParseError, zipfile.BadZipFile, UnicodeError, RecursionError) as exc:
        report.add("incomplete", "input_error", str(exc))
    return emit(report, args)


if __name__ == "__main__":
    sys.exit(main())
