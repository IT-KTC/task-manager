from django import forms
from .models import Task 
from pathlib import Path


class TaskForm(forms.ModelForm):
    class Meta: 
        model = Task 
        fields = [
            "title",
            "description",
            "status",
            "completed",
            "attachment",
            "image"
        ]
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
