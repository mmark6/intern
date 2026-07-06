"""
URL configuration for the Dashboard app.
"""
from django.urls import path
from .views import (
    DashboardSummaryView,
    DashboardProjectsBreakdownView,
    DashboardTaskStatisticsView,
    DashboardUserTasksView,
)

urlpatterns = [
    path('', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary-explicit'),
    path('projects-breakdown/', DashboardProjectsBreakdownView.as_view(), name='dashboard-projects-breakdown'),
    path('task-statistics/', DashboardTaskStatisticsView.as_view(), name='dashboard-task-statistics'),
    path('user-tasks/', DashboardUserTasksView.as_view(), name='dashboard-user-tasks'),
]
