from rest_framework.test import APITestCase
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Task
from rest_framework import status
from django.urls import reverse
User = get_user_model()
# Create your tests here.

class TeskAPITest(APITestCase): 
    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="12345678"
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="12345678"
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Learn Django",
            description="Learn DRF testing",
            status="pending",
            completed=False,
        )
    def test_task_list_requires_authentication(self):
        response = self.client.get(
            "/api/tasks/"
        )
        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ]
        )
    def test_user_can_list_own_tasks(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/tasks/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
    def test_user_only_sees_own_tasks(self):

        Task.objects.create(
            user=self.other_user,
            title="Other User Task",
            status="pending",
            completed=False,
        )

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/tasks/"
        )

        self.assertEqual(
            response.data["count"],
            1
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Learn Django"
        )
    def test_user_can_create_task(self):

        self.client.force_authenticate(
            user=self.user
        )

        data = {
            "title": "Learn React",
            "description": "Next step",
            "status": "pending",
            "completed": False,
        }

        response = self.client.post(
            "/api/tasks/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
    def test_owner_can_update_task(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {
                "completed": True
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.task.refresh_from_db()

        self.assertTrue(
            self.task.completed
        )
    def test_other_user_cannot_update_task(self):

        self.client.force_authenticate(
            user=self.other_user
        )

        response = self.client.patch(
            f"/api/tasks/{self.task.id}/",
            {
                "completed": True
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )
    def test_owner_can_delete_task(self):

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.delete(
            f"/api/tasks/{self.task.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Task.objects.filter(
                id=self.task.id
            ).exists()
        )
    def test_search_tasks(self):

        Task.objects.create(
            user=self.user,
            title="Learn React",
            status="pending",
            completed=False,
        )

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/tasks/?search=django"
        )

        self.assertEqual(
            response.data["count"],
            1
        )

        self.assertEqual(
            response.data["results"][0]["title"],
            "Learn Django"
        )
    def test_filter_by_status(self):

        Task.objects.create(
            user=self.user,
            title="Finished Task",
            status="completed",
            completed=True,
        )

        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            "/api/tasks/?status=pending"
        )

        self.assertEqual(
            response.data["count"],
            1
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            "pending"
        )

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

