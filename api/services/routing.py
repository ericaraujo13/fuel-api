import requests
import polyline
import os

URL = "https://api.openrouteservice.org/v2/directions/driving-car"

def _get_ors_api_key():
    return os.getenv("ORS_API_KEY")

def get_route(start, end):
    ors_api_key = _get_ors_api_key()
    if not ors_api_key:
        raise Exception("Missing ORS_API_KEY (configure it in .env file)")

    headers = {
        "Authorization": ors_api_key,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [float(start[0]), float(start[1])],
            [float(end[0]), float(end[1])]
        ]
    }

    res = requests.post(URL, json=body, headers=headers)

    if res.status_code != 200:
        raise Exception(f"ORS error: {res.status_code} - {res.text}")

    data = res.json()

    encoded = data["routes"][0]["geometry"]

    return {
        "coordinates": decode_polyline(encoded)
    }


def decode_polyline(encoded):
    coords = polyline.decode(encoded)
    return [[lon, lat] for lat, lon in coords]