"""Read a named active Fusion design in one call. Run inside Fusion, not a shell.

Call collect(document_name, report_path, ...) from the existing MCP script route.
No geometry, selection, camera or document-activation changes are performed.
"""
import json
from pathlib import Path
import re

VERSION = "1.0.0"


def active_design(document_name, data_file_id=None):
    import adsk.core as C
    import adsk.fusion as F
    app = C.Application.get()
    doc = app.activeDocument
    if not document_name or not doc or doc.name != document_name:
        raise ValueError("Active document does not match the explicit document name; nothing was changed")
    if data_file_id is None and sum(d.name == document_name for d in app.documents) != 1:
        raise ValueError("Document name is ambiguous; supply its data_file_id")
    if data_file_id is not None and (not doc.dataFile or doc.dataFile.id != data_file_id):
        raise ValueError("Active document data-file ID does not match")
    design = F.Design.cast(app.activeProduct)
    if not design or design.parentDocument != doc:
        raise ValueError("The active product is not the requested Fusion design")
    return app, doc, design


def document_record(doc):
    data = doc.dataFile
    return {"name": doc.name, "is_modified": doc.isModified, "is_saved": doc.isSaved,
            "data_file_id": data.id if data else None, "cloud_version": data.versionNumber if data else None}


def body_record(body):
    box = body.preciseBoundingBox
    lo = [10*getattr(box.minPoint, a) for a in "xyz"]
    hi = [10*getattr(box.maxPoint, a) for a in "xyz"]
    return {"name": body.name, "entity_token": body.entityToken, "solid": body.isSolid,
            "visible": body.isVisible, "bounds_mm": lo+hi, "dimensions_mm": [hi[i]-lo[i] for i in range(3)],
            "volume_mm3": body.volume*1000 if body.isSolid else None}


def occurrence_bindings(design):
    return {o.fullPathName: o for o in design.rootComponent.allOccurrences}


def collect(document_name, report_path, *, data_file_id=None, capture_path=None,
            width=1200, height=900, overwrite=False):
    import adsk.fusion as F
    app, doc, design = active_design(document_name, data_file_id)
    report_path = Path(report_path)
    if report_path.suffix.lower() != ".json": raise ValueError("Use a .json report path")
    paths = [report_path] + ([Path(capture_path)] if capture_path else [])
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError("Report and capture paths must differ")
    if capture_path and Path(capture_path).suffix.lower() != ".png":
        raise ValueError("Use a .png capture path")
    if width <= 0 or height <= 0: raise ValueError("Image size must be positive")
    for path in paths:
        if path.exists() and not overwrite: raise FileExistsError(str(path))
    before = document_record(doc)
    root, rows, components = design.rootComponent, [], {}

    def component_row(component, path, bodies, occurrence=None):
        match = re.match(r"^([A-Z]+\d+)(?=$|[^A-Za-z0-9])", component.name)
        row = {"part_id": match.group(1) if match else None, "component": component.name,
               "occurrence_path": path, "bodies": [body_record(b) for b in bodies],
               "mesh_body_count": component.meshBodies.count}
        if occurrence:
            row.update(visible=occurrence.isVisible, grounded=occurrence.isGrounded,
                       transform_fusion_cm=list(occurrence.transform2.asArray()))
        rows.append(row)
        components[component.entityToken] = component

    component_row(root, "@root", root.bRepBodies)
    for path, occurrence in occurrence_bindings(design).items():
        component_row(occurrence.component, path, occurrence.bRepBodies, occurrence)
    joints = []
    for component in components.values():
        for kind, collection in (("joint", component.joints), ("as_built_joint", component.asBuiltJoints)):
            for joint in collection:
                motion = joint.jointMotion
                row = {"component": component.name, "name": joint.name, "kind": kind,
                       "motion_type": int(motion.jointType), "suppressed": joint.isSuppressed}
                joints.append(row)
    health = []
    for item in design.timeline:
        entity = item.entity
        if hasattr(entity, "healthState") and entity.healthState != F.FeatureHealthStates.HealthyFeatureHealthState:
            health.append({"name": item.name, "message": entity.errorOrWarningMessage})
    parameters = [{"name": p.name, "expression": p.expression, "unit": p.unit, "internal_value": p.value}
                  for p in design.userParameters]
    report = {"tool": "fusion_snapshot", "version": VERSION, "application_version": app.version,
              "document": before, "components": rows, "joints": joints, "user_parameters": parameters,
              "timeline_features": design.timeline.count, "feature_health_issues": health,
              "limits": "Measurements reflect the current pose. Raw Fusion matrices use cm translations; reported bounds and volumes use mm/mm3. No motion, collision, assembly or strength validation."}
    for path in paths: path.parent.mkdir(parents=True, exist_ok=True)
    if app.activeDocument != doc:
        raise RuntimeError("Active document changed during snapshot")
    if capture_path:
        if not app.activeViewport.saveAsImageFile(str(Path(capture_path).resolve()), width, height):
            raise RuntimeError("Viewport capture failed")
        report["capture"] = str(capture_path)
    if app.activeDocument != doc or document_record(doc) != before:
        raise RuntimeError("Document state changed during snapshot; inspect before using the result")
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    summary = {"tool": "fusion_snapshot", "document": doc.name, "occurrences": len(rows)-1,
               "bodies": sum(len(r["bodies"]) for r in rows), "joints": len(joints),
               "parameters": len(parameters), "feature_health_issues": len(health), "report": str(report_path)}
    print(json.dumps(summary))
    return report


def run(_context: str):
    """Fusion Scripts entry point: pass a JSON settings-file path as context."""
    settings = json.loads(Path(_context).read_text(encoding="utf-8"))
    collect(**settings)


if __name__ == "__main__":
    raise SystemExit("Run collect inside Fusion through its existing script/MCP route; see references/reusable-tools.md")
