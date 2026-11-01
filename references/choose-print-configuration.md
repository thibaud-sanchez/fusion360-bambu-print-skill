# choose-print-configuration

Choose Bambu Studio settings from the part's intended use, optimize them with the capabilities already available, and report the actual outcome. This is a reference within `fusion-bambu-print`, not a separate integration or a standalone skill command.

## Select a mode

Honor an explicitly requested mode. During iterative development without another requested mode, use **Prototype**, or **Prototype --mechanical** for working interfaces. Otherwise infer the main purpose from the request and geometry, state the choice, and proceed when the evidence is sufficient. Functional geometry alone does not justify an additional Functional project during a prototype iteration.

## Keep one current prototype project

During development, deliver one current Prototype project, using Prototype --mechanical when necessary. Aim for one plate with all required parts, allowing for actual brim/support footprints, bed limits and compatible settings. If one plate cannot work reliably, explain the concrete constraint and use the minimum necessary plates in that same project where supported.

Determine the required parts from the requested delivery scope, not just the CAD change list. Check a complete assembly or an explicitly requested replacement set against the actual saved project using [Verify the saved delivery](bambu.md#verify-the-saved-delivery). Preserve recorded build orientations during placement unless a justified manufacturing change supersedes them.

Update the current project as needed while preserving recoverable checkpoints and older delivered revisions. Do not generate extra Functional, Quality, Release, alternate-orientation, replacement-only or coupon projects unless requested or already authorized. A small coupon may be proposed when it resolves a specific uncertainty; do not automatically add it to every delivery. Once the user requests another mode, prepare that mode without generating the remaining modes as well.

Time comparisons do not require a collection of delivered variants: when optimization is requested, keep baseline measurements and temporary experiments as evidence, then deliver the selected result. Distinguish internal trials from user-facing projects.

| Mode | Select when | Main objective |
|---|---|---|
| **Prototype** | Visual mock-up, scale check, concept review, or a nonloaded disposable draft | Minimum print time subject to printability |
| **Prototype --mechanical** | Fast iteration that must still assemble, move, transmit force, or test a working fit | Minimum time while protecting functional features |
| **Functional** | A working part, loaded bracket, joint, shaft, clip, gear, or sliding interface | Mechanical resistance, dimensional accuracy, and reliability |
| **Quality** | A display model, decorative shell, visible surface, or a presentation finish | Appearance and surface quality |
| **Release** | A repeatable print profile or local project prepared for sharing on any platform | Reliability, reproducibility, and easy printing and assembly |

A prototype containing working interfaces normally needs **Prototype --mechanical**. Mechanical-looking geometry used only as a visual mock-up can use plain Prototype. For a mixed assembly, select one overall mode and identify protected mechanical or visible components with explicit overrides. Release mode prepares shareable files; it does not imply permission to publish or upload them.

`Prototype --mechanical` is an assistant workflow mode, not a Bambu Studio CLI flag.

## Initial settings

These are starting points for a **0.4 mm nozzle**, not universal limits or mechanically validated presets. Preserve explicit project requirements. Check compatible installed profiles and nozzle limits before applying any value; adapt heights and features for another nozzle or material.

| Setting | Prototype | Functional | Quality | Release |
|---|---:|---:|---:|---:|
| `layer_height`, mm | 0.28 | 0.16–0.20 | 0.12–0.16 | 0.16–0.20 |
| `wall_loops` | 2 | 3–4 | 3 | 3 |
| `sparse_infill_density` | 5–10% | 15–25% | 10–15% | 15% |
| `top_shell_layers` | 3 | 4–5 | 5 | 4–5 |
| `bottom_shell_layers` | 3 | 4–5 | 5 | 4–5 |
| Ironing | Disabled | Retain a justified setting; normally unnecessary on working surfaces | Enable only when a visible surface benefits after inspection | Favor a simple, reproducible setting |
| Supports | Avoid through suitable orientation or geometry | Provide wherever needed | Balance surface finish, removal, and overhang quality | Minimize and make removal accessible |

When geometry does not distinguish between values in a range, use these initial candidates:

- Prototype: 0.28 mm, 2 walls, 5% infill, 3 top and 3 bottom layers, ironing disabled. Increase infill toward 10% if sparse support beneath top surfaces is inadequate.
- Functional: 0.20 mm, 4 walls, 20% infill, 5 top and 5 bottom layers. Use 0.16 mm or local reinforcement where the functional geometry requires it.
- Quality: 0.16 mm, 3 walls, 15% infill, 5 top and 5 bottom layers. Consider 0.12 mm where visible curvature or small details justify the additional time.
- Release: 0.20 mm, 3 walls, 15% infill, 5 top and 5 bottom layers. Use 0.16 mm when the model's details or assembly interfaces need it.

For Functional, prioritize load direction, wall thickness, and raster continuity. Infill percentage is not a strength certificate. For Quality, place seams away from important visible faces, inspect overhangs and top surfaces, and keep tolerances on any working interfaces. For Release, use clear part and plate names, portable documented profiles, consistent placement, accessible support removal, and a saved project that reopens correctly.

### Prototype --mechanical

Start with the fastest settings compatible with the actual interfaces:

- Keep 0.28 mm for coarse, noncritical volumes when the nozzle profile permits it. Consider 0.20–0.24 mm for functional geometry and 0.16 mm where small Z shoulders, retention lips, contact surfaces, or gear features require finer steps. Do not reduce every component's layer height automatically.
- Start working parts at 3 walls and 10–15% infill, with 4 top and bottom layers. Consider 4 walls and 15–25% infill locally at loaded roots, hubs, or fasteners when needed. Noncritical bulk can retain plain Prototype settings and 3 top/bottom layers.
- Inspect actual extrusion at small shafts, clip roots, teeth, slots, holes, and bearing or sliding surfaces. Small parts may already be effectively solid from their walls; raising infill can add little benefit.
- Preserve nominal dimensions and validated dimensional compensations. Coarser Z resolution does not justify changing XY fit allowances. Do not thicken a clip's flexible beam or alter a gear's tooth geometry merely to save time.
- If a critical interface still needs Functional settings, protect that component and retain faster settings elsewhere. Explain the exception in the report.

## Analyze parts before applying settings

For a new or revised design, apply [Design for reliable FDM printing](design-for-reliable-printing.md) before trying to solve orientation, tiny contacts or extensive fragile supports through process settings. All modes, including Prototype, retain the requirement for reliable manufacture.

Identify overall size and quantities; bed contact and stability; thin walls, small holes, lips, and teeth; tolerance-critical axes and fits; loading and layer direction; bridges and overhangs; visible faces and seams; support removal; and assembly access. Use the CAD model, measured mesh, project settings, and sliced preview where available. For a working joint, lever, shaft or reported fracture, follow [Mechanical orientation and assembly](mechanical-orientation-and-assembly.md) before treating process settings as the solution. Preserve the part's load path and the intended flexure during time optimization. Do not infer an exact clearance or wall thickness from an image alone.

Use the project's verified printer, nozzle, plate, and filament first. Otherwise start from **Bambu Lab A1 mini / 0.4 mm / PLA**, label these as planning defaults, and replace them when the project specifies other hardware or material. Verify real compatible profiles before applying them. If profiles or the slicer are unavailable, report proposed settings rather than claiming they were applied.

For components with different needs, use supported object, part, or modifier overrides. Confirm which settings are actually overridable in the installed version and workflow. Do not assume independent layer heights or process presets are supported for every object or plate. If incompatible requirements cannot be expressed safely, use separate compatible plates or projects. Sequential printing is an option only after checking actual toolhead clearances.

## Choose supports from actual geometry

Before applying support type or style, read [Choose support structures](choose-support-structure.md). Select the family, style, placement and removal path per component where supported, rather than inheriting one global choice without assessment. Auto placement does not evaluate which family is best; a hybrid style can combine tree and normal regions. Compare two credible candidates only when useful and slicing is authorized, then retain one selected project.

## Choose brims from actual bed contact

Apply this assessment in every mode, including Prototype. Judge the actual first-layer contact patches, their narrowest supporting span, and the part's height and overhang leverage. The XY bounding box is not the adhesion area: a large hollow or curved part may touch the bed only along a thin rim or a few feet. Consider material warping, the plate and first-layer condition, prior failures, and motion of a moving bed.

- Favor **Outer brim only** (`brim_type="outer_only"`) on parts with little bed contact, especially tall or slender parts, upright pins and antennae, or narrow isolated feet. Multiple tiny parts also warrant considering brims when adhesion is uncertain. Use supported per-object overrides so stable parts need not receive the same brim.
- For **PLA / 0.4 mm nozzle**, use **3–5 mm** as a starting candidate for `brim_width`; 5 mm is a reasonable first candidate for a slender part. Increase only when geometry, prior lifting or a trial justifies it. These are planning heuristics, not guaranteed adhesion or universal size thresholds. A small flat part with adequate contact and a proven process may not need a brim; a large part prone to warping may need one.
- Retain the validated `brim_object_gap`, or inspect the compatible installed preset when no validated value exists. A smaller gap strengthens the attachment but makes removal harder; a larger gap eases removal but can weaken the brim's benefit. Inspect the effective first-layer gap, including elephant-foot compensation. Do not set the gap to zero or disable validated `elefant_foot_compensation` automatically.
- Prefer an external brim for small mechanical parts to keep internal holes and clearances accessible. Check removal access around clips, thin walls, mating edges and print-in-place joints. Do not let brim paths lock moving components together. Explain any cleanup needed before checking fit.

Arrange with room for the **actual brim and support footprints**, not only the model bounds. Inspect the sliced first layer for the generated brim's width, connection and clearance from neighboring bodies and bed limits; overlapping brims can join parts and increase cleanup. Verify object overrides after saving and reopening. If the installed workflow cannot apply them, state that limitation and choose a supported arrangement rather than silently dropping needed adhesion.

A skirt does not attach to the part and is not a replacement for a brim. A brim does not replace indispensable overhang supports, proper plate preparation or a sound first layer. Preserve validated machine and filament settings unless a specific failure justifies a change; reconsider orientation only while protecting functional load paths and tolerances. Include brim scope, width, gap, cleanup and any measured time cost in the configuration report. Do not remove a necessary brim solely to shorten a Prototype estimate.

Sources: [Prusa's brim guidance](https://help.prusa3d.com/article/skirt-and-brim_133969) supports assessing tall parts with small bases and multiple small objects, and gives 3 mm as an adhesion starting point; its controls are not Bambu parameter names. Check Bambu names and enum values against the installed application and [Bambu Studio's configuration definitions](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp). The 3–5 mm range above is a starting policy to assess per part, not a manufacturer guarantee.

## Exact Bambu Studio parameters

Use these internal setting identifiers when reading or writing settings. Match the installed schema, enum values, units, and serialization types; field presence in a preset alone does not prove object-level or CLI support.

| Control | Exact parameter | Handling |
|---|---|---|
| Layer height | `layer_height` | Millimeters; validate against the selected nozzle profile |
| Initial layer height | `initial_layer_print_height` | Separate from normal layer height; retain validated adhesion settings |
| Brim type | `brim_type` | `"outer_only"` is Outer brim only; verify installed enums and object-level support |
| Brim width | `brim_width` | Millimeters; inspect the actual generated footprint and available spacing |
| Brim-object gap | `brim_object_gap` | Millimeters; retain a validated value and balance attachment against removal |
| Wall loops | `wall_loops` | Integer wall count; check actual extrusion widths and thin features |
| Sparse infill density | `sparse_infill_density` | Percentage, commonly serialized as a string such as `"15%"` |
| Sparse infill pattern | `sparse_infill_pattern` | Use an enum accepted by the installed version; compare paths and time |
| Top shell layers | `top_shell_layers` | Count of solid top layers |
| Bottom shell layers | `bottom_shell_layers` | Count of solid bottom layers |
| Minimum top shell thickness | `top_shell_thickness` | Millimeters; can impose more layers than the requested count |
| Minimum bottom shell thickness | `bottom_shell_thickness` | Millimeters; inspect inherited values and effective shells |
| Ironing type | `ironing_type` | Disabled is `"no ironing"` in the verified profile format |
| Enable support | `enable_support` | Preserve the writer's boolean representation; inspect the result |
| Support type | `support_type` | Select a verified family and auto/manual mode from the geometry; follow the support reference |
| Support style | `support_style` | Verify a compatible style and effective default; normal and tree families have different candidates |
| Support on build plate only | `support_on_build_plate_only` | Use only when all required supported regions remain reachable |
| Seam position | `seam_position` | Choose a supported policy or use seam painting through available tools |
| Top surface pattern | `top_surface_pattern` | Select an installed supported pattern for the intended finish |
| XY hole compensation | `xy_hole_compensation` | Retain validated fit calibration unless a measured need justifies a change |
| XY contour compensation | `xy_contour_compensation` | Retain validated dimensions and fit allowances |
| Elephant foot compensation | `elefant_foot_compensation` | This is the exact parameter spelling; preserve validated calibration |

Relevant speed controls include `outer_wall_speed`, `inner_wall_speed`, `sparse_infill_speed`, `top_surface_speed`, and `bridge_speed`. Adjust them only for an identified bottleneck or quality need. Preserve the filament's validated `filament_max_volumetric_speed`, temperatures, cooling, flow calibration, and retraction unless a specific, documented requirement justifies changing them. Check the machine's `min_layer_height` and `max_layer_height`; a mode does not authorize changing hardware limits or machine start/end G-code.

A profile may store a value as a string or a list rather than a JSON number or boolean. Use the format emitted or accepted by the existing tool instead of assuming a generic JSON schema. Verify effective settings after inherited presets and object/modifier overrides have been applied.

**Check effective shell thickness.** For example, 3 layers at 0.20 mm nominally give 0.60 mm, but an inherited `top_shell_thickness` of 1.0 mm can require more top layers. Decide explicitly whether to retain that minimum or adjust it for a noncritical fast prototype. Do not silently remove a functional thickness requirement to reach a nominal layer count. Check sparse top-surface support before reducing infill or solid layers.

The installed application's profiles and exported effective settings are the primary source of truth. Upstream references for checking definitions and defaults are Bambu Studio's [configuration definitions](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp) and [common process profile](https://github.com/bambulab/BambuStudio/blob/master/resources/profiles/BBL/process/fdm_process_common.json). Recheck them against the installed version rather than assuming the upstream branch matches it.

## Optimize using existing capabilities

1. Preserve the original project or configuration. Record the actual slicer version, printer, nozzle, plate, filament profile, relevant calibrations, model revision, quantities, and process settings. When available, slice the current configuration to obtain a baseline estimate before changing it.
2. Inspect installed compatible presets and inheritance. Select a suitable starting preset or duplicate the existing process and apply the selected mode's settings. Keep verified machine and filament settings. Change only the process settings and supported component overrides needed for the purpose.
3. Compare a small number of meaningful candidates. For Prototype, select the fastest printable candidate that satisfies its required function, including the baseline if it remains the best admissible choice. For the other modes, optimize their stated priority and explain the time cost or savings. Do not assume fewer layers or less infill guarantees a proportional reduction in duration.
4. Seek time savings through orientation, unnecessary support volume, repeated travel, noncritical walls or infill, unnecessary solid layers, and ironing before increasing speed beyond a validated process. Preserve bed adhesion and material flow limits. Never disable indispensable supports merely to save time; reorient, redesign or split within the authorized scope, or retain suitable supports and explain why.
5. Reslice changed candidates and inspect first layers, thin features, critical surfaces, bridges, overhangs, support interfaces, isolated regions, and warnings. Check actual parameter application, not only the intended preset. Keep necessary support and mechanical protections even when they cost time.
6. Save the selected configuration and, when requested, a genuine Bambu 3MF through the existing compatible application or tool. Reopen the project to verify objects, profiles, overrides, placement, and slice results. Follow [Bambu preparation](bambu.md) for archive handling and unavailable capabilities. Do not develop a new integration, silently edit archive internals, or start a physical print as part of choosing settings.

Stop when the selected candidate meets the mode's priority and further plausible savings would compromise required printability, tolerances, resistance, or finish. If necessary controls or slicing capabilities are unavailable, provide the supported result and clearly identify what remains proposed or unverified.

## Compare time estimates honestly

Compare the same model revision, quantity, printer, nozzle, and filament using consistent slicer estimate conventions. Record changed orientation, placement, supports, or plate grouping as part of the optimization. Include the total across all required plates and batches; a faster single plate does not establish a faster complete job. Do not change color or material requirements silently to reduce purge time.

For a positive baseline duration `T_initial` and measured candidate duration `T_optimized` in the same units:

- Estimated time saved = `T_initial - T_optimized`.
- Estimated saving percentage = `100 * (T_initial - T_optimized) / T_initial`.

Keep negative results when the selected candidate is slower; explain the benefit required by the chosen mode. If either slicer estimate is missing, or the baseline is zero or not comparable, report the corresponding duration or gain as **unavailable** and say why. Do not invent a baseline, extrapolate a claimed gain from layer height alone, or describe slicer estimates as actual measured printing time.

## Required completion report

Report in the user's language:

- **Selected mode:** mode, selection reason, hardware/material assumptions, and any component exceptions.
- **Applied settings:** exact Bambu parameter names and values, with global/object/modifier scope, including brim type, width and gap for parts needing adhesion help. Separate applied and verified values from proposals. Name retained machine and filament profiles.
- **Time:** initial and optimized slicer estimates, per-plate details when relevant, and totals. Include the absolute and percentage estimated savings when a comparable baseline exists; otherwise state unavailable.
- **Tradeoffs:** expected changes in visible finish, seam appearance, support removal, tolerance, resistance, or durability. Do not infer mechanical validation from successful slicing or a higher infill percentage.
- **Deliverables and checks:** actual saved files, reopening and preview checks, warnings, and outstanding dimensional, fit, clip, load, wear, or physical print tests appropriate to the parts.
