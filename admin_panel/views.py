"""Read-only management dashboard for the existing Django User and Task models.

Only active superusers can see global user and task information. Editing users
continues through the permission-aware built-in Django Admin.
"""

from functools import wraps

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from tasks.models import Task


def superuser_required(view):
    @login_required
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied("Trang quản trị chỉ dành cho superuser.")
        return view(request, *args, **kwargs)

    return guarded


def _task_stats(queryset):
    today = timezone.localdate()
    return queryset.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=Task.Status.PENDING)),
        in_progress=Count("id", filter=Q(status=Task.Status.IN_PROGRESS)),
        completed=Count("id", filter=Q(status=Task.Status.COMPLETED)),
        overdue=Count(
            "id",
            filter=Q(due_date__lt=today) & ~Q(status=Task.Status.COMPLETED),
        ),
    )


@superuser_required
def dashboard(request):
    User = get_user_model()
    user_stats = User.objects.aggregate(
        total=Count("pk"),
        active=Count("pk", filter=Q(is_active=True)),
        inactive=Count("pk", filter=Q(is_active=False)),
        staff=Count("pk", filter=Q(is_staff=True)),
    )
    task_stats = _task_stats(Task.objects.all())
    top_users = (
        User.objects.annotate(task_total=Count("tasks"))
        .order_by("-task_total", "username")[:8]
    )
    recent_tasks = (
        Task.objects.select_related("user")
        .order_by("-created_at", "-pk")[:8]
    )
    return render(
        request,
        "admin_panel/dashboard.html",
        {
            "user_stats": user_stats,
            "task_stats": task_stats,
            "top_users": top_users,
            "recent_tasks": recent_tasks,
        },
    )


@superuser_required
def user_list(request):
    User = get_user_model()
    keyword = request.GET.get("q", "").strip()
    state = request.GET.get("state", "all")
    users = User.objects.annotate(task_total=Count("tasks"))

    if keyword:
        users = users.filter(
            Q(username__icontains=keyword)
            | Q(first_name__icontains=keyword)
            | Q(last_name__icontains=keyword)
            | Q(email__icontains=keyword)
        )
    if state == "active":
        users = users.filter(is_active=True)
    elif state == "inactive":
        users = users.filter(is_active=False)
    elif state == "staff":
        users = users.filter(is_staff=True)
    else:
        state = "all"

    page_obj = Paginator(users.order_by("-date_joined", "-pk"), 20).get_page(
        request.GET.get("page")
    )
    return render(
        request,
        "admin_panel/user_list.html",
        {"page_obj": page_obj, "keyword": keyword, "state": state},
    )


@superuser_required
def user_detail(request, pk):
    User = get_user_model()
    member = get_object_or_404(
        User.objects.prefetch_related("groups", "user_permissions"), pk=pk
    )
    user_tasks = Task.objects.filter(user=member)
    stats = _task_stats(user_tasks)
    page_obj = Paginator(
        user_tasks.order_by("-created_at", "-pk"), 15
    ).get_page(request.GET.get("page"))
    return render(
        request,
        "admin_panel/user_detail.html",
        {"member": member, "stats": stats, "page_obj": page_obj},
    )
