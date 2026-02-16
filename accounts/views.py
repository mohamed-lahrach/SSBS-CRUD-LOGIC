from accounts.permissions import IsSuperAdminorOrgAdmin
from accounts.permissions import IsOwnerOrAdmin
from .serializers import UserCreateSerializer, UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .models import User
from typing import cast


class UserViewSet(ModelViewSet):
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        # Only allow access if authenticated
        if not user.is_authenticated:
            return User.objects.none()

        # Type cast for static analysis
        user = cast(User, user)

        if user.is_superuser:
            return User.objects.all()
        elif user.is_org_admin:
            if user.organization:
                return User.objects.filter(organization=user.organization)
            else:
                return User.objects.none()
        else:
            if user.id:
                return User.objects.filter(id=user.id)
            else:
                return User.objects.none()
    
    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [IsSuperAdminorOrgAdmin()]
        elif self.action == 'retrieve':
            return [IsAuthenticated()]
        elif self.action in ['update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return [IsAuthenticated()]

