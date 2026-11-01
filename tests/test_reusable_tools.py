"""Standalone regressions; live Fusion smoke tests are project-side evidence."""
import contextlib
import io
import json
import base64
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace as NS, ModuleType
import unittest
import xml.etree.ElementTree as ET
import struct
import zlib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
mesh = NS(**runpy.run_path(str(ROOT/"scripts/meshcheck.py")))
snapshot = NS(**runpy.run_path(str(ROOT/"scripts/fusion_snapshot.py")))
export = NS(**runpy.run_path(str(ROOT/"scripts/export_parts.py")))
preview = NS(**runpy.run_path(str(ROOT/"scripts/stl_preview.py")))


def cube(offset=(0, 0, 0), size=(10, 4, 2)):
    vertices = [(offset[0]+x*size[0], offset[1]+y*size[1], offset[2]+z*size[2])
                for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    faces = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
             (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return [tuple(v for i in face for v in vertices[i]) for face in faces]


def ring():
    outer = [(-5, -5), (5, -5), (5, 5), (-5, 5)]
    inner = [(-4, -4), (4, -4), (4, 4), (-4, 4)]
    result = []
    for i in range(4):
        j = (i+1) % 4
        a, b, c, d = (*outer[i], 0), (*outer[j], 0), (*inner[j], 0), (*inner[i], 0)
        aa, bb, cc, dd = (a[0], a[1], 2), (b[0], b[1], 2), (c[0], c[1], 2), (d[0], d[1], 2)
        for quad in [(aa, bb, cc, dd), (a, d, c, b), (a, b, bb, aa), (d, dd, cc, c)]:
            result += [tuple(v for p in (quad[0], quad[1], quad[2]) for v in p),
                       tuple(v for p in (quad[0], quad[2], quad[3]) for v in p)]
    return result


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

    def test_flat_contact_uses_area_not_triangles_or_bounding_box(self):
        report = mesh.inspect(self.file(ring()))
        self.assertEqual(report["status"], "pass", report["findings"])
        self.assertAlmostEqual(report["bed_contact"]["projected_face_area_sum_mm2"], 36)
        self.assertAlmostEqual(report["bed_contact"]["fraction_of_xy_rectangle"], .36)

    def test_bed_plane_does_not_silently_drop_a_floating_model(self):
        p = self.file(cube(offset=(0, 0, 10)))
        report = mesh.inspect(p)
        self.assertEqual(report["bed_contact"]["projected_face_area_sum_mm2"], 0)
        self.assertIn("above_bed", {w["code"] for w in report["warnings"]})
        self.assertAlmostEqual(mesh.inspect(p, bed_z_mm=10)["bed_contact"]["projected_face_area_sum_mm2"], 40)

    def test_point_contact_and_small_base_are_advisories(self):
        points = [(0, 0, 0), (-1, -1, 5), (1, -1, 5), (0, 1, 5)]
        records = [tuple(v for i in face for v in points[i]) for face in [(1, 2, 3), (0, 2, 1), (0, 3, 2), (0, 1, 3)]]
        report = mesh.inspect(self.file(records))
        self.assertEqual(report["status"], "pass")
        self.assertIn("no_flat_bed_contact", {w["code"] for w in report["warnings"]})
        report = mesh.inspect(self.file(cube(size=(.2, .2, 5))))
        self.assertEqual(report["status"], "pass")
        self.assertIn("small_bed_contact", {w["code"] for w in report["warnings"]})

    def test_contact_band_clips_faces_instead_of_counting_whole_face(self):
        area = mesh.clipped_area_xy([(0, 0, -1), (2, 0, 1), (0, 2, 1)], -.1, .1)
        self.assertAlmostEqual(area, .2)

    def test_contact_estimate_is_unavailable_for_bad_winding(self):
        records = [a[:3]+a[6:9]+a[3:6] for a in cube()]
        report = mesh.inspect(self.file(records))
        self.assertEqual(report["bed_contact"]["status"], "unavailable")
        self.assertIsNone(report["bed_contact"]["projected_face_area_sum_mm2"])

    def test_contact_threshold_does_not_change_topology_exit_status(self):
        p = self.file(cube(size=(.2, .2, 5)))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = mesh.main([str(p), "--min-contact-mm2", "2"])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(output.getvalue())["results"][0]["warnings"])


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def file(self, records):
        p = self.root/"A1_Part.stl"; mesh.write_binary(p, records); return p

    def raw_pixels(self, data):
        pos, compressed = 8, b""
        while pos < len(data):
            size = struct.unpack_from(">I", data, pos)[0]
            if data[pos+4:pos+8] == b"IDAT": compressed += data[pos+8:pos+8+size]
            pos += size+12
        return zlib.decompress(compressed)

    def test_multi_view_svg_is_self_contained_and_source_unchanged(self):
        p = self.file(cube()); before = p.read_bytes(); target = self.root/"preview.svg"
        report = preview.preview(p, target, size=64)
        self.assertEqual(report["dimensions_mm"], [10, 4, 2])
        self.assertEqual(report["views"], ["front", "right", "top", "iso"])
        root = ET.parse(target).getroot()
        images = root.findall("{http://www.w3.org/2000/svg}image")
        self.assertEqual(len(images), 4)
        for node in images:
            pixels = self.raw_pixels(base64.b64decode(node.get("href").split(",", 1)[1]))
            self.assertGreater(len(set(pixels)), 4)  # Geometry, not just a background.
        self.assertEqual(p.read_bytes(), before)

    def test_depth_buffer_keeps_nearer_triangle_regardless_of_order(self):
        near = (-1, 0, -1, 1, 0, -1, 0, 0, 1)
        far = (-1, 10, -1, 1, 10, -1, 0, 14, 1)
        def image(records):
            p = self.file(records); lo, hi, _ = preview.bounds_of(p, 1)
            png, _ = preview.render(p, "front", lo, hi, size=64)
            return self.raw_pixels(png)
        expected, distant = image([near]), image([far])
        self.assertNotEqual(expected, distant)
        self.assertEqual(image([near, far]), expected)
        self.assertEqual(image([far, near]), expected)

    def test_scale_is_explicit(self):
        p = self.file(cube(size=(1, .4, .2)))
        report = preview.preview(p, self.root/"preview.svg", views=["iso"], size=64, scale=10)
        for actual, wanted in zip(report["dimensions_mm"], [10, 4, 2]):
            self.assertAlmostEqual(actual, wanted, places=5)

    def test_preview_cannot_overwrite_source(self):
        p = self.file(cube()); before = p.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            status = preview.main([str(p), "--output", str(p)])
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
