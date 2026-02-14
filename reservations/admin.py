from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "passenger_name", "trip", "created_at")
    search_fields = ("passenger_name",)
