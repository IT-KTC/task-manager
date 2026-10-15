from django.db import models
from django.conf import settings
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
    status= models.CharField(max_length=20,default="pending" )
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
        null=True,
        blank=True,
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
class Meta: 
    indexes = [
        models.Index(
            fields=[
                "user",
                "status",
                "-created_at"
            ],
            name="task_user_status_created_idx",
        )
    ]
class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


priority = models.CharField(
    max_length=10,
    choices=Priority.choices,
    default=Priority.MEDIUM,
)