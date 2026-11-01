# Printcheck: saved-project and toolpath checks

Use the bundled [printcheck.py](../scripts/printcheck.py) for repeatable checks of a saved Bambu 3MF and annotated text G-code. It requires **Python 3.10+**, uses only the standard library, and runs outside Fusion. It does not launch applications, slice, edit packages, connect to a printer or install anything.

Execute it rather than loading its source or large G-code files into the conversation. Read this reference when establishing expectations or investigating an incomplete result. Keep the JSON report and optional SVG in the project's verification directory; return the bounded summary to the assistant.

## Commands

Resolve `scripts/printcheck.py` relative to the skill directory, regardless of the project's working directory:

```bash
python3 /path/to/fusion-bambu-print/scripts/printcheck.py check project.3mf \
  --expect fabrication.json --report verification/printcheck.json
```

Default stdout is a short JSON summary with at most 12 findings. `--report` writes the full JSON; its parent directory must exist. `--json` prints the full report instead, useful for `jq` queries. Exit codes: **0** = requested supported checks passed, **1** = discrepancy detected, **2** = incomplete/unsupported input or checks. Errors take precedence over incompleteness in the exit code; inspect all findings. A warning does not by itself fail a check.

```bash
python3 /path/to/fusion-bambu-print/scripts/printcheck.py check project.3mf \
  --expect fabrication.json --json | jq '.findings'

python3 /path/to/fusion-bambu-print/scripts/printcheck.py layers plate_1.gcode \
  --z 10.4 --output verification/layer_10_4.svg
```

Layer SVGs show actual deposited paths at the requested Z (within 0.001 mm), with support paths in orange. Choose an actual toolpath height, not an arbitrary section plane. For an embedded G-code use `layers project.3mf --member Metadata/plate_1.gcode --z ... --output ...`. A drawing is diagnostic evidence, not validation of support coverage.

## Expectation file, version 1

Create or update `verification/fabrication.json` before checking a print delivery:

- Set `schema_version`, delivery `scope`, and the expected part IDs and quantities from the project's parts list.
- Add known dimensions, accepted print orientations, bed limits and agreed settings from the design and manufacturing decisions. Do not derive the reference solely from the file being checked.
- Reuse an existing compatible expectation file when available. Keep it with the corresponding revision's verification outputs.
- Update the affected expectations after an accepted design or settings change. Investigate differences before changing the reference; do not relax requirements merely to obtain a pass.

Run `check project.3mf --expect verification/fabrication.json --report verification/printcheck.json` with the actual paths. Create the output directory if needed and include both paths in the delivery notes.

Without reliable expectations, use an exploratory inventory check and report completeness as unverified. Omit unknown optional values rather than inventing them.

```json
{
  "schema_version": 1,
  "scope": "complete",
  "plates": 1,
  "bed_mm": [0, 0, 180, 180],
  "max_height_mm": 180,
  "tolerance_mm": 0.05,
  "require_gcode": true,
  "settings": {"layer_height": "0.2"},
  "parts": [
    {
      "id": "B1",
      "quantity": 1,
      "dimensions_mm": [40, 30, 8],
      "linear_transform": [1, 0, 0, 0, 1, 0, 0, 0, 1],
      "settings": {"wall_loops": "3", "brim_type": "no_brim"}
    },
    {"id": "A1", "quantity": 2}
  ]
}
```

These numbers describe a hypothetical assembly, not recommended dimensions or universal process values. Replace them with the project requirements. Unknown schema keys are rejected to catch misspelled expectations.

- `scope`: `complete` or `replacements`; the listed print objects are the exact expected delivery in either case. Document reused compatible pieces in the existing assembly guide. A captive multi-body mesh can be one object; the tool does not infer physical body count.
- `parts[].id`: matches an object-name prefix followed by a nonalphanumeric separator or the end of the name. `B1_Base` matches `B1`; `B10_Base` does not. Optional `name` uses an exact saved-object-name match instead. Distinct instances of one object count separately. Unknown objects and incorrect quantities fail.
- `dimensions_mm`: expected oriented X/Y/Z extents, checked using actual transformed mesh vertices. Default tolerance is 0.05 mm. This catches a sideways export but does not prove orientation for symmetric geometry.
- `height_mm` and `mesh_z_direction`: use these instead of fixed X/Y extents when placement may rotate the part around printer Z. `height_mm` checks its build height; `mesh_z_direction` is the expected unit direction of the embedded mesh's positive Z axis in build coordinates (for example `[0, 0, 1]`). Rotation on the bed is allowed; tilting the mesh is not. Do not compare unrotated STL X/Y dimensions to a freely auto-arranged object's X/Y bounds. The direction references the embedded mesh, so retain the original export/orientation record and use height or landmarks to detect a sideways re-export.
- `linear_transform`: optional 9 coefficients, in **3MF row-vector order**, of the complete embedded-mesh-to-build linear transform. All printable mesh leaves must match within 1e-5. Translation is intentionally excluded. This references the embedded mesh frame, not the original CAD frame; a freshly rotated/re-exported mesh can have an identity build transform. Use oriented dimensions and appropriate visual/landmark checks as well.
- `settings`: expected saved project values, using exact Bambu keys. `parts[].settings` checks project + direct plate metadata + object overrides. Requested values unavailable in the saved settings, or conflicting per-part/modifier overrides, require review; the tool does not resolve missing installed presets or modifier volumes. Numeric/string differences such as `3` and `"3"` are accepted; percentages, lists and enums keep their meaning.
- `bed_mm`: usable rectangular XY limits; `max_height_mm`: maximum allowed Z. Geometry checks use vertices; toolpath checks include known bead widths and heights for classified model/support/brim paths. Reserved zones, nonrectangular beds, object separation, adhesion and toolhead clearance remain separate checks.
- `require_gcode`: require deposited-path analysis. With `bed_mm` or protected regions, missing embedded G-code also makes the result incomplete, because mesh bounds cannot establish the support/brim envelope.

## Protected regions

Optionally add axis-aligned forbidden volumes, using **final plate coordinates in millimeters**:

```json
"protected_regions": [
  {
    "id": "bearing-clearance",
    "frame": "plate",
    "plate": 1,
    "bounds_mm": [30, 40, 5, 32, 44, 9],
    "features": ["support"]
  }
]
```

`features` contains case-insensitive substrings of slicer feature labels. A path's estimated bead envelope intersecting a forbidden box fails. Supply a box representing only forbidden space, rather than an entire joint that includes legitimate external supports. The test uses segment/box intersection, including crossings whose endpoints are outside.

V1 intentionally does **not** infer CAD-to-plate transforms for protected regions. Compute them using the actual final placement, verify a known landmark, and record the result. If no model paths are found within a 5 mm neighborhood, the region is unlocated and the result is incomplete. This guard catches many coordinate mistakes but does not prove that a nearby box corresponds to the intended gap. Shapes other than boxes and regions on other plates are unsupported.

## Unsliced or externally sliced projects

An ordinary project may have meshes/settings but no embedded G-code. The tool reports that distinction; it never silently selects an old neighboring `plate_1.gcode`.

An explicit `--gcode plate_1.gcode` can analyze a selected external file. Without its SHA-256 in expectation field `gcode_sha256`, the result is incomplete. Record the hash only after establishing which slicing run produced it and whether the inputs still match. **A matching hash pins the selected file; it does not prove that it was sliced from the current project.** An embedded G-code also needs the normal application reopening/preview checks; its presence alone cannot establish freshness after arbitrary edits.

`check plate_1.gcode` without expectations runs only supported path checks. G-code alone cannot verify an expected project inventory, orientation or object settings; asking for those checks yields an incomplete result.

## Supported scope and limits

- Read-only core/production-extension 3MF mesh/components, including nested transforms, external model parts inside the package, repeated build instances and Bambu plate/object metadata. Millimeter models only. Multi-plate inventory can be checked, but V1 does not resolve multi-plate spatial origins. No mesh repair, topology check or interpretation of arbitrary 3MF extensions.
- Text G-code with Bambu `FEATURE`, `LINE_WIDTH`, `LAYER_HEIGHT` annotations or compatible `TYPE`, `WIDTH`, `HEIGHT` comments. Absolute/relative motion and extrusion, `G92 E`, XY I/J or R arcs are interpreted. Arc subdivision has a 0.02 mm chord tolerance, included conservatively in path envelopes. Feature annotations separate deposition from custom purge/start routines; this is not full firmware simulation.
- Missing feature/width annotations, unsupported commands/arcs, XYZ coordinate resets, inch units or unlocated protected regions prevent a complete result. Binary G-code is unsupported. Width/height envelopes are conservative approximations, not simulated bead shapes.
- Unsupported-island detection, bridge anchoring/sag, full support coverage, layer adhesion, continuous collision detection, retention forces and mechanical durability are **not implemented**. Continue the existing targeted slicer/CAD/physical checks. Do not call `pass` a general printability certificate.

Do not extend the tool to automatically rebuild CAD or reslice on a failed check. Investigate the finding, make the smallest justified correction, and rerun affected checks. This keeps the executable deterministic and inexpensive to use.

## Maintenance

Run the bundled behavioral tests after changing the checker:

```bash
python3 -m unittest discover -s /path/to/fusion-bambu-print/tests -v
```

The fixtures cover missing/duplicate parts, nested rotations, support envelopes, settings precedence, missing/stale external G-code, protected-region crossings/frame mistakes, arcs and unsupported-input behavior. Keep tests generic; historical project data belongs in the project, not this package.

Format references: [3MF Core, matrices and build items](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md), [Bambu project serialization](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp). These describe formats, not a mechanical validation procedure.
