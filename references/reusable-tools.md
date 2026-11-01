# Reusable Fusion and STL tools

Use the bundled helpers for repeated inspection/export work instead of rewriting project-specific API code. Load only the applicable instructions here; run the scripts and keep detailed JSON in the project. These tools do not launch Fusion, create an integration, change mechanism geometry or prepare slicer settings.

| Tool | Where it runs | Purpose |
|---|---|---|
| [fusion_snapshot.py](../scripts/fusion_snapshot.py) | Inside Fusion through its existing script/API route | Read one explicitly named active design; optional current-view PNG |
| [meshcheck.py](../scripts/meshcheck.py) | Ordinary Python 3.10+ | Inspect STL dimensions and topology without changing it |
| [export_parts.py](../scripts/export_parts.py) | Inside Fusion through its existing script/API route | Export selected solid bodies to mm STL with explicit frames/orientations |

Keep these files together with the other scripts when installing the skill. All use the standard library; Fusion tools additionally require the application's in-process `adsk` API. Running the Fusion scripts as shell commands is unsupported. They do not silently activate a different document or close existing documents.

## Snapshot an explicit design

Use `collect(document_name, report_path, data_file_id=None, capture_path=None, width=1200, height=900, overwrite=False)`. Resolve the exact task document from project evidence before calling it. The active document must match; ambiguous names require a cloud data-file ID. A mismatch stops before writing outputs.

For an existing Fusion MCP script executor, use a small wrapper like this, adapting paths and the explicit document name:

```python
import runpy

def run(_context: str):
    tool = runpy.run_path("/path/to/fusion-bambu-print/scripts/fusion_snapshot.py")
    tool["collect"](
        "Bracket — P01",
        "/path/to/project/verification/snapshot.json",
        capture_path="/path/to/project/verification/current_view.png",
    )
```

Use the executor's supported read-only context for this inspection. The tool reads root and nested occurrence bodies, precise bounding boxes, volumes, occurrence matrices, stable IDs detectable from names, user parameters, joint types and timeline health issues. It writes the full JSON and returns a short summary. It does not rename legacy parts; bind them explicitly in the export plan.

Body measurements are in **mm / mm³**, in the root assembly context for occurrence bodies. `transform_fusion_cm` is the raw Fusion row-major 4×4 matrix, with translations in **cm** at indices 3, 7 and 11. Parameter `internal_value` uses Fusion internal units, while its expression and unit are recorded separately. Measurements describe the current pose, not a swept motion envelope.

The optional PNG captures the **current view** without changing visibility, selection, camera or fit. Request/select other views deliberately through the existing application tools when needed; this helper does not invent an exploded view. Existing output filenames are refused unless `overwrite=True` is explicitly supplied. Reading the document does not save it.

## Inspect exported meshes

```bash
python3 /path/to/fusion-bambu-print/scripts/meshcheck.py B1_Base.stl \
  --dimensions-mm 40 30 8 --report verification/mesh.json

python3 /path/to/fusion-bambu-print/scripts/meshcheck.py P1_CaptiveJoint.stl \
  --expected-components 2 --report verification/captive_mesh.json
```

Default stdout is a bounded JSON summary. `--json` prints full results; `--report` writes them locally (parent directory must exist). Exit codes match Printcheck: **0** passed supported checks, **1** discrepancy, **2** incomplete/invalid input. Multiple files can be checked in one call; supplied expectations apply to each file.

The tool accepts binary/ASCII STL, checks finite coordinates, dimensions when supplied, degenerate triangles, boundary/nonmanifold edges, inconsistent winding, signed volume and edge-connected surface shells. Separate shells touching at a shared welded vertex are flagged. It never repairs a mesh.

STL units are **assumed**, not discovered. `--scale` explicitly converts source coordinates to mm (default 1); a cm STL may require 10. Use independent dimensions to detect a wrong scale. Default vertex welding rounds onto a 0.00001 mm grid; `--weld-mm 0` uses exact coordinate equality. Changing the weld grid changes the topology being tested and can conceal tiny gaps or merge close details; do not loosen it merely to obtain a pass.

`--expected-components` counts **edge-connected surface shells**, default 1, not physical parts. Captive assemblies and closed internal cavities can legitimately have multiple shells. Record the expected count from the design. Inner cavity shells can have negative signed volumes while the overall correctly oriented solid remains positive. Results do not establish shell nesting, all vertex-fan conditions, absence of self-intersections, minimum wall thickness, moving clearance, adhesion or strength.

Run this on changed STL exports before slicing; do not recheck unchanged meshes at every conversational turn.

## Export only explicitly selected bodies

Create an independent `export_plan.json` from the part bindings and manufacturing decisions. The plan is separate from Printcheck's `fabrication.json`: it describes how to produce files; the latter describes what the delivery must satisfy.

```json
{
  "schema_version": 1,
  "document": "Bracket — P01",
  "parts": [
    {
      "id": "B1",
      "occurrence": "B1 — Base:1",
      "bodies": ["Base"],
      "frame": "component",
      "file": "B1_Base.stl",
      "rotation_xyz_deg": [0, 0, 0],
      "normalize": true,
      "expected_components": 1
    }
  ]
}
```

- `document` must equal the active design's document name. Optional `data_file_id` binds its cloud identity. The script never switches the active document to make a mismatch disappear.
- `occurrence` is an exact `fullPathName` from the snapshot, including `:1` instance suffixes and `+` for nested paths. Use `@root` for root bodies. `bodies` lists exact native body names in that component; each must identify one solid body. Explicit selection prevents accidentally exporting all instances or hidden reference bodies.
- `frame` is required: `component` uses native local coordinates; `assembly` applies the selected occurrence's complete root-context transform. Fusion may export a body proxy in its local frame, so this tool exports the native body and applies assembly placement to the mm mesh explicitly.
- `rotation_xyz_deg` defaults to `[0,0,0]`: rotate **X, then Y, then Z**, about the shared frame origin. Only export triangles are transformed. `normalize` defaults to true: translate the complete group's minimum X/Y/Z to zero **once**, preserving relative body positions. Use false to retain assembly placement.
- `expected_components` defaults to 1 and is the expected surface-shell count after grouping. All selected bodies share the same rigid print rotation; this tool does not articulate a linkage into a new pose. Choose a suitable source pose explicitly when a captive joint needs one.
- `file` defaults to `<id>.stl` and must be a unique basename beginning with the part ID. Current support is **STL only**. Native/STEP delivery uses the existing Fusion export route when requested.

Invoke through the normal existing Fusion script route:

```python
import runpy

def run(_context: str):
    tool = runpy.run_path("/path/to/fusion-bambu-print/scripts/export_parts.py")
    tool["export_plan"](
        "/path/to/project/export_plan.json",
        "/path/to/project/STL",
    )
```

All bindings and destinations are checked first. STL files are generated in a temporary directory, rotated/grouped and inspected with Meshcheck before publication. The script records source identity, selected bodies, transforms, mm bounds, hashes and mesh results in `exports.json`. These are **observations**, not an automatically generated fabrication reference. Verify known dimensions and critical interfaces against independent requirements.

Existing delivery filenames are refused by default; use a new revision directory or supply `overwrite=True` for an authorized replacement. Final publication is atomic per file, not across the entire batch: a filesystem failure may leave a partial batch without a final report. Inspect outputs before retrying. No source document is saved, renamed, closed or geometrically changed.

Both Fusion scripts also expose `run(context)` accepting the path to a JSON file of their named function arguments. Prefer `runpy.run_path` with a non-`__main__` namespace as above to avoid stale imports or double execution in Fusion's persistent interpreter.

## Maintain and test

```bash
python3 -B -m unittest discover -s /path/to/fusion-bambu-print/tests -v
```

Tests include damaged and multi-shell meshes, orientation/units, wrong-document guards, explicit body bindings, assembly transforms, grouped normalization, failed exports and overwrite protection. Native API behavior also needs a small live test in a disposable task-owned document after relevant API changes; close only that disposable document and restore the previous active document. Never use an unrelated user's model as a fixture.

API references: [Fusion STL export](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExportManager_createSTLExportOptions.htm), [occurrence transform2](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Occurrence_transform2.htm), [Fusion internal units](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/Units_UM.htm). Consult the installed API docstrings when web documentation or version behavior differs.
