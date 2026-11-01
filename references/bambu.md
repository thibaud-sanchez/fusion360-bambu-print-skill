# Bambu Studio preparation

Read [choose-print-configuration](choose-print-configuration.md) before selecting a mode or optimizing parameters. Use profiles matching the actual printer, nozzle, plate, filament, and process. Verify compatibility and inheritance rather than relying on a preset name alone. Never assign a material or color to an unverified AMS slot.

Import at the intended scale, orient and arrange the parts, and verify the printable envelope and alignment of multi-part or multicolor assemblies. Check bed contact, support access, assembly interfaces, and collisions. Slice and inspect layers, missing paths, unsupported islands, bridges, and warnings. Only report time and filament estimates obtained from the slicer.

Choose support family and style using [Choose support structures](choose-support-structure.md). Record the effective `support_type` and `support_style`, including supported component overrides. A preset's default or the word Auto does not establish the best support strategy. Inspect generated coverage and removal access before choosing by time or material.

An STL or geometry-only 3MF is not necessarily a Bambu project with settings, placement, materials, and modifiers. When a Bambu project is requested, save it through a compatible Bambu Studio version or an existing tool with verified compatibility. Reopen it and check objects, profiles, overrides, and placement. Do not claim readiness when slicing, profile compatibility, or reopening remains unverified. Reslice for a changed machine, nozzle, material, or other relevant configuration.

## Verify the saved delivery

Use the existing project part record as the expectation, then inspect the actual saved/reopened project. Do not derive both the expectation and the result from the same export list.

Use the bundled [Printcheck](printcheck.md) for supported inventory, geometry, settings and deposited-path checks. It reads the saved file without opening Bambu; application reopening and checks beyond its documented scope remain necessary. Keep its expectation file and full report with the project rather than embedding model-specific rules in the skill.

- Compare required IDs and quantities with actual objects/instances. Distinguish physical bodies from print objects: a captive multi-body joint may intentionally be one print object. Detect missing parts, duplicates and unintended extra plates; for replacements, identify the compatible parts the user must reuse.
- Confirm scale, intended bed face and functional axis orientation after the complete export/import/placement chain. Use transforms or meaningful geometric landmarks; extents can catch an obvious side rotation but cannot establish orientation for symmetric parts. A label such as "upright" is not verification.
- Check the effective machine, filament, process and relevant object overrides. Inspect actual model, support and brim paths against the usable bed, reserved areas and required inter-object/toolhead clearances. A model-only bounding box or preview thumbnail is insufficient.
- Keep automatic orientation from overriding a deliberate manufacturing decision. If auto-arrangement adds a plate, inspect a credible manual layout without changing validated orientations or reducing necessary clearances. Do not force a single plate when a reliable layout does not fit.
- Tie the report to the actual project and inputs using an existing revision/input record or file hashes where useful. An already-open application can still show an older project when a filename has been overwritten; tell the user to reopen it when relevant. Keep the guide, parts list and selected project consistent.

Report checks that could not be performed as unverified. These checks do not require another slice when the unchanged saved project already has traceable, current results.

## Check mechanical regions in the correct frame

For automated checks near a pivot, running clearance or support-exclusion region, transform that region through the actual CAD-to-mesh and saved object/instance-to-plate transforms. Include normalization, units, rotation and translation; never assume the initial placement survived arrangement. Use the actual instance when the same part appears more than once.

Validate a reused transform/checker with a known landmark and a representative inside/outside case when it is introduced or its coordinate handling changes. Record sampling resolution, tolerances and unsupported path features; an empty match is not a pass if the region was mapped outside the intended part or the parser skipped relevant paths. "No support detected in the sampled region" does not prove that a joint will release or survive use.

## Use the available export route

Do not directly modify a 3MF's internal ZIP/XML structure without validating the format, the writer's compatibility, and the resulting project. Prefer the application's own save/export workflow. An ordinary standalone process-profile JSON is distinct from editing an archive's internals; validate it with the installed slicer before using it. Do not develop a new integration or archive writer for this workflow.

Use the actual capabilities of the existing GUI, installed CLI, or connected tools. Check the installed CLI help before relying on flags or export behavior. Resolve profiles and their inherited settings using an available, verified method. Preserve value types and units when updating exported settings. Do not depend on another project's absolute paths or assume a specific graphical launch workaround is needed everywhere.

Inspect both project warnings and slicing logs or result files when available. A successful exit code alone does not establish printability. If an operation times out, check application health and the actual output files before retrying; do not assume later export steps completed. Do not present old meshes or G-code as the result of a newer optimization.

Treat successful G-code generation and successful project export as separate results. A CLI launch can finish slicing and then fail while generating graphical thumbnails. Reuse a confirmed graphics-capable launch context already available in the environment when needed; do not repeatedly reslice with the same failing launch or handcraft a replacement 3MF. Check installed CLI restrictions before combining image export with slicing/project export. When executing a reusable Python file inside an app, set its module namespace deliberately so an `if __name__ == "__main__"` block does not run once on loading and again through the app entry point.

If Bambu Studio or a compatible slicer is unavailable, deliver the actual files and proposed settings with precise preparation instructions. Mark the project, applied settings, slicing estimates, and checks as unverified where appropriate.
