# Choose support structures

Read before choosing support type or style, and after support failure or difficult removal. Apply in every print mode. An inherited preset is a starting point, not evidence that its support choice suits the part.

## Choose from the geometry

First consider a credible orientation, a buildable chamfer or an accessible split. Retain indispensable support. Identify the actual unsupported areas, their height, contact surfaces and removal path.

Use these starting candidates, then inspect the generated paths:

| Geometry or concern | Candidate | Inspect especially |
|---|---|---|
| Broad horizontal undersides, geometric shelves | Normal / Grid | Coverage and removal access |
| Contour-following coverage with less bulk | Normal / Snug | Tower stability and surface contact |
| Dispersed small overhangs or curved decorative surfaces | Tree / Slim or Organic, if available | Branch reach, anchors and removal |
| Heavier overhangs needing tree routing | Tree / Strong | Footprint, branch strength and access |
| Mixed curved regions and large flat undersides | Tree / Hybrid | Local normal-style regions as well as branches |
| Buried channels, tiny clips or captive joints | Reconsider shape/orientation | Trapped support and damage during cleanup |

These candidates follow Bambu's [support guidance, section 5.5.4](https://csm.bblcdn.com/hub/4668d0ca43994ff3bff4b37f1a65c2e7.pdf#page=60). Its printer-specific examples do not establish settings for another machine. Neither family guarantees easier removal or lower material use for every shape.

## Distinguish type, style and placement

`support_type` selects a family and automatic or manual placement. Supported values must be verified in the installed version; upstream values include `normal(auto)`, `tree(auto)`, `normal(manual)` and `tree(manual)`.

`support_style` controls shape. Examples are `grid`, `snug`, `tree_slim`, `tree_strong`, `tree_hybrid` and `tree_organic`. Check version compatibility, serialization and override scope. Do not infer the effective style from `default`: upstream behavior can depend on options such as variable layer height or support-interface material. See Bambu's [configuration definitions](https://raw.githubusercontent.com/bambulab/BambuStudio/master/src/libslic3r/PrintConfig.cpp).

Auto placement does not select the best family for the project. Hybrid can generate normal-style regions beneath broad flat overhangs, so square-looking supports do not alone establish an incorrect type. This behavior is also explained by a Bambu contributor in [issue #2362](https://github.com/bambulab/BambuStudio/issues/2362); its historical default must not be assumed for newer versions.

Use manual placement or supported painting/blockers when targeted support is appropriate, checking that required regions remain covered. Enable `support_on_build_plate_only` only if all necessary regions remain reachable.

## Preserve fit and practical removability

Keep validated `support_top_z_distance`, `support_bottom_z_distance`, `support_object_xy_distance` and interface settings unless a specific failure warrants adjustment. A type change does not justify closing calibrated gaps. Assess interface coverage separately from the support trunk or grid; fewer contacts can leave a poor bearing or visible surface.

Check that supports can be gripped and removed without breaking an antenna, latch, thin wall or small axle. Keep them out of moving gaps. Inspect tall branches and towers for narrow anchors and excessive leverage, including bed motion. A stronger style is only a candidate, not a cure for an inaccessible or unstable support layout.

## Diagnose a missing support locally

Before another trial, locate the part and the exact first unsupported toolpaths in the sliced layers. Inspect the surface below, bridge anchoring, actual support/interface layers and available vertical/XY space. Check effective object settings, including placement restrictions and any installed small-overhang filtering such as `support_remove_small_overhang`. Merely enabling supports or changing family does not establish coverage of that region.

In a narrow cavity, the available space may not accommodate the requested top/bottom separation and a printable support/interface layer. Check the generated layers rather than relying on a nominal gap calculation. Change only the implicated settings or geometry, then inspect the same region again. Smaller separation can increase adhesion, scarring and removal force; assess access and nearby fragile features before selecting it. Do not copy another part's contact distances as universal defaults or disable filtering globally to resolve one local defect.

Use a relevant part-only trial when it resolves the issue within the authorized scope, then verify the selected arrangement in the final delivered project. Follow [correct-frame checks](bambu.md#check-mechanical-regions-in-the-correct-frame) for automated support-exclusion tests.

## Compare only when useful

When slicing is authorized and both families are plausible, compare at most two credible candidates on the affected parts with the same orientation and other settings. Inspect coverage, stability, contact locations and cleanup access before comparing time and material. Record support-only estimates only when reported by the slicer.

Keep one selected project; internal comparisons do not require extra delivered variants. If estimates or layer previews are unavailable, report a proposed choice and its uncertainty. Do not rerun a whole release for a documentation change.

Report the selected type and style, affected part IDs, reason, removal risks and remaining checks. Use supported object overrides where possible; do not force one family onto all parts simply because they share a plate. If required differences cannot be expressed on one plate, explain the limitation and use the minimum compatible arrangement.
