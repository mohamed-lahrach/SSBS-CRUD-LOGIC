from django.urls import path

from .views import EndTripView, StartTripView, TripDetailView, TripListCreateView


urlpatterns = [
    path("trips/", TripListCreateView.as_view()),
    path("trips/<int:pk>/", TripDetailView.as_view()),
    path("trips/<int:pk>/start/", StartTripView.as_view()),
    path("trips/<int:pk>/end/", EndTripView.as_view()),
]
