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
    
    @action(detail=True, methods=['get'], url_path='report')
    def report(self, request, pk=None):
        """
        Кастомный эндпоинт для получения отчёта по проекту.
        Доступен по URL: /api/projects/{id}/report/
        """
        
        # 1. Получаем объект проекта по его ID (передан в URL)
        #    self.get_object() автоматически проверяет права доступа
        project = self.get_object()
        
        # 2. Получаем все задачи, принадлежащие этому проекту
        #    Это QuerySet (набор задач) – мы будем его фильтровать и агрегировать
        tasks = project.tasks.all()
        
        # ------------------------------------------------------------------
        # 3. Общее количество задач в проекте
        #    count() выполняет SQL запрос SELECT COUNT(*) FROM ...
        total_tasks = tasks.count()
        
        # 4. Текущее время с учётом часового пояса (из настроек TIME_ZONE)
        #    Нужно для сравнения с дедлайнами задач
        now = timezone.now()
        
        # 5. Количество просроченных задач
        #    Условия:
        #    - deadline меньше текущего момента (задача уже должна быть выполнена)
        #    - статус НЕ равен 'DONE' и НЕ равен 'CLOSED' (т.е. задача ещё не завершена)
        #    filter(deadline__lt=now)  – отбираем задачи, у которых deadline < now
        #    exclude(status__in=['DONE','CLOSED']) – исключаем задачи с такими статусами
        #    count() – считаем количество
        bad_deadline_tasks = tasks.filter(
            deadline__lt=now
        ).exclude(status__in=['DONE', 'CLOSED']).count()
        
        # ------------------------------------------------------------------
        # 6. Распределение задач по исполнителям (assignee)
        #    - values('assignee__username') – группируем по имени пользователя-исполнителя
        #      (если исполнитель не назначен, assignee__username будет None)
        #    - annotate(count=Count('id')) – добавляем к каждой группе поле count,
        #      равное количеству задач в этой группе
        #    - order_by('-count') – сортируем группы по убыванию количества задач
        distribution = tasks.values('assignee__username').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 7. Преобразуем результат в удобный для JSON список словарей
        #    Для каждого элемента из distribution:
        #    - если assignee__username равно None, заменяем на строку "Не назначен"
        #    - tasks_count – это количество задач для этого исполнителя
        distribution_list = [
            {"assignee": item['assignee__username'] or "Не назначен", 
             "tasks_count": item['count']}
            for item in distribution
        ]
        
        # ------------------------------------------------------------------
        # 8. Последний дедлайн среди всех задач проекта
        #    aggregate(Max('deadline')) – вычисляет максимальное значение поля deadline
        #    результат – словарь вида {'deadline__max': дата или None}
        last_deadline = tasks.aggregate(Max('deadline'))['deadline__max']
        
        # 9. Формируем словарь с отчётными данными
        report_data = {
            "project_id": project.id,                 # ID проекта
            "project_name": project.name,             # название проекта
            "total_tasks": total_tasks,               # всего задач
            "overdue_tasks": bad_deadline_tasks,           # просроченных задач
            "distribution_by_assignee": distribution_list,  # распределение по исполнителям
            "last_deadline": last_deadline,           # последний дедлайн (или null)
        }
        
        # 10. Возвращаем ответ в формате JSON (DRF сам преобразует словарь в JSON)
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
