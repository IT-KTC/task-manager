
from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile

from .models import UserProfile

User = get_user_model()


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [  # noqa: RUF012
            "username",
            "first_name",
            "last_name",
            "email",
        ]

        labels = {  # noqa: RUF012
            "username": "Tên đăng nhập",
            "first_name": "Tên",
            "last_name": "Họ",
            "email": "Email",
        }

        widgets = {  # noqa: RUF012
            "email": forms.EmailInput(),
        }

    def clean_email(self):
        email = self.cleaned_data.get(
            "email", ""
        ).strip()

        if email and User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "Email này đã được sử dụng."
            )

        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile

        fields = [  # noqa: RUF012
            "avatar",
            "phone",
            "bio",
        ]

        labels = {  # noqa: RUF012
            "avatar": "Ảnh đại diện",
            "phone": "Số điện thoại",
            "bio": "Giới thiệu bản thân",
        }

        widgets = {  # noqa: RUF012
            "avatar": forms.FileInput(
                attrs={
                    "accept": (
                        "image/jpeg,image/png,image/webp"
                    )
                }
            ),
            "phone": forms.TextInput(
                attrs={"type": "tel"}
            ),
            "bio": forms.Textarea(
                attrs={"rows": 4}
            ),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")

        # Không có ảnh mới: giữ ảnh hiện tại.
        if not isinstance(avatar, UploadedFile):
            return avatar

        if avatar.size > 2 * 1024 * 1024:
            raise forms.ValidationError(
                "Ảnh không được vượt quá 2 MB."
            )

        allowed = {
            "JPEG": {".jpg", ".jpeg"},
            "PNG": {".png"},
            "WEBP": {".webp"},
        }

        image = avatar.image
        extension = Path(avatar.name).suffix.lower()

        if extension not in allowed.get(
            image.format, set()
        ):
            raise forms.ValidationError(
                "Chỉ chấp nhận ảnh JPG, PNG hoặc WebP hợp lệ."
            )

        if image.width * image.height > 8_000_000:
            raise forms.ValidationError(
                "Kích thước ảnh quá lớn."
            )

        return avatar
