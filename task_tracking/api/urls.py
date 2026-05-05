from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, StatusViewSet, TaskViewSet, CommentViewSet

from django.urls import path, include


router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r'statuses', StatusViewSet, basename='status')

urlpatterns = [
    path('', include(router.urls)),
]
