import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "stations.json"


def load_stations():
    with open(DATA_PATH) as f:
        return json.load(f)