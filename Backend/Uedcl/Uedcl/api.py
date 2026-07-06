from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
def api_root(request, format=None):
    """API root listing main endpoints."""
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'projects': reverse('project-list', request=request, format=format),
        'tasks': reverse('task-list', request=request, format=format),
        'comments': reverse('comment-list', request=request, format=format),
        'dashboard': reverse('dashboard-summary', request=request, format=format),
        'admin': reverse('admin:index', request=request, format=format),
    })
