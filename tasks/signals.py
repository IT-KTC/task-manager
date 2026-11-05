
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Notification, Task, TaskActivity


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
            "attachment",
            "image",
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
            "attachment",
            "image",
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

@receiver(
    post_save,
    sender=Task,
    dispatch_uid="tasks.log_task_activity",
)
def log_task_activity(
    sender,
    instance,
    created,
    update_fields=None,
    **kwargs,
):
    actor = getattr(
        instance,
        "_activity_actor",
        None
    )

    if created:
        TaskActivity.objects.create(
            task=instance,
            actor=actor,
            action=TaskActivity.Action.CREATED,
            description="Đã tạo công việc.",
            changed_fields=[],
        )
        return

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
        "attachment",
        "image",
    )

    changed = []

    for field in tracked_fields:
        if update_fields is not None and field not in update_fields:
            continue

        old_value = previous.get(field)
        new_value = getattr(instance, field)

        if str(old_value or "") != str(new_value or ""):
            changed.append(field)

    if not changed:
        return

    labels = {
        "title": "tiêu đề",
        "description": "mô tả",
        "priority": "mức độ ưu tiên",
        "due_date": "hạn hoàn thành",
        "attachment": "tệp đính kèm",
        "image": "hình ảnh",
    }

    if "status" in changed:
        status_labels = dict(Task.Status.choices)

        old_status = status_labels.get(
            previous["status"],
            previous["status"],
        )

        new_status = instance.get_status_display()

        action = TaskActivity.Action.STATUS_CHANGED

        description = (
            f'Đã chuyển trạng thái từ "{old_status}" '
            f'sang "{new_status}".'
        )

        other_fields = [
            labels[field]
            for field in changed
            if field != "status"
        ]

        if other_fields:
            description += (
                " Đồng thời cập nhật: "
                + ", ".join(other_fields)
                + "."
            )

    else:
        action = TaskActivity.Action.UPDATED

        description = (
            "Đã cập nhật: "
            + ", ".join(labels[field] for field in changed)
            + "."
        )

    TaskActivity.objects.create(
        task=instance,
        actor=actor,
        action=action,
        description=description,
        changed_fields=changed,
    )
