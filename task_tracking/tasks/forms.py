from django import forms

from .models import User, Project, Task, Comment


class ProjectForm(forms.ModelForm):
    """Форма создания проекта."""
    members = forms.ModelMultipleChoiceField(
        label="Участники",
        queryset=User.objects.all(),
        help_text="Введите имя пользователя участника"
    )

    class Meta:
        model = Project
        fields = ("name", "description", "members")


class TaskForm(forms.ModelForm):
    """Форма создания задачи."""
    assignee = forms.ModelChoiceField(
        label="Исполнитель",
        queryset=User.objects.all(),
        help_text="Введите имя пользователя исполнителя"
    )
    project = forms.ModelChoiceField(
        label="Проект",
        queryset=Project.objects.all(),
        help_text="К какому проекту относится задача"
    )

    class Meta:
        model = Task
        fields = (
            "title",
            "description",
            "priority",
            "status",
            "deadline",
            "assignee",
            "project"
            )


class CommentForm(forms.ModelForm):
    """Форма создания комментария."""

    class Meta:
        model = Comment
        fields = ("text",)
