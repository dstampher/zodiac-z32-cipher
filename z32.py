#!/usr/bin/env python3
"""
Z32 Cipher Solver
=================
Exhaustive search over a structured lexicon of English-language phrases
encoding (distance, clock-hour) coordinate pairs. Candidates are filtered
by cipher length, homophonic lock constraints, and Phillips 66 map bounds.
"""

import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, Tuple, Any, List

from data import (
    CIPHER_LENGTH, EARTH_RADIUS_MI, LOCKS_0_INDEXED,
    MAG_DEC_1970_DEG_EAST, MAP_BOUNDS, MAP_SCALE_MI_PER_IN, POINTS,
)
from geo import haversine, project_point


# ---------------------------------------------------------------------------
# Runtime constants
# ---------------------------------------------------------------------------

def build_runtime_constants() -> Dict[str, Any]:
    return {
        "ANCHOR_LAT": float(POINTS["mt_diablo"]["lat"]),
        "ANCHOR_LON": float(POINTS["mt_diablo"]["lon"]),
        "MAG_DECLINATION": float(MAG_DEC_1970_DEG_EAST),
        "MAP_SCALE": float(MAP_SCALE_MI_PER_IN),
        "MAP_BOUNDS": {k: float(v) for k, v in MAP_BOUNDS.items()},
        "LOCKS": [tuple(x) for x in LOCKS_0_INDEXED],
        "CIPHER_LENGTH": int(CIPHER_LENGTH),
        "EARTH_RADIUS_MI": float(EARTH_RADIUS_MI),
        "CRIME_SCENES": {
            name: (float(POINTS[name]["lat"]), float(POINTS[name]["lon"]))
            for name in ("lake_herman_road", "blue_rock_springs",
                         "lake_berryessa", "presidio_heights")
        },
    }


# ---------------------------------------------------------------------------
# Lexicon
# ---------------------------------------------------------------------------

INTEGERS = {
    0: "ZERO", 1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR",
    5: "FIVE", 6: "SIX", 7: "SEVEN", 8: "EIGHT", 9: "NINE",
    10: "TEN", 11: "ELEVEN", 12: "TWELVE",
}

FRACTIONS = {
    "": 0.0,
    "ANDAHALF": 0.5, "ANDONEHALF": 0.5,
    "ANDATHIRD": 1/3, "ANDONETHIRD": 1/3, "ANDTWOTHIRDS": 2/3,
    "ANDAQUARTER": 0.25, "ANDONEQUARTER": 0.25,
    "ANDAFOURTH": 0.25, "ANDONEFOURTH": 0.25,
    "ANDTHREEQUARTERS": 0.75, "ANDTHREEFOURTHS": 0.75,
    "ANDANEIGHTH": 0.125, "ANDONEEIGHTH": 0.125,
    "ANDTHREEEIGHTHS": 0.375,
    "ANDFIVEEIGHTHS": 0.625, "ANDSEVENEIGHTHS": 0.875,
    "ANDASIXTEENTH": 0.0625, "ANDONESIXTEENTH": 0.0625,
    "ANDTHREESIXTEENTHS": 0.1875, "ANDFIVESIXTEENTHS": 0.3125,
    "ANDSEVENSIXTEENTHS": 0.4375, "ANDNINESIXTEENTHS": 0.5625,
    "ANDELEVENSIXTEENTHS": 0.6875, "ANDTHIRTEENSIXTEENTHS": 0.8125,
    "ANDFIFTEENSIXTEENTHS": 0.9375,
}

PREFIXES = ["", "IN", "AT", "TO", "BY", "GO", "ON"]
RAD_UNITS = ["RAD", "RADS", "RADIAN", "RADIANS"]
DIST_UNITS = ["", "INCH", "INCHES"]


# ---------------------------------------------------------------------------
# Geographic helpers
# ---------------------------------------------------------------------------

def project_from_anchor(distance_inches: float, clock_hour: int,
                        C: Dict[str, Any]) -> Tuple[float, float]:
    distance_miles = distance_inches * C["MAP_SCALE"]
    mag_bearing_deg = (clock_hour % 12) * 30
    true_bearing_deg = (mag_bearing_deg + C["MAG_DECLINATION"]) % 360
    return project_point(
        C["ANCHOR_LAT"], C["ANCHOR_LON"],
        true_bearing_deg, distance_miles, C["EARTH_RADIUS_MI"],
    )


def nearest_crime_scene(lat: float, lon: float,
                        C: Dict[str, Any]) -> Tuple[str, float]:
    best_name, best_dist = "", float("inf")
    for name, (clat, clon) in C["CRIME_SCENES"].items():
        d = haversine(lat, lon, clat, clon, C["EARTH_RADIUS_MI"])
        if d < best_dist:
            best_name, best_dist = name, d
    return best_name, best_dist


def in_map_bounds(lat: float, lon: float, C: Dict[str, Any]) -> bool:
    b = C["MAP_BOUNDS"]
    return b["south"] <= lat <= b["north"] and b["west"] <= lon <= b["east"]


# ---------------------------------------------------------------------------
# Candidate generation (12 template families x prefix x lexicon)
# ---------------------------------------------------------------------------

def generate_all_phrases():
    for dist_int in range(13):
        for angle_int in range(1, 13):
            for frac_str, frac_val in FRACTIONS.items():
                dist_word = INTEGERS[dist_int]
                angle_word = INTEGERS[angle_int]
                distance = dist_int + frac_val

                for rad in RAD_UNITS:
                    for pre in PREFIXES:
                        yield (f"{pre}{dist_word}{frac_str}{rad}{angle_word}", distance, angle_int, "A")
                        yield (f"{pre}{angle_word}{rad}{dist_word}{frac_str}", distance, angle_int, "B")
                        yield (f"{pre}{dist_word}{frac_str}{angle_word}{rad}", distance, angle_int, "C")
                        yield (f"{pre}{angle_word}{dist_word}{frac_str}{rad}", distance, angle_int, "D")
                        yield (f"{pre}{rad}{angle_word}{dist_word}{frac_str}", distance, angle_int, "E")
                        yield (f"{pre}{rad}{dist_word}{frac_str}{angle_word}", distance, angle_int, "F")

                    for dunit in DIST_UNITS:
                        if not dunit:
                            continue
                        for pre in PREFIXES:
                            yield (f"{pre}{dist_word}{frac_str}{dunit}{rad}{angle_word}", distance, angle_int, "G")
                            yield (f"{pre}{dist_word}{frac_str}{dunit}{angle_word}{rad}", distance, angle_int, "H")
                            yield (f"{pre}{angle_word}{rad}{dist_word}{frac_str}{dunit}", distance, angle_int, "I")
                            yield (f"{pre}{angle_word}{dist_word}{frac_str}{dunit}{rad}", distance, angle_int, "J")
                            yield (f"{pre}{dunit}{dist_word}{frac_str}{rad}{angle_word}", distance, angle_int, "K")
                            yield (f"{pre}{rad}{angle_word}{dunit}{dist_word}{frac_str}", distance, angle_int, "L")


# ---------------------------------------------------------------------------
# Human-readable tokenizer
# ---------------------------------------------------------------------------

_WORD_TOKENS = [
    "THIRTEENSIXTEENTHS", "FIFTEENSIXTEENTHS", "ELEVENSIXTEENTHS",
    "SEVENSIXTEENTHS", "NINESIXTEENTHS", "FIVESIXTEENTHS", "THREESIXTEENTHS",
    "THREEQUARTERS", "THREEFOURTHS", "THREEEIGHTHS", "SEVENEIGHTHS", "FIVEEIGHTHS",
    "TWOTHIRDS", "SIXTEENTH", "RADIANS", "RADIAN", "INCHES",
    "TWELVE", "ELEVEN", "QUARTERS", "QUARTER", "FOURTHS", "FOURTH", "EIGHTHS", "EIGHTH",
    "SEVEN", "THREE", "EIGHT", "NINE", "FOUR", "FIVE", "ZERO", "THIRDS", "THIRD", "HALF",
    "INCH", "RADS", "ONE", "TWO", "SIX", "TEN", "RAD", "AND", "THE", "FROM",
    "IN", "AT", "TO", "BY", "GO", "ON", "A",
]


def format_readable(phrase: str) -> str:
    result: List[str] = []
    remaining = phrase
    while remaining:
        for w in _WORD_TOKENS:
            if remaining.startswith(w):
                result.append(w)
                remaining = remaining[len(w):]
                break
        else:
            result.append(remaining[0])
            remaining = remaining[1:]
    return " ".join(result)


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

def solve(C: Dict[str, Any], out_dir: Path) -> Dict[str, Any]:
    print("=" * 78)
    print("Z32 CIPHER SOLVER")
    print("=" * 78)
    print(f"Run: {datetime.now().isoformat()}\n")

    total = 0
    passed_length = passed_locks = passed_bounds = 0
    survivors: List[Dict[str, Any]] = []
    template_survivors: Dict[str, int] = defaultdict(int)

    for phrase, distance, clock_hour, template_id in generate_all_phrases():
        total += 1

        if len(phrase) != C["CIPHER_LENGTH"]:
            continue
        passed_length += 1

        if not all(phrase[i] == phrase[j] for i, j in C["LOCKS"]):
            continue
        passed_locks += 1

        lat, lon = project_from_anchor(distance, clock_hour, C)
        if not in_map_bounds(lat, lon, C):
            continue
        passed_bounds += 1

        scene_name, scene_dist = nearest_crime_scene(lat, lon, C)
        template_survivors[template_id] += 1
        survivors.append({
            "phrase": phrase,
            "readable": format_readable(phrase),
            "distance_inches": distance,
            "clock_hour": clock_hour,
            "latitude": lat,
            "longitude": lon,
            "nearest_scene": scene_name,
            "nearest_dist_mi": scene_dist,
            "template": template_id,
        })

    survivors.sort(key=lambda x: x["nearest_dist_mi"])

    rejection_pct = (1 - passed_bounds / total) * 100
    print(f"Total candidates:        {total:>12,}")
    print(f"Passed length (=32):     {passed_length:>12,}")
    print(f"Passed homophonic locks: {passed_locks:>12,}")
    print(f"Passed map bounds:       {passed_bounds:>12,}")
    print(f"Rejection rate:          {rejection_pct:>11.4f}%")
    print(f"Survivors:               {len(survivors):>12,}")

    if survivors:
        top = survivors[0]
        print(f"\nPRIMARY SOLUTION: {top['readable']}")
        print(f"  {top['distance_inches']} in x {C['MAP_SCALE']} mi/in = "
              f"{top['distance_inches'] * C['MAP_SCALE']:.1f} mi at {top['clock_hour']}:00")
        print(f"  ({top['latitude']:.6f}, {top['longitude']:.6f})")
        print(f"  Nearest: {top['nearest_scene']} ({top['nearest_dist_mi']:.2f} mi)")

    out_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "metadata": {
            "solver_version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "total_candidates": total,
            "passed_length": passed_length,
            "passed_locks": passed_locks,
            "passed_bounds": passed_bounds,
            "rejection_rate_pct": rejection_pct,
            "num_survivors": len(survivors),
        },
        "constants": {
            "anchor": [C["ANCHOR_LAT"], C["ANCHOR_LON"]],
            "mag_declination": C["MAG_DECLINATION"],
            "map_scale_mi_per_inch": C["MAP_SCALE"],
            "locks": C["LOCKS"],
        },
        "lexicon_sizes": {
            "integers": len(INTEGERS),
            "fractions": len(FRACTIONS),
            "prefixes": len(PREFIXES),
            "rad_units": len(RAD_UNITS),
            "dist_units": len(DIST_UNITS),
        },
        "survivors": survivors,
    }

    json_path = out_dir / "z32_results.json"
    csv_path = out_dir / "z32_results.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Plaintext", "Distance_in", "Clock_Hour",
            "Latitude", "Longitude", "Nearest_Scene", "Dist_mi", "Template",
        ])
        for i, s in enumerate(survivors, start=1):
            writer.writerow([
                i, s["readable"], s["distance_inches"], s["clock_hour"],
                f"{s['latitude']:.6f}", f"{s['longitude']:.6f}",
                s["nearest_scene"], f"{s['nearest_dist_mi']:.2f}", s["template"],
            ])

    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Z32 solver")
    parser.add_argument("--out", type=Path, default=Path("output"))
    args = parser.parse_args()
    solve(build_runtime_constants(), args.out)
