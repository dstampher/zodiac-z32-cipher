import folium

# --- COORDINATES ---
ANCHORS = {
    "Mt. Diablo": (37.8816, -121.9144),
    "Presidio Heights": (37.7887, -122.4571),
    "Lake Berryessa": (38.5636, -122.2317)
}

CLUSTER = {
    "Lake Herman Rd": (38.0949, -122.1441),
    "Blue Rock Springs": (38.1260, -122.1911)
}

CENTROID = (38.0780, -122.2011)
SOLUTION = (38.109952, -122.185349)

def create_scientific_map():
    # Use a clean, light base map
    m = folium.Map(location=[38.2, -122.2], zoom_start=10, tiles='CartoDB positron')

    # 1. Draw the Triangle (Dashed Line)
    triangle_points = [ANCHORS["Mt. Diablo"], ANCHORS["Lake Berryessa"], ANCHORS["Presidio Heights"], ANCHORS["Mt. Diablo"]]
    folium.PolyLine(
        locations=triangle_points,
        color="#333333", # Dark Grey
        weight=2,
        dash_array='5, 5',
        opacity=0.8
    ).add_to(m)

    # 2. Add Anchor Points (Black Circles)
    for name, coords in ANCHORS.items():
        folium.CircleMarker(
            location=coords,
            radius=4,
            color="black",
            fill=True,
            fill_color="black",
            fill_opacity=1.0,
            tooltip=name
        ).add_to(m)

    # 3. Add Vallejo Cluster (Orange Circles)
    for name, coords in CLUSTER.items():
        folium.CircleMarker(
            location=coords,
            radius=5,
            color="#FF8C00", # Dark Orange
            fill=True,
            fill_color="#FF8C00",
            fill_opacity=0.8,
            tooltip=f"CRIME SCENE: {name}"
        ).add_to(m)

    # 4. Add Centroid (Blue Crosshair via a Circle with a ring)
    folium.CircleMarker(
        location=CENTROID,
        radius=7,
        color="blue",
        fill=False,    # Hollow circle
        weight=2,
        tooltip="Geometric Centroid"
    ).add_to(m)
    # Add a small dot in the middle of the centroid
    folium.CircleMarker(
        location=CENTROID,
        radius=2,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=1.0
    ).add_to(m)

    # 5. Add SOLUTION (Red Star - slightly larger)
    folium.RegularPolygonMarker(
        location=SOLUTION,
        number_of_sides=5, # Star shape(ish)
        rotation=0,
        radius=8,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=1.0,
        tooltip="Z32 Solution"
    ).add_to(m)

    # 6. Connector Line (Centroid -> Solution)
    folium.PolyLine(
        locations=[CENTROID, SOLUTION],
        color="red",
        weight=1.5,
        opacity=0.6,
        dash_array='3, 3'
    ).add_to(m)

    m.save("map.html")
    print("Map generated: map.html")

if __name__ == "__main__":
    create_scientific_map()