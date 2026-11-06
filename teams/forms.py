
from django import forms
from django.contrib.auth import get_user_model

from tasks.forms import TaskForm

User = get_user_model()
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

class TeamTaskCreateForm(TaskForm):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Chưa phân công",
        label="Người phụ trách",
    )

    def __init__(self, *args, team, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assignee"].queryset = (
            User.objects.filter(
                team_memberships__team=team,
                is_active=True,
            )
            .distinct()
            .order_by("username")
        )


class TeamTaskAssignForm(forms.Form):
    assignee = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        empty_label="Chưa phân công",
        label="Chọn người phụ trách",
    )

    def __init__(self, *args, team, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["assignee"].queryset = (
            User.objects.filter(
                team_memberships__team=team,
                is_active=True,
            )
            .distinct()
            .order_by("username")
        )
