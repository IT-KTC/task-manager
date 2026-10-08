from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view,permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets

from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [
        IsAuthenticated
    ]
    def get_queryset(self):
        return Task.objects.filter(
            user = self.request.user
        ).order_by("-created_at")
    def perform_create(self, serializer):
        serializer.save(
            user = self.request.user
        )