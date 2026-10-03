from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from .models import Task
from .forms import TaskForm
from django.contrib.auth.decorators import login_required
# Create your views here.
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
    tasks = Task.objects.filter(user=request.user)

    search = request.GET.get("search")
    status = request.GET.get("status", "")
    if search:
        tasks = tasks.filter(title__icontains=search)
        if status == "completed":
            tasks = tasks.filter(completed=True)

        elif status == "pending":
            tasks = tasks.filter(completed=False)
    context ={
        "tasks": tasks
    }
    return render(request, "tasks/task_list.html",context)
def task_detail(request):
    return HttpResponse("ok")

def task_about(request):
    return HttpResponse("This is the about page for the task manager application.")
@login_required
def task_create(request):
    if request.method == "POST":
        form =  TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
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
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST": 
        form = TaskForm(request.POST, instance=task )
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
    task = get_object_or_404(Task,pk=pk)
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

def task_detail(request, pk):
    task = get_object_or_404(Task, pk = pk)
    context ={
        "task": task
    }
    return render(request,"tasks/task_detail.html", context )
