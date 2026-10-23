"""Tests for the opt-in local seed command.

Run: python manage.py test tasks.tests_seed_demo -v 2
"""

import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from tasks.models import Task

TEST_ENV = {
    "DJANGO_ENV": "test",
    "TASK_MANAGER_DEMO_PASSWORD": "LocalOnlyDemo#2026!",
}


class SeedDemoCommandTests(TestCase):
    def run_seed(self, *args, password=None):
        env = dict(TEST_ENV)
        if password is not None:
            env["TASK_MANAGER_DEMO_PASSWORD"] = password
        with patch.dict(os.environ, env):
            call_command("seed_demo", *args, verbosity=0)

    def test_creates_six_accounts_and_eight_tasks(self):
        self.run_seed()
        User = get_user_model()
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), 6)
        self.assertEqual(Task.objects.filter(title__startswith="[DEMO]").count(), 8)
        admin = User.objects.get(username="demo_admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.check_password(TEST_ENV["TASK_MANAGER_DEMO_PASSWORD"]))
        staff = User.objects.get(username="demo_staff")
        self.assertTrue(staff.is_staff)
        self.assertFalse(staff.is_superuser)
        self.assertTrue(staff.has_perm("auth.view_user"))
        self.assertTrue(staff.has_perm("tasks.view_task"))
        self.assertFalse(staff.has_perm("tasks.change_task"))
        self.assertTrue(staff.groups.filter(name="DEMO_READ_ONLY").exists())
        self.assertFalse(User.objects.get(username="demo_inactive").is_active)
        self.assertFalse(Task.objects.filter(user__username="demo_empty").exists())

    def test_is_idempotent(self):
        self.run_seed()
        self.run_seed()
        User = get_user_model()
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), 6)
        self.assertEqual(Task.objects.filter(title__startswith="[DEMO]").count(), 8)
        self.assertEqual(Group.objects.filter(name="DEMO_READ_ONLY").count(), 1)

    def test_password_is_preserved_without_explicit_reset(self):
        self.run_seed()
        original = TEST_ENV["TASK_MANAGER_DEMO_PASSWORD"]
        new = "LocalOnlyChanged#2026!"
        self.run_seed(password=new)
        user = get_user_model().objects.get(username="demo_alice")
        self.assertTrue(user.check_password(original))
        self.run_seed("--reset-password", password=new)
        user.refresh_from_db()
        self.assertTrue(user.check_password(new))

    def test_refuses_nonlocal_environment(self):
        from django.core.management.base import CommandError
        env = dict(TEST_ENV)
        env["DJANGO_ENV"] = "pythonanywhere"
        with patch.dict(os.environ, env):  # noqa: SIM117
            with self.assertRaises(CommandError):
                call_command("seed_demo", verbosity=0)
