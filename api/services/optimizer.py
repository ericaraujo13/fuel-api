from .fuel import load_stations
from .geo import haversine, route_distances

MAX_RANGE = 500
MPG = 10

MIN_STOP_DISTANCE = 100
FAR_WINDOW = 50


def find_nearby_stations(point, stations, radius=20):
    lat, lon = point[1], point[0]

    nearby = []
    for s in stations:
        d = haversine(lat, lon, s["lat"], s["lon"])
        if d <= radius:
            nearby.append((s, d))

    return nearby


def compute_fuel_stops(route):
    stations = load_stations()
    coords = route["coordinates"]

    if len(coords) > 2000:
        coords = coords[::10]
    elif len(coords) > 800:
        coords = coords[::5]

    distances = route_distances(coords)

    total_cost = 0
    stops = []

    current_position = 0
    max_iters = 100

    for _ in range(max_iters):
        if current_position >= distances[-1]:
            break

        remaining_distance = distances[-1] - current_position
        if remaining_distance <= MAX_RANGE:
            break

        candidates = []

        for i in range(len(coords)):
            dist = distances[i]

            if dist <= current_position:
                continue

            if dist - current_position > MAX_RANGE:
                break

            if dist - current_position < MIN_STOP_DISTANCE:
                continue

            nearby = find_nearby_stations(coords[i], stations)

            for s, d in nearby:
                candidates.append({
                    "station": s,
                    "distance": dist,
                    "deviation": d
                })

        if not candidates:
            break

        max_dist = max(c["distance"] for c in candidates)

        far_candidates = [
            c for c in candidates
            if c["distance"] >= max_dist - FAR_WINDOW
        ]

        best = min(far_candidates, key=lambda x: x["station"]["price"])

        station = best["station"]
        stop_distance = best["distance"]

        if stops and stops[-1]["name"] == station["name"]:
            current_position += 50
            continue

        distance_since_last_stop = stop_distance - current_position
        gallons = distance_since_last_stop / MPG
        total_cost += gallons * station["price"]

        stops.append({
            "name": station.get("name"),
            "lat": station["lat"],
            "lon": station["lon"],
            "price": round(station["price"], 3),
            "distance_from_start": round(stop_distance, 2)
        })

        if stop_distance <= current_position:
            current_position += 50
        else:
            current_position = stop_distance

    return {
        "stops": stops,
        "total_cost": round(total_cost, 2),
        "total_distance": round(distances[-1], 2)
    }