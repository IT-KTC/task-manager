from pathlib import Path

from django import forms
from PIL import Image, UnidentifiedImageError

from .models import Task, TaskComment


class TaskForm(forms.ModelForm):
    class Meta: 
        model = Task 
        fields = [  # noqa: RUF012
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "attachment",
            "image",
        ]
        widgets = {  # noqa: RUF012
            "due_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }
        labels = {  # noqa: RUF012
            "title": "Tên công việc",
            "description": "Mô tả",
            "status": "Trạng thái",
            "priority": "Mức độ ưu tiên",
            "due_date": "Hạn hoàn thành",
            "attachment": "Tệp đính kèm",
            "image": "Hình ảnh",
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        max_size = 5 * 1024 * 1024
        max_pixels = 10_000_000

        if image.size > max_size:
            raise forms.ValidationError(
                "Image must be smaller than 5 MB."
            )

        try:
            image.seek(0)

            with Image.open(image) as img:
                if img.format not in ("JPEG", "PNG", "WEBP"):
                    raise forms.ValidationError(
                        "Only JPEG, PNG and WEBP are allowed."
                    )

                if img.width * img.height > max_pixels:
                    raise forms.ValidationError(
                        "Image dimensions are too large."
                    )

                img.verify()

        except (UnidentifiedImageError, OSError) as exc:
            raise forms.ValidationError(
                "Invalid image file."
            ) from exc

        finally:
            image.seek(0)

        return image
    def clean_attachment(self):
        max_size = 5 * 1024 * 1024
        file = self.cleaned_data.get(
            "attachment"
        )
        if not file:
            return file
        allowed_extensions = [
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".docx",
        ]
        extension = Path(
            file.name
        ).suffix.lower()
        if extension not in allowed_extensions: 
            raise forms.ValidationError( "Chỉ chấp nhận tệp PDF, JPG, PNG hoặc DOCX.")
        if file.size > max_size:
            raise forms.ValidationError(
                "Tệp đính kèm không được vượt quá 5 MB."
            )
        return file

class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["body"]  # noqa: RUF012

        labels = {  # noqa: RUF012
            "body": "Nội dung bình luận",
        }

        widgets = {  # noqa: RUF012
            "body": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 2000,
                    "placeholder": "Viết bình luận của bạn...",
                }
            ),
        }

    def clean_body(self):
        body = self.cleaned_data["body"].strip()

        if not body:
            raise forms.ValidationError(
                "Vui lòng nhập nội dung bình luận."
            )

        return body
