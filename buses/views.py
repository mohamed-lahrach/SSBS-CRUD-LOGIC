from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Bus
from .serializers import BusSerializer


class BusListCreateView(ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer


class BusDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
