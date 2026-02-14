from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import LifecycleError

from .models import Trip
from .serializers import TripSerializer


class TripListCreateView(ListCreateAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class TripDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer


class StartTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        if trip.start_trip_at is not None:
            raise LifecycleError("This trip has already started.")

        trip.start()

        return Response({"start_trip_at": trip.start_trip_at}, status=status.HTTP_200_OK)


class EndTripView(APIView):
    def post(self, request, pk):
        trip = Trip.objects.get(pk=pk)
        if trip.start_trip_at is None:
            raise LifecycleError("Trip not started yet")

        if trip.end_trip_at is not None:
            raise LifecycleError("Trip already ended")

        trip.end()

        return Response({"end_trip_at": trip.end_trip_at}, status=status.HTTP_200_OK)
