
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from tasks.models import (
    Notification,
    Task,
    TaskActivity,
)
from tasks.services import assign_task
from teams.services import add_team_member, create_team

User = get_user_model()


class TaskAssignmentServiceTests(TestCase):

    def setUp(self):
        self.leader = User.objects.create_user(
            username="assignment_leader_service",
            password="StrongPassword123!"
        )

        self.member = User.objects.create_user(
            username="assignment_member_service",
            password="StrongPassword123!"
        )

        self.member2 = User.objects.create_user(
            username="assignment_member2_service",
            password="StrongPassword123!"
        )

        self.outsider = User.objects.create_user(
            username="assignment_outsider_service",
            password="StrongPassword123!"
        )

        self.team = create_team(
            user=self.leader,
            name="Nhóm phát triển"
        )

        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member2
        )

        self.task = Task.objects.create(
            user=self.leader,
            team=self.team,
            title="Thiết kế giao diện"
        )

    def test_leader_can_assign_task(self):
        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.assignee,
            self.member
        )

    def test_member_cannot_assign_task(self):
        with self.assertRaises(PermissionDenied):
            assign_task(
                actor=self.member,
                task=self.task,
                assignee=self.member2
            )

    def test_outsider_cannot_assign_task(self):
        with self.assertRaises(PermissionDenied):
            assign_task(
                actor=self.outsider,
                task=self.task,
                assignee=self.member
            )

    def test_cannot_assign_to_outsider(self):
        with self.assertRaises(ValidationError):
            assign_task(
                actor=self.leader,
                task=self.task,
                assignee=self.outsider
            )

    def test_cannot_assign_personal_task(self):
        personal_task = Task.objects.create(
            user=self.leader,
            title="Công việc cá nhân"
        )

        with self.assertRaises(ValidationError):
            assign_task(
                actor=self.leader,
                task=personal_task,
                assignee=self.member
            )

    def test_assignment_creates_activity(self):
        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        activity = TaskActivity.objects.get(
            task=self.task,
            action=TaskActivity.Action.ASSIGNED
        )

        self.assertEqual(
            activity.actor,
            self.leader
        )

    def test_assignment_sends_notification(self):
        before = Notification.objects.filter(
            user=self.member
        ).count()

        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        after = Notification.objects.filter(
            user=self.member
        ).count()

        self.assertEqual(after, before + 1)

    def test_reassignment(self):
        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member2
        )

        self.task.refresh_from_db()

        self.assertEqual(
            self.task.assignee,
            self.member2
        )

        self.assertTrue(
            TaskActivity.objects.filter(
                task=self.task,
                action=TaskActivity.Action.REASSIGNED
            ).exists()
        )

    def test_same_assignee_does_not_duplicate(self):
        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        before = TaskActivity.objects.filter(
            task=self.task
        ).count()

        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        after = TaskActivity.objects.filter(
            task=self.task
        ).count()

        self.assertEqual(before, after)

    def test_unassign_task(self):
        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=self.member
        )

        assign_task(
            actor=self.leader,
            task=self.task,
            assignee=None
        )

        self.task.refresh_from_db()

        self.assertIsNone(self.task.assignee)

        self.assertTrue(
            TaskActivity.objects.filter(
                task=self.task,
                action=TaskActivity.Action.UNASSIGNED
            ).exists()
        )
