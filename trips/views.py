import logging

from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import LifecycleError

from .models import Trip
from .serializers import TripSerializer

audit_logger = logging.getLogger("audit")


def _audit_user(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return getattr(user, "id", str(user))
    return "anonymous"


class TripListCreateView(ListCreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    def perform_create(self, serializer):
        trip = serializer.save()
        audit_logger.info(
            "user=%s action=trip.create trip=%s route=%s transition=%s->%s",
            _audit_user(self.request),
            trip.id,
            trip.route_id,
            "NONE",
            trip.status,
        )


class TripDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    def perform_destroy(self, instance):
        trip_id = instance.id
        super().perform_destroy(instance)
        audit_logger.info(
            "user=%s action=trip.delete trip=%s",
            _audit_user(self.request),
            trip_id,
        )


class StartTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        before_status = trip.status
        if trip.start_trip_at is not None:
            raise LifecycleError("This trip has already started.")

        trip.start()
        audit_logger.info(
            "user=%s action=trip.start trip=%s transition=%s->%s",
            _audit_user(request),
            trip.id,
            before_status,
            trip.status,
        )

        return Response({"start_trip_at": trip.start_trip_at}, status=status.HTTP_200_OK)


class EndTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        before_status = trip.status
        if trip.start_trip_at is None:
            raise LifecycleError("Trip not started yet")

        if trip.end_trip_at is not None:
            raise LifecycleError("Trip already ended")

        trip.end()
        audit_logger.info(
            "user=%s action=trip.end trip=%s transition=%s->%s",
            _audit_user(request),
            trip.id,
            before_status,
            trip.status,
        )

        return Response({"end_trip_at": trip.end_trip_at}, status=status.HTTP_200_OK)
