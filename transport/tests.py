from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from .models import Bus, Route, Trip, Reservation


# =========================================
# MODEL TESTS
# =========================================

class ModelBusinessRulesTests(TestCase):

    def setUp(self):
        self.bus = Bus.objects.create(matricule="B1", capacity=2)
        self.route = Route.objects.create(bus=self.bus, direction="A → B")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    # -------- Lifecycle --------

    def test_cannot_start_without_reservations(self):
        with self.assertRaises(ValueError):
            self.trip.start()

    def test_start_sets_fields(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()

        self.assertEqual(self.trip.status, Trip.STATUS_STARTED)
        self.assertIsNotNone(self.trip.start_trip_at)

    def test_end_without_start_blocked(self):
        with self.assertRaises(ValueError):
            self.trip.end()

    def test_end_sets_fields(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()

        self.assertEqual(self.trip.status, Trip.STATUS_ENDED)
        self.assertIsNotNone(self.trip.end_trip_at)

    # -------- Freeze --------

    def test_started_trip_is_immutable(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()

        self.trip.depart_time = timezone.now()

        with self.assertRaises(ValueError):
            self.trip.save()

    def test_ended_trip_is_immutable(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()

        self.trip.depart_time = timezone.now()

        with self.assertRaises(ValueError):
            self.trip.save()

    # -------- Capacity --------

    def test_seats_left_calculation(self):
        self.assertEqual(self.trip.seats_left(), 2)

        Reservation.objects.create(trip=self.trip, passenger_name="A")
        self.assertEqual(self.trip.seats_left(), 1)


# =========================================
# API TESTS
# =========================================

class EndpointTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="B1", capacity=1)
        self.route = Route.objects.create(bus=self.bus, direction="A → B")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    # -------- Reservation rules --------

    def test_cannot_reserve_full_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")

        response = self.client.post("/api/reservations/", {
            "trip": self.trip.id,
            "passenger_name": "Sara"
        })

        self.assertEqual(response.status_code, 400)

    def test_cannot_reserve_started_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()

        response = self.client.post("/api/reservations/", {
            "trip": self.trip.id,
            "passenger_name": "Sara"
        })

        self.assertEqual(response.status_code, 400)

    # -------- Lifecycle endpoints --------

    def test_start_endpoint(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")

        response = self.client.post(f"/api/trips/{self.trip.id}/start/")

        self.assertEqual(response.status_code, 200)

    def test_end_before_start_blocked(self):
        response = self.client.post(f"/api/trips/{self.trip.id}/end/")

        self.assertEqual(response.status_code, 400)

    # -------- Freeze via API --------

    def test_cannot_edit_started_trip_via_api(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()

        response = self.client.put(f"/api/trips/{self.trip.id}/", {
            "route": self.route.id,
            "depart_time": timezone.now(),
            "status": Trip.STATUS_STARTED
        }, format="json")

        self.assertEqual(response.status_code, 400)

    # -------- Dependency protection --------

    def test_cannot_delete_trip_with_reservations(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")

        response = self.client.delete(f"/api/trips/{self.trip.id}/")

        self.assertEqual(response.status_code, 400)

    def test_cannot_delete_route_with_trips(self):
        response = self.client.delete(f"/api/routes/{self.route.id}/")

        self.assertEqual(response.status_code, 400)

    def test_cannot_delete_bus_with_routes(self):
        response = self.client.delete(f"/api/buses/{self.bus.id}/")

        self.assertEqual(response.status_code, 400)