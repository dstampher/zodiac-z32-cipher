#!/usr/bin/env python3
"""
Z32 Cipher Solver

Solves the Zodiac Killer's 32-character cipher by generating candidate plaintexts,
filtering by cipher constraints, and scoring by proximity to crime scenes.
Outputs all ranked candidates.
"""

import math
from dataclasses import dataclass
from itertools import product

# =============================================================================
# CONSTANTS
# =============================================================================

MT_DIABLO = (37.881628, -121.914382)

# Phillips 66 map: 1 inch = 6.4 miles
MAP_SCALE = 6.4

# Magnetic declination ~17° east of true north in 1970 Bay Area
MAGNETIC_DECLINATION = 17.0

# Map bounds (approximate extent of Phillips 66 map)
MAP_BOUNDS = {"north": 38.8, "south": 37.3, "east": -121.0, "west": -123.0}

# Zodiac crime scenes
CRIME_SCENES = {
    "Lake Herman Road": (38.0949, -122.1441),
    "Blue Rock Springs": (38.1189, -122.1528),
    "Lake Berryessa": (38.5755, -122.2274),
    "Presidio Heights": (37.7875, -122.4564),
}

# Z32 cipher constraints (0-indexed positions that must have matching letters)
CONSTRAINTS = [(0, 25), (1, 31), (5, 13)]

# Number words
NUMBERS = {
    0: "ZERO", 1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE",
    6: "SIX", 7: "SEVEN", 8: "EIGHT", 9: "NINE", 10: "TEN",
    11: "ELEVEN", 12: "TWELVE"
}

# Fraction words and their decimal values
FRACTIONS = {
    "": 0,
    "ANDAHALF": 0.5,
    "ANDAQUARTER": 0.25,
    "ANDTHREEQUARTERS": 0.75,
    "ANDANEIGHTH": 0.125,
    "ANDTHREEEIGHTHS": 0.375,
    "ANDFIVEEIGHTHS": 0.625,
    "ANDSEVENEIGHTHS": 0.875,
    "ANDASIXTEENTH": 0.0625,
    "ANDTHREESIXTEENTHS": 0.1875,
    "ANDFIVESIXTEENTHS": 0.3125,
    "ANDSEVENSIXTEENTHS": 0.4375,
    "ANDNINESIXTEENTHS": 0.5625,
    "ANDELEVENSIXTEENTHS": 0.6875,
    "ANDTHIRTEENSIXTEENTHS": 0.8125,
    "ANDFIFTEENSIXTEENTHS": 0.9375,
    "ANDATHIRD": 1/3,
    "ANDTWOTHIRDS": 2/3,
}

# Prefix options
PREFIXES = ["", "IN", "INCH", "INCHES"]

# Radian word options
RADIAN_WORDS = ["RAD", "RADS", "RADIAN", "RADIANS"]


# =============================================================================
# DATA CLASS
# =============================================================================

@dataclass
class Candidate:
    plaintext: str
    readable: str
    distance_inches: float
    angle_clock: int
    lat: float
    lon: float
    distance_miles: float
    score: float
    nearest_scene: str
    nearest_distance: float
    lhr_distance: float 


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def passes_constraints(phrase: str) -> bool:
    """Check if a 32-character phrase satisfies the Z32 repeat constraints."""
    if len(phrase) != 32:
        return False
    for pos_a, pos_b in CONSTRAINTS:
        if phrase[pos_a] != phrase[pos_b]:
            return False
    return True


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in miles between two coordinates."""
    R = 3958.8  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def project_location(distance_inches: float, clock_hour: int) -> tuple[float, float]:
    """Project from Mt. Diablo using polar coordinates."""
    distance_miles = distance_inches * MAP_SCALE
    
    # Convert clock position to degrees (12 o'clock = 0°, clockwise)
    magnetic_bearing = (clock_hour % 12) * 30
    
    # Adjust for magnetic declination
    true_bearing = (magnetic_bearing + MAGNETIC_DECLINATION) % 360
    
    # Convert to radians
    bearing_rad = math.radians(true_bearing)
    origin_lat_rad = math.radians(MT_DIABLO[0])
    origin_lon_rad = math.radians(MT_DIABLO[1])
    
    # Angular distance
    R = 3958.8
    angular_dist = distance_miles / R
    
    # Haversine projection
    target_lat_rad = math.asin(
        math.sin(origin_lat_rad) * math.cos(angular_dist) +
        math.cos(origin_lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
    )
    target_lon_rad = origin_lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(origin_lat_rad),
        math.cos(angular_dist) - math.sin(origin_lat_rad) * math.sin(target_lat_rad)
    )
    
    return math.degrees(target_lat_rad), math.degrees(target_lon_rad)


def is_on_map(lat: float, lon: float) -> bool:
    """Check if coordinates fall within Phillips 66 map bounds."""
    return (MAP_BOUNDS["south"] <= lat <= MAP_BOUNDS["north"] and
            MAP_BOUNDS["west"] <= lon <= MAP_BOUNDS["east"])


def score_location(lat: float, lon: float) -> tuple[float, str, float, float]:
    """Score a location by proximity to Zodiac crime scenes."""
    distances = {name: haversine(lat, lon, *coords) 
                 for name, coords in CRIME_SCENES.items()}
    nearest = min(distances, key=distances.get)
    nearest_dist = distances[nearest]
    lhr_dist = distances["Lake Herman Road"]
    
    # Score: inverse of distance to nearest crime scene
    score = 1 / (nearest_dist + 0.1)
    
    return score, nearest, nearest_dist, lhr_dist


def make_readable(phrase: str) -> str:
    """Add spaces to make phrase human-readable."""
    tokens = [
        "THIRTEENSIXTEENTHS", "FIFTEENSIXTEENTHS", "ELEVENSIXTEENTHS",
        "NINESIXTEENTHS", "SEVENSIXTEENTHS", "FIVESIXTEENTHS", 
        "THREESIXTEENTHS", "ASIXTEENTH",
        "THREEQUARTERS", "AQUARTER",
        "SEVENEIGHTHS", "FIVEEIGHTHS", "THREEEIGHTHS", "ANEIGHTH",
        "TWOTHIRDS", "ATHIRD",
        "AHALF",
        "RADIANS", "RADIAN", "RADS", "RAD",
        "INCHES", "INCH",
        "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN", "SEVENTEEN", 
        "EIGHTEEN", "NINETEEN", "ELEVEN", "TWELVE", "TWENTY",
        "THREE", "SEVEN", "EIGHT", "FOUR", "FIVE", "NINE",
        "ZERO", "ONE", "TWO", "SIX", "TEN",
        "SIXTEENTHS", "SIXTEENTH",
        "QUARTERS", "QUARTER", 
        "EIGHTHS", "EIGHTH",
        "THIRDS", "THIRD",
        "HALF",
        "AND", "A", "IN"
    ]
    
    splits = {
        "SEVENEIGHTHS": ["SEVEN", "EIGHTHS"],
        "FIVEEIGHTHS": ["FIVE", "EIGHTHS"],
        "THREEEIGHTHS": ["THREE", "EIGHTHS"],
        "ANEIGHTH": ["AN", "EIGHTH"],
        "THREEQUARTERS": ["THREE", "QUARTERS"],
        "AQUARTER": ["A", "QUARTER"],
        "TWOTHIRDS": ["TWO", "THIRDS"],
        "ATHIRD": ["A", "THIRD"],
        "AHALF": ["A", "HALF"],
        "ASIXTEENTH": ["A", "SIXTEENTH"],
        "THIRTEENSIXTEENTHS": ["THIRTEEN", "SIXTEENTHS"],
        "FIFTEENSIXTEENTHS": ["FIFTEEN", "SIXTEENTHS"],
        "ELEVENSIXTEENTHS": ["ELEVEN", "SIXTEENTHS"],
        "NINESIXTEENTHS": ["NINE", "SIXTEENTHS"],
        "SEVENSIXTEENTHS": ["SEVEN", "SIXTEENTHS"],
        "FIVESIXTEENTHS": ["FIVE", "SIXTEENTHS"],
        "THREESIXTEENTHS": ["THREE", "SIXTEENTHS"],
    }
    
    result = []
    remaining = phrase
    
    while remaining:
        matched = False
        for token in tokens:
            if remaining.startswith(token):
                if token in splits:
                    result.extend(splits[token])
                else:
                    result.append(token)
                remaining = remaining[len(token):]
                matched = True
                break
        if not matched:
            result.append(remaining[0])
            remaining = remaining[1:]
    
    return " ".join(result)


# =============================================================================
# CANDIDATE GENERATION
# =============================================================================

def generate_phrases():
    """Generate all 32-character candidate phrases."""
    phrases = set()
    distance_nums = range(0, 13)
    angle_nums = range(1, 13)
    
    for dist_val, angle_val in product(distance_nums, angle_nums):
        dist_word = NUMBERS[dist_val]
        angle_word = NUMBERS[angle_val]
        
        for frac_word, frac_val in FRACTIONS.items():
            for prefix in PREFIXES:
                for radian in RADIAN_WORDS:
                    # Template 1
                    phrase = f"{prefix}{dist_word}{frac_word}{radian}{angle_word}"
                    if len(phrase) == 32:
                        phrases.add((phrase, dist_val + frac_val, angle_val))
                    
                    # Template 2
                    phrase = f"{prefix}{angle_word}{radian}{dist_word}{frac_word}"
                    if len(phrase) == 32:
                        phrases.add((phrase, dist_val + frac_val, angle_val))
                    
                    # Template 3 (no prefix)
                    if prefix == "":
                        phrase = f"{dist_word}{frac_word}{radian}{angle_word}"
                        if len(phrase) == 32:
                            phrases.add((phrase, dist_val + frac_val, angle_val))
                        
                        phrase = f"{angle_word}{radian}{dist_word}{frac_word}"
                        if len(phrase) == 32:
                            phrases.add((phrase, dist_val + frac_val, angle_val))
    
    return list(phrases)


def solve() -> list[Candidate]:
    """Run the full solver pipeline and return all candidates."""
    # Generate
    all_phrases = generate_phrases()
    print(f"Generated {len(all_phrases)} 32-character phrases")
    
    # Filter by constraints
    valid = [(p, d, a) for p, d, a in all_phrases if passes_constraints(p)]
    print(f"Passed cipher constraints: {len(valid)}")
    
    # Calculate locations and filter by map bounds
    candidates = []
    for phrase, dist_inches, angle_clock in valid:
        lat, lon = project_location(dist_inches, angle_clock)
        
        if not is_on_map(lat, lon):
            continue
        
        score, nearest, nearest_dist, lhr_dist = score_location(lat, lon)
        
        candidates.append(Candidate(
            plaintext=phrase,
            readable=make_readable(phrase),
            distance_inches=dist_inches,
            angle_clock=angle_clock,
            lat=lat,
            lon=lon,
            distance_miles=dist_inches * MAP_SCALE,
            score=score,
            nearest_scene=nearest,
            nearest_distance=nearest_dist,
            lhr_distance=lhr_dist
        ))
    
    print(f"On Phillips 66 map: {len(candidates)}")
    
    # Sort by score (highest first)
    candidates.sort(key=lambda c: c.score, reverse=True)
    
    return candidates


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("Z32 CIPHER SOLVER")
    print("=" * 70)
    print()
    
    # Solve and get ALL candidates
    candidates = solve()
    
    print()
    print("=" * 70)
    print(f"ALL CANDIDATES (Ranked 1 to {len(candidates)})")
    print("=" * 70)
    
    for i, c in enumerate(candidates, 1):
        print(f"\n#{i}")
        print(f"  Plaintext: {c.plaintext}")
        print(f"  Readable:  {c.readable}")
        print(f"  Distance:  {c.distance_inches} in × 6.4 mi/in = {c.distance_miles:.1f} miles")
        print(f"  Angle:     {c.angle_clock} o'clock ({(c.angle_clock % 12) * 30}° magnetic)")
        print(f"  Location:  {c.lat:.6f}, {c.lon:.6f}")
        print(f"  → Lake Herman Road: {c.lhr_distance:.2f} miles")
        if c.nearest_scene != "Lake Herman Road":
            print(f"  → {c.nearest_scene}: {c.nearest_distance:.2f} miles")
        print(f"  Maps:      https://www.google.com/maps?q={c.lat},{c.lon}")

if __name__ == "__main__":
    main()