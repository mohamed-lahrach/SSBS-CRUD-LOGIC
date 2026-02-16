from django.urls import include, path

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("", include("organization.urls")),
    path("", include("buses.urls")),
    path("", include("routes.urls")),
    path("", include("trips.urls")),
    path("", include("reservations.urls")),
]
