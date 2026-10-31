# Mechanical orientation and assembly

Read this when designing a functional FDM part, choosing its build orientation, investigating a fracture, or simplifying an articulated assembly. Use the project's actual printer, material, clearances and test history; this is not a universal requirement to print every part flat.

## Choose orientation from the load path

Identify where forces enter and leave the part, the directions of bending and tension, torque transmission, and the sections that intentionally flex during assembly. Mark thin roots, slots, shoulders, sharp internal corners and the junction between a lever and its hub. Consider assembly loads as well as normal operation.

Use **printer XY** for the bed and **printer Z** for the layer stacking direction. Keep these distinct from the CAD assembly axes. Record the actual rotation or a clear oriented view for each exported part.

| Feature | Orientation decision |
|---|---|
| Cantilever latch or forked snap pin | Prefer continuous material along the beam and through its root. When practical, place its length and bending action in the printing plane; inspect the root rather than assuming the whole part's largest face gives the strongest result. |
| Flat lever, crank arm or linkage | Favor an orientation that carries its main tensile and bending stresses along deposited material. Check the hub and any projecting shaft separately. |
| C-shaped retaining ring | Its arms can often flex within the printing plane. Provide an accessible insertion direction and adequate finger access. |
| Combined disc, shaft and latch | The disc's convenient flat orientation may leave the latch beams standing across layer interfaces. Compare a different retention location, a split component or a supported orientation. |
| Round journal or sliding pin | Preserve the working contact surface and measured fit. Flattening a loaded round journal merely to obtain a bed face changes the mechanism and needs verification. |

FDM properties depend on direction, geometry and processing. Avoid configurations that put a critical latch root in layer-separating tension or peel when a practical alternative exists. A horizontal orientation does not guarantee strength under every load. A vertical solid shaft is not equivalent to a vertical, thin, repeatedly bent latch.

Changing orientation can compromise roundness, fit, bed contact, overhangs or assembly access. If one piece contains conflicting requirements, compare an integrated planar latch, a separate printed axle or another joint arrangement. Balance the extra assembly work against the actual strength benefit; do not split every model automatically.

## Design the flexible section, not just a thicker part

A thicker snap beam generally needs more force to reach the same deflection and can make assembly harder. Consider effective flexible length, required deflection, a tapered lead-in, a smooth root transition, room for the beam to move, and retention after engagement. Preserve the bearing or torque-transmitting section when revising the latch.

Do not compensate for a poor load path only with infill, extra walls or finer layers. Inspect actual extrusion through thin roots and clips. Material changes, temperatures, cooling and annealing require a justified project need; keep validated profiles unless the evidence supports a change. Estimated beam strain or a successful slice is not a material or fatigue qualification.

## Respond to a physical failure

1. Identify the exact part and fracture location. Distinguish a flexible latch from a rigid arm, a main shaft from an eccentric pin, and insertion failure from failure during operation.
2. Retrieve the actual STL orientation, project placement, filament and effective settings where available. A delivered orientation does not establish which orientation the user actually printed.
3. Record the observed failure separately from proposed causes. Delamination, excessive interference, a short beam, a sharp notch and a blocked flexure can produce similar symptoms.
4. Correct the relevant geometry, orientation or assembly path, preserve the previous version, and recheck affected fits and toolpaths. Use a small representative joint or replacement part for a new physical trial when it can resolve the uncertainty without reprinting an entire assembly.
5. Report what was measured, what remains inferred, and which assembly or cycling test is still needed. Do not call the redesign mechanically validated before a relevant physical test.

## Simplify assembly without losing required constraints

Apply [Design for reliable FDM printing](design-for-reliable-printing.md) when choosing which parts to merge. A small number of large press-together parts may be a better manufacturing plan than a tightly enclosed print-in-place mechanism with fragile supports.

Reduce both the number of distinct parts and the number of delicate assembly actions. A separate tiny retaining clip may work mechanically while being inconvenient to grip.

- Consider integrating a retaining feature into a linkage end or moving the flexible latch to a part that prints in a better orientation. Verify its free rotation, axial clearance, elastic movement, insertion access and release path.
- Keep a key, flat or other torque connection when it transmits rotation or fixes a required phase. A freely rotating pivot or static cover pin may not need a key if separate locating surfaces already constrain the assembly. Verify those constraints before removing the key.
- Use accessible lead-ins, visible alignment, captive hardware, rounded gripping surfaces and features that reject the wrong orientation naturally. Do not change a calibrated working clearance without evidence.
- Sample the actual assembly sequence. A radial snap may become impossible after the enclosure is closed; a retained shaft may prevent installing its bearing. A visually plausible joint is not proof that it can be assembled.

Prefer straightforward improvements before adding intricate printed hinges, spring networks or new mechanisms.

When an enclosure already captures a shaft, a broad rigid locating foot may be enough to secure its bearing after assembly. Verify the complete constraint and insertion sequence before adding another latch. Closing a radial snap seat can remove its insertion path; check temporary assembly positions and neighboring rails as well as the final fit.

Use KISS as the default architecture rule. Preserve reliable tested retention instead of replacing it solely to reduce the part count. If a small retaining clip works but is hard to handle, first consider an accessible larger grip and a stable print face. Do not add a freely rotating grip, compliant network or captive joint unless its practical benefit justifies the extra printing and assembly risk. Thin open hooks that carry bearing loads require a new load path or a sturdier bearing, not only tighter snap interference.

## Evaluate print-in-place selectively

Use a print-in-place joint only when the actual clearance can be resolved by the selected machine and material, all intended moving regions can be printed, and the joint can be freed and inspected without inaccessible supports. Consider radial and axial gaps separately, first-layer expansion, seam placement, bridges, trapped material, rotation limits and wear.

Do not replace a verified printable assembly with a merged mesh and call it print-in-place. Multiple disconnected solids can be intentional moving parts: a mesh check must distinguish an intended articulated assembly from an accidental disconnected fragment. Inspect the actual sliced gaps and extrusion paths, including the first layers of each region. If a pin starts in midair or a buried bearing needs inaccessible support, retain a simple assembled joint or revise the geometry.

A small clearance coupon or representative joint can be more useful than a full new model. Keep a previous assembled version when introducing an untested print-in-place alternative.

## Document assembly for each delivered version

For an assembly deliverable, include a guide matching that exact revision and its part files. Provide a numbered overview and an exploded view for each assembly step, showing incoming parts separated along the intended insertion direction while previously assembled parts stay together. Use actual CAD geometry or clearly identified CAD illustration copies; do not substitute an invented picture for the real interfaces.

Use the stable part IDs shared with Fusion and exports, following [part identity](efficient-iterations-and-part-identity.md#give-parts-stable-identities). Put these IDs on exploded-view callouts and in the parts list; assembly step numbers are separate. State order, alignment/keying, push/slide/rotate direction, support/brim removal and any authorized gluing. Prefer large accessible press-together actions; show unavoidable delicate operations explicitly. Mark print-in-place bodies as captive: a conceptual exploded view must not instruct the user to dismantle them. Distinguish an illustrated sequence from a mechanically checked insertion path and a physically tested assembly.

Preserve guides with older revisions. Record known failures and unverified retention so an outdated guide is not mistaken for a corrected release. Use a short guide for a simple assembly and one clear image per meaningful step for a complex one.

## References and evidence

- [Prusa: Modeling with 3D printing in mind](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) discusses directional strength, orientation, splitting models and iterative fit testing.
- [Formlabs: Designing 3D printed snap-fit enclosures](https://formlabs.com/blog/designing-3d-printed-snap-fit-enclosures/) discusses snap geometry, tolerancing, roots and process-dependent orientation. Apply its FDM guidance to FDM; do not import SLA or SLS rules without checking the process.
- [Makers Making Change: Snap Fits](https://makersmakingchange.github.io/OpenAT_Design_Guide/Design_Elements_For_3D_Printed_Parts/Snap_Fits.html) documents practical assembly and orientation considerations. Its example clearances are starting evidence, not universal printer calibration.

Treat forum reports and other printable models as design ideas tied to their material, machine and geometry. Distinguish an author's observed test from an untested suggestion, and validate a borrowed principle in the current project.
