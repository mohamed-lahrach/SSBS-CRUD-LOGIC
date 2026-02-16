from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from buses.models import Bus
from reservations.models import Reservation
from routes.models import Route
from trips.models import Trip


class ReservationModelTests(TestCase):
    def test_str_representation(self):
        bus = Bus.objects.create(matricule="RS-01", capacity=5)
        route = Route.objects.create(bus=bus, direction="R1 -> R2")
        trip = Trip.objects.create(route=route, depart_time=timezone.now())
        reservation = Reservation.objects.create(trip=trip, passenger_name="Mina")
        self.assertEqual(str(reservation), f"Mina -> Trip {trip.id}")


class ReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="RS-10", capacity=2)
        self.route = Route.objects.create(bus=self.bus, direction="Alpha -> Beta")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    def test_list_reservations(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        response = self.client.get("/api/v1/reservations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_reservation_success(self):
        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Reservation.objects.filter(passenger_name="Sara").exists())

    def test_create_reservation_rejects_invalid_trip(self):
        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": 999999, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("trip", response.data)

    def test_create_reservation_rejects_missing_passenger_name(self):
        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": self.trip.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("passenger_name", response.data)

    def test_create_reservation_rejects_started_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_create_reservation_rejects_ended_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_create_reservation_rejects_full_trip(self):
        one_seat_bus = Bus.objects.create(matricule="RS-11", capacity=1)
        one_seat_route = Route.objects.create(bus=one_seat_bus, direction="One -> Two")
        one_seat_trip = Trip.objects.create(route=one_seat_route, depart_time=timezone.now())
        Reservation.objects.create(trip=one_seat_trip, passenger_name="Ali")

        response = self.client.post(
            "/api/v1/reservations/",
            {"trip": one_seat_trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "capacity_error")

    def test_retrieve_reservation_success(self):
        reservation = Reservation.objects.create(trip=self.trip, passenger_name="Nora")
        response = self.client.get(f"/api/v1/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], reservation.id)

    def test_retrieve_reservation_not_found(self):
        response = self.client.get("/api/v1/reservations/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_reservation_success(self):
        reservation = Reservation.objects.create(trip=self.trip, passenger_name="Nora")
        response = self.client.delete(f"/api/v1/reservations/{reservation.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reservation.objects.filter(id=reservation.id).exists())

