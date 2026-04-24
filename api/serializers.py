from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2,
        help_text="[longitude, latitude]",
    )
    end = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2,
        help_text="[longitude, latitude]",
    )
