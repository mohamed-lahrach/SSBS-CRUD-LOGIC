from django.urls import path

from .views import BusDetailView, BusListCreateView


urlpatterns = [
    path("buses/", BusListCreateView.as_view()),
    path("buses/<int:pk>/", BusDetailView.as_view()),
]
