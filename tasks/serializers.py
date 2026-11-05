from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source = "user.username")
    class Meta:
        model = Task
        fields = [  # noqa: RUF012
            "id",
            "user",
            "title",
            "description",
            "status",
            "completed",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
        ]

    
    def create(self, validated_data):
        task = Task(**validated_data)

        request = self.context.get("request")

        if request and request.user.is_authenticated:
            task._activity_actor = request.user

        task.save()
        return task


    def update(self, instance, validated_data):
        request = self.context.get("request")

        if request and request.user.is_authenticated:
            instance._activity_actor = request.user

        return super().update(instance, validated_data)

    def validate(self, attrs):
        status_provided = "status" in attrs
        completed_provided = "completed" in attrs

        if status_provided:
            expected_completed = (
                attrs["status"] == Task.Status.COMPLETED
            )

            if (
                completed_provided
                and attrs["completed"] != expected_completed
            ):
                raise serializers.ValidationError({
                    "completed": (
                        "Completed must match the task status."
                    )
                })

            attrs["completed"] = expected_completed

        elif completed_provided:
            if attrs["completed"]:
                attrs["status"] = Task.Status.COMPLETED

            elif (
                self.instance is not None
                and self.instance.status == Task.Status.COMPLETED
            ):
                attrs["status"] = Task.Status.PENDING

        return attrs