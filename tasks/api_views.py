from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view,permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Task
from .serializers import TaskSerializer


@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def task_list_api(request):
    if request.method == "GET":
        tasks = Task.objects.filter(user = request.user).order_by("-created_at")
        serializer = TaskSerializer(tasks,many = True)
        return Response(serializer.data)
    if request.method == "POST":
        serializer = TaskSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save(user = request.user)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
    return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET","PUT","PATCH","DELETE"])
@permission_classes([IsAuthenticated])
def task_detail_api(request, pk):
    task = get_object_or_404(
        Task,
        pk = pk,
        user = request.user
    )
    if request.method == "GET":
        serializer = TaskSerializer(task)
        return Response(
            serializer.data
        )
    if request.method in [
    "PUT",
    "PATCH",
]:

        serializer = TaskSerializer(
        task,
        data=request.data,
        partial=(
            request.method == "PATCH"
        )
    )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    if request.method == "DELETE": 
        task.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )