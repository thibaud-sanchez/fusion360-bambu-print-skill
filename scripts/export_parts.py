"""Export explicitly bound solid bodies to oriented mm STL files inside Fusion.

Run export_plan(plan_path, output_dir) through the existing Fusion script tool.
Never saves, activates, closes, renames or changes a source design.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
import os
import runpy
from types import SimpleNamespace

# Load the bundled files explicitly, avoiding stale same-name module imports
# in Fusion's long-lived Python interpreter. Neither file's main block runs.
_SCRIPTS = Path(__file__).resolve().parent
snapshot = SimpleNamespace(**runpy.run_path(str(_SCRIPTS/"fusion_snapshot.py")))
meshcheck = SimpleNamespace(**runpy.run_path(str(_SCRIPTS/"meshcheck.py")))

VERSION = "1.0.0"


def load_plan(path):
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(plan) - {"schema_version", "document", "data_file_id", "parts"} or plan.get("schema_version") != 1:
        raise ValueError("Expected export plan schema_version=1 with documented keys")
    if not isinstance(plan.get("document"), str) or not plan["document"]:
        raise ValueError("An explicit active document name is required")
    if not isinstance(plan.get("parts"), list) or not plan["parts"]:
        raise ValueError("A nonempty parts list is required")
    ids, files = set(), set()
    for p in plan["parts"]:
        if set(p) - {"id", "occurrence", "bodies", "frame", "file", "rotation_xyz_deg", "normalize", "expected_components"}:
            raise ValueError("Unknown export part key")
        pid = p.get("id", "")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*", pid) or pid in ids:
            raise ValueError("Part IDs must be unique simple identifiers")
        ids.add(pid)
        name = p.get("file", pid+".stl")
        if Path(name).name != name or "/" in name or "\\" in name or not name.lower().endswith(".stl") or name.casefold() in files:
            raise ValueError("STL filenames must be unique basenames")
        if not re.match(re.escape(pid)+r"(?=$|[^A-Za-z0-9])", Path(name).stem):
            raise ValueError("STL filename must start with its part ID")
        p["file"] = name; files.add(name.casefold())
        if not isinstance(p.get("occurrence"), str) or not p["occurrence"]:
            raise ValueError("An exact occurrence path or @root is required")
        bodies = p.get("bodies")
        if not isinstance(bodies, list) or not bodies or not all(isinstance(b, str) and b for b in bodies) or len(bodies) != len(set(bodies)):
            raise ValueError("Explicit distinct body names are required")
        if p.get("frame") not in ("component", "assembly"):
            raise ValueError("frame must be component or assembly")
        rotation = p.get("rotation_xyz_deg", [0, 0, 0])
        if len(rotation) != 3 or not all(math.isfinite(float(v)) for v in rotation):
            raise ValueError("rotation_xyz_deg must contain three finite angles")
        if type(p.get("normalize", True)) is not bool:
            raise ValueError("normalize must be boolean")
        if type(p.get("expected_components", 1)) is not int or p.get("expected_components", 1) < 1:
            raise ValueError("expected_components must be a positive integer")
    return plan


def bind_parts(design, plan):
    occurrences = snapshot.occurrence_bindings(design)
    bound = []
    for part in plan["parts"]:
        path = part["occurrence"]
        occurrence = None if path == "@root" else occurrences.get(path)
        if path != "@root" and occurrence is None:
            raise ValueError(f"Occurrence not found: {path}")
        component = occurrence.component if occurrence else design.rootComponent
        matches = {}
        for name in part["bodies"]:
            candidates = [b for b in component.bRepBodies if b.name == name]
            if len(candidates) != 1 or not candidates[0].isSolid:
                raise ValueError(f"Expected one solid body named {name!r} in {path!r}")
            body = candidates[0]
            matches[name] = body
        matrix = list(occurrence.transform2.asArray()) if occurrence and part["frame"] == "assembly" else None
        bound.append((part, matches, matrix))
    return bound


def export_plan(plan_path, output_dir, *, overwrite=False):
    import adsk.fusion as F
    plan_path, output_dir = Path(plan_path), Path(output_dir)
    plan = load_plan(plan_path)
    app, doc, design = snapshot.active_design(plan["document"], plan.get("data_file_id"))
    bound = bind_parts(design, plan)  # Resolve every target before writing any exports.
    before = snapshot.document_record(doc)
    targets = [output_dir/p["file"] for p, _, _ in bound] + [output_dir/"exports.json"]
    if plan_path.resolve() in {p.resolve() for p in targets}:
        raise ValueError("Export output would overwrite the input plan")
    for p in targets:
        if p.exists() and not overwrite: raise FileExistsError(str(p))
        if p.exists() and not p.is_file(): raise ValueError(f"Not a regular output file: {p}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    # Temporary files are outside the source design; keep a multi-body group's
    # relative placement by normalizing all its triangles together, only once.
    with tempfile.TemporaryDirectory(prefix="fusion-export-", dir=output_dir.parent) as temporary:
        temp = Path(temporary)
        for index, (part, bodies, matrix) in enumerate(bound):
            raw_files = []
            for body_index, body in enumerate(bodies.values()):
                raw = temp/f"raw_{index}_{body_index}.stl"
                options = design.exportManager.createSTLExportOptions(body, str(raw))
                if not options: raise RuntimeError("Fusion did not create STL export options")
                options.isBinaryFormat = True
                options.unitType = F.DistanceUnits.MillimeterDistanceUnits
                options.meshRefinement = F.MeshRefinementSettings.MeshRefinementHigh
                if not design.exportManager.execute(options) or not raw.exists():
                    raise RuntimeError("Fusion STL export failed")
                raw_files.append(raw)
            rotation = part.get("rotation_xyz_deg", [0, 0, 0])

            def oriented():
                for raw in raw_files:
                    for tri in meshcheck.triangles(raw):
                        if matrix is not None:
                            # Fusion STL export of a BRepBody proxy can ignore
                            # assembly placement. Always export native bodies,
                            # then apply the recorded occurrence transform here.
                            tri = tuple(sum(matrix[4*r+c]*tri[k+c] for c in range(3)) + 10*matrix[4*r+3]
                                        for k in (0, 3, 6) for r in range(3))
                        yield meshcheck.transformed(tri, rotation)

            lo = [math.inf]*3
            for tri in oriented():
                for i in range(9): lo[i % 3] = min(lo[i % 3], tri[i])
            if not all(math.isfinite(v) for v in lo): raise ValueError("Empty or invalid export")
            offset = lo if part.get("normalize", True) else [0, 0, 0]
            staged = temp/part["file"]
            meshcheck.write_binary(staged, (tuple(v-offset[i % 3] for i, v in enumerate(tri)) for tri in oriented()))
            checked = meshcheck.inspect(staged, expected_components=part.get("expected_components", 1))
            if checked["status"] != "pass":
                raise ValueError(f"Mesh check failed for {part['id']}: {json.dumps(checked['findings'])}")
            rows.append({"id": part["id"], "occurrence": part["occurrence"], "bodies": list(bodies),
                         "frame": part["frame"], "file": part["file"], "rotation_xyz_deg": rotation,
                         "component_to_assembly_fusion_cm": matrix,
                         "shared_translation_mm": [-v for v in offset], "units": "mm",
                         "dimensions_mm": checked["dimensions_mm"], "bounds_mm": checked["bounds_mm"],
                         "sha256": checked["sha256"], "triangles": checked["triangles"],
                         "edge_connected_shells": checked["edge_connected_shells"], "mesh_status": checked["status"]})
        if app.activeDocument != doc or snapshot.document_record(doc) != before:
            raise RuntimeError("Source document/state changed during export; no staged results were published")
        report = {"tool": "export_parts", "version": VERSION, "document": before,
                  "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(), "parts": rows,
                  "limits": "Observed export results, not independent fabrication expectations. STL only; no slicer, fit or strength validation. Per-file publication is atomic; a filesystem error during the final batch can leave a partial delivery."}
        (temp/"exports.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Recheck destinations after potentially slow native export work.
        for p in targets:
            if p.exists() and not overwrite: raise FileExistsError(str(p))
        for p in targets: os.replace(temp/p.name, p)
    print(json.dumps({"tool": "export_parts", "document": doc.name, "parts": [r["id"] for r in rows],
                      "report": str(output_dir/"exports.json"), "source_modified": False}))
    return report


def run(_context: str):
    settings = json.loads(Path(_context).read_text(encoding="utf-8"))
    export_plan(**settings)


if __name__ == "__main__":
    raise SystemExit("Run export_plan inside Fusion through its existing script/MCP route; see references/reusable-tools.md")
