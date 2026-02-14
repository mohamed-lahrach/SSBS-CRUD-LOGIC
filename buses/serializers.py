from rest_framework import serializers

from .models import Bus


class BusSerializer(serializers.ModelSerializer):
    capacity = serializers.IntegerField(min_value=1)

    class Meta:
        model = Bus
        fields = "__all__"
