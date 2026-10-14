import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from remnant_matcher import candidate_result, match_remnants  # noqa: E402


class RemnantMatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data" / "synthetic_cases.json").open(encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_same_project_plate_is_eligible(self):
        offcut = self.data["offcuts"][0]
        part = self.data["requirements"][0]
        result = candidate_result(offcut, part, self.data["policy"])
        self.assertTrue(result["eligible"], result["reason"])

    def test_cross_project_reuse_blocked_without_approval(self):
        offcut = self.data["offcuts"][1]
        part = self.data["requirements"][0]
        result = candidate_result(offcut, part, self.data["policy"])
        self.assertFalse(result["eligible"])
        self.assertIn("project_transfer_not_authorised", result["reason"])

    def test_draft_revision_is_rejected(self):
        offcut = self.data["offcuts"][0]
        part = self.data["requirements"][3]
        result = candidate_result(offcut, part, self.data["policy"])
        self.assertFalse(result["eligible"])
        self.assertIn("part_revision_not_released", result["reason"])

    def test_hold_offcut_is_rejected(self):
        offcut = self.data["offcuts"][3]
        part = self.data["requirements"][0]
        result = candidate_result(offcut, part, self.data["policy"])
        self.assertFalse(result["eligible"])
        self.assertIn("offcut_not_available", result["reason"])

    def test_matcher_does_not_assign_offcut_twice(self):
        result = match_remnants(self.data)
        matched_ids = [m["offcut_id"] for m in result["matches"]]
        self.assertEqual(len(matched_ids), len(set(matched_ids)))


if __name__ == "__main__":
    unittest.main()
