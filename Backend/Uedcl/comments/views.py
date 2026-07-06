"""
Comment views.

Refactored to use DRF's APIView so JWT authentication runs.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Comment
from .serializers import CommentSerializer


class CommentListCreateView(APIView):
    """
    GET  /api/comments/                 -> list (optionally filter ?task_id=)
    POST /api/comments/                 -> create
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        comments = Comment.objects.all()
        task_id = request.query_params.get('task_id')
        if task_id:
            comments = comments.filter(task_id=task_id)
        serializer = CommentSerializer(comments, many=True)
        # Log comment list view
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'COMMENT', None, 'Comment List', f'Viewed comments ({comments.count()} total)')
        except Exception:
            pass
        return Response({
            'success': True,
            'count': comments.count(),
            'comments': serializer.data,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            # Log audit
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'CREATE', 'COMMENT', comment.id, f'Task #{comment.task_id}', f'Created comment on task')
            except Exception:
                pass
            return Response({
                'success': True,
                'message': 'Comment created successfully',
                'comment': CommentSerializer(comment).data,
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(APIView):
    """
    GET    /api/comments/<pk>/   -> retrieve
    PATCH  /api/comments/<pk>/   -> update (author only)
    DELETE /api/comments/<pk>/   -> delete (author only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_comment(self, pk):
        try:
            return Comment.objects.get(pk=pk), None
        except Comment.DoesNotExist:
            return None, Response({
                'success': False,
                'error': 'Comment not found',
            }, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk):
        comment, err = self._get_comment(pk)
        if err:
            return err
        # Log comment view
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'VIEW', 'COMMENT', comment.id, f'Comment #{comment.id}', f'Viewed comment')
        except Exception:
            pass
        return Response({
            'success': True,
            'comment': CommentSerializer(comment).data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        comment, err = self._get_comment(pk)
        if err:
            return err
        if request.user != getattr(comment, 'author', None):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            # Log audit
            try:
                from audit_logs.utils import log_audit
                log_audit(request, 'UPDATE', 'COMMENT', comment.id, f'Comment #{comment.id}', f'Updated comment')
            except Exception:
                pass
            return Response({
                'success': True,
                'message': 'Comment updated successfully',
                'comment': CommentSerializer(comment).data,
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors,
        }, status=status.HTTP_400_BAD_REQUEST)

    put = patch

    def delete(self, request, pk):
        comment, err = self._get_comment(pk)
        if err:
            return err
        if request.user != getattr(comment, 'author', None):
            return Response({
                'success': False,
                'error': 'Permission denied',
            }, status=status.HTTP_403_FORBIDDEN)
        comment_id = comment.id
        comment.delete()
        # Log audit
        try:
            from audit_logs.utils import log_audit
            log_audit(request, 'DELETE', 'COMMENT', comment_id, f'Comment #{comment_id}', f'Deleted comment')
        except Exception:
            pass
        return Response({
            'success': True,
            'message': 'Comment deleted successfully',
        }, status=status.HTTP_204_NO_CONTENT)
