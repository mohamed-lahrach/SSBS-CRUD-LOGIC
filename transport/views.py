from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveDestroyAPIView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError

from django.db.models import ProtectedError

from .models import Bus, Trip, Route, Reservation
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
    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete bus assigned to routes"},
                status=status.HTTP_400_BAD_REQUEST
            )


# -------- TRIP CRUD --------
class TripListCreateView(ListCreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class TripDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete trip with existing reservations"},
                status=status.HTTP_400_BAD_REQUEST
            )


# -------- TRIP ACTIONS --------
class StartTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)

        if trip.start_trip_at is not None:
            return Response(
                {"error": "This trip has already started."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            trip.start()
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"start_trip_at": trip.start_trip_at},
            status=status.HTTP_200_OK
        )


class EndTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)

        if trip.start_trip_at is None:
            return Response(
                {"error": "Trip not started yet"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if trip.end_trip_at is not None:
            return Response(
                {"error": "Trip already ended"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            trip.end()
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            raise ValidationError("Cannot reserve this non-CREATED trip")

        if trip.seats_left() <= 0:
            raise ValidationError("No seats available")

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

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"error": "Cannot delete route with existing trips"},
                status=status.HTTP_400_BAD_REQUEST
            )