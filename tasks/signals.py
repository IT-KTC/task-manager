from django.db.models.signals import (
    pre_save,
    post_save,
    post_delete,
)

from django.dispatch import receiver

from .models import Task

@receiver(
    pre_save, sender=Task
)
def before_task_save(sender, instance, **kwarg):
    instance.title = instance.title.strip()
    print("pre_save: Đang chuẩn bị lưu Task")
@receiver(post_save, sender=Task)
def after_task_save(sender, instance, created, **kwargs):

    if created:
        print(
            "post_save: Task mới được tạo:",
            instance.pk
        )

    else:
        print(
            "post_save: Task được cập nhật:",
            instance.pk
        )
@receiver(post_delete, sender=Task)
def after_task_delete(sender, instance, **kwargs):

    print(
        "post_delete: Task đã bị xóa:",
        instance.pk
    )