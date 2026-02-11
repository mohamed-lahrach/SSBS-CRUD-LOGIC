from django.db import models
from django.utils import timezone

from .exceptions import FreezeError, LifecycleError


class Bus(models.Model):
    matricule = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    # 🔒 freeze bus if used by routes
    def save(self, *args, **kwargs):
        if self.pk is not None:
            old = Bus.objects.get(pk=self.pk)

            if old.routes.exists():
                raise FreezeError("Cannot modify bus assigned to routes")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bus {self.matricule}"


class Route(models.Model):
    bus = models.ForeignKey(
        Bus,
        on_delete=models.PROTECT,
        related_name="routes"
    )
    direction = models.CharField(max_length=100)

    def __str__(self):
        return f"Route {self.id} - {self.direction}"


class Trip(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_STARTED = "STARTED"
    STATUS_ENDED = "ENDED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_STARTED, "Started"),
        (STATUS_ENDED, "Ended"),
    ]

    route = models.ForeignKey(
        Route,
        on_delete=models.PROTECT,
        related_name="trips"
    )

    depart_time = models.DateTimeField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED
    )

    start_trip_at = models.DateTimeField(null=True, blank=True)
    end_trip_at = models.DateTimeField(null=True, blank=True)

    # 🔒 structural freeze guard
    def _check_structural_freeze(self):
        if self.pk is None:
            return

        old = Trip.objects.get(pk=self.pk)

        frozen = old.status in [self.STATUS_STARTED, self.STATUS_ENDED]

        if not frozen:
            return

        structural_changed = (
            old.route != self.route or
            old.depart_time != self.depart_time
        )

        if structural_changed:
            raise FreezeError("Trip structure is frozen")

    def save(self, *args, **kwargs):
        self._check_structural_freeze()
        super().save(*args, **kwargs)

    def seats_left(self):
        return self.route.bus.capacity - self.reservations.count()

    def start(self):
        if self.status != self.STATUS_CREATED:
            raise LifecycleError("Trip cannot be started")

        if self.reservations.count() == 0:
            raise LifecycleError("Cannot start trip with zero reservations")

        self.start_trip_at = timezone.now()
        self.status = self.STATUS_STARTED
        super().save()  # bypass guard intentionally

    def end(self):
        if self.status != self.STATUS_STARTED:
            raise LifecycleError("Trip cannot be ended")

        self.end_trip_at = timezone.now()
        self.status = self.STATUS_ENDED
        super().save()  # bypass guard intentionally

    def __str__(self):
        return f"Trip {self.id} - {self.route.direction} ({self.status})"

class Reservation(models.Model):
    trip = models.ForeignKey(
        Trip,
        on_delete=models.PROTECT,
        related_name="reservations"
    )
    passenger_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger_name} → Trip {self.trip.id}"
