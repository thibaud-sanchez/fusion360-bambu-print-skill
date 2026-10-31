# Bambu Studio preparation

Read [choose-print-configuration](choose-print-configuration.md) before selecting a mode or optimizing parameters. Use profiles matching the actual printer, nozzle, plate, filament, and process. Verify compatibility and inheritance rather than relying on a preset name alone. Never assign a material or color to an unverified AMS slot.

Import at the intended scale, orient and arrange the parts, and verify the printable envelope and alignment of multi-part or multicolor assemblies. Check bed contact, support access, assembly interfaces, and collisions. Slice and inspect layers, missing paths, unsupported islands, bridges, and warnings. Only report time and filament estimates obtained from the slicer.

An STL or geometry-only 3MF is not necessarily a Bambu project with settings, placement, materials, and modifiers. When a Bambu project is requested, save it through a compatible Bambu Studio version or an existing tool with verified compatibility. Reopen it and check objects, profiles, overrides, and placement. Do not claim readiness when slicing, profile compatibility, or reopening remains unverified. Reslice for a changed machine, nozzle, material, or other relevant configuration.

Do not directly modify a 3MF's internal ZIP/XML structure without validating the format, the writer's compatibility, and the resulting project. Prefer the application's own save/export workflow. An ordinary standalone process-profile JSON is distinct from editing an archive's internals; validate it with the installed slicer before using it. Do not develop a new integration or archive writer for this workflow.

Use the actual capabilities of the existing GUI, installed CLI, or connected tools. Check the installed CLI help before relying on flags or export behavior. Resolve profiles and their inherited settings using an available, verified method. Preserve value types and units when updating exported settings. Do not depend on another project's absolute paths or assume a specific graphical launch workaround is needed everywhere.

Inspect both project warnings and slicing logs or result files when available. A successful exit code alone does not establish printability. If an operation times out, check application health and the actual output files before retrying; do not assume later export steps completed. Do not present old meshes or G-code as the result of a newer optimization.

If Bambu Studio or a compatible slicer is unavailable, deliver the actual files and proposed settings with precise preparation instructions. Mark the project, applied settings, slicing estimates, and checks as unverified where appropriate.
