import math


def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def route_distances(coords):
    distances = [0]

    for i in range(1, len(coords)):
        prev = coords[i - 1]
        curr = coords[i]

        d = haversine(prev[1], prev[0], curr[1], curr[0])
        distances.append(distances[-1] + d)

    return distances