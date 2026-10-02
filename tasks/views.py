from django.shortcuts import render
from django.http import HttpResponse
from .models import Task
# Create your views here.
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

def task_list(request): 
    tasks = Task.objects.all()
    context ={
        "tasks": tasks
    }
    return render(request, "tasks/task_list.html",context)
def task_detail(request):
    return HttpResponse("ok")

def task_about(request):
    return HttpResponse("This is the about page for the task manager application.")