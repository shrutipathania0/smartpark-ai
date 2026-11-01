"""
Unit Tests for ANPR Text Validator and Normalizer
Tests Indian registration patterns, position-based character correction (O/0, I/1, B/8, S/5).
"""
import unittest
from anpr.plate_validator import (
    validate_and_normalize_plate,
    clean_ocr_text,
    normalize_standard_plate,
    normalize_bharat_series
)

class TestPlateValidator(unittest.TestCase):
    def test_clean_ocr_text(self):
        """Strips noise, punctuation, hyphens and converts to uppercase."""
        self.assertEqual(clean_ocr_text("dl-01-ab-1234"), "DL01AB1234")
        self.assertEqual(clean_ocr_text("MH.12.DE 5678"), "MH12DE5678")

    def test_standard_indian_plate_valid(self):
        """Standard format DL01AB1234 validation."""
        res = validate_and_normalize_plate("DL01AB1234")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["normalized_text"], "DL01AB1234")
        self.assertEqual(res["format_type"], "STANDARD")
        self.assertEqual(res["state_code"], "DL")

    def test_smart_character_disambiguation_digits_to_letters(self):
        """In state position (first 2 chars), 0 must become O, 1 must become I."""
        # OD (Odisha) with 0D
        res = validate_and_normalize_plate("0D02AB1234")
        self.assertEqual(res["normalized_text"], "OD02AB1234")
        self.assertEqual(res["state_code"], "OD")

    def test_smart_character_disambiguation_letters_to_digits(self):
        """In registration numbers (last 4 chars), O must become 0, B must become 8, I must become 1."""
        res = validate_and_normalize_plate("DL01AB12O4")
        self.assertEqual(res["normalized_text"], "DL01AB1204")

        res2 = validate_and_normalize_plate("MH12DEB123")
        self.assertEqual(res2["normalized_text"], "MH12DE8123")

    def test_bharat_series_validation(self):
        """Bharat Series 22BH1234AA."""
        res = validate_and_normalize_plate("22BH1234AA")
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["format_type"], "BHARAT_SERIES")
        self.assertEqual(res["normalized_text"], "22BH1234AA")

    def test_invalid_plate_flagging(self):
        """Unrecognized string flagged invalid with confidence penalty."""
        res = validate_and_normalize_plate("XYZ")
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["format_type"], "INVALID")
        self.assertGreater(res["confidence_penalty"], 0.2)

if __name__ == "__main__":
    unittest.main()

