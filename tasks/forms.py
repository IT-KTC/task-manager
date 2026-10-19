from pathlib import Path

from django import forms
from PIL import Image, UnidentifiedImageError

from .models import Task


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
            raise forms.ValidationError( "file type is not allowed")
        if file.size > max_size:
            raise forms.ValidationError(
                "file must be smaller than 5 MB"
            )
        return file
