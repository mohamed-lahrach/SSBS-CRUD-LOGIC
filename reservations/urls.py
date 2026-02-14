from django.urls import path

from .views import ReservationDetailView, ReservationListCreateView


urlpatterns = [
    path("reservations/", ReservationListCreateView.as_view()),
    path("reservations/<int:pk>/", ReservationDetailView.as_view()),
]
