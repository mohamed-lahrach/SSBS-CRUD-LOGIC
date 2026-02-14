from django.db import models

from trips.models import Trip


class Reservation(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name="reservations")
    passenger_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger_name} -> Trip {self.trip.id}"
