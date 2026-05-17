from rest_framework import serializers
from django.contrib.auth import get_user_model
from tasks.models import Project, Task, Comment, Status

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей (только чтение)."""

    class Meta:
        model = User
        fields = ("id", "username")
        read_only_fields = (
            "id",
            "username",
        )


class ProjectSerializer(serializers.ModelSerializer):
    """Сериализатор для проектов."""

    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True,  # не возвращается при GET
        source="members",
    )

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "description",
            "created_at",
            "owner",
            "members",
            "member_ids",
        )
        read_only_fields = ("id", "created_at", "owner")


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = (
            "id",
            "title"
        )
        read_only_fields = ("id",)


class TaskSerializer(serializers.ModelSerializer):
    """Сериализатор для задач."""

    author = UserSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="assignee",
        allow_null=True,  # может быть пустым
    )
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), write_only=True, source="project"
    )
    project = ProjectSerializer(read_only=True)
    status = StatusSerializer(read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        queryset=Status.objects.all(),
        write_only=True,
        source="status",
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "priority",
            "status",
            "status_id",
            "deadline",
            "created_at",
            "author",
            "assignee",
            "assignee_id",
            "project_id",
            "project",
        )
        read_only_fields = ("id", "created_at", "author")


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""

    author = UserSerializer(read_only=True)
    task_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), write_only=True, source="task"
    )
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "text", "created_at", "author", "task_id", "task")
        read_only_fields = ("id", "created_at", "author")
