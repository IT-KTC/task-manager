from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="admin_dashboard"),
    path("users/", views.user_list, name="admin_users"),
    path("users/<int:pk>/", views.user_detail, name="admin_user_detail"),
]
