


from django.db.models import Count, Q
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Task
from .permissions import IsOwner
from .serializers import TaskSerializer
from .services import complete_task


class TaskViewSet(viewsets.ModelViewSet):


    serializer_class = TaskSerializer


    permission_classes = (
        IsAuthenticated,
        IsOwner,
    )

    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
    )


    search_fields = (
        "title",
        "description",
    )


    ordering_fields = (
        "created_at",
        "updated_at",
        "title",
    )

    ordering = ("-created_at",)


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
       
       
        queryset = self.filter_queryset(
            self.get_queryset()
        )
        counts = queryset.aggregate(
            total_count=Count("id"),
            completed_count=Count(
                "id",
                filter=Q(completed=True),
            ),
            incomplete_count=Count(
                "id",
                filter=Q(completed=False),
            ),
    )

        return Response({
            "total": counts["total_count"],
            "completed": counts["completed_count"],
            "incomplete": counts["incomplete_count"],
        })

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