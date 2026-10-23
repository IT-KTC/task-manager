"""Create repeatable, non-production test users and representative Task records.

Usage:
    TASK_MANAGER_DEMO_PASSWORD=... python manage.py seed_demo
    TASK_MANAGER_DEMO_PASSWORD=... python manage.py seed_demo --reset-password

This command refuses non-local DJANGO_ENV values, never deletes or changes
existing Task objects, and preserves existing user roles/profile fields.
"""

import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from tasks.models import Task

TEST_USERS = (
    {
        "username": "demo_admin",
        "first_name": "Admin",
        "last_name": "Demo",
        "email": "demo_admin@example.invalid",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    },
    {
        "username": "demo_staff",
        "first_name": "Staff",
        "last_name": "Demo",
        "email": "demo_staff@example.invalid",
        "is_staff": True,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "demo_alice",
        "first_name": "Alice",
        "last_name": "Demo",
        "email": "demo_alice@example.invalid",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "demo_bob",
        "first_name": "Bob",
        "last_name": "Demo",
        "email": "demo_bob@example.invalid",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "demo_empty",
        "first_name": "Empty",
        "last_name": "Demo",
        "email": "demo_empty@example.invalid",
        "is_staff": False,
        "is_superuser": False,
        "is_active": True,
    },
    {
        "username": "demo_inactive",
        "first_name": "Inactive",
        "last_name": "Demo",
        "email": "demo_inactive@example.invalid",
        "is_staff": False,
        "is_superuser": False,
        "is_active": False,
    },
)

# offset days are calculated from the date the command is first run.
TASK_FIXTURES = (
    ("demo_alice", "[DEMO] Tìm hiểu Django ORM", "pending", "high", -2),
    ("demo_alice", "[DEMO] Viết API Task", "in_progress", "high", 2),
    ("demo_alice", "[DEMO] Hoàn thiện trang đăng nhập", "completed", "medium", -1),
    ("demo_alice", "[DEMO] Lập kế hoạch Sprint", "pending", "low", None),
    ("demo_bob", "[DEMO] Kiểm tra user ownership", "completed", "high", 0),
    ("demo_bob", "[DEMO] Thiết kế Kanban", "in_progress", "medium", 7),
    ("demo_bob", "[DEMO] Viết unit test", "pending", "medium", 1),
    ("demo_bob", "[DEMO] Kiểm tra task quá hạn", "pending", "low", -3),
)


class Command(BaseCommand):
    help = "Seed 6 test accounts and 8 sample Tasks for local development only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset passwords of existing demo_* accounts to the environment value.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        environment = os.environ.get("DJANGO_ENV", "local").strip().lower()
        if environment not in {"local", "development", "test"}:
            raise CommandError(
                "Refusing to seed outside local/development/test. "
                "Set DJANGO_ENV=local only on an isolated development database."
            )

        password = os.environ.get("TASK_MANAGER_DEMO_PASSWORD", "")
        if (
            len(password) < 12
            or password.strip() != password
            or password.lower().startswith(("replace", "changeme", "example"))
            or "<" in password
            or ">" in password
        ):
            raise CommandError(
                "Set TASK_MANAGER_DEMO_PASSWORD in .env to a non-placeholder "
                "local-only password of at least 12 characters."
            )

        User = get_user_model()
        user_map = {}
        new_users = 0
        new_tasks = 0

        for fixture in TEST_USERS:
            username = fixture["username"]
            existing = User.objects.filter(username=username).first()
            if existing is None:
                user = User(**fixture)
                user.set_password(password)
                user.save()
                new_users += 1
            else:
                user = existing
                if options["reset_password"]:
                    user.set_password(password)
                    user.save(update_fields=["password"])
                # Do not alter existing role, active flag, names or e-mail.
            user_map[username] = user

        # Only add read permissions. Do not give demo_staff change/delete permissions.
        UserModel = get_user_model()
        view_user_code = f"view_{UserModel._meta.model_name}"
        view_task_code = f"view_{Task._meta.model_name}"
        try:
            view_user_permission = Permission.objects.get(
                content_type__app_label=UserModel._meta.app_label,
                content_type__model=UserModel._meta.model_name,
                codename=view_user_code,
            )
            view_task_permission = Permission.objects.get(
                content_type__app_label=Task._meta.app_label,
                content_type__model=Task._meta.model_name,
                codename=view_task_code,
            )
        except Permission.DoesNotExist as exc:
            raise CommandError(
                "Permissions unavailable. Run python manage.py migrate first."
            ) from exc

        group, _ = Group.objects.get_or_create(name="DEMO_READ_ONLY")
        group.permissions.add(view_user_permission, view_task_permission)
        user_map["demo_staff"].groups.add(group)

        today = timezone.localdate()
        for username, title, status, priority, due_offset in TASK_FIXTURES:
            due_date = None if due_offset is None else today + timedelta(days=due_offset)
            _, created = Task.objects.get_or_create(
                user=user_map[username],
                title=title,
                defaults={
                    "description": "Dữ liệu DEMO tự động tạo để thử chức năng Task Manager.",
                    "status": status,
                    "priority": priority,
                    "due_date": due_date,
                },
            )
            if created:
                new_tasks += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed completed: {new_users} new users, {new_tasks} new Tasks."
            )
        )
        self.stdout.write(
            "Accounts: " + ", ".join(u["username"] for u in TEST_USERS)
        )
        self.stdout.write("Password: from TASK_MANAGER_DEMO_PASSWORD (not printed).")
        self.stdout.write(
            "Existing usernames, permissions, passwords and Tasks are preserved "
            "unless --reset-password is specified (passwords only)."
        )
