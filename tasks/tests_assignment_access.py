
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from tasks.models import Notification, Task, TaskComment
from teams.models import TeamMembership
from teams.services import add_team_member, create_team

User = get_user_model()


class AssignedTaskAccessTests(TestCase):

    def setUp(self):
        # Dùng thư mục tạm để kiểm thử file upload.
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)

        media_settings = override_settings(
            MEDIA_ROOT=self.temp_media.name
        )
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.leader = User.objects.create_user(
            username="access_leader",
            password="StrongPassword123!"
        )

        self.member = User.objects.create_user(
            username="access_member",
            password="StrongPassword123!"
        )

        self.outsider = User.objects.create_user(
            username="access_outsider",
            password="StrongPassword123!"
        )

        self.team = create_team(
            user=self.leader,
            name="Nhóm kiểm thử quyền Task"
        )

        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        self.task = Task.objects.create(
            user=self.leader,
            team=self.team,
            assignee=self.member,
            title="Công việc được giao"
        )

    def test_assignee_can_view_task(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse("task_detail", args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_view_task(self):
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse("task_detail", args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_assignee_cannot_edit_task(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("task_update", args=[self.task.pk]),
            {"title": "Thay đổi trái phép"}
        )

        self.assertEqual(response.status_code, 404)

        self.task.refresh_from_db()
        self.assertEqual(
            self.task.title,
            "Công việc được giao"
        )

    def test_assignee_cannot_delete_task(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse("task_delete", args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Task.objects.filter(pk=self.task.pk).exists()
        )

    def test_assignee_cannot_change_status(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "task_quick_status",
                args=[self.task.pk]
            ),
            {"status": Task.Status.IN_PROGRESS}
        )

        self.assertEqual(response.status_code, 404)

    def test_assignee_sees_task_in_list(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse("task_list")
        )

        self.assertContains(
            response,
            "Công việc được giao"
        )

    def test_assignee_can_comment(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "task_comment_add",
                args=[self.task.pk]
            ),
            {"body": "Em đã nhận công việc."}
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TaskComment.objects.filter(
                task=self.task,
                author=self.member
            ).exists()
        )

    def test_assignee_can_view_timeline(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "task_timeline",
                args=[self.task.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_assignee_can_download_attachment(self):
        self.task.attachment.save(
            "private.pdf",
            ContentFile(b"%PDF-1.4 test"),
            save=True
        )

        self.client.force_login(self.member)

        response = self.client.get(
            reverse(
                "task_download",
                args=[self.task.pk]
            )
        )

        self.assertEqual(response.status_code, 200)
        response.close()

    def test_outsider_cannot_download_attachment(self):
        self.task.attachment.save(
            "private.pdf",
            ContentFile(b"%PDF-1.4 test"),
            save=True
        )

        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse(
                "task_download",
                args=[self.task.pk]
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_removed_member_loses_access(self):
        TeamMembership.objects.filter(
            team=self.team,
            user=self.member
        ).delete()

        self.client.force_login(self.member)

        response = self.client.get(
            reverse("task_detail", args=[self.task.pk])
        )

        self.assertEqual(response.status_code, 404)

   
    def test_notification_opens_assigned_task(self):
        notification = Notification.objects.create(
            user=self.member,
            task=self.task,
            message="Bạn được giao công việc."
        )

        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "notification_mark_read",
                args=[notification.pk]
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "task_detail",
                args=[self.task.pk]
            )
        )

    def test_personal_task_still_private(self):
        personal_task = Task.objects.create(
            user=self.leader,
            title="Công việc cá nhân"
        )

        self.assertTrue(
            Task.objects.visible_to(
                self.leader
            ).filter(pk=personal_task.pk).exists()
        )

        self.assertFalse(
            Task.objects.visible_to(
                self.member
            ).filter(pk=personal_task.pk).exists()
        )
