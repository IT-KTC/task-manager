from django.urls import include, path

from . import views

urlpatterns = [
  path("", views.task_list,name="task_list"),
   
    path("about/", views.task_about, name="task_about"),
    path("mytasks/",views.my_tasks,name="my_tasks"),
    path("create/", views.task_create, name="task_create"),
    path("<int:pk>/edit/",views.task_update,name="task_update"),
    path("<int:pk>/delete/",views.task_delete,name="task_delete"),
    path("<int:pk>/detail/",views.task_detail,name="task_detail"),
    path("<int:pk>/download/",views.task_download,name="task_download"),
    path(
    "<int:pk>/image/",
    views.task_image,
    name="task_image",
    ),
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),
    path("async-test/", views.async_test, name="async_test"),
    path(
        "<int:pk>/quick-status/",
        views.task_quick_status,
        name="task_quick_status",
    ),
    path(
      "kanban/",
      views.kanban_board,
      name="kanban_board",
    ),
    path(
        "<int:pk>/kanban-move/",
        views.kanban_move_task,
        name="kanban_move_task",
    ),
]