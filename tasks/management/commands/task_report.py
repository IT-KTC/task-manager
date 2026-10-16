import logging

from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db.models import Count, Q

from tasks.models import Task


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = "Thống kê Task toàn hệ thống hoặc theo User"

    def add_arguments(self, parser):

        parser.add_argument(
            "--user-id",
            type=int,
            help="Chỉ thống kê Task của User ID này",
        )

    def handle(self, *args, **options):

        user_id = options["user_id"]

        queryset = Task.objects.all()

        if user_id is not None:

            User = get_user_model()

            if not User.objects.filter(
                pk=user_id
            ).exists():
                raise CommandError(
                    f"User ID {user_id} không tồn tại"
                )

            queryset = queryset.filter(
                user_id=user_id
            )

        result = queryset.aggregate(
            total=Count("id"),
            completed=Count(
                "id",
                filter=Q(completed=True),
            ),
            incomplete=Count(
                "id",
                filter=Q(completed=False),
            ),
        )

        self.stdout.write("=== TASK REPORT ===")

        if user_id is not None:
            self.stdout.write(
                f"User ID: {user_id}"
            )
        else:
            self.stdout.write(
                "Phạm vi: Toàn hệ thống"
            )

        self.stdout.write(
            f"Tổng số Task: {result['total']}"
        )
        self.stdout.write(
            f"Đã hoàn thành: {result['completed']}"
        )
        self.stdout.write(
            f"Chưa hoàn thành: {result['incomplete']}"
        )

        logger.info(
            "Generated task report, user_id=%s, total=%s",
            user_id,
            result["total"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Report hoàn thành!"
            )
        )