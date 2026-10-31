# Design for reliable FDM printing

Read this **before choosing an architecture or finalizing a part**, and after a physical print failure. Choose how each part will print while designing it. A supported render or a successful slice does not establish a reliable manufacturing plan.

## Start from function and orientation

Apply **KISS (Keep It Simple, Stupid)**. Establish the minimum required function, retain known working solutions and justify extra degrees of freedom or retention mechanisms. Prefer a sturdy closed bearing over a thin open cradle when it meets the assembly path, and a fixed grip over a separately rotating handle when free rotation is not needed. A few robust, easy-to-print parts can be simpler than one intricate articulated print. After a failure, change the relevant feature and test it before introducing unrelated mechanisms.

Identify the geometry that actually performs the job: load paths, bearing surfaces, motion, clearances and retention. Compare practical build orientations early, together with strength and visible finish. Keep decorative surfaces where they can print cleanly and put compromises on hidden, nonfunctional faces.

Prefer substantial planar bed contact. Rounded shells can have a hidden flat rim, small landing pads or a modest flat underside while retaining a rounded exterior. Measure actual first-layer contact and support footprints; an XY bounding box does not measure adhesion. Avoid a sphere, thin edge or tiny tip as the sole support for a tall or wide part. Do not flatten a working journal, change a cam profile or consume a calibrated clearance just to obtain a bed face.

Question unnecessary geometry. An eccentric drive may need only a rigid arm and an offset pin, rather than a complete disc. Retain a full circular rim when it serves as a bearing, gear, cam, guard or required inertia. Check the complete motion envelope after any simplification.

## Make overhangs and assembly deliberate

- Favor buildable slopes and chamfers on downward-facing edges. About 45 degrees **from the bed plane** is a conservative starting design heuristic, not a universal support threshold. Keep the angle convention explicit. Visible curves may remain curved when their orientation prints well.
- Assess bridge length, anchoring at both ends, material, cooling and sag clearance. Use the project's demonstrated bridging ability or a representative trial; do not declare an arbitrary span safe because the slicer labels it a bridge.
- Avoid tiny loose pins, retainers and short split forks when an integral solid stud, a larger accessible clip, a captive joint or another simple connection meets the function. Preserve torque transmission and phase where required. Inspect actual extrusion through load-bearing roots; minimum printable detail is not minimum useful strength.
- For small decorative or color inserts, **do not use miniature split pins or micro-barbs when a monolithic feature or an authorized broad glue seat can do the job**. Prefer a substantial insert with a stable print face, an accessible bonding surface and, where suitable, an integral pupil/detail to paint. Reject a retention design that depends on fragile prongs, support removal around a tiny stem or unverified one/two-line loaded roots; redesign before delivery. Do not infer adhesive permission for structural or moving joints from permission to glue decorative eyes.
- Compare a few large parts that press together with a print-in-place assembly. Choose print-in-place only when every body has a buildable start, moving gaps remain free, and any supports can be removed. Count handling steps and delicate operations as well as bodies; fewer STL files can still mean a less reliable print.

For load direction and flexible joints use [Mechanical orientation and assembly](mechanical-orientation-and-assembly.md). Keep validated machine and filament profiles unless evidence justifies a change.

## Treat support dependence as a design cost

Inspect the supports needed by the chosen orientation before finishing the geometry. Tall thin trees, long unsupported branches, tiny contact points, poor support adhesion or supports trapped in joints are reasons to reconsider shape, orientation or a split. When supports remain necessary, use a stable, accessible arrangement verified in the installed slicer; normal and tree supports have different stability and removal tradeoffs. Never switch off an indispensable support to hide the problem.

Compare meaningful alternatives using actual previews and estimates when available. Record support material/time if reported, contact locations, removal access and the visible surfaces affected. Do not invent those measurements. A brim may help adhesion, but cannot correct a part beginning in midair or a long sagging bridge. Apply [selective brims](choose-print-configuration.md#choose-brims-from-actual-bed-contact) where justified, and keep them out of moving gaps.

## Recheck the manufacturing plan

Before delivery, inspect the first layers, changes in contact area, first layers of each feature, thin paths, downward surfaces, bridges and support interfaces. State the intended orientation and any cleanup. Reconsider the design when a small feature depends on a fragile support tower, a critical face prints against difficult supports, or assembly requires manipulating tiny unsupported features.

After an observed failure, record the exact revision, orientation, process and affected region separately from the suspected cause. Physical results take precedence over earlier numerical readiness claims. Recheck CAD and toolpaths, preserve the failed version, and prefer a relevant local trial or replacement part over immediately repeating the entire assembly. Identify which fixes were modeled, sliced and physically tested; do not claim a zero-failure design.

When delivering an assembled object, provide a version-matched assembly guide with numbered parts and ordered, real exploded views, following [Mechanical orientation and assembly](mechanical-orientation-and-assembly.md#document-assembly-for-each-delivered-version).

## Primary references

- [UltiMaker: Design for FDM/FFF](https://ultimaker.com/learn/design-for-fff-3d-printing-maximize-your-success/) — orientation early in design, tolerances and bottom-edge chamfers.
- [Prusa: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) — overhangs, splitting parts, directional strength, thin features and fit.
- [UltiMaker: Support settings](https://support.ultimaker.com/articles/Knowledge/1667417606331) — support stability and removal tradeoffs. These are process principles, not Bambu parameter names or presets to copy.

The design decisions above are a reusable synthesis; numeric values remain project-specific candidates until verified on the actual printer and material.
