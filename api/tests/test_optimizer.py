from unittest.mock import patch

from django.test import SimpleTestCase

from api.services.optimizer import MPG, compute_fuel_stops


class ComputeFuelStopsTests(SimpleTestCase):
    @patch("api.services.optimizer.load_stations")
    @patch("api.services.optimizer.route_distances")
    def test_no_stops_when_destination_within_tank_range(
        self, mock_distances, _mock_load
    ):
        mock_distances.return_value = [0.0, 400.0]

        out = compute_fuel_stops({"coordinates": [[-90.0, 40.0], [-89.0, 40.0]]})

        self.assertEqual(out["stops"], [])
        self.assertEqual(out["total_cost"], 0.0)
        self.assertEqual(out["total_distance"], 400.0)

    @patch("api.services.optimizer.find_nearby_stations")
    @patch("api.services.optimizer.load_stations")
    @patch("api.services.optimizer.route_distances")
    def test_one_stop_cost_is_gallons_times_price(
        self, mock_distances, mock_load, mock_nearby
    ):
        mock_distances.return_value = [0.0, 250.0, 750.0]
        mock_load.return_value = []

        station = {"name": "MOCK STOP", "lat": 40.0, "lon": -90.0, "price": 3.0}

        def nearby(point, stations, radius=20):
            return [(station, 2.0)]

        mock_nearby.side_effect = nearby

        out = compute_fuel_stops(
            {"coordinates": [[-90.0, 40.0], [-89.0, 40.0], [-88.0, 40.0]]}
        )

        self.assertEqual(len(out["stops"]), 1)
        self.assertEqual(out["stops"][0]["name"], "MOCK STOP")
        expected_gallons = 250.0 / MPG
        self.assertAlmostEqual(
            out["total_cost"],
            round(expected_gallons * 3.0, 2),
            places=2,
        )
