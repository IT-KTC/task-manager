from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Task
from django.urls import reverse
# Create your tests here.
class TaskModelTest(TestCase):
    def setUp(self): 
        User = get_user_model()
        self.user_a = User.objects.create_user(
            username="user_a",
            password="12345678test"
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            password="12345678test"

        )
        self.task_a = Task.objects.create(
            user = self.user_a,
            title="task of user a",
            description="this task belongs to user a",
            status="pending",
            completed=False
        )
        self.task_b = Task.objects.create(
            user=self.user_b,
            title="task of user b",
            description="this task belongs to user b",
            status="completed",
            completed=True
        )
    def test_task_title(self):
        self.assertEqual(
            self.task_a.title,
            "task of user a"
        )
    def test_task_string(self):
        self.assertEqual(
            str(self.task_a),
            "task of user a"
        )
    def test_task_requires_login(self):
        response = self.client.get(
            reverse("task_list")
        )
        self.assertEqual(
        response.status_code,
        302
    )
    def test_logged_in_user_can_access_task_list(self):
        self.client.login(
            username="user_a",
            password="12345678test"
        )
        response = self.client.get(
        reverse("task_list")
        )
        self.assertEqual(
        response.status_code,
        200
    )
    def test_user_only_sees_own_tasks(self):
        self.client.login(
        username="user_a",
        password="12345678test"
        )

        response = self.client.get(
            reverse("task_list")
        )
        self.assertContains(
            response,"task of user a"
        )
        self.assertNotContains(
            response,
            "task of user b"
        )
    def test_create_task_assigns_current_user(self):
        self.client.login(
            username="user_a",
            password="12345678test"
        )
        self.client.post(

            reverse("task_create"),
            {
                "title": "new task",
                "description": "new task description",
                "status": "pending",
                "completed": False,
            }
        )
        task =Task.objects.get(
            title = "new task"
        )
        self.assertEqual(
            task.user,
            self.user_a
        )
    def test_user_cannot_view_other_users_task(self):
        self.client.login(
            username="user_b",
            password="12345678test"
        )

        response = self.client.get(
            reverse(
                "task_detail",
                kwargs={
                    "pk": self.task_a.pk
                }
            )
        )
        self.assertEqual(
            response.status_code,
            404
        )
    def test_user_cannot_update_other_users_task(self):

        self.client.login(
            username="user_b",
            password="12345678test"
        )

        response = self.client.get(
            reverse(
                "task_update",
                kwargs={
                    "pk": self.task_a.pk
                }
            )
        )

        self.assertEqual(
            response.status_code,
            404
        )
    def test_user_cannot_delete_other_users_task(self):
        self.client.login(
            username="user_b",
            password="12345678test"
        )
        response = self.client.get(
            reverse("task_delete",
                kwargs = {
                    "pk": self.task_a.pk
                }
            )

        )
        self.assertEqual(
            response.status_code,
            404
        )
    def test_user_cannot_download_other_users_file(self):

        self.client.login(
        username="user_b",
        password="12345678test"
    )

        response = self.client.get(
        reverse(
            "task_download",
            kwargs={
                "pk": self.task_a.pk
            }
        )
    )

        self.assertEqual(
            response.status_code,
            404
        )

