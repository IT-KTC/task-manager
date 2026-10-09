from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view,permission_classes

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, filters

from .models import Task
from .serializers import TaskSerializer
from .permissions import IsOwner
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [
        IsAuthenticated, IsOwner
    ]
    filter_backends = [
        filters.SearchFilter
    ]
    search_fields = [
        "title",
        "description"
    ]
    ordering = ["-created_at"]
    def get_queryset(self):
        queryset = Task.objects.filter(
            user = self.request.user
        ).order_by("-created_at")

        status_value = self.request.query_params.get("status")
        if status_value: 
            queryset = queryset.filter(status = status_value)
        return queryset
    def perform_create(self, serializer):
        serializer.save(
            user = self.request.user
        )
