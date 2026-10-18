import logging
from io import BytesIO
from pathlib import Path

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image, ImageOps

from .models import Task

logger = logging.getLogger(__name__)


@shared_task
def resize_task_image(task_id):
    task = Task.objects.filter(pk=task_id).first()

    if task is None:
        logger.warning(
            "Task %s no longer exists",
            task_id,
        )
        return

    if not task.image:
        return

    original_name = task.image.name

    # Không xử lý lại ảnh đã resize
    if original_name.startswith("task_images/processed/"):
        return

    storage = task.image.storage

    # Đọc ảnh gốc
    with storage.open(original_name, "rb") as file, Image.open(file) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")

        resized_image = ImageOps.fit(
            image,
            (800, 800),
        )

        buffer = BytesIO()
        resized_image.save(
            buffer,
            format="JPEG",
            quality=85,
        )

    # Lưu ảnh mới trước khi cập nhật database
    filename = (
        f"{Path(original_name).stem}_800x800.jpg"
    )

    new_name = storage.save(
        f"task_images/processed/{filename}",
        ContentFile(buffer.getvalue()),
    )

    try:
        # Chỉ cập nhật nếu ảnh chưa bị thay đổi
        updated = Task.objects.filter(
            pk=task_id,
            image=original_name,
        ).update(
            image=new_name,
            updated_at=timezone.now(),
        )

    except Exception:
        storage.delete(new_name)
        raise

    if not updated:
        # Task đã bị xóa hoặc thay ảnh trong lúc xử lý
        storage.delete(new_name)
        logger.info(
            "Image changed while processing Task %s",
            task_id,
        )
        return

    logger.info(
        "Resized image for Task %s: %s",
        task_id,
        new_name,
    )

@shared_task
def process_task(task_id):

    task = Task.objects.get(
        pk=task_id
    )

    print(
        f"processing: {task.title}"
    )