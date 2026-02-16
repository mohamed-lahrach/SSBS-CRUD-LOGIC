from rest_framework.permissions import BasePermission, IsAuthenticated

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_superuser
        )
 
class IsSuperAdminorOrgAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_org_admin
            )
        )
    # def has_object_permission(self, request, view, obj):
    #     return (
    #         request.user.is_authenticated
    #         and (
    #             request.user.is_superuser
    #             or (request.user.is_org_admin and obj.organization == request.user.organization)
    #         )
    #     )

class IsOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_superuser
            or (request.user.is_org_admin 
                    and obj.organization == request.user.organization)
            or          (obj.id == request.user.id)
        )

class IsDriver(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_driver
            )
        )

class IsPassenger(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.is_passenger
            )
        )
