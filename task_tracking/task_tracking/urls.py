from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from django.contrib import admin
from django.urls import path, include, reverse_lazy


urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("tasks.urls")),  # подключаем маршруты mail
    path("api/", include("api.urls")),  # подключаем маршруты api

    # API документация
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # Пути для Djoser JWT API
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Подключаем urls.py приложения для работы с пользователями.
    path("auth/", include("django.contrib.auth.urls")),
    path(
        "auth/registration/",
        CreateView.as_view(
            template_name="registration/registration_form.html",
            form_class=UserCreationForm,
            success_url=reverse_lazy("index"),
        ),
        name="registration",
    ),
]
