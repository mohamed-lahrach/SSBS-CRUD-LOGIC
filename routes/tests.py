from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from buses.models import Bus
from routes.models import Route
from trips.models import Trip
from django.utils import timezone


class RouteModelTests(TestCase):
    def test_str_representation(self):
        bus = Bus.objects.create(matricule="RB-01", capacity=30)
        route = Route.objects.create(bus=bus, direction="City A -> City B")
        self.assertEqual(str(route), f"Route {route.id} - City A -> City B")


class RouteApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="RB-10", capacity=32)
        self.route = Route.objects.create(bus=self.bus, direction="North -> South")

    def test_list_routes(self):
        response = self.client.get("/api/v1/routes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_route_success(self):
        free_bus = Bus.objects.create(matricule="RB-11", capacity=20)
        response = self.client.post(
            "/api/v1/routes/",
            {"bus": free_bus.id, "direction": "East -> West"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Route.objects.filter(direction="East -> West").exists())

    def test_create_route_rejects_invalid_bus(self):
        response = self.client.post(
            "/api/v1/routes/",
            {"bus": 999999, "direction": "Invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bus", response.data)

    def test_create_route_rejects_missing_direction(self):
        response = self.client.post(
            "/api/v1/routes/",
            {"bus": self.bus.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("direction", response.data)

    def test_retrieve_route_success(self):
        response = self.client.get(f"/api/v1/routes/{self.route.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.route.id)

    def test_retrieve_route_not_found(self):
        response = self.client.get("/api/v1/routes/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_route_success(self):
        new_bus = Bus.objects.create(matricule="RB-12", capacity=44)
        response = self.client.put(
            f"/api/v1/routes/{self.route.id}/",
            {"bus": new_bus.id, "direction": "South -> North"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db()
        self.assertEqual(self.route.direction, "South -> North")
        self.assertEqual(self.route.bus_id, new_bus.id)

    def test_delete_route_success_when_no_trips(self):
        response = self.client.delete(f"/api/v1/routes/{self.route.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Route.objects.filter(id=self.route.id).exists())

    def test_delete_route_rejects_when_it_has_trips(self):
        Trip.objects.create(route=self.route, depart_time=timezone.now())
        response = self.client.delete(f"/api/v1/routes/{self.route.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

