import asyncio
import logging
import mimetypes
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, Q, Value, When
from django.http import (
    FileResponse,
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import TaskCommentForm, TaskForm
from .models import (
    Notification,
    Task,
    TaskActivity,
    TaskComment,
)
from .services import change_task_status, move_task_to_status
from .tasks import resize_task_image

logger = logging.getLogger(__name__)

def queue_image_resize(task_id):
    try:
        resize_task_image.delay(task_id)
    except Exception:
        logger.exception(
            "Failed to enqueue image resize for Task %s",
            task_id,
        )

# Create your views here.
@login_required
@require_POST
def task_quick_status(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )
    task._activity_actor = request.user 
    new_status = request.POST.get("status", "")

    try:
        change_task_status(task, new_status)
    except ValidationError:
        return HttpResponseBadRequest(
            "Invalid status transition."
        )

    messages.success(
        request,
        f"Task updated to {task.get_status_display()}."
    )


    next_url = request.POST.get("next", "")

    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)

    return redirect("task_list")

@login_required
def kanban_board(request):
    tasks = Task.objects.for_user(
        request.user
    ).order_by("-created_at", "-pk")

    
    columns = [
        {
            "key": Task.Status.PENDING,
            "title": "Chờ thực hiện",
            "description": "Công việc chưa bắt đầu",
            "tasks": tasks.filter(
                status=Task.Status.PENDING
            ),
        },
        {
            "key": Task.Status.IN_PROGRESS,
            "title": "Đang thực hiện",
            "description": "Công việc đang được xử lý",
            "tasks": tasks.filter(
                status=Task.Status.IN_PROGRESS
            ),
        },
        {
            "key": Task.Status.COMPLETED,
            "title": "Hoàn thành",
            "description": "Công việc đã hoàn tất",
            "tasks": tasks.filter(
                status=Task.Status.COMPLETED
            ),
        },
    ]


    return render(
        request,
        "tasks/kanban_board.html",
        {"columns": columns},
    )
@login_required
@require_POST
def kanban_move_task(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )
    task._activity_actor = request.user
    new_status = request.POST.get("status", "")

    try:
        move_task_to_status(task, new_status)

    except ValidationError:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid task status.",
            },
            status=400,
        )

    return JsonResponse({
        "success": True,
        "task_id": task.pk,
        "status": task.status,
        "completed": task.completed,
        "is_overdue": task.is_overdue,
    })
@login_required
def dashboard(request):

    tasks = Task.objects.for_user(request.user)

    stats = tasks.aggregate(
        total_count=Count("id"),
        overdue_count=Count(
            "id",
            filter=(
                Q(due_date__lt=timezone.localdate())
                & ~Q(status=Task.Status.COMPLETED)
            ),
        ),
        pending_count=Count(
            "id",
            filter=Q(status=Task.Status.PENDING),
        ),

        progress_count=Count(
            "id",
            filter=Q(status=Task.Status.IN_PROGRESS),
        ),

        completed_count=Count(
            "id",
            filter=Q(status=Task.Status.COMPLETED),
        ),
    )


    total = stats["total_count"]
    completed = stats["completed_count"]

    completion_rate = (
        round(completed / total * 100)
        if total > 0
        else 0
    )


    recent_tasks = tasks.order_by(
        "-created_at",
        "-pk",
    )[:5]


    context = {
        **stats,
        "completion_rate": completion_rate,
        "recent_tasks": recent_tasks,
    }

    return render(
        request,
        "tasks/dashboard.html",
        context,
    )

async def async_test(request):
    await asyncio.sleep(3)
    return HttpResponse(
        "async task finished"
    )
@login_required
def task_download(request,pk):
    task =get_object_or_404(Task, pk = pk , user = request.user)
    if not task.attachment: 
        raise Http404("file not found")

    try: 
        file = task.attachment.storage.open(
            task.attachment.name,
            "rb"
        )
    except OSError as exc:
        raise Http404("File not found") from exc

    
    response = FileResponse(
        file,
        as_attachment=True,
        filename=Path(task.attachment.name).name,
        content_type="application/octet-stream",
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response

@login_required
def task_image(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )

    if not task.image:
        raise Http404("Image not found")

    content_type, _ = mimetypes.guess_type(
        task.image.name
    )

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    }

    if content_type not in allowed_types:
        raise Http404("Unsupported image type")

    try:
        file = task.image.storage.open(
            task.image.name,
            "rb",
        )
    except OSError as exc:
        raise Http404("Image not found") from exc

    response = FileResponse(
        file,
        content_type=content_type,
    )

    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"

    return response
@login_required
def my_tasks(request): 

    my_tasks = [
        
            "1. Learn git: ",
                "Status: In progress",
        
        
            "2. Build Task Manager: ",
                "Status: Pending",
        
        
            "3. Practice Git: ",
                "Status: Completed",
        
    ]
    context ={
            "username": "Cohan",
            "my_tasks": my_tasks
        }
    return render(request, "tasks/my_tasks.html",context)

@login_required
def task_list(request):
    tasks = Task.objects.for_user(request.user)

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    overdue = request.GET.get("overdue", "").strip()
    sort = request.GET.get("sort", "newest").strip()


    if search:
        tasks = tasks.filter(title__icontains=search)

  
    if status in Task.Status.values:
        tasks = tasks.filter(status=status)

    if priority in Task.Priority.values:
        tasks = tasks.filter(priority=priority)

 
    if overdue == "1":
        tasks = tasks.filter(
            due_date__lt=timezone.localdate()
        ).exclude(
            status=Task.Status.COMPLETED
        )


    if sort == "deadline":
        tasks = tasks.order_by(
            F("due_date").asc(nulls_last=True),
            "-pk",
        )

    elif sort == "priority":
        tasks = tasks.annotate(
            priority_order=Case(
                When(
                    priority=Task.Priority.HIGH,
                    then=Value(0),
                ),
                When(
                    priority=Task.Priority.MEDIUM,
                    then=Value(1),
                ),
                When(
                    priority=Task.Priority.LOW,
                    then=Value(2),
                ),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by(
            "priority_order",
            F("due_date").asc(nulls_last=True),
            "-pk",
        )

    elif sort == "oldest":
        tasks = tasks.order_by("created_at", "pk")

    else:
        sort = "newest"
        tasks = tasks.order_by("-created_at", "-pk")

  
    paginator = Paginator(tasks, 5)
    page_obj = paginator.get_page(request.GET.get("page"))

 
    context = {
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "priority": priority,
        "overdue": overdue,
        "sort": sort,
    }

    return render(
        request,
        "tasks/task_list.html",
        context,
    )

def task_about(request):
    return HttpResponse("This is the about page for the task manager application.")
@login_required
def task_create(request):
    if request.method == "POST":
        form =  TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task._activity_actor = request.user
            with transaction.atomic():
                task.save()
                if task.image: 
                    transaction.on_commit(
                        lambda task_id = task.pk: queue_image_resize(task_id))
                messages.success(request,"task created successfully")
                return redirect("task_list")
        
    else: 
        form = TaskForm()
    context = {
        "form": form
    }
    return render(request, "tasks/task_form.html", context)
@login_required
def task_update(request,pk):
    task = get_object_or_404(Task, pk=pk, user = request.user)
    task._activity_actor = request.user
    if request.method == "POST": 
        form = TaskForm(request.POST, request.FILES,instance=task )
        if form.is_valid(): 
            form.save()
            messages.success(
            request,
            "task updated successfully"
            )
            return redirect("task_list")
    else: 
        form = TaskForm(instance=task)
    context ={
        "form": form,
        "task": task
    }
    return render(request, "tasks/task_form.html",context)
@login_required
def task_delete(request,pk):
    task = get_object_or_404(Task,pk=pk,user = request.user)
    if request.method == "POST": 
        task.delete()
        messages.success(
        request,
        "task deleted successfully"
        )
        return redirect("task_list")
    context = {
        "task":task
    }
    return render(request,"tasks/task_confirm_delete.html", context)


def _task_community_context(request,task,comment_form=None):
    comments = task.comments.select_related(
        "author"
    ).all()

    comment_page = Paginator(
        comments,
        10
    ).get_page(
        request.GET.get("comments_page")
    )

    activity_recent = (
        task.activities
        .select_related("actor")
        .all()[:8]
    )

    return {
        "task": task,
        "comment_form": (
            comment_form
            if comment_form is not None
            else TaskCommentForm()
        ),
        "comment_page": comment_page,
        "activity_recent": activity_recent,
    }


@login_required
def task_detail(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )

    context = _task_community_context(
        request,
        task,
    )

    return render(
        request,
        "tasks/task_detail.html",
        context,
    )

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        user=request.user
    )

    page_obj = Paginator(
        notifications,
        20
    ).get_page(request.GET.get("page"))

    return render(
        request,
        "tasks/notifications.html",
        {"page_obj": page_obj}
    )


@login_required
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(
            update_fields=["is_read"]
        )

    if notification.task_id:
        task_exists = Task.objects.filter(
            pk=notification.task_id,
            user=request.user
        ).exists()

        if task_exists:
            return redirect(
                "task_detail",
                pk=notification.task_id
            )

    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    messages.success(
        request,
        "Đã đánh dấu tất cả thông báo là đã đọc."
    )

    return redirect("notification_list")


@login_required
@require_POST
def task_comment_add(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )

    form = TaskCommentForm(request.POST)

    if form.is_valid():
        with transaction.atomic():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()

            TaskActivity.objects.create(
                task=task,
                actor=request.user,
                action=TaskActivity.Action.COMMENT_ADDED,
                description="Đã thêm một bình luận.",
            )

        messages.success(
            request,
            "Đã thêm bình luận."
        )

        return redirect("task_detail", pk=task.pk)

    context = _task_community_context(
        request,
        task,
        comment_form=form,
    )

    return render(
        request,
        "tasks/task_detail.html",
        context,
        status=400,
    )


@login_required
@require_POST
def task_comment_delete(request, pk, comment_id):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )

    comment = get_object_or_404(
        TaskComment,
        pk=comment_id,
        task=task,
        author=request.user,
    )

    with transaction.atomic():
        comment.delete()

        TaskActivity.objects.create(
            task=task,
            actor=request.user,
            action=TaskActivity.Action.COMMENT_DELETED,
            description="Đã xóa một bình luận.",
        )

    messages.success(
        request,
        "Đã xóa bình luận."
    )

    return redirect("task_detail", pk=task.pk)


@login_required
def task_timeline(request, pk):
    task = get_object_or_404(
        Task,
        pk=pk,
        user=request.user,
    )

    activities = task.activities.select_related(
        "actor"
    ).all()

    page_obj = Paginator(
        activities,
        20
    ).get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "tasks/task_timeline.html",
        {
            "task": task,
            "page_obj": page_obj,
        },
    )
