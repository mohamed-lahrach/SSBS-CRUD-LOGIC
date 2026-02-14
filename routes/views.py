from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Route
from .serializers import RouteSerializer


class RouteListCreateView(ListCreateAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class RouteDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
