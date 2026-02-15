"""Shared geographic and mathematical utilities for the Z32 project."""

import math
import random
from typing import Tuple


def haversine(lat1: float, lon1: float, lat2: float, lon2: float,
              earth_radius: float = 3958.8) -> float:
    """Great-circle distance in miles between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return earth_radius * 2 * math.asin(math.sqrt(a))


def true_bearing(from_lat: float, from_lon: float,
                 to_lat: float, to_lon: float) -> float:
    """True (geographic) bearing in degrees from point A to point B."""
    lat1, lon1 = map(math.radians, [from_lat, from_lon])
    lat2, lon2 = map(math.radians, [to_lat, to_lon])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def mag_bearing(from_lat: float, from_lon: float,
                to_lat: float, to_lon: float,
                declination_east: float) -> float:
    """Magnetic bearing (true bearing minus easterly declination)."""
    tb = true_bearing(from_lat, from_lon, to_lat, to_lon)
    return (tb - declination_east + 360) % 360


def bearing_to_clock(mag_bearing_deg: float) -> float:
    """Convert magnetic bearing (0-360 deg) to continuous clock hour (1-12)."""
    hour = mag_bearing_deg / 30.0
    return 12.0 if abs(hour) < 1e-12 else hour


def project_point(start_lat: float, start_lon: float,
                  bearing_deg: float, distance_miles: float,
                  earth_radius: float = 3958.8) -> Tuple[float, float]:
    """Forward geodesic projection on a sphere. Returns (lat, lon) in degrees."""
    lat1 = math.radians(start_lat)
    lon1 = math.radians(start_lon)
    brng = math.radians(bearing_deg)
    d = distance_miles / earth_radius
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(brng)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(d) * math.cos(lat1),
        math.cos(d) - math.sin(lat1) * math.sin(lat2),
    )
    return math.degrees(lat2), math.degrees(lon2)


def angular_separation(a_deg: float, b_deg: float) -> float:
    """Smallest absolute angular separation between two bearings."""
    diff = (a_deg - b_deg + 180.0) % 360.0 - 180.0
    return abs(diff)


def angle_from_sides(adj1: float, adj2: float, opposite: float) -> float:
    """Interior angle (degrees) opposite to `opposite` side, via law of cosines."""
    denom = max(2.0 * adj1 * adj2, 1e-12)
    cos_ang = (adj1 ** 2 + adj2 ** 2 - opposite ** 2) / denom
    cos_ang = max(min(cos_ang, 1.0), -1.0)
    return math.degrees(math.acos(cos_ang))


def to_local_miles(lat: float, lon: float,
                   origin_lat: float, origin_lon: float) -> Tuple[float, float]:
    """Tangent-plane approximation (x, y) in miles from an origin. Adequate for Bay Area scale."""
    x = (lon - origin_lon) * 69.0 * math.cos(math.radians(origin_lat))
    y = (lat - origin_lat) * 69.0
    return x, y


def sample_point_in_triangle(
    a: Tuple[float, float],
    b: Tuple[float, float],
    c: Tuple[float, float],
    rng: random.Random,
) -> Tuple[float, float]:
    """Uniformly sample a point inside a triangle defined by vertices a, b, c."""
    r1, r2 = rng.random(), rng.random()
    s = math.sqrt(r1)
    x = (1 - s) * a[0] + s * (1 - r2) * b[0] + s * r2 * c[0]
    y = (1 - s) * a[1] + s * (1 - r2) * b[1] + s * r2 * c[1]
    return x, y
