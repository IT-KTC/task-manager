
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Team, TeamMembership
from .permissions import (
    is_team_leader,
    is_team_member,
)
from .services import (
    add_team_member,
    create_team,
    remove_team_member,
)

User = get_user_model()


class TeamTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="team_leader",
            password="StrongPassword123!"
        )

    def test_create_team(self):
        team = create_team(
            user=self.user,
            name="Nhóm phát triển Task Manager"
        )

        self.assertEqual(
            team.created_by,
            self.user
        )

    def test_creator_becomes_leader(self):
        team = create_team(
            user=self.user,
            name="Nhóm lập trình"
        )

        membership = TeamMembership.objects.get(
            team=team,
            user=self.user
        )

        self.assertEqual(
            membership.role,
            TeamMembership.Role.LEADER
        )

    def test_cannot_duplicate_membership(self):
        team = create_team(
            user=self.user,
            name="Nhóm kiểm thử"
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            TeamMembership.objects.create(
                team=team,
                user=self.user,
                role=TeamMembership.Role.MEMBER
            )

class TeamPermissionTests(TestCase):

    def setUp(self):
        self.leader = User.objects.create_user(
            username="leader_test",
            password="StrongPassword123!"
        )

        self.member = User.objects.create_user(
            username="member_test",
            password="StrongPassword123!"
        )

        self.outsider = User.objects.create_user(
            username="outsider_test",
            password="StrongPassword123!"
        )

        self.team = create_team(
            user=self.leader,
            name="Nhóm kiểm thử phân quyền"
        )

    def test_creator_is_team_leader(self):
        self.assertTrue(
            is_team_leader(self.leader, self.team)
        )

    def test_outsider_is_not_member(self):
        self.assertFalse(
            is_team_member(self.outsider, self.team)
        )

    def test_leader_can_add_member(self):
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        self.assertTrue(
            is_team_member(self.member, self.team)
        )

        self.assertFalse(
            is_team_leader(self.member, self.team)
        )

    def test_outsider_cannot_add_member(self):
        with self.assertRaises(PermissionDenied):
            add_team_member(
                actor=self.outsider,
                team=self.team,
                new_member=self.member
            )

    def test_member_cannot_add_member(self):
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        with self.assertRaises(PermissionDenied):
            add_team_member(
                actor=self.member,
                team=self.team,
                new_member=self.outsider
            )

    def test_cannot_add_duplicate_member(self):
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        with self.assertRaises(ValidationError):
            add_team_member(
                actor=self.leader,
                team=self.team,
                new_member=self.member
            )

    def test_leader_can_remove_member(self):
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        remove_team_member(
            actor=self.leader,
            team=self.team,
            member=self.member
        )

        self.assertFalse(
            is_team_member(self.member, self.team)
        )

    def test_member_cannot_remove_member(self):
        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

        with self.assertRaises(PermissionDenied):
            remove_team_member(
                actor=self.member,
                team=self.team,
                member=self.leader
            )

    def test_leader_cannot_remove_self(self):
        with self.assertRaises(ValidationError):
            remove_team_member(
                actor=self.leader,
                team=self.team,
                member=self.leader
            )

class TeamWebTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="team_web_user",
            password="StrongPassword123!"
        )

    def test_team_list_requires_login(self):
        response = self.client.get(
            reverse("team_list")
        )

        self.assertEqual(response.status_code, 302)

    def test_user_can_create_team(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("team_create"),
            {
                "name": "Nhóm phát triển",
                "description": "Xây dựng Task Manager"
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TeamMembership.objects.filter(
                user=self.user,
                team__name="Nhóm phát triển",
                role=TeamMembership.Role.LEADER
            ).exists()
        )

    def test_invalid_form_does_not_create_team(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("team_create"),
            {"name": "   "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Team.objects.count(),
            0
        )

class TeamDetailTests(TestCase):

    def setUp(self):
        self.leader = User.objects.create_user(
            username="detail_leader",
            password="StrongPassword123!"
        )

        self.member = User.objects.create_user(
            username="detail_member",
            password="StrongPassword123!"
        )

        self.outsider = User.objects.create_user(
            username="detail_outsider",
            password="StrongPassword123!"
        )

        self.team = create_team(
            user=self.leader,
            name="Nhóm kiểm thử chi tiết"
        )

        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

    def test_leader_can_view_team(self):
        self.client.force_login(self.leader)

        response = self.client.get(
            reverse("team_detail", args=[self.team.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_member_can_view_team(self):
        self.client.force_login(self.member)

        response = self.client.get(
            reverse("team_detail", args=[self.team.pk])
        )

        self.assertEqual(response.status_code, 200)

    def test_outsider_cannot_view_team(self):
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse("team_detail", args=[self.team.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_cannot_view_team(self):
        response = self.client.get(
            reverse("team_detail", args=[self.team.pk])
        )

        self.assertEqual(response.status_code, 302)

    def test_team_detail_shows_members(self):
        self.client.force_login(self.leader)

        response = self.client.get(
            reverse("team_detail", args=[self.team.pk])
        )

        self.assertContains(response, "detail_leader")
        self.assertContains(response, "detail_member")
        self.assertNotContains(response, "detail_outsider")

class TeamMemberWebTests(TestCase):

    def setUp(self):
        self.leader = User.objects.create_user(
            username="web_leader",
            password="StrongPassword123!"
        )

        self.member = User.objects.create_user(
            username="web_member",
            password="StrongPassword123!"
        )

        self.new_user = User.objects.create_user(
            username="web_new_user",
            password="StrongPassword123!"
        )

        self.outsider = User.objects.create_user(
            username="web_outsider",
            password="StrongPassword123!"
        )

        self.team = create_team(
            user=self.leader,
            name="Nhóm thử nghiệm"
        )

        add_team_member(
            actor=self.leader,
            team=self.team,
            new_member=self.member
        )

    def test_leader_can_open_add_form(self):
        self.client.force_login(self.leader)

        response = self.client.get(
            reverse(
                "team_member_add",
                args=[self.team.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_leader_can_add_member(self):
        self.client.force_login(self.leader)

        response = self.client.post(
            reverse(
                "team_member_add",
                args=[self.team.pk]
            ),
            {"username": self.new_user.username}
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TeamMembership.objects.filter(
                team=self.team,
                user=self.new_user,
                role=TeamMembership.Role.MEMBER
            ).exists()
        )

    def test_member_cannot_add_member(self):
        self.client.force_login(self.member)

        response = self.client.post(
            reverse(
                "team_member_add",
                args=[self.team.pk]
            ),
            {"username": self.new_user.username}
        )

        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_add_member(self):
        self.client.force_login(self.outsider)

        response = self.client.post(
            reverse(
                "team_member_add",
                args=[self.team.pk]
            ),
            {"username": self.new_user.username}
        )

        self.assertEqual(response.status_code, 404)

    def test_duplicate_member_is_rejected(self):
        self.client.force_login(self.leader)

        response = self.client.post(
            reverse(
                "team_member_add",
                args=[self.team.pk]
            ),
            {"username": self.member.username}
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            TeamMembership.objects.filter(
                team=self.team,
                user=self.member
            ).count(),
            1
        )

    def test_leader_can_remove_member(self):
        self.client.force_login(self.leader)

        membership = TeamMembership.objects.get(
            team=self.team,
            user=self.member
        )

        response = self.client.post(
            reverse(
                "team_member_remove",
                args=[self.team.pk, membership.pk]
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            TeamMembership.objects.filter(
                pk=membership.pk
            ).exists()
        )

    def test_member_cannot_remove_member(self):
        self.client.force_login(self.member)

        membership = TeamMembership.objects.get(
            team=self.team,
            user=self.member
        )

        response = self.client.post(
            reverse(
                "team_member_remove",
                args=[self.team.pk, membership.pk]
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_cannot_remove_team_leader(self):
        self.client.force_login(self.leader)

        membership = TeamMembership.objects.get(
            team=self.team,
            user=self.leader
        )

        response = self.client.post(
            reverse(
                "team_member_remove",
                args=[self.team.pk, membership.pk]
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            TeamMembership.objects.filter(
                pk=membership.pk
            ).exists()
        )

    def test_remove_requires_post(self):
        self.client.force_login(self.leader)

        membership = TeamMembership.objects.get(
            team=self.team,
            user=self.member
        )

        response = self.client.get(
            reverse(
                "team_member_remove",
                args=[self.team.pk, membership.pk]
            )
        )

        self.assertEqual(response.status_code, 405)
