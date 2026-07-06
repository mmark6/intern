

from django.urls import path
from .views import ProjectListCreateView, ProjectDetailView, ProjectDeadlineCheckView

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('check-deadlines/', ProjectDeadlineCheckView.as_view(), name='project-check-deadlines'),
]
