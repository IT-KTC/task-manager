from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.


class TaskQuerySet(models.QuerySet):
    def pending(self):
        return self.filter(status = "pending")
    def complete(self):
        return self.filter(completed = True)
    def for_user(self,user ):
        return self.filter(user = user)
    def recent(self):
        return self.order_by("-created_at")



class Task(models.Model):
    title= models.CharField(max_length=200)
    description= models.TextField(blank=True)
   
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title
    objects = TaskQuerySet.as_manager()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
       
    )
    attachment = models.FileField(
        upload_to="task_attachments/",
        blank=True
    )
    image = models.ImageField(
        upload_to="task_image/",
        blank = True,
        null = True
    )
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ thực hiện"
        IN_PROGRESS = "in_progress", "Đang thực hiện"
        COMPLETED = "completed", "Hoàn thành"
    status= models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING )
    class Priority(models.TextChoices):
        LOW = "low", "Thấp"
        MEDIUM = "medium", "Trung bình"
        HIGH = "high", "Cao"
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    due_date = models.DateField(
        null=True,
        blank=True,
    )
    @property
    def is_overdue(self):
        if self.due_date is None:
            return False

        if self.status == self.Status.COMPLETED:
            return False

        return self.due_date < timezone.localdate()
    def save(self, *args, **kwargs):
   
        self.completed = (
            self.status == self.Status.COMPLETED
        )

   
        update_fields = kwargs.get("update_fields")

        if update_fields is not None:
            fields = set(update_fields)

            if "status" in fields or "completed" in fields:
                fields.add("completed")

            kwargs["update_fields"] = fields

        super().save(*args, **kwargs)
    class Meta: 
        indexes = [  # noqa: RUF012
            models.Index(
                fields=[
                    "user",
                    "status",
                    "-created_at"
                ],
                name="task_user_status_created_idx",
            )
        ]

class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_notifications",
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]  # noqa: RUF012
        indexes = [  # noqa: RUF012
            models.Index(
                fields=["user", "is_read", "-created_at"],
                name="notification_user_unread_idx",
            )
        ]

    def __str__(self):
        return self.message

class TaskComment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="task_comments",
    )

    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]  # noqa: RUF012

    def __str__(self):
        return f"Bình luận #{self.pk} - Task #{self.task_id}"


class TaskActivity(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Tạo công việc"
        UPDATED = "updated", "Cập nhật công việc"
        STATUS_CHANGED = "status_changed", "Đổi trạng thái"
        COMMENT_ADDED = "comment_added", "Thêm bình luận"
        COMMENT_DELETED = "comment_deleted", "Xóa bình luận"

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="activities",
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="task_activities",
    )

    action = models.CharField(
        max_length=30,
        choices=Action.choices,
    )

    description = models.CharField(max_length=500)

    changed_fields = models.JSONField(
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]  # noqa: RUF012

    def __str__(self):
        return f"{self.get_action_display()} - Task #{self.task_id}"
