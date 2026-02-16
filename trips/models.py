from django.db import models
from django.utils import timezone


class Trip(models.Model):
    # --------------------------
    # lifecycle states
    # --------------------------
    STATUS_CREATED = "CREATED"
    STATUS_STARTED = "STARTED"
    STATUS_ENDED = "ENDED"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Created"),
        (STATUS_STARTED, "Started"),
        (STATUS_ENDED, "Ended"),
    ]

    # --------------------------
    # structure
    # --------------------------
    route = models.ForeignKey(
        "routes.Route",
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

    # --------------------------
    # enforce CREATED at birth
    # --------------------------
    def _enforce_birth_state(self):
        if self.pk is None:
            self.status = self.STATUS_CREATED

    # --------------------------
    # structural freeze guard
    # --------------------------
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
            raise ValueError("Trip structure is frozen")

    # --------------------------
    # unified save pipeline
    # --------------------------
    def save(self, *args, **kwargs):
        self._enforce_birth_state()
        self._check_structural_freeze()
        super().save(*args, **kwargs)

    # --------------------------
    # domain logic
    # --------------------------
    def seats_left(self):
        return self.route.bus.capacity - self.reservations.count()

    # --------------------------
    # lifecycle transitions
    # --------------------------
    def start(self):
        if self.status != self.STATUS_CREATED:
            raise ValueError("Trip cannot be started")

        if self.reservations.count() == 0:
            raise ValueError("Cannot start trip with zero reservations")

        self.start_trip_at = timezone.now()
        self.status = self.STATUS_STARTED
        super().save()  # bypass freeze intentionally

    def end(self):
        if self.status != self.STATUS_STARTED:
            raise ValueError("Trip cannot be ended")

        self.end_trip_at = timezone.now()
        self.status = self.STATUS_ENDED
        super().save()  # bypass freeze intentionally

    # --------------------------
    # debug display
    # --------------------------
    def __str__(self):
        return f"Trip {self.id} - {self.route.direction} ({self.status})"