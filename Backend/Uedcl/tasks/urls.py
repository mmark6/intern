
from django.urls import path
from .views import TaskListCreateView, TaskDetailView, TaskStatusView, TaskDeadlineCheckView

urlpatterns = [
    path('', TaskListCreateView.as_view(), name='task-list-create'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/status/', TaskStatusView.as_view(), name='task-status'),
    path('check-deadlines/', TaskDeadlineCheckView.as_view(), name='task-check-deadlines'),
]
