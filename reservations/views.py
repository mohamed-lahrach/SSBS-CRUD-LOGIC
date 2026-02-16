import logging

from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView

from core.exceptions import CapacityError, LifecycleError
from trips.models import Trip

from .models import Reservation
from .serializers import ReservationSerializer

audit_logger = logging.getLogger("audit")


def _audit_user(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return getattr(user, "id", str(user))
    return "anonymous"


class ReservationListCreateView(ListCreateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def perform_create(self, serializer):
        trip = serializer.validated_data["trip"]

        if trip.status != Trip.STATUS_CREATED:
            raise LifecycleError("Cannot reserve this non-CREATED trip")

        if trip.seats_left() <= 0:
            raise CapacityError("No seats available")

        reservation = serializer.save()
        audit_logger.info(
            "user=%s action=reservation.create trip=%s reservation=%s",
            _audit_user(self.request),
            trip.id,
            reservation.id,
        )


class ReservationDetailView(RetrieveDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def perform_destroy(self, instance):
        reservation_id = instance.id
        trip_id = instance.trip_id
        super().perform_destroy(instance)
        audit_logger.info(
            "user=%s action=reservation.delete trip=%s reservation=%s",
            _audit_user(self.request),
            trip_id,
            reservation_id,
        )
