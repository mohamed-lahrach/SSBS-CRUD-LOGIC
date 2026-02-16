from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from buses.models import Bus
from reservations.models import Reservation
from routes.models import Route
from trips.models import Trip


class TripModelTests(TestCase):
    def setUp(self):
        self.bus = Bus.objects.create(matricule="TB-01", capacity=2)
        self.route = Route.objects.create(bus=self.bus, direction="A -> B")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    def test_new_trip_is_created_with_created_status(self):
        trip = Trip.objects.create(
            route=self.route,
            depart_time=timezone.now(),
            status=Trip.STATUS_STARTED,
        )
        self.assertEqual(trip.status, Trip.STATUS_CREATED)

    def test_seats_left_calculation(self):
        self.assertEqual(self.trip.seats_left(), 2)
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.assertEqual(self.trip.seats_left(), 1)

    def test_start_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.assertEqual(self.trip.status, Trip.STATUS_STARTED)
        self.assertIsNotNone(self.trip.start_trip_at)

    def test_start_rejects_without_reservations(self):
        with self.assertRaises(ValueError):
            self.trip.start()

    def test_end_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        self.assertEqual(self.trip.status, Trip.STATUS_ENDED)
        self.assertIsNotNone(self.trip.end_trip_at)

    def test_end_rejects_before_start(self):
        with self.assertRaises(ValueError):
            self.trip.end()

    def test_started_trip_freezes_structure(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.depart_time = timezone.now()
        with self.assertRaises(ValueError):
            self.trip.save()

    def test_ended_trip_freezes_structure(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        self.trip.depart_time = timezone.now()
        with self.assertRaises(ValueError):
            self.trip.save()


class TripApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="TB-10", capacity=3)
        self.route = Route.objects.create(bus=self.bus, direction="C -> D")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    def test_list_trips(self):
        response = self.client.get("/api/v1/trips/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_trip_success(self):
        response = self.client.post(
            "/api/v1/trips/",
            {"route": self.route.id, "depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_trip_rejects_invalid_route(self):
        response = self.client.post(
            "/api/v1/trips/",
            {"route": 999999, "depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route", response.data)

    def test_retrieve_trip_success(self):
        response = self.client.get(f"/api/v1/trips/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.trip.id)

    def test_retrieve_trip_not_found(self):
        response = self.client.get("/api/v1/trips/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_trip_success_before_start(self):
        response = self.client.patch(
            f"/api/v1/trips/{self.trip.id}/",
            {"depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_trip_rejects_structural_changes_after_start(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        with self.assertRaises(ValueError):
            self.client.put(
                f"/api/v1/trips/{self.trip.id}/",
                {
                    "route": self.route.id,
                    "depart_time": timezone.now().isoformat(),
                    "status": Trip.STATUS_STARTED,
                },
                format="json",
            )

    def test_delete_trip_success_without_reservations(self):
        response = self.client.delete(f"/api/v1/trips/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_trip_rejects_with_reservations(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        response = self.client.delete(f"/api/v1/trips/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

    def test_start_endpoint_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        response = self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("start_trip_at", response.data)

    def test_start_endpoint_rejects_second_start(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        response = self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_end_endpoint_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        response = self.client.post(f"/api/v1/trips/{self.trip.id}/end/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("end_trip_at", response.data)

    def test_end_endpoint_rejects_before_start(self):
        response = self.client.post(f"/api/v1/trips/{self.trip.id}/end/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_end_endpoint_rejects_second_end(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/v1/trips/{self.trip.id}/start/")
        self.client.post(f"/api/v1/trips/{self.trip.id}/end/")
        response = self.client.post(f"/api/v1/trips/{self.trip.id}/end/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")
