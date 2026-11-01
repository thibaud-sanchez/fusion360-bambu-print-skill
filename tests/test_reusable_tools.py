"""Standalone regressions; live Fusion smoke tests are project-side evidence."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace as NS, ModuleType
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
mesh = NS(**runpy.run_path(str(ROOT/"scripts/meshcheck.py")))
snapshot = NS(**runpy.run_path(str(ROOT/"scripts/fusion_snapshot.py")))
export = NS(**runpy.run_path(str(ROOT/"scripts/export_parts.py")))


def cube(offset=(0, 0, 0), size=(10, 4, 2)):
    vertices = [(offset[0]+x*size[0], offset[1]+y*size[1], offset[2]+z*size[2])
                for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    faces = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
             (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return [tuple(v for i in face for v in vertices[i]) for face in faces]


class MeshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def file(self, records, name="part.stl"):
        p = self.root/name; mesh.write_binary(p, records); return p

    def test_closed_cube_dimensions_and_volume(self):
        p = self.file(cube())
        report = mesh.inspect(p, dimensions_mm=[10, 4, 2])
        self.assertEqual(report["status"], "pass", report)
        self.assertAlmostEqual(report["signed_volume_mm3"], 80)
        self.assertEqual(report["edge_connected_shells"], 1)

    def test_missing_face_fails_closure(self):
        report = mesh.inspect(self.file(cube()[:-1]))
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["boundary_edges"], 3)

    def test_reversed_facet_fails_winding(self):
        records = cube(); a = records[0]; records[0] = a[:3]+a[6:9]+a[3:6]
        report = mesh.inspect(self.file(records))
        self.assertGreater(report["inconsistent_winding_edges"], 0)

    def test_reversed_shell_fails_signed_volume(self):
        records = [a[:3]+a[6:9]+a[3:6] for a in cube()]
        self.assertEqual(mesh.inspect(self.file(records))["status"], "fail")

    def test_two_captive_shells_need_explicit_count(self):
        p = self.file(cube()+cube((20, 0, 0)))
        self.assertEqual(mesh.inspect(p)["status"], "fail")
        self.assertEqual(mesh.inspect(p, expected_components=2)["status"], "pass")

    def test_point_contact_does_not_merge_shells(self):
        p = self.file(cube()+cube((10, 4, 2)))
        report = mesh.inspect(p, expected_components=2)
        self.assertEqual(report["edge_connected_shells"], 2)
        self.assertIn("shells_touching_at_vertices", {f["code"] for f in report["findings"]})

    def test_duplicate_facet_fails_nonmanifold_check(self):
        records = cube(); records.append(records[0])
        self.assertGreater(mesh.inspect(self.file(records))["nonmanifold_edges"], 0)

    def test_units_are_explicit_and_scale_is_checked(self):
        p = self.file(cube(size=(1, .4, .2)))
        self.assertEqual(mesh.inspect(p, dimensions_mm=[10, 4, 2])["status"], "fail")
        self.assertEqual(mesh.inspect(p, scale=10, dimensions_mm=[10, 4, 2])["status"], "pass")

    def test_ascii_and_binary_with_solid_header(self):
        p = self.file(cube())
        data = p.read_bytes(); p.write_bytes(b"solid misleading".ljust(80, b" ")+data[80:])
        self.assertEqual(mesh.inspect(p)["status"], "pass")
        ascii_path = self.root/"ascii.stl"
        lines = ["solid cube"]
        for tri in cube():
            lines += ["facet normal 0 0 0", "outer loop"]
            lines += ["vertex "+" ".join(map(str, tri[i:i+3])) for i in (0, 3, 6)]
            lines += ["endloop", "endfacet"]
        lines.append("endsolid cube"); ascii_path.write_text("\n".join(lines))
        self.assertEqual(mesh.inspect(ascii_path)["status"], "pass")

    def test_truncated_and_nonfinite_inputs_are_incomplete(self):
        p = self.file(cube()); p.write_bytes(p.read_bytes()[:-1])
        output = io.StringIO()
        with contextlib.redirect_stdout(output): status = mesh.main([str(p)])
        self.assertEqual(status, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "incomplete")

    def test_report_cannot_overwrite_stl(self):
        p = self.file(cube()); before = p.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()): status = mesh.main([str(p), "--report", str(p)])
        self.assertEqual(status, 2); self.assertEqual(p.read_bytes(), before)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.plan = {"schema_version": 1, "document": "Test assembly", "parts": [
            {"id": "B1", "occurrence": "@root", "bodies": ["One"], "frame": "component", "file": "B1_Base.stl"}]}

    def write_plan(self):
        p = self.root/"plan.json"; p.write_text(json.dumps(self.plan)); return p

    def fake_fusion(self, fail=False):
        class Manager:
            def createSTLExportOptions(_, body, filename): return NS(body=body, filename=filename)
            def execute(_, options):
                if fail: return False
                mesh.write_binary(options.filename, cube(options.body.offset))
                return True
        doc = NS(name="Test assembly", isModified=False, isSaved=False, dataFile=None)
        body = NS(name="One", isSolid=True, offset=(0, 0, 0))
        other = NS(name="Two", isSolid=True, offset=(20, 0, 0))
        design = NS(rootComponent=NS(bRepBodies=[body, other], allOccurrences=[]), exportManager=Manager())
        app = NS(activeDocument=doc)
        adsk = ModuleType("adsk"); fusion = ModuleType("adsk.fusion")
        fusion.DistanceUnits = NS(MillimeterDistanceUnits="mm")
        fusion.MeshRefinementSettings = NS(MeshRefinementHigh="high")
        adsk.fusion = fusion
        return app, doc, design, {"adsk": adsk, "adsk.fusion": fusion}

    def test_unknown_or_escaping_plan_is_rejected(self):
        for name in ("../B1.stl", "B1/part.stl", "B1\\part.stl"):
            self.plan["parts"][0]["file"] = name
            with self.assertRaises(ValueError): export.load_plan(self.write_plan())

    def test_missing_body_is_detected_before_publication(self):
        app, doc, design, _ = self.fake_fusion()
        self.plan["parts"][0]["bodies"] = ["Missing"]
        with self.assertRaises(ValueError): export.bind_parts(design, self.plan)

    def test_successful_export_and_shared_group_translation(self):
        app, doc, design, modules = self.fake_fusion()
        self.plan["parts"][0].update(bodies=["One", "Two"], rotation_xyz_deg=[0, 0, 90], expected_components=2)
        plan = self.write_plan(); out = self.root/"exports"
        with patch.dict(sys.modules, modules), patch.object(export.snapshot, "active_design", return_value=(app, doc, design)), contextlib.redirect_stdout(io.StringIO()):
            report = export.export_plan(plan, out)
        row = report["parts"][0]
        self.assertEqual(row["dimensions_mm"], [4, 30, 2])
        self.assertEqual(row["edge_connected_shells"], 2)
        self.assertTrue((out/"exports.json").exists())
        self.assertEqual(json.loads((out/"exports.json").read_text())["parts"][0]["units"], "mm")
        self.assertFalse(doc.isModified)

    def test_failed_native_export_publishes_no_files(self):
        app, doc, design, modules = self.fake_fusion(fail=True)
        out = self.root/"exports"
        with patch.dict(sys.modules, modules), patch.object(export.snapshot, "active_design", return_value=(app, doc, design)):
            with self.assertRaises(RuntimeError): export.export_plan(self.write_plan(), out)
        self.assertFalse(out.exists())

    def test_existing_delivery_is_not_overwritten_by_default(self):
        app, doc, design, modules = self.fake_fusion()
        out = self.root/"exports"; out.mkdir(); target = out/"B1_Base.stl"; target.write_bytes(b"preserve")
        with patch.dict(sys.modules, modules), patch.object(export.snapshot, "active_design", return_value=(app, doc, design)):
            with self.assertRaises(FileExistsError): export.export_plan(self.write_plan(), out)
        self.assertEqual(target.read_bytes(), b"preserve")

    def test_active_document_guard_rejects_other_project(self):
        adsk = ModuleType("adsk"); core = ModuleType("adsk.core"); fusion = ModuleType("adsk.fusion")
        core.Application = NS(get=lambda: NS(activeDocument=NS(name="Unrelated")))
        adsk.core, adsk.fusion = core, fusion
        with patch.dict(sys.modules, {"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion}):
            with self.assertRaises(ValueError): snapshot.active_design("Expected")

    def test_export_preserves_assembly_rotation_and_cm_translation(self):
        app, doc, design, modules = self.fake_fusion()
        matrix = [0, -1, 0, 4, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        occurrence = NS(fullPathName="B1:1", component=design.rootComponent, transform2=NS(asArray=lambda: matrix))
        design.rootComponent.allOccurrences = [occurrence]
        self.plan["parts"][0].update(occurrence="B1:1", frame="assembly", normalize=False)
        with patch.dict(sys.modules, modules), patch.object(export.snapshot, "active_design", return_value=(app, doc, design)), contextlib.redirect_stdout(io.StringIO()):
            report = export.export_plan(self.write_plan(), self.root/"exports")
        self.assertEqual(report["parts"][0]["bounds_mm"], [36, 0, 0, 40, 10, 2])


if __name__ == "__main__":
    unittest.main()
