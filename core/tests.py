from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from buses.models import Bus
from core.exceptions import FreezeError, LifecycleError
from reservations.models import Reservation
from routes.models import Route
from trips.models import Trip


class ModelBusinessRulesTests(TestCase):
    def setUp(self):
        self.bus = Bus.objects.create(matricule="B1", capacity=2)
        self.route = Route.objects.create(bus=self.bus, direction="A -> B")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    def test_bus_can_update_without_routes(self):
        free_bus = Bus.objects.create(matricule="B2", capacity=10)
        free_bus.capacity = 12
        free_bus.save()
        self.assertEqual(free_bus.capacity, 12)

    def test_bus_cannot_update_when_assigned_to_route(self):
        self.bus.capacity = 5
        with self.assertRaises(FreezeError):
            self.bus.save()

    def test_trip_can_change_structure_before_start(self):
        new_route = Route.objects.create(
            bus=Bus.objects.create(matricule="B3", capacity=3),
            direction="B -> C",
        )
        self.trip.route = new_route
        self.trip.depart_time = timezone.now()
        self.trip.save()
        self.assertEqual(self.trip.route_id, new_route.id)

    def test_cannot_start_without_reservations(self):
        with self.assertRaises(LifecycleError):
            self.trip.start()

    def test_start_sets_fields(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.assertEqual(self.trip.status, Trip.STATUS_STARTED)
        self.assertIsNotNone(self.trip.start_trip_at)

    def test_cannot_start_twice(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        with self.assertRaises(LifecycleError):
            self.trip.start()

    def test_end_without_start_blocked(self):
        with self.assertRaises(LifecycleError):
            self.trip.end()

    def test_end_sets_fields(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        self.assertEqual(self.trip.status, Trip.STATUS_ENDED)
        self.assertIsNotNone(self.trip.end_trip_at)

    def test_cannot_end_twice(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        with self.assertRaises(LifecycleError):
            self.trip.end()

    def test_started_trip_is_immutable(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.depart_time = timezone.now()
        with self.assertRaises(FreezeError):
            self.trip.save()

    def test_ended_trip_is_immutable(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.trip.start()
        self.trip.end()
        self.trip.depart_time = timezone.now()
        with self.assertRaises(FreezeError):
            self.trip.save()

    def test_seats_left_calculation(self):
        self.assertEqual(self.trip.seats_left(), 2)
        Reservation.objects.create(trip=self.trip, passenger_name="A")
        self.assertEqual(self.trip.seats_left(), 1)


class ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.bus = Bus.objects.create(matricule="B1", capacity=2)
        self.route = Route.objects.create(bus=self.bus, direction="A -> B")
        self.trip = Trip.objects.create(route=self.route, depart_time=timezone.now())

    def test_bus_list_create_retrieve_update_delete_success(self):
        list_response = self.client.get("/api/buses/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            "/api/buses/",
            {"matricule": "B2", "capacity": 20},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        bus_id = create_response.data["id"]

        get_response = self.client.get(f"/api/buses/{bus_id}/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["matricule"], "B2")

        update_response = self.client.put(
            f"/api/buses/{bus_id}/",
            {"matricule": "B2-NEW", "capacity": 30},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["capacity"], 30)

        delete_response = self.client.delete(f"/api/buses/{bus_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_bus_create_rejects_invalid_capacity(self):
        response = self.client.post(
            "/api/buses/",
            {"matricule": "B3", "capacity": -1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("capacity", response.data)

    def test_bus_update_rejects_when_assigned(self):
        response = self.client.put(
            f"/api/buses/{self.bus.id}/",
            {"matricule": "B1", "capacity": 10},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "freeze_error")

    def test_bus_delete_rejects_when_assigned(self):
        response = self.client.delete(f"/api/buses/{self.bus.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

    def test_route_list_create_retrieve_update_delete_success(self):
        list_response = self.client.get("/api/routes/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        free_bus = Bus.objects.create(matricule="B4", capacity=10)
        create_response = self.client.post(
            "/api/routes/",
            {"bus": free_bus.id, "direction": "C -> D"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        route_id = create_response.data["id"]

        get_response = self.client.get(f"/api/routes/{route_id}/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        update_response = self.client.put(
            f"/api/routes/{route_id}/",
            {"bus": free_bus.id, "direction": "C -> E"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["direction"], "C -> E")

        delete_response = self.client.delete(f"/api/routes/{route_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_route_create_rejects_invalid_bus(self):
        response = self.client.post(
            "/api/routes/",
            {"bus": 999999, "direction": "Invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("bus", response.data)

    def test_route_delete_rejects_when_has_trips(self):
        response = self.client.delete(f"/api/routes/{self.route.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

    def test_trip_list_create_retrieve_update_delete_success(self):
        list_response = self.client.get("/api/trips/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        free_bus = Bus.objects.create(matricule="B5", capacity=5)
        free_route = Route.objects.create(bus=free_bus, direction="X -> Y")
        create_response = self.client.post(
            "/api/trips/",
            {"route": free_route.id, "depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        trip_id = create_response.data["id"]

        get_response = self.client.get(f"/api/trips/{trip_id}/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            f"/api/trips/{trip_id}/",
            {"depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/trips/{trip_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_trip_create_rejects_invalid_route(self):
        response = self.client.post(
            "/api/trips/",
            {"route": 999999, "depart_time": timezone.now().isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("route", response.data)

    def test_start_endpoint_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        response = self.client.post(f"/api/trips/{self.trip.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("start_trip_at", response.data)

    def test_start_endpoint_rejects_without_reservations(self):
        response = self.client.post(f"/api/trips/{self.trip.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_start_endpoint_rejects_second_start(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        first = self.client.post(f"/api/trips/{self.trip.id}/start/")
        second = self.client.post(f"/api/trips/{self.trip.id}/start/")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.data["code"], "lifecycle_error")

    def test_end_endpoint_success(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/trips/{self.trip.id}/start/")
        response = self.client.post(f"/api/trips/{self.trip.id}/end/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("end_trip_at", response.data)

    def test_end_endpoint_rejects_before_start(self):
        response = self.client.post(f"/api/trips/{self.trip.id}/end/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_end_endpoint_rejects_second_end(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/trips/{self.trip.id}/start/")
        first = self.client.post(f"/api/trips/{self.trip.id}/end/")
        second = self.client.post(f"/api/trips/{self.trip.id}/end/")
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second.data["code"], "lifecycle_error")

    def test_trip_update_rejects_structural_changes_after_start(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/trips/{self.trip.id}/start/")
        response = self.client.put(
            f"/api/trips/{self.trip.id}/",
            {
                "route": self.route.id,
                "depart_time": timezone.now().isoformat(),
                "status": Trip.STATUS_STARTED,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "freeze_error")

    def test_trip_delete_rejects_when_has_reservations(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        response = self.client.delete(f"/api/trips/{self.trip.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "protected_delete")

    def test_reservation_list_create_retrieve_delete_success(self):
        list_response = self.client.get("/api/reservations/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)

        create_response = self.client.post(
            "/api/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        reservation_id = create_response.data["id"]

        get_response = self.client.get(f"/api/reservations/{reservation_id}/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/reservations/{reservation_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_reservation_create_rejects_invalid_trip(self):
        response = self.client.post(
            "/api/reservations/",
            {"trip": 999999, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("trip", response.data)

    def test_reservation_create_rejects_missing_passenger_name(self):
        response = self.client.post(
            "/api/reservations/",
            {"trip": self.trip.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("passenger_name", response.data)

    def test_reservation_create_rejects_started_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/trips/{self.trip.id}/start/")
        response = self.client.post(
            "/api/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_reservation_create_rejects_ended_trip(self):
        Reservation.objects.create(trip=self.trip, passenger_name="Ali")
        self.client.post(f"/api/trips/{self.trip.id}/start/")
        self.client.post(f"/api/trips/{self.trip.id}/end/")
        response = self.client.post(
            "/api/reservations/",
            {"trip": self.trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "lifecycle_error")

    def test_reservation_create_rejects_full_trip(self):
        one_seat_bus = Bus.objects.create(matricule="B6", capacity=1)
        one_seat_route = Route.objects.create(bus=one_seat_bus, direction="L -> M")
        one_seat_trip = Trip.objects.create(route=one_seat_route, depart_time=timezone.now())
        Reservation.objects.create(trip=one_seat_trip, passenger_name="Ali")
        response = self.client.post(
            "/api/reservations/",
            {"trip": one_seat_trip.id, "passenger_name": "Sara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "capacity_error")

    def test_get_non_existing_resource_returns_404(self):
        response = self.client.get("/api/trips/999999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
