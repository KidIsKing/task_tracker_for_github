from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    # Главная страница → список проектов
    path("", views.project_list, name="project_list"),
    # Проекты
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:pk>/edit/", views.project_edit, name="project_edit"),
    path(
        "projects/<int:pk>/delete/",
        views.project_delete,
        name="project_delete"
    ),
    # Задачи
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    # Комментарии
    path(
        "tasks/<int:task_id>/comment/",
        views.comment_create,
        name="comment_create"
    ),
]
