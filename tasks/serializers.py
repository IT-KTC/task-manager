from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source = "user.username")
    class Meta:
        model = Task
        fields = [
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