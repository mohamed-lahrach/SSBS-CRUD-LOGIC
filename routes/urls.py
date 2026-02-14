from django.urls import path

from .views import RouteDetailView, RouteListCreateView


urlpatterns = [
    path("routes/", RouteListCreateView.as_view()),
    path("routes/<int:pk>/", RouteDetailView.as_view()),
]
