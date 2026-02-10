from django.urls import path
from .views import (
    BusListCreateView,
    BusDetailView,
    TripListCreateView,
    TripDetailView,
    StartTripView,
    EndTripView,
    ReservationListCreateView,
    ReservationDetailView,
    RouteListCreateView,
    RouteDetailView
)

urlpatterns = [
    # BUS
    path("buses/", BusListCreateView.as_view()),
    path("buses/<int:pk>/", BusDetailView.as_view()),

    # TRIP CRUD
    path("trips/", TripListCreateView.as_view()),
    path("trips/<int:pk>/", TripDetailView.as_view()),

    # TRIP ACTIONS
    path("trips/<int:pk>/start/", StartTripView.as_view()),
    path("trips/<int:pk>/end/", EndTripView.as_view()),

    # RESERVATION ACTIONS
    path("reservations/", ReservationListCreateView.as_view()),
    path("reservations/<int:pk>/", ReservationDetailView.as_view()),

    #ROUTE ACTIONS
    path("routes/", RouteListCreateView.as_view()),
    path("routes/<int:pk>/", RouteDetailView.as_view()),
]