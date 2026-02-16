import logging

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Route
from .serializers import RouteSerializer

audit_logger = logging.getLogger("audit")


def _audit_user(request):
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        return getattr(user, "id", str(user))
    return "anonymous"


class RouteListCreateView(ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def perform_create(self, serializer):
        route = serializer.save()
        audit_logger.info(
            "user=%s action=route.create route=%s bus=%s",
            _audit_user(self.request),
            route.id,
            route.bus_id,
        )


class RouteDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def perform_destroy(self, instance):
        route_id = instance.id
        super().perform_destroy(instance)
        audit_logger.info(
            "user=%s action=route.delete route=%s",
            _audit_user(self.request),
            route_id,
        )
