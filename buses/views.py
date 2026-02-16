import logging

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Bus
from .serializers import BusSerializer

audit_logger = logging.getLogger("audit")


def _audit_user(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return getattr(user, "id", str(user))
    return "anonymous"


class BusListCreateView(ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

    def perform_create(self, serializer):
        bus = serializer.save()
        audit_logger.info(
            "user=%s action=bus.create bus=%s",
            _audit_user(self.request),
            bus.id,
        )


class BusDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

    def perform_destroy(self, instance):
        bus_id = instance.id
        super().perform_destroy(instance)
        audit_logger.info(
            "user=%s action=bus.delete bus=%s",
            _audit_user(self.request),
            bus_id,
        )
