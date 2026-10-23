from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from tasks.models import Task


User = get_user_model()


class AdminPanelTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(
            username="root_admin", email="admin@example.test", password="strong-test-password"
        )
        self.member = User.objects.create_user(
            username="alice", email="alice@example.test", password="strong-test-password"
        )
        self.other = User.objects.create_user(
            username="bob", password="strong-test-password"
        )
        Task.objects.create(user=self.member, title="Alice Task", status=Task.Status.PENDING)
        Task.objects.create(user=self.other, title="Bob Task", status=Task.Status.COMPLETED)

    def test_anonymous_user_redirects_to_login(self):
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_regular_user_is_forbidden(self):
        self.client.force_login(self.member)
        for name in ("admin_dashboard", "admin_users"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("admin_user_detail", args=[self.other.pk])).status_code,
            403,
        )

    def test_superuser_dashboard_counts_all_users_tasks(self):
        self.client.force_login(self.root)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_stats"]["total"], 3)
        self.assertEqual(response.context["task_stats"]["total"], 2)
        self.assertEqual(response.context["task_stats"]["completed"], 1)

    def test_user_detail_shows_only_that_users_tasks(self):
        self.client.force_login(self.root)
        response = self.client.get(reverse("admin_user_detail", args=[self.member.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Task")
        self.assertNotContains(response, "Bob Task")
        self.assertEqual(response.context["stats"]["total"], 1)

    def test_user_list_filters_by_username(self):
        self.client.force_login(self.root)
        response = self.client.get(reverse("admin_users"), {"q": "alice"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_inactive_superuser_cannot_access(self):
        self.root.is_active = False
        self.root.save(update_fields=["is_active"])
        self.client.force_login(self.root)
        response = self.client.get(reverse("admin_dashboard"))
        self.assertNotEqual(response.status_code, 200)
