def check_centroid():
    # 1. The Three Points of the "Zodiac Triangle"
    points = [
        (37.7887, -122.4571), # Paul Stine (Presidio)
        (38.5636, -122.2317), # Lake Berryessa
        (37.8816, -121.9144)  # Mt. Diablo
    ]
    
    # 2. Calculate Centroid (Average of Lat/Lons)
    avg_lat = sum(p[0] for p in points) / 3
    avg_lon = sum(p[1] for p in points) / 3
    centroid = (avg_lat, avg_lon)
    
    solution = (38.109952, -122.185349)
    
    # 3. Calculate Distance (Haversine)
    import math
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [centroid[0], centroid[1], solution[0], solution[1]])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    dist = 2 * R * math.asin(math.sqrt(a))
    
    print(f"Geometric Centroid: {centroid[0]:.4f}, {centroid[1]:.4f}")
    print(f"Solution Location:  {solution[0]:.4f}, {solution[1]:.4f}")
    print(f"Distance between them: {dist:.2f} miles")

if __name__ == "__main__":
    check_centroid()