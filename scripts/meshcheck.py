#!/usr/bin/env python3
"""Inspect ASCII/binary STL topology and dimensions. Python 3.10+, no dependencies."""
from array import array
from collections import Counter
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

VERSION = "1.1.0"


def triangles(path):
    """Yield nine coordinates per triangle; STL coordinates have no declared unit."""
    path = Path(path)
    size = path.stat().st_size
    with path.open("rb") as stream:
        header = stream.read(84)
        count = struct.unpack_from("<I", header, 80)[0] if len(header) == 84 else -1
        if count >= 0 and size == 84 + count * 50:
            for _ in range(count):
                yield struct.unpack("<12fH", stream.read(50))[3:12]
            return
    # An exact binary-size match takes precedence over a misleading 'solid' header.
    facet, vertices, ended = False, [], False
    with path.open(encoding="ascii") as stream:
        first = stream.readline().strip()
        if not first.lower().startswith("solid"):
            raise ValueError("Not a supported STL (possibly truncated binary STL)")
        for line in stream:
            text = line.strip().lower()
            if not text:
                continue
            if text.startswith("facet normal"):
                if facet: raise ValueError("Nested STL facet")
                facet, vertices = True, []
            elif text.startswith("vertex "):
                values = text.split()[1:]
                if not facet or len(values) != 3: raise ValueError("Invalid STL vertex")
                vertices.extend(float(v) for v in values)
            elif text == "endfacet":
                if not facet or len(vertices) != 9: raise ValueError("STL facet needs three vertices")
                yield tuple(vertices)
                facet = False
            elif text.startswith("endsolid"):
                ended = True
            elif text.startswith("solid"):
                ended = False  # Multiple ASCII solids are supported.
            elif text not in ("outer loop", "endloop"):
                raise ValueError("Unsupported ASCII STL line")
        if facet or not ended:
            raise ValueError("Incomplete ASCII STL")


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def transformed(tri, rotation=(0, 0, 0)):
    """Apply Rx, then Ry, then Rz in degrees, about the shared origin."""
    rx, ry, rz = (math.radians(float(v)) for v in rotation)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    out = []
    for i in (0, 3, 6):
        x, y, z = tri[i:i+3]
        y, z = cx*y-sx*z, sx*y+cx*z
        x, z = cy*x+sy*z, -sy*x+cy*z
        x, y = cz*x-sz*y, sz*x+cz*y
        out.extend((x, y, z))
    return tuple(out)


def write_binary(path, records):
    """Write a new binary STL with normals recomputed from winding."""
    count = 0
    with Path(path).open("wb") as stream:
        stream.write(b"STL coordinates in mm; fusion-bambu-print".ljust(80, b" ") + struct.pack("<I", 0))
        for tri in records:
            if len(tri) != 9 or not all(math.isfinite(v) for v in tri):
                raise ValueError("Non-finite or malformed triangle")
            a, b, c = tri[:3], tri[3:6], tri[6:9]
            n = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
            length = math.sqrt(sum(v*v for v in n))
            normal = tuple(v/length for v in n) if length else (0, 0, 0)
            stream.write(struct.pack("<12fH", *normal, *tri, 0))
            count += 1
        stream.seek(80)
        stream.write(struct.pack("<I", count))
    return count


def clipped_area_xy(points, low_z, high_z):
    """Projected polygon area inside a Z band, not a triangle-count proxy."""
    polygon = list(points)
    for plane, above in ((low_z, True), (high_z, False)):
        result = []
        if not polygon: return 0.
        a = polygon[-1]
        for b in polygon:
            inside_a = a[2] >= plane if above else a[2] <= plane
            inside_b = b[2] >= plane if above else b[2] <= plane
            if inside_a != inside_b:
                fraction = (plane-a[2])/(b[2]-a[2])
                result.append(tuple(a[i]+fraction*(b[i]-a[i]) for i in range(3)))
            if inside_b: result.append(b)
            a = b
        polygon = result
    # Shift to a local origin before the shoelace sum to limit cancellation.
    if len(polygon) < 3: return 0.
    origin = polygon[0]
    xy = [(p[0]-origin[0], p[1]-origin[1]) for p in polygon]
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(xy, xy[1:]+xy[:1])))/2


def inspect(path, *, scale=1., weld_mm=0.00001, expected_components=1,
            dimensions_mm=None, tolerance_mm=.05, bed_z_mm=0., contact_band_mm=.02,
            min_contact_mm2=1.):
    if not all(math.isfinite(v) for v in (scale, weld_mm, tolerance_mm)) or scale <= 0 or weld_mm < 0 or tolerance_mm <= 0:
        raise ValueError("scale/tolerance must be positive; weld tolerance must be nonnegative")
    if not all(math.isfinite(v) for v in (bed_z_mm, contact_band_mm, min_contact_mm2)) or contact_band_mm <= 0 or min_contact_mm2 < 0:
        raise ValueError("Bed Z must be finite; contact band positive; minimum contact nonnegative")
    if type(expected_components) is not int or expected_components < 1:
        raise ValueError("expected_components must be a positive integer")
    vertices, edges, parents, ranks, faces = {}, {}, array("I"), bytearray(), array("I")
    lo, hi = [math.inf]*3, [-math.inf]*3
    degenerates, volume, digest = 0, 0., hashlib.sha256()
    per_face_volumes = array("d")
    near_bed_area, contact_faces = 0., 0
    flat_cosine = math.cos(math.radians(5))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    def union(a, b):
        a, b = find(a), find(b)
        if a == b: return
        if ranks[a] < ranks[b]: a, b = b, a
        parents[b] = a
        if ranks[a] == ranks[b]: ranks[a] += 1

    reference = None
    for face_id, raw in enumerate(triangles(path)):
        if not all(math.isfinite(v) for v in raw): raise ValueError("Non-finite STL coordinate")
        tri = tuple(v*scale for v in raw)
        if not all(math.isfinite(v) for v in tri): raise ValueError("Coordinate overflow after scale")
        pts = [tri[i:i+3] for i in (0, 3, 6)]
        ids = []
        for p in pts:
            key = tuple(round(v/weld_mm) for v in p) if weld_mm else p
            if key not in vertices: vertices[key] = len(vertices)
            ids.append(vertices[key])
            for axis, value in enumerate(p):
                lo[axis], hi[axis] = min(lo[axis], value), max(hi[axis], value)
        parents.append(face_id); ranks.append(0); faces.extend(ids)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            key = (min(a, b), max(a, b))
            if key in edges:
                item = edges[key]; item[0] += 1; item[1] += 1 if a < b else -1
                union(face_id, item[2])
            else:
                edges[key] = [1, 1 if a < b else -1, face_id]
        a, b, c = pts
        n = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
        normal_length = math.sqrt(sum(v*v for v in n))
        if len(set(ids)) < 3 or normal_length < 1e-12: degenerates += 1
        if normal_length > 0 and n[2]/normal_length <= -flat_cosine:
            area = clipped_area_xy(pts, bed_z_mm-contact_band_mm, bed_z_mm+contact_band_mm)
            near_bed_area += area
            if area > 0: contact_faces += 1
        # A nearby common reference reduces cancellation for translated models.
        if reference is None: reference = a
        aa, bb, cc = [tuple(p[i]-reference[i] for i in range(3)) for p in pts]
        term = sum(aa[i]*cross(bb, cc)[i] for i in range(3))/6
        volume += term; per_face_volumes.append(term)
    count = len(parents)
    if not count: raise ValueError("STL contains no triangles")
    components, component_volumes, owners, pinches = Counter(), Counter(), {}, set()
    for i in range(count):
        root = find(i); components[root] += 1; component_volumes[root] += per_face_volumes[i]
        for vertex in faces[3*i:3*i+3]:
            if vertex in owners and owners[vertex] != root: pinches.add(vertex)
            owners[vertex] = root
    boundary = sum(v[0] == 1 for v in edges.values())
    nonmanifold = sum(v[0] > 2 for v in edges.values())
    inconsistent = sum(v[0] == 2 and v[1] != 0 for v in edges.values())
    dims = [hi[i]-lo[i] for i in range(3)]
    findings = []
    for code, value in [("boundary_edges", boundary), ("nonmanifold_edges", nonmanifold),
                        ("inconsistent_winding_edges", inconsistent), ("degenerate_triangles", degenerates),
                        ("shells_touching_at_vertices", len(pinches))]:
        if value: findings.append({"severity": "error", "code": code, "count": value})
    if len(components) != expected_components:
        findings.append({"severity": "error", "code": "component_count", "expected": expected_components, "actual": len(components)})
    if volume <= 0:
        findings.append({"severity": "error", "code": "nonpositive_signed_volume", "actual_mm3": volume})
    if dimensions_mm is not None:
        if len(dimensions_mm) != 3 or not all(math.isfinite(v) and v > 0 for v in dimensions_mm):
            raise ValueError("Expected dimensions must contain three positive finite millimeter values")
        if any(abs(a-b) > tolerance_mm for a, b in zip(dims, dimensions_mm)):
            findings.append({"severity": "error", "code": "dimensions_mismatch", "expected_mm": list(dimensions_mm), "actual_mm": dims})
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024*1024), b""): digest.update(block)
    warnings = []
    rectangle_area = dims[0]*dims[1]
    fraction = near_bed_area/rectangle_area if rectangle_area > 0 else 0.
    reliable_normals = not boundary and not nonmanifold and not inconsistent and not degenerates and volume > 0
    contact_status = "measured" if reliable_normals else "unavailable"
    if not reliable_normals:
        warnings.append({"code": "contact_unverified_topology", "message": "Contact estimate needs a closed, consistently wound mesh; review topology findings first"})
    else:
        if lo[2] > bed_z_mm+contact_band_mm:
            warnings.append({"code": "above_bed", "gap_mm": lo[2]-bed_z_mm})
        elif lo[2] < bed_z_mm-contact_band_mm:
            warnings.append({"code": "below_bed", "depth_mm": bed_z_mm-lo[2]})
        if near_bed_area <= 1e-9:
            warnings.append({"code": "no_flat_bed_contact", "message": "No near-horizontal downward face area found at this bed plane; inspect orientation, intended supports and sliced first layer"})
        elif near_bed_area < min_contact_mm2:
            warnings.append({"code": "small_bed_contact", "area_mm2": near_bed_area, "threshold_mm2": min_contact_mm2})
        if near_bed_area > 0 and fraction < .05:
            warnings.append({"code": "low_contact_fraction", "fraction_of_xy_rectangle": fraction, "advisory_threshold": .05})
        if fraction > 1.00001:
            warnings.append({"code": "overlapping_contact_suspected", "message": "Summed projected face areas exceed the XY rectangle; this is not a union-area measurement"})
    bed_contact = {"status": contact_status, "bed_z_mm": bed_z_mm, "half_band_mm": contact_band_mm,
                   "max_face_tilt_deg": 5., "projected_face_area_sum_mm2": near_bed_area if reliable_normals else None,
                   "contributing_triangles": contact_faces if reliable_normals else None,
                   "xy_rectangle_mm2": rectangle_area, "fraction_of_xy_rectangle": fraction if reliable_normals else None,
                   "min_contact_advisory_mm2": min_contact_mm2,
                   "method": "Clip downward faces within 5 deg of horizontal to bed Z +/- half_band, sum XY projected areas; no automatic drop, overlap union, supports, brim or first-layer simulation"}
    return {"file": str(path), "sha256": digest.hexdigest(), "status": "fail" if findings else "pass",
            "triangles": count, "welded_vertices": len(vertices), "bounds_mm": lo+hi, "dimensions_mm": dims,
            "closed_edge_manifold": not boundary and not nonmanifold, "boundary_edges": boundary,
            "nonmanifold_edges": nonmanifold, "inconsistent_winding_edges": inconsistent,
            "degenerate_triangles": degenerates, "edge_connected_shells": len(components),
            "shells": [{"triangles": components[k], "signed_volume_mm3": component_volumes[k]} for k in components],
            "signed_volume_mm3": volume, "weld_grid_mm": weld_mm, "coordinate_scale_to_mm": scale,
            "bed_contact": bed_contact, "warnings": warnings,
            "findings": findings, "limits": "STL units are assumed via scale. Edge-connected surface shells are not physical body counts. Grid welding can merge details or miss close vertices across cell boundaries. Contact is geometric area near an explicit plane, not adhesion or actual first-layer coverage. No self-intersection, vertex-link manifold, wall-thickness, nesting, clearance or strength proof."}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sources", nargs="+", type=Path)
    p.add_argument("--scale", type=float, default=1., help="Source-coordinate to mm multiplier; not auto-detected")
    p.add_argument("--weld-mm", type=float, default=.00001)
    p.add_argument("--expected-components", type=int, default=1, help="Expected edge-connected surface shells per file")
    p.add_argument("--dimensions-mm", type=float, nargs=3)
    p.add_argument("--tolerance-mm", type=float, default=.05)
    p.add_argument("--bed-z-mm", type=float, default=0., help="Explicit bed plane in mm; never moves the model")
    p.add_argument("--contact-band-mm", type=float, default=.02, help="Half-width of near-bed measurement band")
    p.add_argument("--min-contact-mm2", type=float, default=1., help="Advisory threshold, not an adhesion guarantee")
    p.add_argument("--report", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    rows, incomplete = [], False
    if args.report and args.report.resolve() in {s.resolve() for s in args.sources}:
        print(json.dumps({"tool": "meshcheck", "status": "incomplete", "error": "Report must not overwrite an input"})); return 2
    for source in args.sources:
        try:
            rows.append(inspect(source, scale=args.scale, weld_mm=args.weld_mm,
                                expected_components=args.expected_components, dimensions_mm=args.dimensions_mm,
                                tolerance_mm=args.tolerance_mm, bed_z_mm=args.bed_z_mm,
                                contact_band_mm=args.contact_band_mm, min_contact_mm2=args.min_contact_mm2))
        except (OSError, ValueError, OverflowError, struct.error) as exc:
            incomplete = True
            rows.append({"file": str(source), "status": "incomplete", "error": str(exc)})
    failed = any(r["status"] == "fail" for r in rows)
    report = {"tool": "meshcheck", "version": VERSION, "status": "fail" if failed else "incomplete" if incomplete else "pass", "meshes": rows}
    if args.report:
        try: args.report.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        except OSError as exc:
            report["report_error"] = str(exc); incomplete = True
            if not failed: report["status"] = "incomplete"
    summary = {"tool": "meshcheck", "version": VERSION, "status": report["status"], "files": len(rows),
               "results": [{k: row[k] for k in ("file", "status", "dimensions_mm", "edge_connected_shells", "bed_contact", "warnings", "findings", "error") if k in row} for row in rows[:12]],
               "results_omitted": max(0, len(rows)-12), "report": str(args.report) if args.report else None}
    if "report_error" in report: summary["report_error"] = report["report_error"]
    print(json.dumps(report if args.json else summary, allow_nan=False))
    return 1 if failed else 2 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
