from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets
from .serializers import UserSerializer
from django.contrib.auth import get_user_model
User = get_user_model()
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    def get_permissions(self):
        if self.action == "me":
            permission_classes = [
                IsAuthenticated
            ]
        else: 
            permission_classes = [
                IsAdminUser
            ]
        return [
            permission()
            for permission in permission_classes
        ]
    @action(
        detail=False,
        methods=["get","patch"],
        url_name="me"
    )
    def me(self, request): 
        if request.method == "GET": 
            serializer = self.get_serializer(
                request.user
            )
            return Response(
                serializer.data
            )
        serializer = self.get_serializer(
            request.user,
            data = request.data,
            partial = True
        )
        serializer.is_valid(
            raise_exception = True
        )
        serializer.save()
        return Response(
            serializer.data
        ) 