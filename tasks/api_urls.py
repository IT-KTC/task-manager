from django.urls import path
from rest_framework.routers import DefaultRouter
from .api_views import TaskViewSet  
from . import api_views
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.security import login_rate_limit
router = DefaultRouter()
router.register(
    "tasks",
    TaskViewSet,
    basename="task"
)

urlpatterns = router.urls + [
    path(
        "token/",
        login_rate_limit(TokenObtainPairView.as_view()),
        name="token_obtain_pair",
    ),

    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
