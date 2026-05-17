from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model

from django.utils import timezone
from django.db.models import Count, Max

from tasks.models import Project, Task, Comment
from .serializers import ProjectSerializer, TaskSerializer, CommentSerializer
from .permissions import IsProjectMember, IsProjectOwner, IsAssigneeOrAuthor


User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    """Класс для управления проектами."""

    serializer_class = ProjectSerializer
    permission_classes = (IsAuthenticated, IsProjectMember)
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("name", "description")
    ordering_fields = ("name", "created_at")
    ordering = ("-created_at")

    def get_queryset(self):
        """Отображаются только проекты, где пользоватеь - участник."""
        return Project.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        """При создании проекта владелец - текущий пользователь."""
        project = serializer.save(owner=self.request.user)
        project.members.add(self.request.user)

    def get_permissions(self):
        """Для обновления и удаления нужны права владельца."""
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = (IsAuthenticated, IsProjectOwner)
        return super().get_permissions()

    # Создаём кастомный эндпоинт .../add_member/
    @action(
        detail=True,  # эндпоинт для конкретного объекта
        methods=["post"],
        permission_classes=(IsAuthenticated, IsProjectOwner),
    )
    def add_member(self, request, pk=None):
        """Добавить участника в проект."""
        project = self.get_object()
        user_id = request.data.get("user_id")

        user = User.objects.get(pk=user_id)

        if user in project.members.all():
            return Response({"error": "Пользователь уже в проекте"}, status=400)

        project.members.add(user)
        return Response({"status": "Пользователь добавлен", "username": user.username})

    # Создаём кастомный эндпоинт .../remove_member/
    @action(
        detail=True,  # эндпоинт для конкретного объекта
        methods=["post"],
        permission_classes=(IsAuthenticated, IsProjectOwner),
    )
    def remove_member(self, request, pk=None):
        """Удалить участника из проекта."""
        project = self.get_object()
        user_id = request.data.get("user_id")

        user = User.objects.get(pk=user_id)

        if user == project.owner:
            return Response({"error": "Нельзя исключить владельца проекта"}, status=400)

        if user not in project.members.all():
            return Response({"error": "Пользователь не в проекте"}, status=400)

        project.members.remove(user)
        return Response({"status": "Пользователь удалён"})

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        project = self.get_object()
        tasks = project.tasks.all()

        now = timezone.now()

        # Все задачи (сериализованные)
        all_tasks_qs = tasks.select_related('assignee', 'author').order_by('-created_at')
        all_tasks_data = TaskSerializer(all_tasks_qs, many=True).data

        # Просроченные и невыполненные задачи
        bad_deadline_qs = tasks.filter(
            deadline__lt=now
        ).exclude(
            status__in=["DONE", "CLOSED"]
        ).select_related('assignee', 'author').order_by('deadline')
        
        bad_deadline_data = TaskSerializer(bad_deadline_qs, many=True).data

        # Распределение задач по исполнителям (с деталями задач)
        distribution = tasks.values("assignee__username").annotate(
            count=Count("id")
        ).order_by("assignee__username")

        distribution_list = []
        for item in distribution:
            username = item["assignee__username"]
            
            # Получаем задачи конкретного исполнителя
            if username:
                user_tasks = tasks.filter(assignee__username=username)
            else:
                user_tasks = tasks.filter(assignee__isnull=True)
                
            distribution_list.append({
                "assignee": username or "Не назначен",
                "tasks_count": item["count"],
                "tasks": TaskSerializer(user_tasks, many=True).data  # ← список задач
            })

        # Последний дедлайн
        last_deadline = tasks.aggregate(Max("deadline"))["deadline__max"]

        report_data = {
            "project_id": project.id,
            "project_name": project.name,
            "total_tasks": len(all_tasks_data),
            "bad_deadline_tasks": len(bad_deadline_data),
            "bad_deadline_tasks_list": bad_deadline_data,
            "all_tasks": all_tasks_data,
            "distribution_list": distribution_list,
            "last_deadline": last_deadline,
        }
        return Response(report_data)


class TaskViewSet(viewsets.ModelViewSet):
    """Класс для управления задачами."""

    serializer_class = TaskSerializer
    permission_classes = (IsAuthenticated, IsProjectMember)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ("status", "priority", "assignee", "project", "deadline")
    search_fields = ("title", "description")
    ordering_fields = ("created_at", "deadline", "priority", "status")
    ordering = ("-created_at")

    def get_queryset(self):
        """Отображаются только задачи, где пользоватеь - участник."""
        return Task.objects.filter(project__members=self.request.user)

    def perform_create(self, serializer):
        """При создании задачи автор - текущий пользователь."""
        task = serializer.save(author=self.request.user)

        # Если исполнитель назначен и он не участник проекта – добавляем
        if task.assignee and task.assignee not in task.project.members.all():
            task.project.members.add(task.assignee)

        # Если автор ранее не участник - добавляем
        if self.request.user not in task.project.members.all():
            task.project.members.add(self.request.user)

    def get_permissions(self):
        """Для обновления и удаления особые права."""
        if self.action in ["update", "partial_update", "destroy"]:
            self.permission_classes = (
                IsAuthenticated,
                IsAssigneeOrAuthor | IsProjectOwner,
            )
        return super().get_permissions()


class CommentViewSet(viewsets.ModelViewSet):
    """Класс для управления комментариями."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticated, IsProjectMember)

    def get_queryset(self):
        """Пользователь видит комментарии из доступных проектов."""
        return Comment.objects.filter(task__project__members=self.request.user)

    def perform_create(self, serializer):
        """При создании комментария автор - текущий пользователь"""
        serializer.save(author=self.request.user)

    def get_permissions(self):
        """Удалять комментарии может только владелец проекта"""
        if self.action == "destroy":
            self.permission_classes = (IsAuthenticated, IsProjectOwner)
        return super().get_permissions()
