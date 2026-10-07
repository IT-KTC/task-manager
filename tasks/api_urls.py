from django.urls import path

from . import api_views


urlpatterns = [

    path(
        "tasks/",
        api_views.task_list_api,
        name="api_task_list"
    ),

    path(
        "tasks/<int:pk>/",
        api_views.task_detail_api,
        name="api_task_detail"
    ),
]