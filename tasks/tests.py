from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken,
)

from tasks.models import Task

from .forms import TaskForm
from .models import Task
from .tasks import resize_task_image

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
    def test_api_status_update_syncs_completed(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/tasks/{self.task.pk}/",
            {"status": "completed"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.COMPLETED,
        )
        self.assertTrue(self.task.completed)


    def test_api_rejects_conflicting_status(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/tasks/{self.task.pk}/",
            {
                "status": "completed",
                "completed": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
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
    def test_stats_only_counts_current_user_tasks(self):
        Task.objects.create(
            user = self.user,
            title = "Completed Task",
            status = "completed",
            completed = True
        )
        Task.objects.create(
            user = self.other_user,
            title = "Other User Task",
            status = "completed",
            completed = True
        )
        self.client.force_authenticate(user = self.user)
        response = self.client.get("/api/tasks/stats/")
        self.assertEqual(response.status_code,200)
        self.assertEqual(
            response.data,
            { 
                "total":2,
                "completed": 1,
                "incomplete":1
            
            }
        
        )
    def test_stats_updates_after_creating_task(self):
        self.client.force_authenticate(user = self.user)
        first_response = self.client.get("/api/tasks/stats/")
        self.assertEqual(
            first_response.data["total"],
            1
        )
        Task.objects.create(
            user = self.user,
            title = "New Task",
            status = "pending",
            completed = False
        )
        second_response = self.client.get("/api/tasks/stats/")
        self.assertEqual(
            second_response.data["total"],
            2,
        )
    def test_stats_filters_by_status(self):
        Task.objects.create(
            user = self.user,
            title = "Finished Task",
            status = "completed",
            completed = True
        )
        self.client.force_authenticate(user = self.user)
        response = self.client.get("/api/tasks/stats/",{"status": "pending"})
        self.assertEqual(response.status_code,200)
        self.assertEqual(
            response.data,
            {
            "total":1,
            "completed":0,
            "incomplete": 1
            },
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
            password="12345678test",
        )

        response = self.client.post(
            reverse("task_create"),
            {
                "title": "new task",
                "description": "new task description",
                "status": "pending",
                "completed": False,
                "priority": Task.Priority.MEDIUM,
            },
        )

        self.assertRedirects(
            response,
            reverse("task_list"),
        )

        task = Task.objects.get(
            title="new task"
        )

        self.assertEqual(
            task.user,
            self.user_a,
        )

        self.assertEqual(
            task.priority,
            Task.Priority.MEDIUM,
        )
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
    def test_filter_status_without_search(self):
        Task.objects.create(
            user=self.user_a,
            title="Finished Task A",
            status="completed",
            completed=True,
        )

        self.client.login(
            username="user_a",
            password="12345678test",
        )

        response = self.client.get(
            reverse("task_list"),
            {"status": "completed"},
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        titles = [
            task.title
            for task in response.context["page_obj"]
        ]

        self.assertEqual(
            titles,
            ["Finished Task A"],
        )

class ResizeImageTests(TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        media_override = override_settings(
            MEDIA_ROOT=self.temp_dir.name
        )
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = User.objects.create_user(
            username="image_tester",
            password="testpass123",
        )

        buffer = BytesIO()

        Image.new(
            "RGB",
            (1200, 600),
        ).save(
            buffer,
            format="PNG",
        )

        uploaded_image = SimpleUploadedFile(
            "original.png",
            buffer.getvalue(),
            content_type="image/png",
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Test Image",
            image=uploaded_image,
        )

    def test_image_is_resized(self):
        original_name = self.task.image.name
        storage = self.task.image.storage

        resize_task_image.run(self.task.pk)

        self.task.refresh_from_db()

        self.assertNotEqual(
            self.task.image.name,
            original_name,
        )

        with storage.open(
            self.task.image.name,
            "rb",
        ) as file, Image.open(file) as image:
            self.assertEqual(
                image.size,
                (800, 800),
            )
            self.assertEqual(
                image.format,
                "JPEG",
            )

        # Ảnh gốc vẫn được giữ
        self.assertTrue(
            storage.exists(original_name)
        )

    def test_resize_does_not_run_twice(self):
        resize_task_image.run(self.task.pk)

        self.task.refresh_from_db()
        first_image_name = self.task.image.name

        resize_task_image.run(self.task.pk)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.image.name,
            first_image_name,
        )

    def test_missing_task_is_ignored(self):
        resize_task_image.run(999999)

    def test_broken_image_preserves_original(self):
        broken_file = SimpleUploadedFile(
            "broken.png",
            b"this is not a real image",
            content_type="image/png",
        )

        self.task.image = broken_file
        self.task.save(update_fields=["image"])

        original_name = self.task.image.name
        storage = self.task.image.storage

        with self.assertRaises(UnidentifiedImageError):
            resize_task_image.run(self.task.pk)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.image.name,
            original_name,
        )

        self.assertTrue(
            storage.exists(original_name)
        )
class PrivateTaskMediaTests(TestCase):

    def setUp(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        media_settings = override_settings(
            MEDIA_ROOT=temp_dir.name
        )
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.owner = User.objects.create_user(
            username="owner_media",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="other_media",
            password="testpass123",
        )

        buffer = BytesIO()
        Image.new(
            "RGB",
            (20, 20),
        ).save(buffer, format="PNG")

        self.task = Task.objects.create(
            user=self.owner,
            title="Private Task",
            attachment=SimpleUploadedFile(
                "private.pdf",
                b"%PDF-1.4\nTest",
                content_type="application/pdf",
            ),
            image=SimpleUploadedFile(
                "private.png",
                buffer.getvalue(),
                content_type="image/png",
            ),
        )

    def test_owner_can_access_media(self):
        self.client.force_login(self.owner)

        for name in ("task_download", "task_image"):
            response = self.client.get(
                reverse(name, args=[self.task.pk])
            )

            self.assertEqual(
                response.status_code,
                200,
            )

            self.assertTrue(response.streaming)

            content = b"".join(
                response.streaming_content
            )

            self.assertGreater(len(content), 0)
    def test_other_user_cannot_access_media(self):
        self.client.force_login(self.other_user)

        for name in ("task_download", "task_image"):
            response = self.client.get(
                reverse(name, args=[self.task.pk])
            )
            self.assertEqual(response.status_code, 404)

    def test_anonymous_cannot_access_media(self):
        for name in ("task_download", "task_image"):
            response = self.client.get(
                reverse(name, args=[self.task.pk])
            )
            self.assertEqual(response.status_code, 302)
class TaskUploadValidationTests(SimpleTestCase):

    def test_rejects_large_attachment(self):
        large_file = SimpleUploadedFile(
            "document.pdf",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="application/pdf",
        )

        form = TaskForm(
            data={"title": "Test Task"},
            files={"attachment": large_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("attachment", form.errors)

    def test_rejects_invalid_attachment_extension(self):
        invalid_file = SimpleUploadedFile(
            "script.exe",
            b"invalid content",
            content_type="application/octet-stream",
        )

        form = TaskForm(
            data={"title": "Test Task"},
            files={"attachment": invalid_file},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("attachment", form.errors)
class TaskAPISecurityTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username="security_owner",
            password="TestPass123!",
        )
        self.other_user = User.objects.create_user(
            username="security_other",
            password="TestPass123!",
        )
        
        
        self.task = Task.objects.create(
            user=self.owner,
            title="Private Task",
            status="pending",
            completed=False,
        )
    def test_anonymous_cannot_access_tasks(self):
        response = self.client.get("/api/tasks/")
        self.assertIn(
            response.status_code,
            [401, 403],
        )
    def test_valid_jwt_can_access_api(self):
        token = RefreshToken.for_user(self.owner)
        self.client.credentials(
            HTTP_AUTHORIZATION = f"Bearer {token.access_token}"
        )
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, 200)
    def test_other_user_cannot_access_private_task(self):
        self.client.force_authenticate(
            user=self.other_user
        )

        url = f"/api/tasks/{self.task.pk}/"

        for response in (
            self.client.get(url),
            self.client.patch(
                url,
                {"title": "Unauthorized"},
                format="json",
            ),
            self.client.delete(url),
        ):
            self.assertEqual(response.status_code, 404)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.title,
            "Private Task",
        )

    def test_user_cannot_fake_task_owner(self):
        self.client.force_authenticate(
            user=self.owner
        )

        response = self.client.post(
            "/api/tasks/",
            {
                "title": "Forged Ownership",
                "user": self.other_user.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)

        created_task = Task.objects.get(
            pk=response.data["id"]
        )

        self.assertEqual(
            created_task.user,
            self.owner,
        )
class SessionConnectionTests(TestCase):

    def test_force_login(self):
        User = get_user_model()

        user = User.objects.create_user(
            username="session_test",
            password="testpass123",
        )

        self.client.force_login(user)

        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            user.pk,
        )
class DashboardTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard_user",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="another_user",
            password="testpass123",
        )

        Task.objects.create(
            user=self.user,
            title="Pending Task",
            status="pending",
        )

        Task.objects.create(
            user=self.user,
            title="Completed Task",
            status="completed",
            completed=True,
        )

        Task.objects.create(
            user=self.other_user,
            title="Secret Task",
            status="pending",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(response.status_code, 302)

    def test_dashboard_statistics(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 2)
        self.assertEqual(response.context["pending_count"], 1)
        self.assertEqual(response.context["completed_count"], 1)
        self.assertEqual(response.context["completion_rate"], 50)

    def test_dashboard_shows_only_own_tasks(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertContains(response, "Pending Task")
        self.assertContains(response, "Completed Task")
        self.assertNotContains(response, "Secret Task")
    def test_dashboard_overdue_count(self):
        yesterday = timezone.localdate() - timedelta(days=1)

        # Task quá hạn của User hiện tại
        Task.objects.create(
            user=self.user,
            title="Overdue Task",
            status=Task.Status.IN_PROGRESS,
            due_date=yesterday,
        )

        # Task đã hoàn thành: không tính là overdue
        Task.objects.create(
            user=self.user,
            title="Completed Old Task",
            status=Task.Status.COMPLETED,
            completed=True,
            due_date=yesterday,
        )

        # Task của người khác: không được tính
        Task.objects.create(
            user=self.other_user,
            title="Other User Overdue",
            status=Task.Status.PENDING,
            due_date=yesterday,
        )

        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.context["overdue_count"],
            1,
        )
class TaskPriorityDeadlineTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="priority_user",
            password="testpass123",
        )

    def test_default_priority(self):
        task = Task.objects.create(
            user=self.user,
            title="Default Priority Task",
        )

        self.assertEqual(
            task.priority,
            Task.Priority.MEDIUM,
        )

    def test_overdue_task(self):
        task = Task.objects.create(
            user=self.user,
            title="Overdue Task",
            status=Task.Status.PENDING,
            due_date=timezone.localdate()
            - timedelta(days=1),
        )

        self.assertTrue(task.is_overdue)

    def test_completed_task_is_not_overdue(self):
        task = Task.objects.create(
            user=self.user,
            title="Completed Task",
            status=Task.Status.COMPLETED,
            due_date=timezone.localdate()
            - timedelta(days=1),
        )

        self.assertFalse(task.is_overdue)

    def test_task_without_deadline(self):
        task = Task.objects.create(
            user=self.user,
            title="No Deadline",
        )

        self.assertFalse(task.is_overdue)
class TaskAdvancedFilterTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="filter_user",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="other_filter_user",
            password="testpass123",
        )

        yesterday = timezone.localdate() - timedelta(days=1)
        tomorrow = timezone.localdate() + timedelta(days=1)

        Task.objects.create(
            user=self.user,
            title="Urgent Report",
            status="pending",
            priority="high",
            due_date=yesterday,
        )

        Task.objects.create(
            user=self.user,
            title="Documentation",
            status="in_progress",
            priority="medium",
            due_date=tomorrow,
        )

        Task.objects.create(
            user=self.user,
            title="No Deadline Task",
            status="pending",
            priority="low",
        )

        Task.objects.create(
            user=self.other_user,
            title="Secret Urgent Task",
            status="pending",
            priority="high",
            due_date=yesterday,
        )

        self.client.force_login(self.user)

    def test_filter_high_priority(self):
        response = self.client.get(
            reverse("task_list"),
            {"priority": "high"},
        )

        titles = [
            task.title for task in response.context["page_obj"]
        ]

        self.assertEqual(titles, ["Urgent Report"])

    def test_filter_overdue(self):
        response = self.client.get(
            reverse("task_list"),
            {"overdue": "1"},
        )

        titles = [
            task.title for task in response.context["page_obj"]
        ]

        self.assertEqual(titles, ["Urgent Report"])

    def test_combined_filters(self):
        response = self.client.get(
            reverse("task_list"),
            {
                "search": "Urgent",
                "status": "pending",
                "priority": "high",
                "overdue": "1",
            },
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            1,
        )

    def test_sort_by_deadline(self):
        response = self.client.get(
            reverse("task_list"),
            {"sort": "deadline"},
        )

        titles = [
            task.title for task in response.context["page_obj"]
        ]

        self.assertEqual(
            titles,
            ["Urgent Report", "Documentation", "No Deadline Task"],
        )

class TaskQuickStatusTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="quick_user",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="quick_other",
            password="testpass123",
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Quick Action Task",
            status=Task.Status.PENDING,
            completed=False,
        )

        self.url = reverse(
            "task_quick_status",
            args=[self.task.pk],
        )

        self.client.force_login(self.user)

    def test_full_task_workflow(self):
        transitions = [
            (Task.Status.IN_PROGRESS, False),
            (Task.Status.COMPLETED, True),
            (Task.Status.PENDING, False),
        ]

        for new_status, expected_completed in transitions:
            response = self.client.post(
                self.url,
                {"status": new_status},
            )

            self.assertEqual(response.status_code, 302)

            self.task.refresh_from_db()

            self.assertEqual(
                self.task.status,
                new_status,
            )

            self.assertEqual(
                self.task.completed,
                expected_completed,
            )

    def test_invalid_transition(self):
        response = self.client.post(
            self.url,
            {"status": Task.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 400)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_other_user_cannot_update_task(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            self.url,
            {"status": Task.Status.IN_PROGRESS},
        )

        self.assertEqual(response.status_code, 404)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_get_request_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_redirect_preserves_filters(self):
        previous_page = (
            reverse("task_list")
            + "?priority=high&sort=deadline&page=2"
        )

        response = self.client.post(
            self.url,
            {
                "status": Task.Status.IN_PROGRESS,
                "next": previous_page,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            previous_page,
        )
class TaskStatusSyncTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="sync_user",
            password="testpass123",
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Status Sync Task",
            status=Task.Status.PENDING,
        )

    def test_completed_syncs_with_status(self):
        self.task.status = Task.Status.COMPLETED
        self.task.save(update_fields=["status"])

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.COMPLETED,
        )

        self.assertTrue(self.task.completed)

    def test_reopening_task_resets_completed(self):
        self.task.status = Task.Status.COMPLETED
        self.task.save()

        self.task.status = Task.Status.IN_PROGRESS
        self.task.save(update_fields=["status"])

        self.task.refresh_from_db()

        self.assertFalse(self.task.completed)

    def test_model_corrects_inconsistent_data(self):
        self.task.status = Task.Status.PENDING
        self.task.completed = True

        self.task.save()
        self.task.refresh_from_db()

        self.assertFalse(self.task.completed)
class KanbanBoardTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="kanban_user",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="kanban_other",
            password="testpass123",
        )

        for status_value in Task.Status.values:
            Task.objects.create(
                user=self.user,
                title=f"My {status_value} task",
                status=status_value,
            )

        Task.objects.create(
            user=self.other_user,
            title="Private other task",
            status=Task.Status.PENDING,
        )

        self.url = reverse("kanban_board")

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_board_groups_tasks_correctly(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

        columns = response.context["columns"]

        self.assertEqual(len(columns), 3)

        for column in columns:
            self.assertEqual(
                len(column["tasks"]),
                1,
            )

            task = column["tasks"][0]

            self.assertEqual(
                task.status,
                column["key"],
            )

    def test_other_user_tasks_are_hidden(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertNotContains(
            response,
            "Private other task",
        )
class KanbanMoveTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="kanban_move_user",
            password="testpass123",
        )

        self.other_user = User.objects.create_user(
            username="kanban_move_other",
            password="testpass123",
        )

        self.task = Task.objects.create(
            user=self.user,
            title="Drag Test Task",
            status=Task.Status.PENDING,
            completed=False,
        )

        self.url = reverse(
            "kanban_move_task",
            args=[self.task.pk],
        )

        self.client.force_login(self.user)

    def test_move_to_completed(self):
        response = self.client.post(
            self.url,
            {"status": Task.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.COMPLETED,
        )

        self.assertTrue(self.task.completed)

    def test_move_back_to_pending(self):
        self.task.status = Task.Status.COMPLETED
        self.task.save()

        response = self.client.post(
            self.url,
            {"status": Task.Status.PENDING},
        )

        self.assertEqual(response.status_code, 200)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

        self.assertFalse(self.task.completed)

    def test_invalid_status(self):
        response = self.client.post(
            self.url,
            {"status": "unknown"},
        )

        self.assertEqual(response.status_code, 400)

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_other_user_cannot_move_task(self):
        self.client.force_login(self.other_user)

        response = self.client.post(
            self.url,
            {"status": Task.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 404)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.status,
            Task.Status.PENDING,
        )

    def test_get_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
class TaskDualUploadTests(TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        media_override = override_settings(
            MEDIA_ROOT=self.temp_dir.name
        )
        media_override.enable()
        self.addCleanup(media_override.disable)

        self.user = User.objects.create_user(
            username="dual_upload_user",
            password="testpass123",
        )

        self.client.force_login(self.user)

    def test_create_task_with_image_and_attachment(self):
        buffer = BytesIO()

        Image.new(
            "RGB",
            (100, 100),
        ).save(buffer, format="PNG")

        image = SimpleUploadedFile(
            "test_image.png",
            buffer.getvalue(),
            content_type="image/png",
        )

        attachment = SimpleUploadedFile(
            "test_document.pdf",
            b"%PDF-1.4\nTest document",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("task_create"),
            {
                "title": "Dual Upload Test",
                "description": "Testing two uploads",
                "status": Task.Status.PENDING,
                "priority": Task.Priority.MEDIUM,
                "image": image,
                "attachment": attachment,
            },
        )

        if response.status_code == 200:
            print(response.context["form"].errors)

        self.assertRedirects(
            response,
            reverse("task_list"),
        )

        task = Task.objects.get(
            title="Dual Upload Test",
            user=self.user,
        )

        self.assertTrue(task.image.name)
        self.assertTrue(task.attachment.name)

        self.assertTrue(
            task.image.storage.exists(task.image.name)
        )

        self.assertTrue(
            task.attachment.storage.exists(
                task.attachment.name
            )
        )