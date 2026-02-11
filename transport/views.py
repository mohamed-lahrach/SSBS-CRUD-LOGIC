from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveDestroyAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Bus, Trip, Route, Reservation
from .exceptions import CapacityError, LifecycleError
from .serializers import (
    BusSerializer,
    TripSerializer,
    ReservationSerializer,
    RouteSerializer
)


# -------- BUS --------
class BusListCreateView(ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


class BusDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


# -------- TRIP CRUD --------
class TripListCreateView(ListCreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class TripDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


# -------- TRIP ACTIONS --------
class StartTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        if trip.start_trip_at is not None:
            raise LifecycleError("This trip has already started.")

        trip.start()

        return Response(
            {"start_trip_at": trip.start_trip_at},
            status=status.HTTP_200_OK
        )


class EndTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        if trip.start_trip_at is None:
            raise LifecycleError("Trip not started yet")

        if trip.end_trip_at is not None:
            raise LifecycleError("Trip already ended")

        trip.end()

        return Response(
            {"end_trip_at": trip.end_trip_at},
            status=status.HTTP_200_OK
        )


# -------- RESERVATIONS --------
class ReservationListCreateView(ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.status != Trip.STATUS_CREATED:
            raise LifecycleError("Cannot reserve this non-CREATED trip")

        if trip.seats_left() <= 0:
            raise CapacityError("No seats available")

        serializer.save()


class ReservationDetailView(RetrieveDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer


# -------- ROUTES --------
class RouteListCreateView(ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class RouteDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
