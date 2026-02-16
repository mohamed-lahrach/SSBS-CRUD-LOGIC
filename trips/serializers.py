from rest_framework import serializers

from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            "id",
            "route",
            "depart_time",
            "status",
            "start_trip_at",
            "end_trip_at",
        ]
        read_only_fields = [
            "status",
            "start_trip_at",
            "end_trip_at",
        ]