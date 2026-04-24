from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RouteRequestSerializer
from .services.maps_links import build_google_maps_directions_url, build_osm_directions_url
from .services.routing import get_route
from .services.optimizer import compute_fuel_stops


class RouteView(APIView):

    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid request", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start = serializer.validated_data["start"]
        end = serializer.validated_data["end"]

        try:
            route = get_route(start, end)
            fuel_data = compute_fuel_stops(route)
            stops = fuel_data.get("stops", [])

            return Response({
                "summary": {
                    "total_distance": fuel_data.get("total_distance"),
                    "total_cost": fuel_data.get("total_cost"),
                    "stops_count": len(stops),
                },
                "stops": stops,
                "map_url": build_google_maps_directions_url(start, end, stops),
                "osm_url": build_osm_directions_url(start, end, stops),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Internal error", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
