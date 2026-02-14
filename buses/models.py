from django.db import models

from core.exceptions import FreezeError


class Bus(models.Model):
    matricule = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old = Bus.objects.get(pk=self.pk)
            if old.routes.exists():
                raise FreezeError("Cannot modify bus assigned to routes")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bus {self.matricule}"
