import csv
import requests
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

from dotenv import load_dotenv

INPUT_FILE = "data/fuel-prices.csv"
OUTPUT_FILE = "data/stations.json"

URL = "https://maps.googleapis.com/maps/api/geocode/json"
MAX_WORKERS = 10
LIMIT_ROWS = int(os.getenv("GEOCODE_LIMIT_ROWS", "0"))

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

CACHE_FILE = BASE_DIR / "data" / "geocode_cache.json"

def get_google_api_key():
    return os.getenv("GOOGLE_API_KEY")

def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache_obj):
    CACHE_FILE.write_text(json.dumps(cache_obj, indent=2, sort_keys=True))


cache = load_cache()


def clean_name(name):
    if not name:
        return ""
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def geocode(query):
    if query in cache:
        lat, lon = cache[query]
        return lat, lon

    api_key = get_google_api_key()
    if not api_key:
        raise Exception("Missing GOOGLE_API_KEY (configure it in .env file)")

    params = {
        "address": query,
        "key": api_key,
        "components": "country:US"
    }

    try:
        res = requests.get(URL, params=params, timeout=10)
        data = res.json()

        if data.get("status") == "OK":
            loc = data["results"][0]["geometry"]["location"]
            lat, lon = loc["lat"], loc["lng"]
            cache[query] = [lat, lon]
            return lat, lon

        print(f"[GOOGLE FAIL] {query} → {data.get('status')}")

    except Exception as e:
        print(f"[ERROR] {query} → {e}")

    cache[query] = [None, None]
    return None, None


def geocode_with_fallback(row):
    raw_name = row["Truckstop Name"]
    name = clean_name(raw_name)

    address = (row.get("Address") or "").strip()
    city = row["City"].strip()
    state = row["State"].strip()

    queries = [
        f"{name}, {address}, {city}, {state}, USA",
        f"{address}, {city}, {state}, USA",
        f"{name}, {city}, {state}, USA",
        f"{city}, {state}, USA",
    ]

    for q in queries:
        lat, lon = geocode(q)
        if lat:
            return lat, lon, q

    return None, None, None


def process_row(i, row):
    lat, lon, used_query = geocode_with_fallback(row)

    name = row["Truckstop Name"]

    if lat:
        print(f"[OK] {i} | {name} → {lat}, {lon} ({used_query})")
    else:
        print(f"[FAIL] {i} | {name}")

    if lat and lon:
        try:
            price = float(row["Retail Price"])
        except:
            price = 0.0

        return {
            "opis_id": row.get("OPIS Truckstop ID"),
            "name": name,
            "address": row.get("Address"),
            "city": row.get("City"),
            "state": row.get("State"),
            "lat": lat,
            "lon": lon,
            "price": price
        }

    return None


def main():
    stations = []

    with open(INPUT_FILE) as f:
        rows = list(csv.DictReader(f))
        reader = rows[:LIMIT_ROWS] if LIMIT_ROWS and LIMIT_ROWS > 0 else rows

    deduped = []
    seen_in = set()
    for row in reader:
        opis_id = (row.get("OPIS Truckstop ID") or "").strip()
        key = opis_id or (
            (row.get("Truckstop Name") or "").strip(),
            (row.get("Address") or "").strip(),
            (row.get("City") or "").strip(),
            (row.get("State") or "").strip(),
        )
        if key in seen_in:
            continue
        seen_in.add(key)
        deduped.append(row)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(process_row, i, row)
            for i, row in enumerate(deduped)
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                stations.append(result)

    unique = []
    seen = set()

    for s in stations:
        key = (round(s["lat"], 4), round(s["lon"], 4), s.get("name"))
        if key not in seen:
            seen.add(key)
            unique.append(s)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(unique, f, indent=2)

    save_cache(cache)

if __name__ == "__main__":
    main()