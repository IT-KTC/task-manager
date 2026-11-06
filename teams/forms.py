
from django import forms


class TeamCreateForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        label="Tên nhóm",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nhập tên nhóm"
            }
        )
    )

    description = forms.CharField(
        required=False,
        label="Mô tả",
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Mô tả về nhóm"
            }
        )
    )

class TeamMemberAddForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Tên đăng nhập",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Nhập username của thành viên",
                "autocomplete": "off",
            }
        )
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if not username:
            raise forms.ValidationError(
                "Vui lòng nhập tên đăng nhập."
            )

        return username
