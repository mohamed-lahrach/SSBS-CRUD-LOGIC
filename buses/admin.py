from django.contrib import admin

from .models import Bus


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("id", "matricule", "capacity")
    search_fields = ("matricule",)
