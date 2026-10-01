from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def task_list(request): 
    return HttpResponse("Hello, World! This is the task list view.")
def task_detail(request):
    return HttpResponse("ok")