from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from buses.models import Bus
from core.exceptions import FreezeError
from routes.models import Route


class BusModelTests(TestCase):
    def test_str_representation(self):
        bus = Bus.objects.create(matricule="BUS-01", capacity=40)
        self.assertEqual(str(bus), "Bus BUS-01")

    def test_can_update_when_not_assigned_to_any_route(self):
        bus = Bus.objects.create(matricule="BUS-02", capacity=20)
        bus.capacity = 30
        bus.save()
        bus.refresh_from_db()
        self.assertEqual(bus.capacity, 30)

    def test_cannot_update_when_assigned_to_route(self):
        bus = Bus.objects.create(matricule="BUS-03", capacity=20)
        Route.objects.create(bus=bus, direction="A -> B")

        bus.capacity = 25
        with self.assertRaises(FreezeError):
            bus.save()


class BusApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="BUS-10", capacity=50)

    def test_list_buses(self):
        response = self.client.get("/api/v1/buses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_bus_success(self):
        response = self.client.post(
            "/api/v1/buses/",
            {"matricule": "BUS-11", "capacity": 45},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Bus.objects.filter(matricule="BUS-11").exists())

    def test_create_bus_rejects_non_positive_capacity(self):
        response = self.client.post(
            "/api/v1/buses/",
            {"matricule": "BUS-12", "capacity": 0},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.data)

    def test_retrieve_bus_success(self):
        response = self.client.get(f"/api/v1/buses/{self.bus.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.bus.id)

    def test_retrieve_bus_not_found(self):
        response = self.client.get("/api/v1/buses/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_bus_success_when_free(self):
        response = self.client.put(
            f"/api/v1/buses/{self.bus.id}/",
            {"matricule": "BUS-10-NEW", "capacity": 60},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.bus.refresh_from_db()
        self.assertEqual(self.bus.capacity, 60)

    def test_update_bus_rejects_when_assigned(self):
        Route.objects.create(bus=self.bus, direction="C -> D")
        response = self.client.put(
            f"/api/v1/buses/{self.bus.id}/",
            {"matricule": "BUS-10", "capacity": 55},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "freeze_error")

    def test_delete_bus_success_when_free(self):
        response = self.client.delete(f"/api/v1/buses/{self.bus.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Bus.objects.filter(id=self.bus.id).exists())

    def test_delete_bus_rejects_when_assigned(self):
        Route.objects.create(bus=self.bus, direction="X -> Y")
        response = self.client.delete(f"/api/v1/buses/{self.bus.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

