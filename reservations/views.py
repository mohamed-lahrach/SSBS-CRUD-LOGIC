from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView

from core.exceptions import CapacityError, LifecycleError
from trips.models import Trip

from .models import Reservation
from .serializers import ReservationSerializer


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
