from rest_framework import serializers
from django.contrib.auth import get_user_model
from tasks.models import Project, Task, Comment

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

    # Для чтения: показываем родителя (кратко)
    parent = serializers.PrimaryKeyRelatedField(read_only=True)

    # Для записи: можно указать ID родительской задачи
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='parent'
    )

    # Для чтения: список подзадач (ID)
    subtasks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Task
        fields = (
            "id",
            "title",
            "description",
            "priority",
            "status",
            "deadline",
            "created_at",
            "author",
            "assignee",
            "assignee_id",
            "project_id",
            "project",
            "parent",
            "parent_id",
            "subtasks"
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
