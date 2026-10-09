from django.db import models
from django.conf import settings
# Create your models here.
class Task(models.Model):
    title= models.CharField(max_length=200)
    description= models.TextField(blank=True)
    status= models.CharField(max_length=20,default="pending" )
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.title
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