from django.urls import path 
from . import views

urlpatterns = [
  path("", views.task_list,name="task_list"),
    path("detail/", views.task_detail, name="task_detail"),
    path("about/", views.task_about, name="task_about"),
    path("mytasks/",views.my_tasks,name="my_tasks"),
    path("create/", views.task_create, name="task_create"),
    path("<int:pk>/edit/",views.task_update,name="task_update"),
    path("<int:pk>/delete/",views.task_delete,name="task_delete"),
    path("<int:pk>/detail/",views.task_detail,name="task_detail"),
    path("<int:pk>/download/",views.task_download,name="task_download"),
    path("async-test/", views.async_test, name="async_test")
]