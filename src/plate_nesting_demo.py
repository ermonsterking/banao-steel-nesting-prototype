"""Synthetic 2D plate packing comparison using simple shelf heuristics.

This is a teaching/demo heuristic, NOT an industrial nesting solver. Dimensions are
rectangular, rotation is optional, and kerf/edge trim are simplified. No client data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import argparse
import json


@dataclass
class Shelf:
    y_mm: float
    height_mm: float
    next_x_mm: float = 0.0


@dataclass
class Plate:
    shelves: list[Shelf] = field(default_factory=list)
    next_y_mm: float = 0.0


def _orientations(part: dict[str, Any], kerf_mm: float) -> list[tuple[float, float, str]]:
    w = float(part["width_mm"]) + kerf_mm
    h = float(part["height_mm"]) + kerf_mm
    out = [(w, h, "normal")]
    if part.get("allow_rotation", True) and w != h:
        out.append((h, w, "rotated"))
    return out


def _expand(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expanded = []
    for part in parts:
        qty = int(part.get("quantity", 1))
        if qty < 1:
            raise ValueError(f"quantity must be >= 1 for {part.get('part_id')}")
        for i in range(qty):
            p = dict(part)
            p["part_id"] = str(part["part_id"]) if qty == 1 else f"{part['part_id']}#{i + 1}"
            if float(p["width_mm"]) <= 0 or float(p["height_mm"]) <= 0:
                raise ValueError(f"part dimensions must be positive: {p['part_id']}")
            expanded.append(p)
    return expanded


def _can_place_in_shelf(shelf: Shelf, part: dict[str, Any], stock_w: float,
                         kerf: float) -> list[tuple[float, float, str]]:
    options = []
    for w, h, orientation in _orientations(part, kerf):
        if w <= stock_w - shelf.next_x_mm and h <= shelf.height_mm:
            options.append((w, h, orientation))
    return options


def _choose_new_shelf_orientation(part: dict[str, Any], stock_w: float,
                                  stock_h: float, y: float, kerf: float) -> tuple[float, float, str] | None:
    options = []
    for w, h, orientation in _orientations(part, kerf):
        if w <= stock_w and y + h <= stock_h:
            # Prefer the shorter shelf to leave more usable height, then less width waste.
            options.append((h, stock_w - w, w, orientation))
    if not options:
        return None
    h, _, w, orientation = min(options)
    return w, h, orientation


def pack_shelf(parts: list[dict[str, Any]], stock_width_mm: float, stock_height_mm: float,
               *, kerf_mm: float = 3.0, edge_trim_mm: float = 5.0,
               improved: bool = False) -> dict[str, Any]:
    """Pack rectangles with a simple shelf heuristic and return transparent metrics.

    Baseline is next-fit shelf packing in input order. Improved mode sorts by area
    descending and picks the best existing shelf before opening a new shelf/plate.
    Neither approach is globally optimal or suitable for direct CNC use.
    """
    if stock_width_mm <= 2 * edge_trim_mm or stock_height_mm <= 2 * edge_trim_mm:
        raise ValueError("edge trim leaves no usable stock area")
    usable_w = float(stock_width_mm) - 2 * edge_trim_mm
    usable_h = float(stock_height_mm) - 2 * edge_trim_mm
    expanded = _expand(parts)
    if improved:
        expanded.sort(key=lambda p: (float(p["width_mm"]) * float(p["height_mm"]),
                                     max(float(p["width_mm"]), float(p["height_mm"]))), reverse=True)

    plates: list[Plate] = []
    placements: list[dict[str, Any]] = []
    unplaced: list[str] = []

    def new_plate() -> Plate:
        plate = Plate()
        plates.append(plate)
        return plate

    for part in expanded:
        area = float(part["width_mm"]) * float(part["height_mm"])
        options_existing = []
        if improved:
            for pi, plate in enumerate(plates):
                for si, shelf in enumerate(plate.shelves):
                    for w, h, orientation in _can_place_in_shelf(shelf, part, usable_w, kerf_mm):
                        rem_x = usable_w - shelf.next_x_mm - w
                        rem_h = shelf.height_mm - h
                        options_existing.append(((rem_x, rem_h, pi, si), pi, si, w, h, orientation))
        else:
            if plates and plates[-1].shelves:
                pi, si = len(plates) - 1, len(plates[-1].shelves) - 1
                shelf = plates[pi].shelves[si]
                choices = _can_place_in_shelf(shelf, part, usable_w, kerf_mm)
                if choices:
                    w, h, orientation = min(choices, key=lambda o: (usable_w - shelf.next_x_mm - o[0], shelf.height_mm - o[1]))
                    options_existing.append(((0, 0, pi, si), pi, si, w, h, orientation))
        if options_existing:
            _, pi, si, w, h, orientation = min(options_existing, key=lambda item: item[0])
            plate = plates[pi]
            shelf = plate.shelves[si]
            x, y = shelf.next_x_mm, shelf.y_mm
            shelf.next_x_mm += w
            placements.append({"part_id": part["part_id"], "plate_number": pi + 1,
                               "x_mm": round(x, 2), "y_mm": round(y, 2),
                               "placed_width_mm_including_kerf": round(w, 2),
                               "placed_height_mm_including_kerf": round(h, 2),
                               "orientation": orientation, "net_part_area_mm2": round(area, 2)})
            continue

        # Try adding a new shelf to an existing plate. Improved mode chooses the
        # feasible plate with the least vertical space left after the row is added;
        # baseline only considers the most recently opened plate.
        plate_candidates = range(len(plates)) if improved else ([len(plates) - 1] if plates else [])
        new_shelf_choices = []
        for pi in plate_candidates:
            plate = plates[pi]
            orientation = _choose_new_shelf_orientation(part, usable_w, usable_h, plate.next_y_mm, kerf_mm)
            if orientation:
                w, h, label = orientation
                # Prefer less vertical leftover; deterministic tie-break by plate index.
                new_shelf_choices.append(((usable_h - (plate.next_y_mm + h), pi, h, usable_w - w), pi, w, h, label))
        if new_shelf_choices:
            _, pi, w, h, orientation = min(new_shelf_choices, key=lambda item: item[0])
            plate = plates[pi]
        else:
            orientation = _choose_new_shelf_orientation(part, usable_w, usable_h, 0.0, kerf_mm)
            if not orientation:
                unplaced.append(part["part_id"])
                continue
            plate = new_plate()
            pi = len(plates) - 1
            w, h, label = orientation
        shelf = Shelf(y_mm=plate.next_y_mm, height_mm=h, next_x_mm=w)
        plate.shelves.append(shelf)
        plate.next_y_mm += h
        placements.append({"part_id": part["part_id"], "plate_number": pi + 1,
                           "x_mm": 0.0, "y_mm": round(shelf.y_mm, 2),
                           "placed_width_mm_including_kerf": round(w, 2),
                           "placed_height_mm_including_kerf": round(h, 2),
                           "orientation": label, "net_part_area_mm2": round(area, 2)})

    piece_count = len(expanded)
    placed_ids = {p["part_id"] for p in placements}
    if len(placed_ids) != len(placements):
        raise AssertionError("internal error: part was placed more than once")
    net_area = sum(float(p["width_mm"]) * float(p["height_mm"]) for p in expanded if p["part_id"] in placed_ids)
    stock_area = len(plates) * float(stock_width_mm) * float(stock_height_mm)
    yield_pct = (net_area / stock_area * 100.0) if stock_area else 0.0
    return {
        "method": "best_fit_decreasing_shelf" if improved else "next_fit_shelf_baseline",
        "stock": {"width_mm": stock_width_mm, "height_mm": stock_height_mm,
                   "edge_trim_mm_each_side": edge_trim_mm, "kerf_mm_assumption": kerf_mm},
        "input_piece_count": piece_count,
        "placed_piece_count": len(placements),
        "unplaced_part_ids": unplaced,
        "plates_used": len(plates),
        "net_part_area_mm2_placed": round(net_area, 2),
        "gross_stock_area_mm2": round(stock_area, 2),
        "area_yield_percent": round(yield_pct, 2),
        "area_not_accounted_as_part_percent": round(100.0 - yield_pct, 2),
        "placements": placements,
        "important_limitations": [
            "synthetic rectangular parts only",
            "shelf heuristics, not globally optimal 2D nesting",
            "kerf and trim are simplified approximations",
            "no CNC release, grade/lot checks, complex geometry, grain constraints or production validation",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to a synthetic plate nesting JSON case")
    args = parser.parse_args()
    with Path(args.input).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    stock = data["stock"]
    baseline = pack_shelf(data["parts"], stock["width_mm"], stock["height_mm"],
                          kerf_mm=stock.get("kerf_mm", 3),
                          edge_trim_mm=stock.get("edge_trim_mm", 5), improved=False)
    improved = pack_shelf(data["parts"], stock["width_mm"], stock["height_mm"],
                          kerf_mm=stock.get("kerf_mm", 3),
                          edge_trim_mm=stock.get("edge_trim_mm", 5), improved=True)
    print(json.dumps({"case_name": data.get("case_name", "unnamed synthetic case"),
                      "baseline": baseline, "best_fit_decreasing": improved,
                      "plates_saved_in_this_synthetic_case": baseline["plates_used"] - improved["plates_used"],
                      "not_a_client_result": True}, indent=2))


if __name__ == "__main__":
    main()
