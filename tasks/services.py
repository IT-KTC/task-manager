from django.core.exceptions import ValidationError
from django.db import transaction

from teams.models import TeamMembership
from teams.permissions import require_team_leader

from .models import (
    Notification,
    Task,
    TaskActivity,
)


def move_task_to_status(task, new_status):
    if new_status not in Task.Status.values:
        raise ValidationError("Invalid task status.")
    task.status = new_status
    task.completed = (new_status == Task.Status.COMPLETED)
    task.save(
        update_fields = [
            "status",
            "completed",
            "updated_at",
        ]
    )
    return task

def change_task_status(task, new_status):
    allowed_transitions = {
        Task.Status.PENDING: (Task.Status.IN_PROGRESS,),
        Task.Status.IN_PROGRESS: (Task.Status.COMPLETED,),
        Task.Status.COMPLETED: (Task.Status.PENDING,),
    }

    # Nếu đã ở trạng thái yêu cầu thì không cần cập nhật
    if new_status == task.status:
        return task

    allowed = allowed_transitions.get(task.status, ())

    if new_status not in allowed:
        raise ValidationError(
            "Invalid task status transition."
        )

    task.status = new_status

    task.completed = (
        new_status == Task.Status.COMPLETED
    )

    task.save(
        update_fields=[
            "status",
            "completed",
            "updated_at",
        ]
    )

    return task
def complete_task(task):
    task.completed = True
    task.status = "completed"
    task.save(
        update_fields= [
            "completed",
            "status",
            "updated_at"
        ]
    )
    return task

@transaction.atomic
def assign_task(*, actor, task, assignee):
    
    ask = (
    Task.objects
    .select_for_update()
    .get(pk=task.pk)
)

    if task.team_id is None:
        raise ValidationError(
            "Không thể phân công công việc cá nhân."
        )

    require_team_leader(actor, task.team)

    if assignee is not None:

        if not assignee.is_active:
            raise ValidationError(
                "Không thể giao việc cho tài khoản đã bị vô hiệu hóa."
            )

        is_member = TeamMembership.objects.filter(
            team_id=task.team_id,
            user_id=assignee.pk,
            user__is_active=True,
        ).exists()

        if not is_member:
            raise ValidationError(
                "Người được giao không thuộc nhóm này."
            )

    new_assignee_id = (
        assignee.pk if assignee is not None else None
    )

    if task.assignee_id == new_assignee_id:
        return task

    old_assignee = task.assignee

    if assignee is None:
        action = TaskActivity.Action.UNASSIGNED
        description = "Đã bỏ phân công công việc."

    elif old_assignee is None:
        action = TaskActivity.Action.ASSIGNED
        description = (
            f"Đã giao công việc cho {assignee.username}."
        )

    else:
        action = TaskActivity.Action.REASSIGNED
        description = (
            f"Đã chuyển công việc từ "
            f"{old_assignee.username} "
            f"sang {assignee.username}."
        )


    task.assignee = assignee
    task._activity_actor = actor

    task.save(
        update_fields=["assignee", "updated_at"]
    )


    TaskActivity.objects.create(
        task=task,
        actor=actor,
        action=action,
        description=description,
        changed_fields=["assignee"],
    )
    if assignee is not None:
        Notification.objects.create(
            user=assignee,
            task=task,
            message=(
                f'Bạn được giao công việc "{task.title}".'
            ),
        )

  
    if (
        old_assignee is not None
        and old_assignee.pk != new_assignee_id
    ):
        Notification.objects.create(
            user=old_assignee,
            task=task,
            message=(
                f'Công việc "{task.title}" '
                "không còn được giao cho bạn."
            ),
        )

    return task
