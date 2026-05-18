from django.db import models
from django.contrib.auth import get_user_model


PRIORITY_CHOICES = [
    ('LOW', 'Низкий'),
    ('MEDIUM', 'Средний'),
    ('HIGH', 'Высокий'),
    ('CRITICAL', 'Критический'),
]
STATUS_CHOICES = [
    ('NEW', 'Новая'),
    ('IN_PROGRESS', 'В работе'),
    ('DONE', 'Выполнена'),
    ('CLOSED', 'Закрыта'),
]


User = get_user_model()


class Project(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Название"
    )
    description = models.TextField(
        max_length=500,
        verbose_name="Описание"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    owner = models.ForeignKey(
        User,
        verbose_name="Владелец",
        on_delete=models.CASCADE,
        related_name='owned_projects'
        )
    members = models.ManyToManyField(
        User,
        verbose_name="Участники",
        related_name='projects'
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

    def __str__(self):
        return f"{self.name}"


class Task(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название"
    )
    description = models.TextField(
        max_length=500,
        verbose_name="Описание"
    )
    priority = models.CharField(
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        verbose_name="Приоритет"
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        default="NEW",
        verbose_name="Статус"
    )
    deadline = models.DateTimeField(
        verbose_name="Дедлайн",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_tasks'
    )
    assignee = models.ForeignKey(
        User,
        verbose_name="Исполнитель",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return f"{self.title}"


class Comment(models.Model):
    text = models.TextField(
        max_length=500,
        verbose_name="Текст"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments'
    )
    task = models.ForeignKey(
        Task,
        verbose_name="Задача",
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return f"{self.text}"


class TaskHistory(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="Задача"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Кто изменил"
    )
    changed_fields = models.CharField(
        max_length=100,
        verbose_name="Поле"
    )
    old_value = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Было"
    )
    old_value = models.CharField(
        max_length=250,
        null=True,
        blank=True,
        verbose_name="Стало"
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время изменения"
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "История изменения задачи"
        verbose_name_plural = "История изменения задач"

    def __str__(self):
        return f"{self.task.title} - {self.changed_field}: {self.old_value} -> {self.new_value}"