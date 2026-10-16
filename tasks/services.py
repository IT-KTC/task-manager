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
