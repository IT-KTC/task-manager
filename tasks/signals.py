
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Task


@receiver(pre_save, sender=Task)
def before_task_save(sender, instance, **kwargs):
    instance.title = instance.title.strip()

    if instance._state.adding:
        instance._previous_values = None
        return

    instance._previous_values = (
        Task.objects.filter(pk=instance.pk)
        .values(
            "title",
            "description",
            "status",
            "priority",
            "due_date",
        )
        .first()
    )


@receiver(post_save, sender=Task)
def notify_task_change(
    sender,
    instance,
    created,
    update_fields=None,
    **kwargs,
):
    if created:
        message = (
            f'Công việc "{instance.title}" '
            "đã được tạo."
        )
    else:
        previous = getattr(
            instance,
            "_previous_values",
            None
        )

        if previous is None:
            return

        tracked_fields = (
            "title",
            "description",
            "status",
            "priority",
            "due_date",
        )

        changed_fields = [
            field
            for field in tracked_fields
            if (
                update_fields is None
                or field in update_fields
            )
            and previous[field] != getattr(instance, field)
        ]

        if not changed_fields:
            return

        if "status" in changed_fields:
            message = (
                f'Công việc "{instance.title}" '
                "đã chuyển sang trạng thái "
                f'"{instance.get_status_display()}".'
            )
        else:
            message = (
                f'Công việc "{instance.title}" '
                "đã được cập nhật."
            )

    Notification.objects.create(
        user=instance.user,
        task=instance,
        message=message,
    )
