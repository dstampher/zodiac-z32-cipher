#!/usr/bin/env python3
"""
Z32 Verification Suite - Independent Validation of All Paper Claims
===================================================================
Reads canonical constants from data.py.  Geographic math from geo.py.
Emits structured JSON and human-readable console output.
"""

import math
import json
import argparse
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

from data import (
    CIPHER_LENGTH, EARTH_RADIUS_MI, LOCKS_0_INDEXED,
    MAG_DEC_1970_DEG_EAST, MAP_BOUNDS, MAP_SCALE_MI_PER_IN, POINTS,
)
from geo import (
    haversine, true_bearing, mag_bearing, bearing_to_clock,
    project_point, angular_separation, angle_from_sides,
    to_local_miles, sample_point_in_triangle,
)

# ---------------------------------------------------------------------------
# Constants derived from data.py
# ---------------------------------------------------------------------------

SOLUTION = (float(POINTS["z32_solution"]["lat"]),
            float(POINTS["z32_solution"]["lon"]))

TRIANGLE_ANOMALY = (float(POINTS["triangle_anomaly"]["lat"]),
                    float(POINTS["triangle_anomaly"]["lon"]))

TOTAL_CANDIDATES = 2_044_224
TOTAL_SURVIVORS = 54


def build_constants() -> dict:
    crime_scenes = {
        "Lake Herman Road (12/20/1968)": (
            float(POINTS["lake_herman_road"]["lat"]),
            float(POINTS["lake_herman_road"]["lon"]),
        ),
        "Blue Rock Springs (07/04/1969)": (
            float(POINTS["blue_rock_springs"]["lat"]),
            float(POINTS["blue_rock_springs"]["lon"]),
        ),
        "Lake Berryessa (09/27/1969)": (
            float(POINTS["lake_berryessa"]["lat"]),
            float(POINTS["lake_berryessa"]["lon"]),
        ),
        "Presidio Heights (10/11/1969)": (
            float(POINTS["presidio_heights"]["lat"]),
            float(POINTS["presidio_heights"]["lon"]),
        ),
    }
    return {
        "EARTH_RADIUS_MI": float(EARTH_RADIUS_MI),
        "MT_DIABLO": (float(POINTS["mt_diablo"]["lat"]),
                      float(POINTS["mt_diablo"]["lon"])),
        "MAG_DEC_1970": float(MAG_DEC_1970_DEG_EAST),
        "MAP_SCALE": float(MAP_SCALE_MI_PER_IN),
        "MAP_BOUNDS": {k: float(v) for k, v in MAP_BOUNDS.items()},
        "CRIME_SCENES": crime_scenes,
        "LOCKS": [tuple(x) for x in LOCKS_0_INDEXED],
        "CIPHER_LENGTH": int(CIPHER_LENGTH),
    }


# ---------------------------------------------------------------------------
# Survivor clock-hour distribution loader
# ---------------------------------------------------------------------------

def load_survivor_clock_distribution() -> tuple[dict[int, int], int]:
    z32_json = Path("output/z32_results.json")
    if not z32_json.exists():
        import z32
        z32.solve(z32.build_runtime_constants(), Path("output"))

    with z32_json.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    survivors = payload.get("survivors", [])
    counts: dict[int, int] = {}
    for row in survivors:
        h = int(row["clock_hour"])
        counts[h] = counts.get(h, 0) + 1
    return counts, int(payload["metadata"]["num_survivors"])


# ---------------------------------------------------------------------------
# Helper: equilateral motif summary
# ---------------------------------------------------------------------------

def motif_row(name: str, sides: list[float], angles: list[float],
              labels: list[str]) -> dict:
    mean_side = sum(sides) / 3.0
    side_dev = [((s / mean_side) - 1.0) * 100.0 for s in sides]
    angle_dev = [a - 60.0 for a in angles]
    return {
        "motif": name,
        "sides_mi": [{"edge": lbl, "distance_mi": s} for lbl, s in zip(labels, sides)],
        "angles_deg": angles,
        "side_deviation_pct_from_mean": side_dev,
        "angle_deviation_deg_from_60": angle_dev,
        "max_abs_side_deviation_pct": max(abs(x) for x in side_dev),
        "max_abs_angle_deviation_deg": max(abs(x) for x in angle_dev),
    }


# ===========================================================================
# Core computation
# ===========================================================================

def compute_results(C: dict) -> dict:
    E = C["EARTH_RADIUS_MI"]
    MD = C["MT_DIABLO"]
    DEC = C["MAG_DEC_1970"]
    SCALE = C["MAP_SCALE"]
    SCENES = C["CRIME_SCENES"]
    LOCKS = C["LOCKS"]

    # -- V1: Coordinate derivation ------------------------------------------
    dist_in = 3.375
    clock_hr = 10
    dist_mi = dist_in * SCALE
    mag_brg = (clock_hr % 12) * 30
    true_brg = (mag_brg + DEC) % 360

    proj_lat, proj_lon = project_point(MD[0], MD[1], true_brg, dist_mi, E)
    err_lat = abs(proj_lat - SOLUTION[0])
    err_lon = abs(proj_lon - SOLUTION[1])
    exact = err_lat < 1e-4 and err_lon < 1e-4

    V1 = {
        "plaintext": "IN THREE AND THREE EIGHTHS RADIANS TEN",
        "distance_inches": dist_in,
        "distance_miles": dist_mi,
        "clock_hour": clock_hr,
        "mag_bearing_deg": mag_brg,
        "true_bearing_deg": true_brg,
        "projected": {"lat": proj_lat, "lon": proj_lon},
        "stated_solution": {"lat": SOLUTION[0], "lon": SOLUTION[1]},
        "error": {
            "lat_deg": err_lat, "lon_deg": err_lon,
            "lat_miles": err_lat * 69.0,
            "lon_miles": err_lon * 69.0 * math.cos(math.radians(proj_lat)),
        },
        "exact_match_threshold_deg": 1e-4,
        "exact_match": exact,
    }

    # -- V2: Clock-hour geometry --------------------------------------------
    all_pts = dict(SCENES)
    all_pts["Z32 SOLUTION"] = SOLUTION

    clock_rows = []
    for name, (lat, lon) in all_pts.items():
        tb = true_bearing(MD[0], MD[1], lat, lon)
        mb = mag_bearing(MD[0], MD[1], lat, lon, DEC)
        ck = bearing_to_clock(mb)
        nearest_hr = round(ck)
        if nearest_hr == 0:
            nearest_hr = 12
        clock_rows.append({
            "location": name,
            "true_bearing_deg": tb,
            "mag_bearing_deg": mb,
            "clock_exact": ck,
            "clock_nearest_hour": nearest_hr,
            "error_deg_to_nearest_hour": abs(ck - nearest_hr) * 30,
            "distance_from_mt_diablo_mi": haversine(MD[0], MD[1], lat, lon, E),
        })

    vallejo = {
        "Lake Herman Road": SCENES["Lake Herman Road (12/20/1968)"],
        "Blue Rock Springs": SCENES["Blue Rock Springs (07/04/1969)"],
    }
    vallejo_clock = {}
    for name, (lat, lon) in vallejo.items():
        mb = mag_bearing(MD[0], MD[1], lat, lon, DEC)
        vallejo_clock[name] = {"mag_bearing_deg": mb, "clock_exact": bearing_to_clock(mb)}

    mb_sol = mag_bearing(MD[0], MD[1], SOLUTION[0], SOLUTION[1], DEC)
    ck_sol = bearing_to_clock(mb_sol)

    ph = SCENES["Presidio Heights (10/11/1969)"]
    mb_ph = mag_bearing(MD[0], MD[1], ph[0], ph[1], DEC)
    ck_ph = bearing_to_clock(mb_ph)

    V2 = {
        "rows": clock_rows,
        "vallejo_subset": vallejo_clock,
        "z32_solution": {"mag_bearing_deg": mb_sol, "clock_exact": ck_sol},
        "presidio": {
            "mag_bearing_deg": mb_ph,
            "clock_exact": ck_ph,
            "error_from_8_oclock_deg": abs(ck_ph - 8.0) * 30,
        },
    }

    # -- V3: Geometric centroid ---------------------------------------------
    cardinal = {
        "Mt. Diablo": MD,
        "Lake Berryessa": SCENES["Lake Berryessa (09/27/1969)"],
        "Presidio Heights": ph,
    }
    c_lat = sum(v[0] for v in cardinal.values()) / 3
    c_lon = sum(v[1] for v in cardinal.values()) / 3
    centroid = (c_lat, c_lon)
    cent_to_sol = haversine(c_lat, c_lon, SOLUTION[0], SOLUTION[1], E)

    pts_list = list(cardinal.values())
    names = list(cardinal.keys())
    sides = []
    for i in range(3):
        for j in range(i + 1, 3):
            d = haversine(pts_list[i][0], pts_list[i][1],
                          pts_list[j][0], pts_list[j][1], E)
            sides.append({"pair": f"{names[i]} \u2194 {names[j]}", "distance_mi": d})
    max_span = max(s["distance_mi"] for s in sides)

    all_lats = [v[0] for v in SCENES.values()]
    all_lons = [v[1] for v in SCENES.values()]
    cent_all = (sum(all_lats) / 4, sum(all_lons) / 4)

    d_md_ph = haversine(MD[0], MD[1], ph[0], ph[1], E)
    brs = SCENES["Blue Rock Springs (07/04/1969)"]
    lb = SCENES["Lake Berryessa (09/27/1969)"]
    d_brs_lb = haversine(brs[0], brs[1], lb[0], lb[1], E)

    V3 = {
        "cardinal_points": {k: {"lat": v[0], "lon": v[1]} for k, v in cardinal.items()},
        "centroid": {"lat": c_lat, "lon": c_lon},
        "solution": {"lat": SOLUTION[0], "lon": SOLUTION[1]},
        "centroid_to_solution_mi": cent_to_sol,
        "side_lengths_mi": sides,
        "max_span_mi": max_span,
        "offset_pct_of_max_span": (cent_to_sol / max_span) * 100,
        "distance_symmetry": {
            "md_to_presidio_mi": d_md_ph,
            "brs_to_lb_mi": d_brs_lb,
            "ratio": d_brs_lb / d_md_ph if d_md_ph else float("inf"),
        },
        "all_four_crime_scenes_centroid": {"lat": cent_all[0], "lon": cent_all[1]},
        "all_four_centroid_to_solution_mi": haversine(
            cent_all[0], cent_all[1], SOLUTION[0], SOLUTION[1], E),
    }

    # -- V4: Proximity analysis ---------------------------------------------
    scene_dists = {name: haversine(SOLUTION[0], SOLUTION[1], lat, lon, E)
                   for name, (lat, lon) in SCENES.items()}
    d_tri = haversine(SOLUTION[0], SOLUTION[1],
                      TRIANGLE_ANOMALY[0], TRIANGLE_ANOMALY[1], E)

    V4 = {
        "solution": {"lat": SOLUTION[0], "lon": SOLUTION[1]},
        "crime_scene_distances_mi": scene_dists,
        "triangle_anomaly": {"lat": TRIANGLE_ANOMALY[0], "lon": TRIANGLE_ANOMALY[1]},
        "solution_to_triangle": {
            "miles": d_tri,
            "feet": d_tri * 5280,
            "meters": d_tri * 1609.34,
            "map_inches": d_tri / SCALE,
        },
    }

    # -- V5: Statistical analysis -------------------------------------------
    survival_rate = TOTAL_SURVIVORS / TOTAL_CANDIDATES
    tri_area_sqft = (math.sqrt(3) / 4) * 100 ** 2
    tri_area_sqmi = tri_area_sqft / 5280 ** 2
    map_area_sqmi = (
        (C["MAP_BOUNDS"]["north"] - C["MAP_BOUNDS"]["south"]) * 69.0
        * (C["MAP_BOUNDS"]["east"] - C["MAP_BOUNDS"]["west"]) * 69.0
        * math.cos(math.radians(38.0))
    )
    crime_zone_r = 5.0
    crime_zone_area = math.pi * crime_zone_r ** 2
    p_zone = tri_area_sqmi / crime_zone_area
    p_presidio = 1 / 90
    p_joint = survival_rate * p_zone * p_presidio

    V5 = {
        "constraint_filter": {
            "total_candidates": TOTAL_CANDIDATES,
            "survivors": TOTAL_SURVIVORS,
            "survival_rate": survival_rate,
            "survival_rate_pct": survival_rate * 100,
        },
        "geographic_coincidence": {
            "triangle_area_sqft": tri_area_sqft,
            "triangle_area_sqmi": tri_area_sqmi,
            "map_area_sqmi": map_area_sqmi,
            "p_random_full": tri_area_sqmi / map_area_sqmi,
            "odds_full_map_1_in": map_area_sqmi / tri_area_sqmi,
            "crime_zone_radius_mi": crime_zone_r,
            "crime_zone_area_sqmi": crime_zone_area,
            "p_random_zone": p_zone,
            "odds_zone_1_in": 1 / p_zone,
        },
        "clock_alignment": {
            "p_presidio_8oclock_pm2deg": p_presidio,
            "p_two_vallejo_in_10_sector": 1 / 144,
            "p_solution_in_10_sector": 1 / 12,
        },
        "joint_probability_conservative": {
            "p_joint": p_joint,
            "odds_1_in": 1 / p_joint,
        },
    }

    # -- V6: Homophonic lock proof ------------------------------------------
    sol_str = "INTHREEANDTHREEEIGHTHSRADIANSTEN"
    lock_checks = []
    all_pass = True
    for i, j in LOCKS:
        ok = sol_str[i] == sol_str[j]
        all_pass &= ok
        lock_checks.append({
            "i": i, "j": j,
            "char_i": sol_str[i], "char_j": sol_str[j],
            "pass": ok,
        })

    freq = Counter(sol_str)
    freq_rows = [
        {"char": ch, "count": cnt,
         "positions": [i for i, c in enumerate(sol_str) if c == ch]}
        for ch, cnt in sorted(freq.items(), key=lambda x: -x[1])
    ]

    V6 = {
        "solution_string": sol_str,
        "length": len(sol_str),
        "lock_checks": lock_checks,
        "all_locks_satisfied": all_pass,
        "letter_frequency": freq_rows,
    }

    # -- V7: Near-equilateral 8/10 relation ---------------------------------
    lhr = SCENES["Lake Herman Road (12/20/1968)"]
    bear_sol = true_bearing(MD[0], MD[1], SOLUTION[0], SOLUTION[1])
    bear_ph = true_bearing(MD[0], MD[1], ph[0], ph[1])
    sep_8_10 = angular_separation(bear_sol, bear_ph)

    s_md_sol = haversine(MD[0], MD[1], SOLUTION[0], SOLUTION[1], E)
    s_md_ph = haversine(MD[0], MD[1], ph[0], ph[1], E)
    s_sol_ph = haversine(SOLUTION[0], SOLUTION[1], ph[0], ph[1], E)

    a_md = angle_from_sides(s_md_sol, s_md_ph, s_sol_ph)
    a_sol = angle_from_sides(s_md_sol, s_sol_ph, s_md_ph)
    a_ph = angle_from_sides(s_md_ph, s_sol_ph, s_md_sol)

    sides_710 = [s_md_sol, s_md_ph, s_sol_ph]
    angles_710 = [a_md, a_sol, a_ph]
    mean_s = sum(sides_710) / 3
    sdev = [((s / mean_s) - 1) * 100 for s in sides_710]
    adev = [a - 60 for a in angles_710]

    # Inner triangle: BRS-LHR-Centroid
    s_brs_lhr = haversine(brs[0], brs[1], lhr[0], lhr[1], E)
    s_lhr_c = haversine(lhr[0], lhr[1], c_lat, c_lon, E)
    s_c_brs = haversine(c_lat, c_lon, brs[0], brs[1], E)
    a_brs = angle_from_sides(s_brs_lhr, s_c_brs, s_lhr_c)
    a_lhr = angle_from_sides(s_brs_lhr, s_lhr_c, s_c_brs)
    a_cent = angle_from_sides(s_lhr_c, s_c_brs, s_brs_lhr)

    motifs = [
        motif_row("inner_triangle_brs_lhr_centroid",
                  [s_brs_lhr, s_lhr_c, s_c_brs],
                  [a_brs, a_lhr, a_cent],
                  ["BRS \u2194 LHR", "LHR \u2194 Centroid", "Centroid \u2194 BRS"]),
        motif_row("near_equilateral_md_z32_presidio",
                  sides_710, angles_710,
                  ["Mt. Diablo \u2194 Z32", "Mt. Diablo \u2194 Presidio",
                   "Z32 \u2194 Presidio"]),
    ]

    # Monte Carlo: probability of equilateral within tolerance
    tol_deg = 0.8
    mc_n = 1_000_000
    rng = random.Random(32)

    ref_lat = (MD[0] + lb[0] + ph[0]) / 3
    ref_lon = (MD[1] + lb[1] + ph[1]) / 3
    tri_a = to_local_miles(MD[0], MD[1], ref_lat, ref_lon)
    tri_b = to_local_miles(lb[0], lb[1], ref_lat, ref_lon)
    tri_c = to_local_miles(ph[0], ph[1], ref_lat, ref_lon)
    lhr_xy = to_local_miles(lhr[0], lhr[1], ref_lat, ref_lon)
    brs_xy = to_local_miles(brs[0], brs[1], ref_lat, ref_lon)

    def dist_xy(p, q):
        return math.hypot(p[0] - q[0], p[1] - q[1])

    base = dist_xy(lhr_xy, brs_xy)
    hits = 0
    for _ in range(mc_n):
        p = sample_point_in_triangle(tri_a, tri_b, tri_c, rng)
        d1, d2 = dist_xy(lhr_xy, p), dist_xy(brs_xy, p)
        angs = [angle_from_sides(base, d1, d2),
                angle_from_sides(base, d2, d1),
                angle_from_sides(d1, d2, base)]
        if max(abs(a - 60) for a in angs) <= tol_deg:
            hits += 1

    p_eq = hits / mc_n
    se = math.sqrt(p_eq * (1 - p_eq) / mc_n)

    V7 = {
        "bearings_true_deg": {
            "mt_diablo_to_z32": bear_sol,
            "mt_diablo_to_presidio": bear_ph,
            "angular_separation": sep_8_10,
        },
        "triangle_md_z32_presidio": {
            "sides_mi": {
                "mt_diablo_to_z32": s_md_sol,
                "mt_diablo_to_presidio": s_md_ph,
                "z32_to_presidio": s_sol_ph,
            },
            "interior_angles_deg": {
                "at_mt_diablo": a_md,
                "at_z32": a_sol,
                "at_presidio": a_ph,
            },
            "deviation_from_equilateral": {
                "side_deviation_pct_from_mean": {
                    "mt_diablo_to_z32": sdev[0],
                    "mt_diablo_to_presidio": sdev[1],
                    "z32_to_presidio": sdev[2],
                },
                "angle_deviation_deg_from_60": {
                    "at_mt_diablo": adev[0],
                    "at_z32": adev[1],
                    "at_presidio": adev[2],
                },
                "max_abs_side_deviation_pct": max(abs(x) for x in sdev),
                "max_abs_angle_deviation_deg": max(abs(x) for x in adev),
            },
        },
        "equilateral_motif_residuals": motifs,
        "random_point_equilateral_tolerance": {
            "region": "operational_triangle_md_lb_ph",
            "fixed_edge": "LHR_BRS",
            "tolerance_deg": tol_deg,
            "monte_carlo_samples": mc_n,
            "hits_within_tolerance": hits,
            "probability": p_eq,
            "odds_1_in": (1 / p_eq) if p_eq > 0 else None,
            "standard_error": se,
            "rng_seed": 32,
        },
    }

    # -- V8: Survivor clock-hour distribution -------------------------------
    counts, total_surv = load_survivor_clock_distribution()
    h8, h10 = counts.get(8, 0), counts.get(10, 0)
    combined = h8 + h10
    obs = combined / total_surv if total_surv else 0
    exp = 2 / 12

    V8 = {
        "survivor_total": total_surv,
        "by_clock_hour": {str(k): v for k, v in sorted(counts.items())},
        "hour_8_count": h8,
        "hour_10_count": h10,
        "combined_8_10_count": combined,
        "combined_8_10_fraction": obs,
        "combined_8_10_pct": obs * 100,
        "expected_two_hours_fraction": exp,
        "expected_two_hours_pct": exp * 100,
        "enrichment_vs_random": obs / exp if exp else float("inf"),
    }

    # -- V9: Pre-existing PH-BRS angular separation --------------------------
    bear_brs = true_bearing(MD[0], MD[1], brs[0], brs[1])
    sep_ph_brs = angular_separation(bear_ph, bear_brs)
    sep_ph_lhr = angular_separation(bear_ph,
                                    true_bearing(MD[0], MD[1], lhr[0], lhr[1]))

    mag_ph = mag_bearing(MD[0], MD[1], ph[0], ph[1], DEC)
    mag_brs = mag_bearing(MD[0], MD[1], brs[0], brs[1], DEC)
    mag_lhr = mag_bearing(MD[0], MD[1], lhr[0], lhr[1], DEC)
    mag_sol = mag_bearing(MD[0], MD[1], SOLUTION[0], SOLUTION[1], DEC)

    V9 = {
        "description": "Pre-existing crime-scene angular structure (independent of cipher solution)",
        "ph_brs_separation_deg": sep_ph_brs,
        "ph_brs_delta_from_60": abs(sep_ph_brs - 60),
        "ph_lhr_separation_deg": sep_ph_lhr,
        "ph_lhr_delta_from_60": abs(sep_ph_lhr - 60),
        "ph_sol_separation_deg": sep_8_10,
        "ph_sol_delta_from_60": abs(sep_8_10 - 60),
        "magnetic_bearings": {
            "presidio_heights": mag_ph,
            "blue_rock_springs": mag_brs,
            "lake_herman_road": mag_lhr,
            "z32_solution": mag_sol,
        },
        "clock_hours": {
            "presidio_heights": bearing_to_clock(mag_ph),
            "blue_rock_springs": bearing_to_clock(mag_brs),
            "lake_herman_road": bearing_to_clock(mag_lhr),
            "z32_solution": bearing_to_clock(mag_sol),
        },
    }

    # -- V10: Astronomical date alignments ------------------------------------
    # Winter Solstice 1968: Dec 21, 19:00:18 UTC (source: worldspaceflight.com)
    # LHR attack: Dec 20, 1968 (evening PST) = Dec 21 ~02:00-06:00 UTC
    lhr_date = datetime(1968, 12, 20)
    solstice_1968 = datetime(1968, 12, 21)
    lhr_solstice_offset_days = (lhr_date - solstice_1968).days  # -1

    # Earth Aphelion 1969: ~Jul 4-5, 1969 (source: astropixels.com, NOAA)
    brs_date = datetime(1969, 7, 4)
    aphelion_1969_approx = datetime(1969, 7, 4)  # July 4-5
    brs_aphelion_offset_days = (brs_date - aphelion_1969_approx).days  # 0

    # Autumnal Equinox 1969: Sep 23, 05:06:47 UTC (source: worldspaceflight.com)
    lb_date = datetime(1969, 9, 27)
    equinox_1969 = datetime(1969, 9, 23)
    lb_equinox_offset_days = (lb_date - equinox_1969).days  # 4

    # 3.375-month timer: Z32 mailed Jun 26 1970 -> next communication
    z32_mailed = datetime(1970, 6, 26)
    months_avg = 3.375 * 30.4375  # average days per month
    projected_avg = z32_mailed + timedelta(days=months_avg)
    thirteen_hole_postmark = datetime(1970, 10, 5)
    thirteen_hole_received = datetime(1970, 10, 7)
    timer_offset_postmark = (thirteen_hole_postmark - projected_avg).days
    timer_offset_received = (thirteen_hole_received - projected_avg).days

    V10 = {
        "description": "Astronomical date alignments for Vallejo-area attacks",
        "lake_herman_road": {
            "attack_date": "1968-12-20",
            "astronomical_event": "Winter Solstice",
            "event_date": "1968-12-21",
            "event_time_utc": "19:00:18",
            "source": "worldspaceflight.com (Meeus algorithm)",
            "offset_days": lhr_solstice_offset_days,
            "note": "Attack evening of Dec 20 PST; solstice midday Dec 21 PST",
        },
        "blue_rock_springs": {
            "attack_date": "1969-07-04",
            "astronomical_event": "Earth Aphelion",
            "event_date": "~1969-07-04",
            "source": "astropixels.com (Meeus/JPL), annual range Jul 3-5",
            "offset_days": brs_aphelion_offset_days,
        },
        "lake_berryessa": {
            "attack_date": "1969-09-27",
            "astronomical_event": "Autumnal Equinox",
            "event_date": "1969-09-23",
            "event_time_utc": "05:06:47",
            "source": "worldspaceflight.com (Meeus algorithm)",
            "offset_days": lb_equinox_offset_days,
            "note": "Weaker alignment (4 days offset)",
        },
        "temporal_timer": {
            "z32_mailed": "1970-06-26",
            "value_months": 3.375,
            "projected_date_avg_month": projected_avg.strftime("%Y-%m-%d"),
            "thirteen_hole_postmark": "1970-10-05",
            "thirteen_hole_received": "1970-10-07",
            "source_postmark": "crimelibrary.org",
            "source_received": "Wikipedia (Zodiac Killer article)",
            "offset_from_postmark_days": timer_offset_postmark,
            "offset_from_received_days": timer_offset_received,
        },
    }

    # -- Assemble results ---------------------------------------------------
    results = {
        "metadata": {
            "suite": "z32_verify",
            "generated_at": datetime.now().isoformat(),
            "data_source": "data.py",
        },
        "constants": {
            "earth_radius_mi": E,
            "mt_diablo": {"lat": MD[0], "lon": MD[1]},
            "mag_dec_1970_deg_east": DEC,
            "map_scale_mi_per_in": SCALE,
            "map_bounds": C["MAP_BOUNDS"],
            "locks_0_indexed": [[i, j] for i, j in LOCKS],
            "cipher_length": C["CIPHER_LENGTH"],
        },
        "verification_1_coordinate_derivation": V1,
        "verification_2_clock_hour_geometry": V2,
        "verification_3_geometric_centroid": V3,
        "verification_4_proximity_analysis": V4,
        "verification_5_statistical_analysis": V5,
        "verification_6_homophonic_lock_proof": V6,
        "verification_7_near_equilateral_8_10": V7,
        "verification_8_survivor_clock_distribution": V8,
        "verification_9_preexisting_angular_structure": V9,
        "verification_10_astronomical_date_alignments": V10,
    }

    # Short aliases
    for i in range(1, 11):
        long_keys = [k for k in results if k.startswith(f"verification_{i}_")]
        if long_keys:
            results[f"verification_{i}"] = results[long_keys[0]]

    return results


# ===========================================================================
# Console output
# ===========================================================================

def print_verification(results: dict):
    C = results["constants"]
    V1 = results["verification_1_coordinate_derivation"]
    V2 = results["verification_2_clock_hour_geometry"]
    V3 = results["verification_3_geometric_centroid"]
    V4 = results["verification_4_proximity_analysis"]
    V5 = results["verification_5_statistical_analysis"]
    V6 = results["verification_6_homophonic_lock_proof"]
    V7 = results["verification_7_near_equilateral_8_10"]
    V8 = results["verification_8_survivor_clock_distribution"]
    V9 = results["verification_9_preexisting_angular_structure"]

    def hdr(n, title):
        print("=" * 70)
        print(f"VERIFICATION {n}: {title}")
        print("=" * 70)
        print()

    hdr(1, "Solution Coordinate Derivation")
    print(f"Plaintext: {V1['plaintext']}")
    print(f"  {V1['distance_inches']} in x {C['map_scale_mi_per_in']} mi/in = {V1['distance_miles']} mi")
    print(f"  {V1['clock_hour']}:00 -> {V1['mag_bearing_deg']} deg mag -> {V1['true_bearing_deg']} deg true")
    print(f"  Projected: ({V1['projected']['lat']:.6f}, {V1['projected']['lon']:.6f})")
    print(f"  Stated:    ({V1['stated_solution']['lat']}, {V1['stated_solution']['lon']})")
    print(f"  Error: {V1['error']['lat_deg']:.10f} deg lat, {V1['error']['lon_deg']:.10f} deg lon")
    print(f"  VERDICT: {'EXACT MATCH' if V1['exact_match'] else 'MISMATCH'}\n")

    hdr(2, "Clock-Hour Geometry")
    header = f"{'Location':<35} {'True':>8} {'Mag':>8} {'Clock':>8} {'Nearest':>8}"
    print(header)
    print("-" * len(header))
    for r in V2["rows"]:
        print(f"{r['location']:<35} {r['true_bearing_deg']:>7.2f} deg {r['mag_bearing_deg']:>7.2f} deg "
              f"{r['clock_exact']:>7.2f} {r['clock_nearest_hour']:>7d}h")
    print(f"\n  Presidio Heights: {V2['presidio']['clock_exact']:.2f} o'clock")
    print(f"  Z32 Solution:     {V2['z32_solution']['clock_exact']:.2f} o'clock\n")

    hdr(3, "Geometric Centroid")
    print(f"Centroid: ({V3['centroid']['lat']:.4f}, {V3['centroid']['lon']:.4f})")
    print(f"Solution: ({V3['solution']['lat']:.6f}, {V3['solution']['lon']:.6f})")
    print(f"Distance: {V3['centroid_to_solution_mi']:.2f} mi "
          f"({V3['offset_pct_of_max_span']:.1f}% of {V3['max_span_mi']:.1f} mi span)\n")

    hdr(4, "Proximity Analysis")
    for name, d in V4["crime_scene_distances_mi"].items():
        print(f"  {name:<35} {d:>9.2f} mi")
    t = V4["solution_to_triangle"]
    print(f"\n  Triangle anomaly: {t['miles']:.3f} mi = {t['feet']:.0f} ft = "
          f"{t['meters']:.0f} m ({t['map_inches']:.4f} in on map)\n")

    hdr(5, "Statistical Analysis")
    cf = V5["constraint_filter"]
    print(f"  Candidates: {cf['total_candidates']:,}  Survivors: {cf['survivors']}")
    print(f"  Survival rate: {cf['survival_rate']:.2e}")
    gc = V5["geographic_coincidence"]
    print(f"  P(zone hit): 1 in {gc['odds_zone_1_in']:,.0f}")
    jp = V5["joint_probability_conservative"]
    print(f"  Joint P: {jp['p_joint']:.2e} (1 in {jp['odds_1_in']:,.0f})\n")

    hdr(6, "Homophonic Lock Proof")
    print(f"  String: {V6['solution_string']}  Length: {V6['length']}")
    for lc in V6["lock_checks"]:
        s = "PASS" if lc["pass"] else "FAIL"
        print(f"  [{lc['i']:2d}]='{lc['char_i']}' == [{lc['j']:2d}]='{lc['char_j']}' -> {s}")
    print(f"  All satisfied: {V6['all_locks_satisfied']}\n")

    hdr(7, "Near-Equilateral 8/10 Relation")
    b = V7["bearings_true_deg"]
    print(f"  MD->Z32:     {b['mt_diablo_to_z32']:.3f} deg")
    print(f"  MD->Presidio: {b['mt_diablo_to_presidio']:.3f} deg")
    print(f"  Separation:  {b['angular_separation']:.3f} deg")
    tri = V7["triangle_md_z32_presidio"]
    print(f"  Angles: {tri['interior_angles_deg']['at_mt_diablo']:.3f} deg, "
          f"{tri['interior_angles_deg']['at_z32']:.3f} deg, "
          f"{tri['interior_angles_deg']['at_presidio']:.3f} deg")
    mc = V7["random_point_equilateral_tolerance"]
    if mc["odds_1_in"]:
        print(f"  Monte Carlo: 1 in {mc['odds_1_in']:.0f} (n={mc['monte_carlo_samples']:,})\n")

    hdr(8, "Survivor Clock-Hour Distribution")
    print(f"  Total: {V8['survivor_total']}")
    for hr, cnt in V8["by_clock_hour"].items():
        print(f"    {hr:>2}:00 -> {cnt}")
    print(f"  Hours 8+10: {V8['combined_8_10_count']}/{V8['survivor_total']} "
          f"({V8['combined_8_10_pct']:.1f}%, {V8['enrichment_vs_random']:.1f}x enrichment)\n")

    hdr(9, "Pre-Existing Angular Structure")
    print(f"  PH-BRS separation: {V9['ph_brs_separation_deg']:.2f} deg "
          f"(Delta from 60 deg: {V9['ph_brs_delta_from_60']:.2f} deg)")
    print(f"  PH-LHR separation: {V9['ph_lhr_separation_deg']:.2f} deg "
          f"(Delta from 60 deg: {V9['ph_lhr_delta_from_60']:.2f} deg)")
    print(f"  PH-SOL separation: {V9['ph_sol_separation_deg']:.2f} deg "
          f"(Delta from 60 deg: {V9['ph_sol_delta_from_60']:.2f} deg)")
    print(f"  Magnetic bearings: PH={V9['magnetic_bearings']['presidio_heights']:.2f} deg, "
          f"BRS={V9['magnetic_bearings']['blue_rock_springs']:.2f} deg, "
          f"SOL={V9['magnetic_bearings']['z32_solution']:.2f} deg\n")



    V10 = results["verification_10_astronomical_date_alignments"]
    hdr(10, "Astronomical Date Alignments")
    lhr = V10["lake_herman_road"]
    print(f"  Lake Herman Road: {lhr['attack_date']} vs {lhr['astronomical_event']} "
          f"{lhr['event_date']} (offset: {lhr['offset_days']:+d} day)")
    brs = V10["blue_rock_springs"]
    print(f"  Blue Rock Springs: {brs['attack_date']} vs {brs['astronomical_event']} "
          f"{brs['event_date']} (offset: {brs['offset_days']:+d} day)")
    lb = V10["lake_berryessa"]
    print(f"  Lake Berryessa: {lb['attack_date']} vs {lb['astronomical_event']} "
          f"{lb['event_date']} (offset: {lb['offset_days']:+d} days)")
    tm = V10["temporal_timer"]
    print(f"  3.375-month timer: {tm['z32_mailed']} + {tm['value_months']} mo "
          f"-> {tm['projected_date_avg_month']}")
    print(f"    13-Hole postmark: {tm['thirteen_hole_postmark']} "
          f"(offset: {tm['offset_from_postmark_days']:+d} days)")
    print(f"    13-Hole received: {tm['thirteen_hole_received']} "
          f"(offset: {tm['offset_from_received_days']:+d} days)\n")


# ===========================================================================
# I/O + main
# ===========================================================================

def save_results_json(results: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Saved: {path}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Z32 verification suite")
    parser.add_argument("--json-out", default="output/verify_results.json")
    parser.add_argument("--no-json", action="store_true")
    args = parser.parse_args()

    C = build_constants()
    results = compute_results(C)
    print_verification(results)

    if not args.no_json:
        save_results_json(results, Path(args.json_out))

    print("=" * 70)
    print("VERIFICATION COMPLETE")
    print("=" * 70)
