# data.py - Canonical project data for solver, verification, and figure generation.

EARTH_RADIUS_MI = 3958.8

MAG_DEC_1970_DEG_EAST = 17.0

MAP_SCALE_MI_PER_IN = 6.4
MAP_BOUNDS = {
    "south": 37.3,
    "north": 38.8,
    "west": -123.0,
    "east": -121.0,
}

LOCKS_0_INDEXED = [(0, 25), (1, 31), (5, 13)]
CIPHER_LENGTH = 32

POINTS = {
    "mt_diablo": {
        "lat": 37.881628,
        "lon": -121.914382,
        "source": "USGS GNIS",
        "source_url": "https://edits.nationalmap.gov/apps/gaz-domestic/public/gaz-record/274127",
        "uncertainty_m": 10,
        "notes": "Anchor point for all bearings/projections."
    },

    "lake_herman_road": {
        "lat": 38.0949,
        "lon": -122.1441,
        "source": "Research geocode from primary scene descriptions",
        "source_url": "",
        "uncertainty_m": 50,
        "notes": ""
    },
    "blue_rock_springs": {
        "lat": 38.1260,
        "lon": -122.1911,
        "source": "Research geocode from primary scene descriptions",
        "source_url": "",
        "uncertainty_m": 50,
        "notes": ""
    },
    "lake_berryessa": {
        "lat": 38.5636,
        "lon": -122.2317,
        "source": "Research geocode from primary scene descriptions",
        "source_url": "",
        "uncertainty_m": 50,
        "notes": ""
    },
    "presidio_heights": {
        "lat": 37.7887,
        "lon": -122.4571,
        "source": "Research geocode from primary scene descriptions",
        "source_url": "",
        "uncertainty_m": 50,
        "notes": ""
    },

    "z32_solution": {
        "lat": 38.109952,
        "lon": -122.185349,
        "source": "Derived from plaintext + map scale + declination projection",
        "source_url": "",
        "uncertainty_m": 10,
        "notes": "Computed output, not externally cataloged."
    },

    "triangle_anomaly": {
        "lat": 38.111152764676,
        "lon": -122.18781609349446,
        "source": "Author-measured from imagery placemark",
        "source_url": "",
        "uncertainty_m": 15,
        "notes": ""
    },
}
