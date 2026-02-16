from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Administrator"),
        ("driver", "Driver"),
        ("passenger", "Passenger"),
    ]
    @property
    def is_org_admin(self):
        return self.role == 'admin'

    @property
    def is_driver(self):
        return self.role == 'driver'

    @property
    def is_passenger(self):
        return self.role == 'passenger'

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='passenger')
    organization = models.ForeignKey('organization.Organization',
                            on_delete=models.CASCADE,
                            null=True, blank=True,  # Optional - not all users need organization
                            related_name='users')

    def __str__(self):
        return self.username