from rest_framework.routers import DefaultRouter
from organization.views import OrganizationViewSet

router = DefaultRouter()
router.register(r'organization', OrganizationViewSet, basename='organization')

urlpatterns = router.urls