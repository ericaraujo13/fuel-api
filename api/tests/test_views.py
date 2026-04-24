from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class RouteViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/route/"

    def test_missing_start_and_end_returns_400(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body.get("error"), "Invalid request")
        self.assertIn("details", body)

    def test_invalid_coordinate_length_returns_400(self):
        response = self.client.post(
            self.url,
            {"start": [-74.0], "end": [-118.0, 34.0]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        body = response.json()
        self.assertEqual(body.get("error"), "Invalid request")

    @patch("api.views.compute_fuel_stops")
    @patch("api.views.get_route")
    def test_success_returns_summary_stops_and_map_links(self, mock_get_route, mock_compute):
        mock_get_route.return_value = {
            "coordinates": [[-74.0, 40.7], [-118.0, 34.0]],
        }
        mock_compute.return_value = {
            "total_distance": 100.5,
            "total_cost": 42.0,
            "stops": [
                {
                    "name": "TEST STATION",
                    "lat": 39.0,
                    "lon": -95.0,
                    "price": 3.5,
                    "distance_from_start": 80.0,
                }
            ],
        }

        response = self.client.post(
            self.url,
            {"start": [-74.006, 40.7128], "end": [-118.2437, 34.0522]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["summary"]["total_distance"], 100.5)
        self.assertEqual(data["summary"]["total_cost"], 42.0)
        self.assertEqual(data["summary"]["stops_count"], 1)
        self.assertEqual(len(data["stops"]), 1)
        self.assertIn("google.com/maps", data["map_url"])
        self.assertIn("openstreetmap.org/directions", data["osm_url"])

        mock_get_route.assert_called_once()
        mock_compute.assert_called_once()

    @patch("api.views.get_route", side_effect=RuntimeError("ORS down"))
    def test_service_error_returns_500(self, _mock_route):
        response = self.client.post(
            self.url,
            {"start": [-74.0, 40.7], "end": [-118.0, 34.0]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        body = response.json()
        self.assertEqual(body.get("error"), "Internal error")
        self.assertIn("ORS down", body.get("details", ""))
