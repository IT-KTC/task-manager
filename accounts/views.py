from pathlib import Path

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UserInfoForm, UserProfileForm
from .models import UserProfile
from .security import login_rate_limit

# Create your views here.



def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "Đăng xuất thành công."
        )

        return redirect("login")

@login_rate_limit
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()

            login(request, user)

            messages.success(
                request,
                "Đăng nhập thành công."
            )

        
            if user.is_active and user.is_superuser:
                return redirect("admin_dashboard")

    
            return redirect("task_list")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "accounts/login.html",
        {"form": form}
    )


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Đăng ký thành công. Hãy đăng nhập để tiếp tục."
            )
            return redirect("login")
    else: 
        form = UserCreationForm()

    context = {
        "form": form
    }
    return render(request, "accounts/register.html", context)

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        user_form = UserInfoForm(
            request.POST,
            instance=request.user
        )

        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if (
            user_form.is_valid()
            and profile_form.is_valid()
        ):
            old_avatar = (
                profile.avatar.name
                if profile.avatar else None
            )

            with transaction.atomic():
                user_form.save()
                profile_form.save()

                new_avatar = (
                    profile.avatar.name
                    if profile.avatar else None
                )

                if old_avatar and old_avatar != new_avatar:
                    storage = profile.avatar.storage

                    transaction.on_commit(
                        lambda name=old_avatar: storage.delete(name)
                    )

            messages.success(
                request,
                "Thông tin cá nhân đã được cập nhật!"
            )

            return redirect("profile")

    else:
        user_form = UserInfoForm(
            instance=request.user
        )

        profile_form = UserProfileForm(
            instance=profile
        )

    return render(
        request,
        "accounts/profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "profile": profile,
        }
    )


@login_required
def profile_avatar(request):
    profile = get_object_or_404(
        UserProfile,
        user=request.user
    )

    if not profile.avatar:
        raise Http404("Không tìm thấy ảnh đại diện.")

    allowed_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    extension = Path(
        profile.avatar.name
    ).suffix.lower()

    content_type = allowed_types.get(extension)

    if content_type is None:
        raise Http404("Định dạng ảnh không hợp lệ.")

    try:
        image_file = profile.avatar.storage.open(
            profile.avatar.name,
            "rb"
        )
    except OSError as exc:
        raise Http404(
            "Không tìm thấy file ảnh."
        ) from exc

    response = FileResponse(
        image_file,
        content_type=content_type
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response
