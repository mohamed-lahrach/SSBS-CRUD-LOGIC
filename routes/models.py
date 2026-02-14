from django.db import models

from buses.models import Bus


class Route(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT, related_name="routes")
    direction = models.CharField(max_length=100)

    def __str__(self):
        return f"Route {self.id} - {self.direction}"
