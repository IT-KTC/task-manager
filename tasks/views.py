import asyncio
import logging
import mimetypes
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TaskForm
from .models import Task
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
    tasks = Task.objects.for_user(
        request.user
    )

    search = request.GET.get(
        "search", ""
    ).strip()

    status = request.GET.get(
        "status", ""
    ).strip()

    # Search độc lập
    if search:
        tasks = tasks.filter(
            title__icontains=search
        )

    # Filter độc lập
    if status in {
        "pending",
        "in_progress",
        "completed",
    }:
        tasks = tasks.filter(
            status=status
        )

    # Sorting
    tasks = tasks.order_by(
        "-created_at",
        "-pk",
    )

    paginator = Paginator(tasks, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "tasks/task_list.html",
        {
            "page_obj": page_obj,
            "search": search,
            "status": status,
        },
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
            with transaction.atomic():
                task.save()
                if task.image: 
                    transaction.on_commit(
                        lambda task_id = task.pk: queue_image_resize(task_id))
                messages.success(request,"task created successfully")
                return redirect("task_list")
        else:
            print(form.errors)
    else: 
        form = TaskForm()
    context = {
        "form": form
    }
    return render(request, "tasks/task_form.html", context)
@login_required
def task_update(request,pk):
    task = get_object_or_404(Task, pk=pk, user = request.user)
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
@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk = pk,user = request.user)
    context ={
        "task": task
    }
    return render(request,"tasks/task_detail.html", context )
