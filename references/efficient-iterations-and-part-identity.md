# Efficient iterations and part identity

Use this reference when modifying CAD, resuming work, or preparing iterative print deliveries. Reduce avoidable reasoning, code generation and repeated tool output while preserving necessary checks. Use the existing Fusion API/MCP and slicer capabilities; a new integration is not the default solution.

## Give parts stable identities

- Assign short IDs such as `B1`, `B2` and `A3`, followed by a descriptive name. A letter may group a subsystem when useful; do not impose an elaborate taxonomy. Keep the ID independent of color, assembly-step order, timeline position and revision number.
- Use the same ID in Fusion component names, exported filenames, slicer object names where supported, reports and guide callouts. For example: `B1 — Chassis`, `B1_chassis.stl`, and “Slide A3 — Carriage into B1 — Chassis.” Keep revision labels in the delivery directory or explicit revision metadata.
- Record the mapping once in an existing project table or a small manifest: ID, name, role, quantity, Fusion binding and export filename. Distinguish different part designs from repeated instances of the same part. Keep variants and compatibility explicit; sharing an ID does not establish interchangeability between revisions.
- Keep IDs stable across compatible revisions; do not recycle retired IDs. Record a mapping when splitting or merging parts. For legacy models, map old names first and migrate callers deliberately rather than breaking name-based scripts with an unsolicited rename.

## Keep the delivery scope and physical evidence explicit

Extend the existing part record or progress file rather than creating a parallel tracking system:

- Record whether the current delivery is a complete assembly or a specified replacement set, with required IDs, quantities and compatible reused parts. A list of changed parts is not the delivery list. An unchanged part still belongs in a requested complete plate; do not silently carry a replacement-only scope into the next release.
- For each relevant part, record its intended printer orientation using a rotation/reference frame or an unambiguous oriented view, the reason, and any user-observed success or failure. Distinguish the orientation actually printed from the one previously delivered. Apply explicit orientation corrections to the current preparation source as well as the output, so regeneration does not restore the old rotation.
- Identify physically successful interfaces and their tested revision/configuration. Preserve them during unrelated changes; if an interface must change, state why and mark the affected physical validation as needing renewal. A working clip does not establish that the entire assembly is validated.

Before a costly operation, resolve these records and the changed IDs. Preserve concise outcomes in the resume file; do not reread the full historical conversation or every archived revision to recover a decision already recorded there.

## Resolve the target before a costly change

Identify the exact part, its mating parts and its role: fixed support, moving linkage, main axle, eccentric pin or enclosure. When the request is ambiguous, use an actual annotated view or a small schematic and state the intended assembly action before committing to a full redesign. Ask only if the ambiguity materially changes the solution and cannot be resolved from available evidence.

Check a proposed insertion path and required retention before detailed styling or full export. Collision-free motion alone does not prove that a part can be assembled or cannot fall out. Share the assembly sequence between path checks and illustrated guides rather than independently recreating it.

## Reconstruct a clean part when geometry accumulates

Treat each revision as a finished part design. When repeated edits leave obsolete fixings, overlapping repairs, thin tabs or stepped remnants, reconstruct the affected region or part from its current functions. Preserve the interfaces; replace the accumulated geometry with a coherent design.

1. Identify the current datums, mating dimensions, required motion/assembly clearances and load paths. Distinguish these from old features that no longer serve the selected architecture.
2. Define a simple authoritative envelope and deliberate pockets. Rebuild the complete affected region, including its connections to adjacent material. Remove or replace superseded solids and cuts instead of adding another cover, rib, filler or fillet around them.
3. Give every remaining projection and recess a current purpose. Remove obsolete locating tabs, old latch roots, thin ledges, isolated teeth, tiny notches and accidental sliver faces. Rounding an obsolete feature does not resolve it. Preserve intentionally small functional details where justified by their role and printability.
4. Verify connectivity and printability. One connected solid per intended fixed part is necessary, but does not prove the shape is clean. Boolean Join alone does not eliminate redundant surfaces or a visibly pieced-together form. Multiple deliberate CAD features are acceptable; do not force one operation or erase editable design intent merely to reduce the timeline count.
5. Inspect the actual part from the relevant front, rear, top and detail views. With an annotated issue image, track every marked region and show the corresponding corrected view. Do not substitute an unrelated cosmetic pass or a flattering assembled view for inspecting the identified defects.
6. Recheck the affected interfaces and clearances. Keep the earlier revision recoverable. Mark unresolved functional compromises explicitly instead of presenting them as completed cleanup.

Use a small direct edit when it produces a clean result. Repeated failure or repeated complaints about the same area are reasons to reconsider the construction, rather than continue trimming individual fragments. Preserve deliberate component separation, moving parts and necessary reference entities. This rule does not authorize unrelated redesigns or merging an articulated assembly into one solid.

## Reuse execution, limit repeated context

- Inspect existing helpers before writing replacements for transforms, units, captures, collision checks, mesh inspection or exports. Extract a small tested function when repetition justifies it; do not refactor historical archives or build a general geometry framework as part of an ordinary model edit.
- Useful small helpers include expected-versus-actual part/quantity checks, orientation checks, frame transforms, printable-envelope checks including generated supports/brims, and protected-joint path checks. Parameterize part IDs, frames and expected values instead of copying another model's counts or coordinates. Keep these helpers separate from model-specific geometry; do not build a new library merely to document an iteration.
- Prefer named parameters and reference frames over duplicated coordinates. Reuse native Fusion joints and existing checks where appropriate; do not recreate a second motion model without a concrete need.
- Batch related measurements or motion samples within a supported operation. Serialize Fusion jobs: keep one mutation in flight and avoid interleaved native queries while it is running. Use the supported execution context for Fusion API calls.
- Keep long-running job IDs, revision identifiers and progress in files when supported. After a timeout, inspect progress and outputs before retrying or restarting. An old output file is not evidence that the current run completed.
- Return a short result containing status, revision, relevant part IDs, failures and report path. Keep full logs, layer lists and detailed geometry data in files; read only relevant sections. Load skill references and archived versions only when needed.
- When effort controls are available, reserve intensive reasoning for uncertain architecture and diagnosis. Use established routines for deterministic execution. Do not claim credit savings from fewer calls alone or invent historical usage figures.

## Separate checkpoints from releases

Keep recoverable native checkpoints before risky edits and preserve delivered or physically tested versions. A checkpoint needs only enough state to resume: current revision, changed IDs, last verified checks and next unresolved question. Saving another file does not by itself require another guide, slice, ZIP or full set of variants.

During exploration, modify and test the smallest representative part, joint coupon or assembly that can resolve the uncertainty. Compare a small number of credible alternatives instead of generating exhaustive combinations. After two unsuccessful attempts at the same issue, revisit the diagnosis and evidence before another redesign; do not automatically add more complete variants.

Run checks affected by the change, including mating interfaces, motion envelopes and assembly paths. Reuse prior results only when the relevant geometry, configuration and checker version are demonstrably unchanged; names, timestamps, bounding boxes and volumes alone are insufficient. If impact is uncertain, broaden verification. Reslice affected objects when geometry, orientation or effective print settings change.

Record why a costly rebuild or reslice is needed: changed input, failed check or unresolved question. Documentation-only edits do not require geometry regeneration or slicing. Stop repeating successful unchanged checks once their results are tied to the current inputs. Local validation during exploration does not replace the final saved-project checks when a full project is delivered.

At a delivery milestone, produce the requested exports, a revision-matched guide and verified slicer projects. Inspect and reopen actual deliverables as applicable. Keep older releases intact and mark their known failures. Delete or consolidate archives only when requested.

For iterative Bambu deliveries, follow [one current prototype project](choose-print-configuration.md#keep-one-current-prototype-project). Do not turn saved checkpoints or internal comparisons into extra delivered modes or projects.

Report what changed, what was checked and what still requires a physical test. If usage data is available, track model usage, tool calls and local computation time separately; elapsed Fusion time is not a token measurement.
