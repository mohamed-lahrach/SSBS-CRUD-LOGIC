from rest_framework import serializers
from organization.models import Organization
from .models import User

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'organization']
        read_only_fields = ['id', 'organization', 'role']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'role']

    def validate_role(self, role):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                "Request context is required to validate role."
            )
        user = request.user

        if user.is_superuser:
            return role

        if not user.is_org_admin:
            raise serializers.ValidationError(
                "You are not allowed to assign roles."
            )
        return role

    def create(self, validated_data):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError(
                "Request context is required to validate role."
            )
        creator = request.user

        password = validated_data.pop('password')

        user = User(**validated_data)
        user.organization = creator.organization
        user.set_password(password)
        user.save()

        return user
