
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Notification, Task

User = get_user_model()


class NotificationTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            username="test_user_a",
            password="StrongPass123!"
        )

        self.user_b = User.objects.create_user(
            username="test_user_b",
            password="StrongPass456!"
        )

        self.task = Task.objects.create(
            user=self.user_a,
            title="Kiểm thử thông báo"
        )

    def test_creating_task_creates_notification(self):
        self.assertEqual(
            Notification.objects.filter(
                user=self.user_a
            ).count(),
            1
        )

    def test_status_change_creates_notification(self):
        self.task.status = Task.Status.COMPLETED

        self.task.save(
            update_fields=["status", "updated_at"]
        )

        self.assertEqual(
            Notification.objects.filter(
                user=self.user_a
            ).count(),
            2
        )

    def test_user_cannot_read_other_users_notification(self):
        notification = Notification.objects.get(
            user=self.user_a
        )

        self.client.force_login(self.user_b)

        response = self.client.post(
            reverse(
                "notification_mark_read",
                args=[notification.pk]
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )

    def test_owner_can_mark_notification_read(self):
        notification = Notification.objects.get(
            user=self.user_a
        )

        self.client.force_login(self.user_a)

        response = self.client.post(
            reverse(
                "notification_mark_read",
                args=[notification.pk]
            )
        )

        self.assertEqual(response.status_code, 302)

        notification.refresh_from_db()

        self.assertTrue(notification.is_read)

    def test_anonymous_user_cannot_view_notifications(self):
        response = self.client.get(
            reverse("notification_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_read_action_rejects_get(self):
        notification = Notification.objects.get(
            user=self.user_a
        )

        self.client.force_login(self.user_a)

        response = self.client.get(
            reverse(
                "notification_mark_read",
                args=[notification.pk]
            )
        )

        self.assertEqual(response.status_code, 405)
