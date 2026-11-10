"""只使用非文字合成图形；这些测试不证明东巴文真实样本准确率。"""
import base64
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw
from jsonschema import Draft202012Validator, ValidationError

from components.handwriting_canvas import decode_canvas
from services.dongba_data import DATA_DIR, geometry_reference, load_catalog
from services.dongba_evaluator import MISMATCH, binarize, edit_photo, evaluate


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.reference = geometry_reference()

    def test_identical_and_natural_scale_translation(self):
        exact = evaluate(self.reference, self.reference)
        self.assertEqual(exact["similarity"], 100)
        self.assertEqual(exact["status"], "close")
        self.assertIsNone(exact["is_correct"])
        variant = Image.new("RGB", (800, 700), "white")
        variant.paste(self.reference.resize((360, 360)), (240, 160))
        result = evaluate(self.reference, variant)
        self.assertGreater(result["similarity"], 90)

    def test_wrong_shape_and_blank(self):
        wrong = Image.new("RGB", (480, 480), "white")
        ImageDraw.Draw(wrong).line((50, 240, 430, 240), fill="black", width=12)
        result = evaluate(self.reference, wrong)
        self.assertEqual(result["status"], "mismatch")
        self.assertEqual(result["summary"], MISMATCH)
        self.assertFalse(result["is_correct"])
        for color in ["white", "black"]:
            result = evaluate(self.reference, Image.new("RGB", (480, 480), color))
            self.assertEqual(result["status"], "invalid")
            self.assertIsNone(result["similarity"])

    def test_missing_structure_and_direction(self):
        missing = self.reference.copy()
        ImageDraw.Draw(missing).rectangle((0, 0, 480, 245), fill="white")
        result = evaluate(self.reference, missing)
        self.assertNotEqual(result["status"], "close")
        self.assertTrue(result["structure_errors"])
        rotated = evaluate(self.reference, self.reference.rotate(90))
        self.assertNotEqual(rotated["status"], "close")
        self.assertTrue(any("方向" in e for e in rotated["structure_errors"]))

    def test_preprocessing_and_transport(self):
        output = edit_photo(self.reference, 90, (10, 10, 90, 90))
        self.assertEqual(output.size, (384, 384))
        with self.assertRaises(ValueError):
            edit_photo(self.reference, crop=(80, 0, 20, 100))
        self.assertEqual(binarize(self.reference, remove_background=True).mode, "L")
        buffer = BytesIO()
        self.reference.save(buffer, format="PNG")
        restored = decode_canvas("data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode())
        self.assertEqual(evaluate(self.reference, restored)["similarity"], 100)
        for invalid in [None, "data:image/png;base64,@@@", "<script>"]:
            with self.assertRaises(ValueError):
                decode_canvas(invalid)

    def test_transparent_background(self):
        image = Image.new("RGBA", (480, 480))
        ImageDraw.Draw(image).ellipse((100, 100, 300, 300), outline="black", width=10)
        result = evaluate(image, image)
        self.assertEqual(result["similarity"], 100)


class CatalogTests(unittest.TestCase):
    def entry(self):
        return {"character_id": "test-only", "reference_image": "fixture.png", "chinese_meaning": "非文字测试",
                "structure_description": "测试图形", "learning_tips": "仅用于测试", "data_source": "synthetic_test",
                "review_status": "verified", "usage_permission": "authorized", "reviewer": "test", "reviewed_at": "test"}

    def test_empty_catalog_and_schema(self):
        self.assertEqual(load_catalog(), [])
        for name in ["characters.schema.json", "training_record.schema.json"]:
            Draft202012Validator.check_schema(json.loads((DATA_DIR/name).read_text(encoding="utf-8")))

    def test_import_review_gate_and_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            geometry_reference().save(root / "fixture.png")
            entry = self.entry()
            def write(entries):
                (root / "characters.json").write_text(json.dumps(entries), encoding="utf-8")
            write([entry])
            self.assertEqual(len(load_catalog(root)), 1)
            entry["review_status"] = "pending"
            write([entry])
            self.assertEqual(load_catalog(root), [])
            entry["review_status"] = "verified"
            entry["reference_image"] = "../outside.png"
            write([entry])
            with self.assertRaises(ValueError):
                load_catalog(root)
            entry["reference_image"] = "fixture.png"
            write([entry, entry])
            with self.assertRaises(ValueError):
                load_catalog(root)

    def test_prototype_score_is_not_training_label(self):
        schema = json.loads((DATA_DIR / "training_record.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        record = {"character_id": "test", "reference_image": "reference.png", "user_handwriting_image": "user.png",
                  "similarity_label": None, "structure_errors": [], "evaluation_feedback": [], "data_source": "test",
                  "consent": False, "label_source": "unlabeled", "prototype_score": 88}
        validator.validate(record)
        record["similarity_label"] = .88
        with self.assertRaises(ValidationError):
            validator.validate(record)


if __name__ == "__main__":
    unittest.main()
