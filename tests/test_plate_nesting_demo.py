import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from plate_nesting_demo import pack_shelf  # noqa: E402


class PlateNestingDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data" / "plate_nesting_cases.json").open(encoding="utf-8") as handle:
            cls.data = json.load(handle)
        cls.stock = cls.data["stock"]

    def _result(self, improved):
        return pack_shelf(
            self.data["parts"], self.stock["width_mm"], self.stock["height_mm"],
            kerf_mm=self.stock["kerf_mm"], edge_trim_mm=self.stock["edge_trim_mm"],
            improved=improved,
        )

    def test_both_methods_place_every_synthetic_part(self):
        for improved in (False, True):
            result = self._result(improved)
            self.assertEqual(result["placed_piece_count"], result["input_piece_count"])
            self.assertEqual(result["unplaced_part_ids"], [])

    def test_best_fit_decreasing_uses_fewer_plates_for_this_case(self):
        baseline = self._result(False)
        improved = self._result(True)
        self.assertLess(improved["plates_used"], baseline["plates_used"])

    def test_placements_stay_within_usable_sheet_and_do_not_overlap(self):
        usable_w = self.stock["width_mm"] - 2 * self.stock["edge_trim_mm"]
        usable_h = self.stock["height_mm"] - 2 * self.stock["edge_trim_mm"]
        for improved in (False, True):
            result = self._result(improved)
            by_plate = {}
            for item in result["placements"]:
                x, y = item["x_mm"], item["y_mm"]
                w = item["placed_width_mm_including_kerf"]
                h = item["placed_height_mm_including_kerf"]
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, usable_w + 1e-9)
                self.assertLessEqual(y + h, usable_h + 1e-9)
                by_plate.setdefault(item["plate_number"], []).append((x, y, w, h))
            for rects in by_plate.values():
                for i, a in enumerate(rects):
                    for b in rects[i + 1:]:
                        ax, ay, aw, ah = a
                        bx, by, bw, bh = b
                        overlaps = (ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by)
                        self.assertFalse(overlaps, f"placements overlap: {a} and {b}")

    def test_invalid_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            pack_shelf([{"part_id": "bad", "width_mm": 0, "height_mm": 12}], 1000, 800)


if __name__ == "__main__":
    unittest.main()
