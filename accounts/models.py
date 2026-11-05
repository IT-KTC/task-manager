
from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/",
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    def __str__(self):
        return f"Profile of {self.user.username}"
