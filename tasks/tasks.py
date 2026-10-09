from celery import shared_task

from .models import Task
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


@shared_task
def resize_task_image(task_id):
    task = Task.objects.get(pk = task.id)
    if not task.image:
        return 
    task.image.open("rb")
    image = Image.open(
        task.image
    )
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    resized_image = ImageOps.fit(image,  (800, 800))
    buffer = BytesIO()
    resized_image.save(
        buffer,
        format="JPEG",
        quality = 85
    )
    old_name = task.image.name
    filename = (Path(old_name).stem
        + "_800x800.jpg"
    )
    new_name = (
        "task_images/"
        + filename
    )
    task.image.storage.delete(old_name)
    task.image.save(
        new_name,
        ContentFile(
            buffer.getvalue()
        ),
        save=False
    )
    task.save(
        update_fields=["image"]
    )


@shared_task
def process_task(task_id):

    task = Task.objects.get(
        pk=task_id
    )

    print(
        f"processing: {task.title}"
    )