from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, TaskViewSet, CommentViewSet, NotificationsViewSet

from django.urls import path, include


router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"notifications", NotificationsViewSet, basename="notification")

urlpatterns = [
    path('', include(router.urls)),
]
