from django.urls import include, path

urlpatterns = [
    path("", include("buses.urls")),
    path("", include("routes.urls")),
    path("", include("trips.urls")),
    path("", include("reservations.urls")),
]
