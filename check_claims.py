#!/usr/bin/env python3
"""
Validate every quantitative claim in the paper against solver/verify outputs.

Usage:
    python check_claims.py --tex ./docs/Stampher_2026_Zodiac_Z32_GeoCSP.tex
    python check_claims.py --skip-run  # if output/ already fresh
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
Z32_JSON = OUTPUT / "z32_results.json"
VERIFY_JSON = OUTPUT / "verify_results.json"
CLAIM_MAP = OUTPUT / "claim_map.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout)
        print(r.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def find_clock_row(rows: list[dict], location: str) -> dict:
    for row in rows:
        if row.get("location") == location:
            return row
    raise KeyError(f"Not found: {location}")


def close(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol


def rounded(a: float, digits: int) -> float:
    return round(float(a), digits)


@dataclass
class Claim:
    id: str
    label: str
    source: str
    expected: Any
    extract: Callable[[dict, dict], Any]
    compare: Callable[[Any, Any], bool]
    tex_patterns: list[str]


def build_claims() -> list[Claim]:
    return [
        Claim("total_candidates", "Total candidates",
              "z32 -> metadata.total_candidates", 2_044_224,
              lambda z, v: int(z["metadata"]["total_candidates"]),
              lambda a, e: a == e, ["2,044,224"]),

        Claim("survivors", "Survivors",
              "z32 -> metadata.num_survivors", 54,
              lambda z, v: int(z["metadata"]["num_survivors"]),
              lambda a, e: a == e, ["54"]),

        Claim("passed_length", "Passed length filter",
              "z32 -> metadata.passed_length", 154_572,
              lambda z, v: int(z["metadata"]["passed_length"]),
              lambda a, e: a == e, ["154,572"]),

        Claim("passed_locks", "Passed homophonic locks",
              "z32 -> metadata.passed_locks", 61,
              lambda z, v: int(z["metadata"]["passed_locks"]),
              lambda a, e: a == e, ["61"]),

        Claim("rejection_rate", "Rejection rate",
              "z32 -> metadata.rejection_rate_pct", 99.9974,
              lambda z, v: rounded(z["metadata"]["rejection_rate_pct"], 4),
              lambda a, e: close(a, e, 1e-4), ["99.9974\\%"]),

        Claim("solution_coords", "Solution coordinates",
              "verify V1 -> projected", (38.109952, -122.185349),
              lambda z, v: (
                  rounded(v["verification_1_coordinate_derivation"]["projected"]["lat"], 6),
                  rounded(v["verification_1_coordinate_derivation"]["projected"]["lon"], 6),
              ),
              lambda a, e: a == e, ["38.10995", "122.18535"]),

        Claim("dist_brs", "Distance to BRS",
              "verify V4 -> BRS", 1.15,
              lambda z, v: rounded(
                  v["verification_4_proximity_analysis"]["crime_scene_distances_mi"]
                  ["Blue Rock Springs (07/04/1969)"], 2),
              lambda a, e: close(a, e, 1e-2), ["1.15"]),

        Claim("dist_lhr", "Distance to LHR",
              "verify V4 -> LHR", 2.47,
              lambda z, v: rounded(
                  v["verification_4_proximity_analysis"]["crime_scene_distances_mi"]
                  ["Lake Herman Road (12/20/1968)"], 2),
              lambda a, e: close(a, e, 1e-2), ["2.47"]),

        Claim("dist_triangle", "Distance to triangle anomaly",
              "verify V4 -> triangle", {"meters": 254, "miles": 0.158, "feet": 833},
              lambda z, v: {
                  "meters": int(round(v["verification_4_proximity_analysis"]["solution_to_triangle"]["meters"])),
                  "miles": rounded(v["verification_4_proximity_analysis"]["solution_to_triangle"]["miles"], 3),
                  "feet": int(round(v["verification_4_proximity_analysis"]["solution_to_triangle"]["feet"])),
              },
              lambda a, e: a == e, ["0.158", "833", "254"]),

        Claim("map_offset", "Map-scale offset",
              "verify V4 -> map_inches", 0.0246,
              lambda z, v: rounded(
                  v["verification_4_proximity_analysis"]["solution_to_triangle"]["map_inches"], 4),
              lambda a, e: close(a, e, 1e-4), ["0.0246"]),

        Claim("centroid_loc", "Centroid location",
              "verify V3 -> centroid", (38.0780, -122.2011),
              lambda z, v: (
                  rounded(v["verification_3_geometric_centroid"]["centroid"]["lat"], 4),
                  rounded(v["verification_3_geometric_centroid"]["centroid"]["lon"], 4),
              ),
              lambda a, e: a == e, ["38.0780", "122.2011"]),

        Claim("centroid_dist", "Centroid-to-solution",
              "verify V3 -> centroid_to_solution_mi", 2.37,
              lambda z, v: rounded(v["verification_3_geometric_centroid"]["centroid_to_solution_mi"], 2),
              lambda a, e: close(a, e, 1e-2), ["2.37"]),

        Claim("max_span", "Max span",
              "verify V3 -> max_span_mi", 54.9,
              lambda z, v: rounded(v["verification_3_geometric_centroid"]["max_span_mi"], 1),
              lambda a, e: close(a, e, 0.1), ["54.9"]),

        Claim("offset_pct", "Offset % of span",
              "verify V3 -> offset_pct", 4.3,
              lambda z, v: rounded(v["verification_3_geometric_centroid"]["offset_pct_of_max_span"], 1),
              lambda a, e: close(a, e, 0.1), ["4.3\\%"]),

        Claim("presidio_clock", "Presidio clock hour",
              "verify V2 -> presidio.clock_exact", 8.03,
              lambda z, v: rounded(v["verification_2_clock_hour_geometry"]["presidio"]["clock_exact"], 2),
              lambda a, e: close(a, e, 1e-2), ["8.03"]),

        Claim("lhr_clock", "LHR clock hour",
              "verify V2 -> vallejo LHR", 10.09,
              lambda z, v: rounded(
                  v["verification_2_clock_hour_geometry"]["vallejo_subset"]
                  ["Lake Herman Road"]["clock_exact"], 2),
              lambda a, e: close(a, e, 1e-2), ["10.09"]),

        Claim("brs_clock", "BRS clock hour",
              "verify V2 -> vallejo BRS", 10.04,
              lambda z, v: rounded(
                  v["verification_2_clock_hour_geometry"]["vallejo_subset"]
                  ["Blue Rock Springs"]["clock_exact"], 2),
              lambda a, e: close(a, e, 1e-2), ["10.04"]),

        Claim("z32_clock", "Z32 clock hour",
              "verify V2 -> z32_solution", 10.00,
              lambda z, v: rounded(v["verification_2_clock_hour_geometry"]["z32_solution"]["clock_exact"], 2),
              lambda a, e: close(a, e, 1e-2), ["10.00"]),

        Claim("presidio_mag", "Presidio mag bearing",
              "verify V2 -> presidio mag", 240.93,
              lambda z, v: rounded(v["verification_2_clock_hour_geometry"]["presidio"]["mag_bearing_deg"], 2),
              lambda a, e: close(a, e, 1e-2), ["240.93"]),

        Claim("lhr_mag", "LHR mag bearing",
              "verify V2 -> LHR mag", 302.74,
              lambda z, v: rounded(
                  find_clock_row(v["verification_2_clock_hour_geometry"]["rows"],
                                 "Lake Herman Road (12/20/1968)")["mag_bearing_deg"], 2),
              lambda a, e: close(a, e, 1e-2), ["302.74"]),

        Claim("brs_mag", "BRS mag bearing",
              "verify V2 -> BRS mag", 301.34,
              lambda z, v: rounded(
                  find_clock_row(v["verification_2_clock_hour_geometry"]["rows"],
                                 "Blue Rock Springs (07/04/1969)")["mag_bearing_deg"], 2),
              lambda a, e: close(a, e, 1e-2), ["301.34"]),

        Claim("z32_mag", "Z32 mag bearing",
              "verify V2 -> z32 mag", 300.00,
              lambda z, v: rounded(v["verification_2_clock_hour_geometry"]["z32_solution"]["mag_bearing_deg"], 2),
              lambda a, e: close(a, e, 1e-2), ["300.00"]),

        Claim("inner_sides", "Inner triangle sides",
              "verify V7 motif 0 sides", [3.34, 3.31, 3.36],
              lambda z, v: [rounded(e["distance_mi"], 2)
                            for e in v["verification_7_near_equilateral_8_10"]
                            ["equilateral_motif_residuals"][0]["sides_mi"]],
              lambda a, e: a == e, ["3.34", "3.31", "3.36"]),

        Claim("inner_angles", "Inner triangle angles",
              "verify V7 motif 0 angles", [59.2, 60.7, 60.0],
              lambda z, v: [rounded(a, 1)
                            for a in v["verification_7_near_equilateral_8_10"]
                            ["equilateral_motif_residuals"][0]["angles_deg"]],
              lambda a, e: a == e, ["59.2", "60.7", "60.0"]),

        Claim("inner_max_dev", "Inner max angle dev",
              "verify V7 motif 0 max dev", 0.8,
              lambda z, v: rounded(
                  v["verification_7_near_equilateral_8_10"]
                  ["equilateral_motif_residuals"][0]["max_abs_angle_deviation_deg"], 1),
              lambda a, e: close(a, e, 0.1), ["0.8"]),

        Claim("angular_sep", "Angular separation MD->Z32 vs MD->PH",
              "verify V7 bearings", 59.07,
              lambda z, v: rounded(
                  v["verification_7_near_equilateral_8_10"]["bearings_true_deg"]["angular_separation"], 2),
              lambda a, e: close(a, e, 1e-2), ["59.07"]),

        Claim("op_tri_sides", "Operational triangle sides",
              "verify V3 sides", [50.2, 30.3, 54.9],
              lambda z, v: [rounded(r["distance_mi"], 1)
                            for r in v["verification_3_geometric_centroid"]["side_lengths_mi"]],
              lambda a, e: a == e, ["50.2", "30.3", "54.9"]),

        Claim("survival_rate", "Survival rate",
              "verify V5 survival_rate", 2.64e-5,
              lambda z, v: float(v["verification_5_statistical_analysis"]["constraint_filter"]["survival_rate"]),
              lambda a, e: math.isclose(a, e, rel_tol=0.01), ["2.64 \\times 10^{-5}"]),

        Claim("zone_odds", "Geographic zone odds",
              "verify V5 zone odds", 506_000,
              lambda z, v: int(round(
                  v["verification_5_statistical_analysis"]["geographic_coincidence"]["odds_zone_1_in"], -3)),
              lambda a, e: a == e, ["506,000"]),

        Claim("dist_87pct", "Survivor 8/10 concentration",
              "verify V8", {"hour8": 25, "hour10": 22, "combined": 47, "total": 54, "pct": 87.0, "enrichment": 5.2},
              lambda z, v: {
                  "hour8": int(v["verification_8_survivor_clock_distribution"]["hour_8_count"]),
                  "hour10": int(v["verification_8_survivor_clock_distribution"]["hour_10_count"]),
                  "combined": int(v["verification_8_survivor_clock_distribution"]["combined_8_10_count"]),
                  "total": int(v["verification_8_survivor_clock_distribution"]["survivor_total"]),
                  "pct": rounded(v["verification_8_survivor_clock_distribution"]["combined_8_10_pct"], 1),
                  "enrichment": rounded(v["verification_8_survivor_clock_distribution"]["enrichment_vs_random"], 1),
              },
              lambda a, e: a == e, ["47/54", "87.0\\%", "5.2"]),

        # V9: Pre-existing angular structure
        Claim("ph_brs_sep", "PH-BRS angular separation",
              "verify V9 ph_brs_separation_deg", 60.41,
              lambda z, v: rounded(
                  v["verification_9_preexisting_angular_structure"]["ph_brs_separation_deg"], 2),
              lambda a, e: close(a, e, 1e-2), ["60.41"]),

        Claim("ph_brs_delta", "PH-BRS delta from 60 deg",
              "verify V9 ph_brs_delta_from_60", 0.41,
              lambda z, v: rounded(
                  v["verification_9_preexisting_angular_structure"]["ph_brs_delta_from_60"], 2),
              lambda a, e: close(a, e, 1e-2), ["0.41"]),

        # V10: Astronomical date alignments
        Claim("lhr_solstice_offset", "LHR-solstice offset",
              "verify V10 lake_herman_road.offset_days", -1,
              lambda z, v: int(
                  v["verification_10_astronomical_date_alignments"]["lake_herman_road"]["offset_days"]),
              lambda a, e: a == e, []),

        Claim("brs_aphelion_offset", "BRS-aphelion offset",
              "verify V10 blue_rock_springs.offset_days", 0,
              lambda z, v: int(
                  v["verification_10_astronomical_date_alignments"]["blue_rock_springs"]["offset_days"]),
              lambda a, e: a == e, []),

        Claim("timer_postmark_offset", "3.375-month timer postmark offset",
              "verify V10 temporal_timer.offset_from_postmark_days", -2,
              lambda z, v: int(
                  v["verification_10_astronomical_date_alignments"]["temporal_timer"]["offset_from_postmark_days"]),
              lambda a, e: abs(a - e) <= 1, []),

        Claim("timer_received_offset", "3.375-month timer received offset",
              "verify V10 temporal_timer.offset_from_received_days", 0,
              lambda z, v: int(
                  v["verification_10_astronomical_date_alignments"]["temporal_timer"]["offset_from_received_days"]),
              lambda a, e: abs(a - e) <= 1, []),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check paper claims")
    parser.add_argument("--tex", default="./docs/Stampher_2026_Zodiac_Z32_GeoCSP.tex")
    parser.add_argument("--skip-run", action="store_true")
    args = parser.parse_args()

    tex_path = ROOT.parent / args.tex  # TeX lives one level up from z32/
    if not tex_path.exists():
        tex_path = ROOT / args.tex
    if not tex_path.exists():
        raise FileNotFoundError(f"TeX not found: {args.tex}")

    if not args.skip_run:
        run([sys.executable, "z32.py", "--out", "output"])
        run([sys.executable, "verify.py", "--json-out", "output/verify_results.json"])

    z = read_json(Z32_JSON)
    v = read_json(VERIFY_JSON)
    tex = tex_path.read_text(encoding="utf-8")
    claims = build_claims()

    records: list[dict[str, Any]] = []
    all_ok = True
    for c in claims:
        actual = c.extract(z, v)
        val_ok = c.compare(actual, c.expected)
        tex_ok = all(p in tex for p in c.tex_patterns)
        passed = val_ok and tex_ok
        all_ok &= passed
        records.append({
            "id": c.id, "label": c.label,
            "expected": c.expected, "actual": actual,
            "value_ok": val_ok, "tex_ok": tex_ok, "pass": passed,
        })
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {c.label}")
        if not passed:
            if not val_ok:
                print(f"  expected: {c.expected}")
                print(f"  actual:   {actual}")
            if not tex_ok:
                missing = [p for p in c.tex_patterns if p not in tex]
                print(f"  missing TeX patterns: {missing}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "tex_file": str(tex_path),
        "summary": {
            "total": len(records),
            "passed": sum(1 for r in records if r["pass"]),
            "failed": sum(1 for r in records if not r["pass"]),
            "all_pass": all_ok,
        },
        "claims": records,
    }
    with CLAIM_MAP.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote: {CLAIM_MAP}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
