from rest_framework.routers import DefaultRouter
from django.urls import path
from accounts.views import UserViewSet

# Uncomment the lines below to enable JWT authentication endpoints

# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

router = DefaultRouter()
router.register("users", UserViewSet, basename='user')

urlpatterns = [
    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] + router.urls