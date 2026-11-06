
from django.contrib.auth import get_user_model
from django.test import TestCase

from tasks.models import Task
from teams.services import (
    add_team_member,
    create_team,
)

User = get_user_model()


class TaskAssignmentModelTests(TestCase):

    def setUp(self):
        # Tạo tài khoản trưởng nhóm
        self.leader = User.objects.create_user(
            username="assignment_leader",
            password="StrongPassword123!"
        )

        # Tạo tài khoản thành viên
        self.member = User.objects.create_user(
            username="assignment_member",
            password="StrongPassword123!"
        )

        # Tạo nhóm
        self.team = create_team(
            user=self.leader,
            name="Team Development"
        )

        # Thêm thành viên vào nhóm
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

    def test_personal_task_still_works(self):
        task = Task.objects.create(
            user=self.member,
            title="Công việc cá nhân"
        )

        self.assertIsNone(task.team)
        self.assertIsNone(task.assignee)

    def test_team_task_has_assignee(self):
        task = Task.objects.create(
            user=self.leader,
            team=self.team,
            assignee=self.member,
            title="Thiết kế giao diện"
        )

        self.assertEqual(
            task.user,
            self.leader
        )

        self.assertEqual(
            task.team,
            self.team
        )

        self.assertEqual(
            task.assignee,
            self.member
        )

    def test_team_task_can_be_unassigned(self):
        task = Task.objects.create(
            user=self.leader,
            team=self.team,
            title="Công việc chưa phân công"
        )

        self.assertIsNone(task.assignee)
        self.assertEqual(task.team, self.team)
