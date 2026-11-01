# FDM checks

During architecture and geometry design, first apply [Design for reliable FDM printing](design-for-reliable-printing.md). Choose the build orientation and landing surfaces before treating supports as a remedy, then perform the checks below.

Check the overall envelope against the actual printable volume; body count and bed contact; closed, nondegenerate meshes and disconnected regions; walls, small details, bridges, and overhangs; stability and adhesion area. Compare candidate orientations for supports, visible surfaces, time, and load direction, including weakness across layer boundaries. A disconnected model region can be printable when suitable supports are provided.

A native body reported as solid with one lump can still contain a tangential, zero-thickness connection that exports as a nonmanifold edge. Join load-bearing roots through a finite area, not only a shared edge or point. Locate a failed mesh connection and correct its native geometry; do not hide a structural disconnection with automatic slicer repair or silently discard a component.

For small contact patches, slender parts or lifting risk, apply the selective-brim assessment in [choose-print-configuration](choose-print-configuration.md#choose-brims-from-actual-bed-contact). Inspect actual first-layer contact and removal access rather than adding a brim based only on overall part size.

Relate wall thickness to extrusion width and function. Inspect the slice to confirm that thin features receive actual toolpaths. Overhang behavior depends on material, cooling, orientation, and the angle convention: 45 degrees is a useful starting heuristic, not a universal limit. Chamfers, self-supporting shapes, or splitting a part can help when they preserve function. Assess bridges and cantilevers in their real printing orientation.

For assemblies, distinguish clearance per side from total or diametral clearance and make critical values editable. Printed fit depends on material, axis direction, calibration, and slicer behavior; use a small fit coupon when the interface is critical. For loaded or heated parts, choose material, orientation, and thickness for the actual service conditions. Geometry checks do not establish strength in service.

Use available measurement or analysis tools and identify units, orientation, method, and limitations. A rendered image cannot establish an exact minimum wall thickness. Report missing or partial measurements as unknown. Automated checks can miss defects and do not replace slice inspection or a physical test.

For functional load paths, latch roots, orientation tradeoffs, failure diagnosis, assembly access and print-in-place alternatives, use [Mechanical orientation and assembly](mechanical-orientation-and-assembly.md). Select orientation before finalizing interfaces and process settings.
