from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from organization.models import Organization
from organization.serializer import OrganizationSerializer
from accounts.permissions import IsSuperAdminorOrgAdmin

# Create your views here.

class OrganizationViewSet(ModelViewSet):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.all()
        elif hasattr(user, 'organization') and user.organization:
            return Organization.objects.filter(id=user.organization.id)
        return Organization.objects.none()

    def get_permissions(self):
        if self.action in ['create','update', 'partial_update', 'destroy']:
            return [IsSuperAdminorOrgAdmin()]
        return [IsAuthenticated()]
