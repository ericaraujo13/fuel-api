from urllib.parse import quote_plus, urlencode


def build_google_maps_directions_url(start, end, stops):
    origin = f"{start[1]},{start[0]}"
    destination = f"{end[1]},{end[0]}"
    waypoints = [
        f'{s["lat"]},{s["lon"]}'
        for s in stops
        if s.get("lat") is not None and s.get("lon") is not None
    ][:20]

    points = [origin, *waypoints, destination]
    path = "/".join(quote_plus(p) for p in points)
    return f"https://www.google.com/maps/dir/{path}"


def build_osm_directions_url(start, end, stops):
    points = [
        (start[1], start[0]),
        *[
            (s["lat"], s["lon"])
            for s in stops
            if s.get("lat") is not None and s.get("lon") is not None
        ],
        (end[1], end[0]),
    ]
    points = points[:22]
    route = ";".join(f"{lat},{lon}" for lat, lon in points)
    params = {"engine": "fossgis_osrm_car", "route": route}
    return "https://www.openstreetmap.org/directions?" + urlencode(params, quote_via=quote_plus)
