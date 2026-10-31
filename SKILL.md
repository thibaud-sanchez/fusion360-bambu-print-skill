---
name: fusion-bambu-print
description: Design or modify parametric Fusion 360 models for FDM printing, choose and optimize Bambu Studio settings, assess printability, and prepare or troubleshoot Bambu 3MF projects. Use for Prototype, Functional, Quality, or Release print preparation, including fast mechanical prototypes.
---

# Fusion 360 to Bambu printing

Produce an editable model and a print configuration appropriate to the actual machine, parts, and intended use. Respond in the user's language. Only claim application access, exported files, measurements, or slicing results that were actually obtained.

## Establish the project context

- Identify intended use, overall dimensions, critical interfaces, loads, environment, material, and deliverables. Consult project files and connected tools before asking for information. State reasonable assumptions for noncritical details; ask only for indispensable facts that cannot be inferred.
- Prefer the project's verified printer, nozzle, plate, and filament settings. Otherwise, use **Bambu Lab A1 mini / 0.4 mm nozzle / PLA** as replaceable planning defaults, explicitly identifying them as assumptions until the corresponding profiles are verified. Never infer AMS availability or slot assignments.
- Discover the tools and application capabilities available in the environment. Use Fusion for a requested native Fusion model. Reuse existing Bambu Studio capabilities, its installed CLI, or available compatible tools; do not build a new integration to choose settings. A server mentioned by another project is not evidence that it is installed here.

## Choose the print configuration

Before selecting a process preset, changing print parameters, or optimizing print time, read [choose-print-configuration](references/choose-print-configuration.md).

That reference defines selection of **Prototype**, **Prototype --mechanical**, **Functional**, **Quality**, and **Release**, their initial settings, component overrides, selective brims for adhesion and stability, exact Bambu parameter names, and the comparison report. During development, keep one current prototype project and aim for one plate; additional modes and user-facing variants require a request or existing authorization. Explicit user requirements take precedence over defaults. Apply the reference to settings-only requests even when no CAD changes are needed.

## Design, verify, and prepare

For CAD changes and iterative print preparation, read [Efficient iterations and part identity](references/efficient-iterations-and-part-identity.md). Keep stable part IDs such as `B1 — Chassis` across Fusion, exports, reports and assembly guides; keep revision labels separate. For existing models, map legacy names before renaming anything that scripts depend on.

Reuse existing helpers and validate the smallest useful change before rebuilding a complete delivery. Preserve recoverable checkpoints without treating every checkpoint as a release. Return concise tool summaries and keep detailed logs in files. A timeout does not establish that a Fusion operation stopped; check its status before retrying.

Apply **KISS — Keep It Simple, Stupid**: prefer the simplest printable mechanism that meets the user's actual needs. Reuse working geometry and retention where appropriate; add complexity only for a specific unmet requirement or demonstrated failure. Compare total print reliability and assembly effort, not only part count. Decorative moving grips, extra linkages, miniature clips and print-in-place joints are optional; omit them when they add failure modes without a requested benefit.

Before committing to geometry or grouping parts, read [Design for reliable FDM printing](references/design-for-reliable-printing.md). Choose a credible build orientation and stable bed contact during design. Prefer functional shapes and accessible large connections that reduce support dependence and delicate assembly; compare these with print-in-place where appropriate. A physical failure requires reassessing that manufacturing plan even when prior CAD and slicing checks passed.

1. Build parametric solids with named dimensions, constrained sketches, readable feature history, and separate moving or assembled components. Preserve existing work and export a native editable file when requested and available. Read [Fusion design and export](references/fusion.md) for API, unit handling, and closing completed task documents while preserving unsaved work and keeping the working project active.
2. Design around FDM orientation, bed contact, support removal, bridges, overhangs, layer direction, wall thickness, and assembly access. Measure geometry and mesh integrity using the available tools. Read [FDM checks](references/dfam.md); design heuristics do not establish material performance. For shafts, levers, snap fits, physical breakage or assembly simplification, read [Mechanical orientation and assembly](references/mechanical-orientation-and-assembly.md) before fixing the geometry and build orientation.
3. Export in the correct units, verify scale after import, and preserve distinct parts where needed. Apply the selected mode through verified profiles and supported controls. Read [Bambu preparation](references/bambu.md) for slicing, genuine project files, and reopening checks.
4. Inspect actual sliced layers and warnings. Correct relevant model or configuration defects, then repeat the affected checks. Separate measurements from assumptions and unavailable checks. A successful slice does not validate mechanical strength, snap-fit behavior, dimensional fit, or durability.

Uploading to a service or starting a physical print requires an explicit user request and an identified destination. Check accessible printer, plate, material, and job state before starting; do not invent missing device status or identifiers.

## Report the result

Describe actual files, dimensions, assumptions, applied configuration, checks, warnings, and remaining physical tests. For an assembly release, include a version-matched guide with stable part IDs and ordered real exploded views, following [Mechanical orientation and assembly](references/mechanical-orientation-and-assembly.md#document-assembly-for-each-delivered-version); internal checkpoints do not require a new guide. For configuration or optimization work, include the selected mode, exact parameter names and their scope, baseline and optimized slicer estimates when available, estimated time savings, and quality or strength tradeoffs, following the reference's report format. Report unavailable estimates as unavailable.
