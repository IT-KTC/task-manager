from django.conf import settings
from django.db import models

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
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
    status= models.CharField(max_length=20,choices=Status.choices,default=Status.PENDING )
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