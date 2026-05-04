# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Project, Task
from .forms import ProjectForm, TaskForm, CommentForm


@login_required
def project_list(request):
    """Список проектов, где пользователь является участником."""
    projects = Project.objects.filter(members=request.user)

    paginator = Paginator(projects, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    template_name = "tasks/project_list.html"
    context = {
        "page_obj": page_obj
        }
    return render(request, template_name, context)


@login_required
def project_create(request):
    """Создание проекта с автодобавлением создателя, как владельца."""
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            # Создаём запись без сохранения в БД (commit=False)
            project = form.save(commit=False)
            # Устанавливаем владельца
            project.owner = request.user
            # Сохраняем в БД
            project.save()
            # Сохраняем members (связь ManyToMany - многие ко многим)
            form.save_m2m()
            # Добавляем создателя в участники
            project.members.add(request.user)
            return redirect("tasks:project_list")
    else:
        form = ProjectForm()

    template_name = "tasks/project_form.html"
    context = {
        "form": form
    }
    return render(request, template_name, context)


@login_required
def project_detail(request, pk):
    """Страница конкретного проекта."""
    project = get_object_or_404(Project, pk=pk)

    if request.user not in project.members.all():
        return redirect("tasks:project_list")

    # Пагинация для задач проекта
    tasks = project.tasks.all()

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    template_name = "tasks/project_detail.html"
    context = {
        "project": project,
        "page_obj": page_obj,
    }
    return render(request, template_name, context,)


@login_required
def project_edit(request, pk):
    """Редактирование проекта с проверкой доступа."""
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return redirect("tasks:project_list")

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("tasks:project_detail", pk=project.pk)
    else:
        form = ProjectForm(instance=project)

    template_name = "tasks/project_form.html"
    context = {
        "form": form
    }
    return render(request, template_name, context)


@login_required
def project_delete(request, pk):
    """Удаление проекта с проверкой доступа."""
    project = get_object_or_404(Project, pk=pk)

    if project.owner != request.user:
        return redirect("tasks:project_list")

    project.delete()
    return redirect("tasks:project_list")


@login_required
def task_list(request):
    """Список задач из проектов, где пользователь является участником."""
    tasks = Task.objects.filter(project__members=request.user)

    # Фильтрация по статусу
    status = request.GET.get("status")
    if status:
        tasks = tasks.filter(status=status)
    # Фильтрация по приоритету
    priority = request.GET.get("priority")
    if priority:
        tasks = tasks.filter(priority=priority)
    # Фильтрация по исполнителю
    assignee = request.GET.get("assignee")
    if assignee:
        tasks = tasks.filter(assignee__username=assignee)

    paginator = Paginator(tasks, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    template_name = "tasks/task_list.html"
    context = {
        "page_obj": page_obj
    }
    return render(request, template_name, context)


@login_required
def task_create(request):
    """Создание задачи с автодобавлением создателя,
    как автора, и исполнителя в участники."""
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.save()

            # Добавление исполнителя в участники с проверкой
            assignee = form.cleaned_data.get("assignee")
            if assignee and assignee not in task.project.members.all():
                task.project.members.add(assignee)

            task.project.members.add(request.user)
            return redirect("tasks:task_detail", pk=task.pk)
    else:
        form = TaskForm()

    template_name = "tasks/task_form.html"
    context = {
        "form": form
    }
    return render(request, template_name, context)


@login_required
def task_detail(request, pk):
    """Просмотр конкретной задачи."""
    task = get_object_or_404(Task, pk=pk)

    if request.user not in task.project.members.all():
        return redirect("tasks:task_list")

    comments = task.comments.all().select_related("author")
    comment_form = CommentForm()

    template_name = "tasks/task_detail.html"
    context = {
        "task": task,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, template_name, context)


@login_required
def task_edit(request, pk):
    """Редактирование задачи с проверкой доступа."""
    task = get_object_or_404(Task, pk=pk)
    project = task.project

    # Права: владелец проекта, автор задачи (только ограниченные поля),
    # исполнитель (только статус/приоритет)
    if not (project.owner == request.user or task.author == request.user):
        return redirect("task_detail", pk=pk)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            # Если пользователь – автор, он не может менять assignee и project
            if task.author == request.user and project.owner != request.user:
                # Запрещаем изменение assignee и project
                if ("assignee" in form.changed_data or
                   "project" in form.changed_data):

                    template_name = "tasks/task_form.html"
                    context = {
                        "form": form
                    }
                    return render(request, template_name, context)

            updated_task = form.save(commit=False)

            # Если пользователь – исполнитель - может менять status и priority
            if task.assignee == request.user and not (
                project.owner == request.user or task.author == request.user
            ):
                # Разрешены только status и priority
                allowed_fields = {"status", "priority"}
                if any(field not in allowed_fields
                       for field in form.changed_data):

                    template_name = "tasks/task_form.html"
                    context = {
                        "form": form
                    }
                    return render(request, template_name, context)

            updated_task.save()

            return redirect("tasks:task_detail", pk=pk)
    else:
        form = TaskForm(instance=task)

    template_name = "tasks/task_form.html"
    context = {
        "form": form
    }
    return render(request, template_name, context)


@login_required
def task_delete(request, pk):
    """Удаление задачи с проверкой доступа."""
    task = get_object_or_404(Task, pk=pk)

    # Или владелец проекта, или автор задачи
    if not (task.project.owner == request.user or task.author == request.user):
        return redirect("tasks:task_detail", pk=pk)

    if request.method == "POST":
        task.delete()
        return redirect("tasks:project_detail", pk=task.project.pk)


@login_required
def comment_create(request, task_id):
    """Создание комментария для задач проекта."""
    task = get_object_or_404(Task, pk=task_id)

    if request.user not in task.project.members.all():
        return redirect("tasks:task_detail", pk=task_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.task = task
            comment.save()
        else:
            form = CommentForm()

    return redirect("tasks:task_detail", pk=task_id)
