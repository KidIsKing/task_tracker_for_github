from rest_framework.permissions import BasePermission, SAFE_METHODS
from tasks.models import Project, Task, Comment


class IsProjectMember(BasePermission):
    """Проверка пользователя, как участника."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return request.user in obj.members.all()
        elif isinstance(obj, Task):
            return request.user in obj.project.members.all()
        elif isinstance(obj, Comment):
            return request.user in obj.task.project.members.all()
        return False


class IsProjectOwner(BasePermission):
    """Проверка на владельца."""

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return obj.owner == request.user
        elif isinstance(obj, Task):
            return obj.project.owner == request.user
        elif isinstance(obj, Comment):
            return obj.task.project.owner == request.user
        return False


class IsAssigneeOrAuthor(BasePermission):
    """Исполнитель может менять статус/приоритет, автор – описание/удаление."""

    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Task):
            return False

        # Владелец проекта имеет все права
        if obj.project.owner == request.user:
            return True

        # Исполнитель может менять статус и приоритет
        if obj.assignee == request.user and request.method in ["PATCH", "PUT"]:
            return True

        # Автор может удалять и менять описание
        if obj.author == request.user and request.method in ["DELETE", "PATCH", "PUT"]:
            return True

        # Чтение доступно всем участникам проекта
        if request.method in SAFE_METHODS:
            return request.user in obj.project.members.all()

        return False
