"""Behavioral regression tests. Run: python3 -m unittest discover -s tests -v"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "printcheck.py"
spec = importlib.util.spec_from_file_location("printcheck", SCRIPT)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
IDENTITY = "1 0 0 0 1 0 0 0 1 0 0 0"
GCODE = """; FEATURE: Custom
G90
M83
G1 X10 Y10 Z0.2
; FEATURE: Outer wall
; LINE_WIDTH: 0.4
; LAYER_HEIGHT: 0.2
G1 X20 E1
G1 Y20 E1
"""


class PrintcheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = pc.main([str(a) for a in args] + ["--json"])
        return status, json.loads(out.getvalue())

    def plan(self, **overrides):
        value = {"schema_version": 1, "scope": "complete", "plates": 1,
                 "parts": [{"id": "B1", "quantity": 1, "dimensions_mm": [10, 4, 2]}]}
        value.update(overrides)
        p = self.root / "expected.json"
        p.write_text(json.dumps(value))
        return p

    def project(self, transform=IDENTITY, copies=1, gcode=GCODE, name="B1_Base", plate_count=1,
                per_part="", nested=False):
        vertices = ''.join(f'<vertex x="{x}" y="{y}" z="{z}"/>'
                           for x in (10, 20) for y in (10, 14) for z in (0, 2))
        faces = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
                 (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
        triangles = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces)
        mesh = f'<model xmlns="{CORE}"><resources><object id="1"><mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object></resources></model>'
        child = '<component p:path="/3D/mesh.model" objectid="1"/>'
        if nested:
            inner = f'<object id="3"><components>{child}</components></object>'
            child = '<component objectid="3" transform="1 0 0 0 1 0 0 0 1 5 0 0"/>'
        else:
            inner = ""
        items = ''.join(f'<item objectid="2" transform="{transform}"/>' for _ in range(copies))
        model = f'<model xmlns="{CORE}" xmlns:p="{PROD}"><resources>{inner}<object id="2"><components>{child}</components></object></resources><build>{items}</build></model>'
        instances = ''.join(f'<model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="{i}"/></model_instance>' for i in range(copies))
        plates = f'<plate><metadata key="plater_id" value="1"/>{instances}</plate>' + '<plate/>'*(plate_count-1)
        settings = f'<config><object id="2"><metadata key="name" value="{name}"/><metadata key="wall_loops" value="3"/>{per_part}</object>{plates}</config>'
        p = self.root / "project.3mf"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("3D/3dmodel.model", model)
            z.writestr("3D/mesh.model", mesh)
            z.writestr("Metadata/model_settings.config", settings)
            z.writestr("Metadata/project_settings.config", json.dumps({"wall_loops": "2"}))
            if gcode is not None:
                z.writestr("Metadata/plate_1.gcode", gcode)
        return p

    def codes(self, report):
        return {x["code"] for x in report["findings"]}

    def test_valid_package_and_object_setting_precedence(self):
        plan = self.plan(parts=[{"id": "B1", "settings": {"wall_loops": 3}}],
                         settings={"wall_loops": 2}, bed_mm=[0, 0, 30, 30], require_gcode=True)
        source = self.project()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        status, report = self.run_tool("check", source, "--expect", plan)
        self.assertEqual(status, 0, report)
        self.assertEqual(report["project"]["objects"][0]["dimensions_mm"], [10, 4, 2])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest)

    def test_missing_part_and_unexpected_part_are_detected(self):
        plan = self.plan(parts=[{"id": "B1"}, {"id": "A1"}])
        status, report = self.run_tool("check", self.project(name="B10_Base"), "--expect", plan)
        self.assertEqual(status, 1)
        self.assertIn("part_quantity", self.codes(report))
        self.assertIn("unexpected_object", self.codes(report))

    def test_duplicate_instance_is_not_hidden_by_object_dictionary(self):
        status, report = self.run_tool("check", self.project(copies=2), "--expect", self.plan())
        self.assertEqual(status, 1)
        self.assertIn("part_quantity", self.codes(report))

    def test_rotation_is_detected_with_nested_component_translation(self):
        rotate = "0 1 0 -1 0 0 0 0 1 30 0 0"
        status, report = self.run_tool("check", self.project(transform=rotate, nested=True), "--expect", self.plan())
        self.assertEqual(status, 1)
        self.assertIn("dimensions_mismatch", self.codes(report))
        obj = report["project"]["objects"][0]
        self.assertEqual(obj["bounds_mm"], [16, 15, 0, 20, 25, 2])

    def test_transform_detects_rotation_of_a_symmetric_object(self):
        rotate = "-1 0 0 0 -1 0 0 0 1 40 40 0"
        plan = self.plan(parts=[{"id": "B1", "linear_transform": list(pc.IDENTITY[:9])}])
        status, report = self.run_tool("check", self.project(transform=rotate), "--expect", plan)
        self.assertEqual(status, 1)
        self.assertIn("orientation_mismatch", self.codes(report))

    def test_brim_or_support_outside_bed_is_detected(self):
        gcode = GCODE + "; FEATURE: Support\nG1 X31 E1\n"
        status, report = self.run_tool("check", self.project(gcode=gcode), "--expect", self.plan(bed_mm=[0, 0, 30, 30]))
        self.assertEqual(status, 1)
        self.assertIn("outside_bed", self.codes(report))

    def test_missing_gcode_is_incomplete_not_a_pass(self):
        status, report = self.run_tool("check", self.project(gcode=None), "--expect", self.plan(require_gcode=True))
        self.assertEqual(status, 2)
        self.assertIn("gcode_missing", self.codes(report))

    def test_external_gcode_needs_explicit_binding(self):
        g = self.root / "plate.gcode"
        g.write_text(GCODE)
        source = self.project(gcode=None)
        status, report = self.run_tool("check", source, "--expect", self.plan(), "--gcode", g)
        self.assertEqual(status, 2)
        self.assertIn("external_gcode_unbound", self.codes(report))
        plan = self.plan(gcode_sha256=pc.sha256(g))
        self.assertEqual(self.run_tool("check", source, "--expect", plan, "--gcode", g)[0], 0)

    def test_wrong_support_setting_is_detected(self):
        plan = self.plan(parts=[{"id": "B1", "settings": {"wall_loops": "4"}}])
        status, report = self.run_tool("check", self.project(), "--expect", plan)
        self.assertEqual(status, 1)
        self.assertIn("setting_mismatch", self.codes(report))

    def test_unresolved_volume_override_does_not_pass(self):
        part = '<part id="1" subtype="normal_part"><metadata key="wall_loops" value="5"/></part>'
        status, report = self.run_tool("check", self.project(per_part=part), "--expect", self.plan(parts=[{"id": "B1", "settings": {"wall_loops": "3"}}]))
        self.assertEqual(status, 2)
        self.assertIn("part_override", self.codes(report))

    def test_extra_plate_is_detected_and_spatial_scope_is_incomplete(self):
        status, report = self.run_tool("check", self.project(plate_count=2), "--expect", self.plan())
        self.assertEqual(status, 1)
        self.assertIn("plate_count", self.codes(report))
        self.assertIn("multiple_plate_frames", self.codes(report))

    def region(self, bounds):
        return [{"id": "bearing", "frame": "plate", "bounds_mm": bounds, "features": ["support"]}]

    def test_crossing_segment_hits_protected_region_not_just_endpoints(self):
        gc = GCODE + "; FEATURE: Support\nG1 X0 E1\n"
        plan = self.plan(protected_regions=self.region([8, 19, 0, 12, 21, 1]))
        status, report = self.run_tool("check", self.project(gcode=gc), "--expect", plan)
        self.assertEqual(status, 1)
        self.assertIn("protected_region_hit", self.codes(report))

    def test_wrong_coordinate_frame_cannot_produce_empty_pass(self):
        plan = self.plan(protected_regions=self.region([100, 100, 0, 102, 102, 1]))
        status, report = self.run_tool("check", self.project(), "--expect", plan)
        self.assertEqual(status, 2)
        self.assertIn("region_unlocated", self.codes(report))

    def test_arc_extremum_is_included_in_envelope(self):
        gc = GCODE + "G1 X20 Y10\nG3 X10 Y10 I-5 J0 E1\n"
        report = pc.Report("memory")
        pc.inspect_paths(io.StringIO(gc), {}, report, "memory")
        self.assertGreater(report.data["gcode"][0]["bead_envelope_bounds_mm"][4], 20)
        self.assertEqual(report.finish(), 0)

    def test_radius_form_and_full_circle_arcs(self):
        for code in ("G3 X10 Y10 R5 E1", "G2 X20 Y10 I-5 J0 E1"):
            report = pc.Report("memory")
            paths = list(pc.segments(io.StringIO(GCODE + "G1 X20 Y10\n"+code+"\n"), report))
            self.assertGreater(len(paths), 10)
            self.assertEqual(report.finish(), 0, report.data)

    def test_relative_coordinates_absolute_extrusion_and_g92_e(self):
        gc = GCODE + "M82\nG92 E0\nG91\nG1 X2 E1\n"
        paths = list(pc.segments(io.StringIO(gc), pc.Report("memory")))
        self.assertEqual(paths[-1][1], (22, 20, .2))

    def test_unknown_arc_or_coordinate_reset_is_incomplete(self):
        for code in ("G18\nG2 X10 E1 I-5", "G92 X0", "G1 Xnan Y22 E1"):
            report = pc.Report("memory")
            list(pc.segments(io.StringIO(GCODE + code + "\n"), report))
            self.assertEqual(report.finish(), 2, report.data)

    def test_no_annotations_is_incomplete(self):
        report = pc.Report("memory")
        pc.inspect_paths(io.StringIO("G1 X10 E1\n"), {}, report, "memory")
        self.assertEqual(report.finish(), 2)

    def test_svg_and_report_are_generated_without_modifying_source(self):
        source = self.root / "plate.gcode"
        source.write_text(GCODE)
        svg, report = self.root / "layer.svg", self.root / "report.json"
        status, result = self.run_tool("layers", source, "--z", .2, "--output", svg, "--report", report)
        self.assertEqual(status, 0, result)
        self.assertIn("<path", svg.read_text())
        self.assertEqual(json.loads(report.read_text())["status"], "pass")
        self.assertEqual(source.read_text(), GCODE)

    def test_input_cannot_be_overwritten_by_report(self):
        source = self.project()
        before = source.read_bytes()
        status, _ = self.run_tool("check", source, "--report", source)
        self.assertEqual(status, 2)
        self.assertEqual(source.read_bytes(), before)

    def test_unknown_manifest_key_is_rejected(self):
        status, report = self.run_tool("check", self.project(), "--expect", self.plan(plate=1))
        self.assertEqual(status, 2)
        self.assertIn("input_error", self.codes(report))

    def test_missing_setting_is_unverified_rather_than_a_value_mismatch(self):
        status, report = self.run_tool("check", self.project(), "--expect", self.plan(settings={"missing_profile_key": 3}))
        self.assertEqual(status, 2)
        self.assertIn("setting_unavailable", self.codes(report))

    def test_required_unknown_extension_is_incomplete(self):
        source = self.project()
        other = self.root / "unknown.3mf"
        with zipfile.ZipFile(source) as src, zipfile.ZipFile(other, "w") as dst:
            for item in src.infolist():
                data = src.read(item.filename)
                if item.filename == "3D/3dmodel.model":
                    data = data.replace(b'<model ', b'<model xmlns:other="urn:unsupported" requiredextensions="other" ', 1)
                dst.writestr(item.filename, data)
        status, report = self.run_tool("check", other, "--expect", self.plan())
        self.assertEqual(status, 2)
        self.assertIn("unsupported_input", self.codes(report))

    def test_permitted_yaw_does_not_fail_height_or_axis_checks(self):
        plan = self.plan(parts=[{"id": "B1", "height_mm": 2, "mesh_z_direction": [0, 0, 1]}])
        yaw = "0 1 0 -1 0 0 0 0 1 30 0 0"
        status, report = self.run_tool("check", self.project(transform=yaw), "--expect", plan)
        self.assertEqual(status, 0, report)

    def test_sideways_rotation_fails_when_yaw_is_allowed(self):
        plan = self.plan(parts=[{"id": "B1", "height_mm": 2, "mesh_z_direction": [0, 0, 1]}])
        tilt = "1 0 0 0 0 1 0 -1 0 0 20 0"
        status, report = self.run_tool("check", self.project(transform=tilt), "--expect", plan)
        self.assertEqual(status, 1)
        self.assertIn("height_mismatch", self.codes(report))
        self.assertIn("orientation_mismatch", self.codes(report))


if __name__ == "__main__":
    unittest.main()
