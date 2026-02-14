from django.contrib import admin

from .models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("id", "direction", "bus")
    list_select_related = ("bus",)
    search_fields = ("direction", "bus__matricule")
