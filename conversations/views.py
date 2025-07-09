from django.utils import timezone
from django.shortcuts import render
from django.db.models import F

from rest_framework import viewsets, permissions
from .models import Message
from .serializers import MessageSerializer
from topics.models import Topic

class IsAllowedToReply(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        topic_id = request.data.get("topic")
        if not topic_id:
            return False
        try:
            topic = Topic.objects.get(id=topic_id)
            return topic.can_user_reply(request.user)
        except Topic.DoesNotExist:
            return False


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsAllowedToReply]

    base_queryset = Message.objects.select_related('topic', 'sender').order_by('created_at')

    def get_queryset(self):
        """
        If the client passed ?topic=<id>, filter down to just that topic’s messages;
        otherwise return the full list.
        """
        qs = self.base_queryset
        topic_id = self.request.query_params.get('topic')
        if topic_id is not None:
            qs = qs.filter(topic_id=topic_id)
        return qs
    
    def perform_create(self, serializer):
        # bump topic counters
        topic = serializer.validated_data['topic']
        topic.total_messages = F('total_messages') + 1
        topic.last_activity = timezone.now()
        topic.save(update_fields=['total_messages', 'last_activity'])
        
        # save message with the current user as sender
        serializer.save(sender=self.request.user)


