from django.db import models
from django.utils import timezone

from core.exceptions import FreezeError, LifecycleError
from routes.models import Route


class Trip(models.Model):
    STATUS_CREATED = "CREATED"
    STATUS_STARTED = "STARTED"
    STATUS_ENDED = "ENDED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_STARTED, "Started"),
        (STATUS_ENDED, "Ended"),
    ]

    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="trips")
    depart_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_CREATED)
    start_trip_at = models.DateTimeField(null=True, blank=True)
    end_trip_at = models.DateTimeField(null=True, blank=True)

    def _check_structural_freeze(self):
        if self.pk is None:
            return

        old = Trip.objects.get(pk=self.pk)
        frozen = old.status in [self.STATUS_STARTED, self.STATUS_ENDED]

        if not frozen:
            return

        structural_changed = old.route != self.route or old.depart_time != self.depart_time
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
        super().save()

    def end(self):
        if self.status != self.STATUS_STARTED:
            raise LifecycleError("Trip cannot be ended")

        self.end_trip_at = timezone.now()
        self.status = self.STATUS_ENDED
        super().save()

    def __str__(self):
        return f"Trip {self.id} - {self.route.direction} ({self.status})"
