#!/usr/bin/env python3
import math
from itertools import product

# --- CONFIGURATION ---
ANCHOR = (37.881628, -121.914382)  # Mt. Diablo
MAG_DEC = 17.0                     # 1970 Declination
SCALE   = 6.4                      # Miles per inch
BOUNDS  = (37.3, 38.8, -123.0, -121.0) # S, N, W, E

CRIME_SCENES = {
    # Validated via Police Reports
    "LHR": (38.0949, -122.1441),  # Lake Herman Road (Faraday/Jensen)
    "BRS": (38.1260, -122.1911),  # Blue Rock Springs (Ferrin/Mageau)
    "LB":  (38.5636, -122.2317),  # Lake Berryessa (Shepard/Hartnell)
    "PH":  (37.7887, -122.4571)   # Presidio Heights (Stine)
}

# 0-indexed constraints: (0=25), (1=31), (5=13)
LOCKS = [(0, 25), (1, 31), (5, 13)]

NUMS = {0:"ZERO",1:"ONE",2:"TWO",3:"THREE",4:"FOUR",5:"FIVE",6:"SIX",
        7:"SEVEN",8:"EIGHT",9:"NINE",10:"TEN",11:"ELEVEN",12:"TWELVE"}

FRACS = {"":0, "ANDAHALF":0.5, "ANDAQUARTER":0.25, "ANDTHREEQUARTERS":0.75,
         "ANDANEIGHTH":0.125, "ANDTHREEEIGHTHS":0.375, "ANDFIVEEIGHTHS":0.625, "ANDSEVENEIGHTHS":0.875,
         "ANDATHIRD":1/3, "ANDTWOTHIRDS":2/3}

UNITS = ["", "IN", "INCH", "INCHES"]
RADS  = ["RAD", "RADS", "RADIAN", "RADIANS"]

def get_coords(inches, clock):
    """Project inches@clock from Anchor to (lat, lon)."""
    miles = inches * SCALE
    bearing = math.radians(((clock % 12) * 30 + MAG_DEC) % 360)
    lat1, lon1 = map(math.radians, ANCHOR)
    ang_dist = miles / 3958.8

    lat2 = math.asin(math.sin(lat1)*math.cos(ang_dist) + math.cos(lat1)*math.sin(ang_dist)*math.cos(bearing))
    lon2 = lon1 + math.atan2(math.sin(bearing)*math.sin(ang_dist)*math.cos(lat1), math.cos(ang_dist)-math.sin(lat1)*math.sin(lat2))
    return math.degrees(lat2), math.degrees(lon2)

def solve():
    print("SCORE | PHRASE | LAT, LON | DIST_TO_SCENE")
    
    # Generate all permutations (Distance x Angle x Fraction x Prefix x Radian)
    for d, a, f_str, pre, rad in product(range(13), range(1,13), FRACS, UNITS, RADS):
        # Build phrase variations
        d_str, a_str = NUMS[d], NUMS[a]
        phrases = [
            f"{pre}{d_str}{f_str}{rad}{a_str}",  # "THREE RADIANS SIX"
            f"{pre}{a_str}{rad}{d_str}{f_str}"   # "SIX RADIANS THREE"
        ]

        for p in phrases:
            # 1. Length & Constraint Filter (Fastest fail)
            if len(p) != 32 or any(p[i] != p[j] for i, j in LOCKS):
                continue

            # 2. Project
            lat, lon = get_coords(d + FRACS[f_str], a)

            # 3. Map Bounds Filter
            if not (BOUNDS[0] <= lat <= BOUNDS[1] and BOUNDS[2] <= lon <= BOUNDS[3]):
                continue

            # 4. Score (Nearest Neighbor)
            nearest_dist = min(
                3958.8 * 2 * math.asin(math.sqrt(math.sin(math.radians(lat-clat)/2)**2 + 
                math.cos(math.radians(lat))*math.cos(math.radians(clat))*math.sin(math.radians(lon-clon)/2)**2))
                for clat, clon in CRIME_SCENES.values()
            )
            
            print(f"{100/(nearest_dist+.01):.1f} | {p} | {lat:.6f},{lon:.6f} | {nearest_dist:.2f}mi")

if __name__ == "__main__":
    solve()