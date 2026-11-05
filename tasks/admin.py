from django.contrib import admin

from .models import Task


# Register your models here.
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display =(
        "id",
        "user",
        "title",
        "status",
        "completed",
        "created_at",
    )
    search_fields = (
        "title","description"
    )
    list_filter = (
        "status",
        "completed",
    )
    ordering = (
        "-created_at",
    )
    def save_model(self, request, obj, form, change):
        obj._activity_actor = request.user
        super().save_model(request, obj, form, change)