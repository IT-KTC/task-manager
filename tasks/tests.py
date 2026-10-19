from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
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