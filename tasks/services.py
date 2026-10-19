from django.core.exceptions import ValidationError

from .models import Task


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
