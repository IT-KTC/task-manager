
from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.team_list,
        name="team_list"
    ),

    path(
        "create/",
        views.team_create,
        name="team_create"
    ),

    path(
        "<int:pk>/members/add/",
        views.team_member_add,
        name="team_member_add"
    ),

    path(
        "<int:pk>/members/<int:membership_id>/remove/",
        views.team_member_remove,
        name="team_member_remove"
    ),

    path(
        "<int:pk>/",
        views.team_detail,
        name="team_detail"
    ),
]
