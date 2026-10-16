from django.db.models import Count, Q

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Task
from .serializers import TaskSerializer
from .permissions import IsOwner
from .services import complete_task
from hashlib import sha256
from django.core.cache import cache
class TaskViewSet(viewsets.ModelViewSet):


    serializer_class = TaskSerializer


    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]


    search_fields = [
        "title",
        "description",
    ]


    ordering_fields = [
        "created_at",
        "updated_at",
        "title",
    ]


    ordering = ["-created_at"]


    def get_queryset(self):

        queryset = Task.objects.for_user(self.request.user)


    
        status_value = self.request.query_params.get("status")

        if status_value:
            queryset = queryset.filter(
                status=status_value
            )

        return queryset


    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )


    @action(
        detail=False,
        methods=["get"],
        url_path="stats"
    )
    def stats(self, request):
        query_hash = sha256(request.get_full.path().encore("utf-8")).hexdigest()
        cache_key = (f"task_stats:user:{request.user.pk}"f"{query_hash}")
        result = cache.get(cache_key)
        if result is not None:
            print("CACHE HIT")
            return Response(result)
        print("CACHE MISS")
        queryset = self.filter_queryset(
            self.get_queryset()
        )
        result = queryset.aggregate(
            total=Count("id"),
            completed=Count(
                "id",
                filter=Q(completed=True)
            ),
            incomplete=Count(
                "id",
                filter=Q(completed=False)
            ),
        )
        cache.set(
            cache_key,
            result,
            timeout=30  
        )
        return Response(result)

    @action(
        detail=True,
        methods=["post"],
        url_path="complete"
    )
    def complete(self, request, pk =None):
        task = self.get_object()
        complete_task(task)
        serializer = self.get_serializer(task)
        return Response(serializer.data)