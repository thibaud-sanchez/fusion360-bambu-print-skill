# Efficient iterations and part identity

Use this reference when modifying CAD, resuming work, or preparing iterative print deliveries. Reduce avoidable reasoning, code generation and repeated tool output while preserving necessary checks. Use the existing Fusion API/MCP and slicer capabilities; a new integration is not the default solution.

## Give parts stable identities

- Assign short IDs such as `B1`, `B2` and `A3`, followed by a descriptive name. A letter may group a subsystem when useful; do not impose an elaborate taxonomy. Keep the ID independent of color, assembly-step order, timeline position and revision number.
- Use the same ID in Fusion component names, exported filenames, slicer object names where supported, reports and guide callouts. For example: `B1 — Chassis`, `B1_chassis.stl`, and “Slide A3 — Carriage into B1 — Chassis.” Keep revision labels in the delivery directory or explicit revision metadata.
- Record the mapping once in an existing project table or a small manifest: ID, name, role, quantity, Fusion binding and export filename. Distinguish different part designs from repeated instances of the same part. Keep variants and compatibility explicit; sharing an ID does not establish interchangeability between revisions.
- Keep IDs stable across compatible revisions; do not recycle retired IDs. Record a mapping when splitting or merging parts. For legacy models, map old names first and migrate callers deliberately rather than breaking name-based scripts with an unsolicited rename.

## Resolve the target before a costly change

Identify the exact part, its mating parts and its role: fixed support, moving linkage, main axle, eccentric pin or enclosure. When the request is ambiguous, use an actual annotated view or a small schematic and state the intended assembly action before committing to a full redesign. Ask only if the ambiguity materially changes the solution and cannot be resolved from available evidence.

Check a proposed insertion path and required retention before detailed styling or full export. Collision-free motion alone does not prove that a part can be assembled or cannot fall out. Share the assembly sequence between path checks and illustrated guides rather than independently recreating it.

## Reuse execution, limit repeated context

- Inspect existing helpers before writing replacements for transforms, units, captures, collision checks, mesh inspection or exports. Extract a small tested function when repetition justifies it; do not refactor historical archives or build a general geometry framework as part of an ordinary model edit.
- Prefer named parameters and reference frames over duplicated coordinates. Reuse native Fusion joints and existing checks where appropriate; do not recreate a second motion model without a concrete need.
- Batch related measurements or motion samples within a supported operation. Serialize Fusion jobs: keep one mutation in flight and avoid interleaved native queries while it is running. Use the supported execution context for Fusion API calls.
- Keep long-running job IDs, revision identifiers and progress in files when supported. After a timeout, inspect progress and outputs before retrying or restarting. An old output file is not evidence that the current run completed.
- Return a short result containing status, revision, relevant part IDs, failures and report path. Keep full logs, layer lists and detailed geometry data in files; read only relevant sections. Load skill references and archived versions only when needed.
- When effort controls are available, reserve intensive reasoning for uncertain architecture and diagnosis. Use established routines for deterministic execution. Do not claim credit savings from fewer calls alone or invent historical usage figures.

## Separate checkpoints from releases

Keep recoverable native checkpoints before risky edits and preserve delivered or physically tested versions. A checkpoint needs only enough state to resume: current revision, changed IDs, last verified checks and next unresolved question. Saving another file does not by itself require another guide, slice, ZIP or full set of variants.

During exploration, modify and test the smallest representative part, joint coupon or assembly that can resolve the uncertainty. Compare a small number of credible alternatives instead of generating exhaustive combinations. After two unsuccessful attempts at the same issue, revisit the diagnosis and evidence before another redesign; do not automatically add more complete variants.

Run checks affected by the change, including mating interfaces, motion envelopes and assembly paths. Reuse prior results only when the relevant geometry, configuration and checker version are demonstrably unchanged; names, timestamps, bounding boxes and volumes alone are insufficient. If impact is uncertain, broaden verification. Reslice affected objects when geometry, orientation or effective print settings change.

At a delivery milestone, produce the requested exports, a revision-matched guide and verified slicer projects. Inspect and reopen actual deliverables as applicable. Keep older releases intact and mark their known failures. Delete or consolidate archives only when requested.

For iterative Bambu deliveries, follow [one current prototype project](choose-print-configuration.md#keep-one-current-prototype-project). Do not turn saved checkpoints or internal comparisons into extra delivered modes or projects.

Report what changed, what was checked and what still requires a physical test. If usage data is available, track model usage, tool calls and local computation time separately; elapsed Fusion time is not a token measurement.
