from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "route", "status", "depart_time", "start_trip_at", "end_trip_at")
    search_fields = ("route__direction", "route__bus__matricule")
