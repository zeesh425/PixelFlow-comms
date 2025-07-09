from rest_framework import serializers
from .models import Message
from users.models import CustomUser
from users.serializers import UserSummarySerializer  # Create this if needed

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    tagged_users = UserSummarySerializer(many=True, read_only=True)
    tagged_users_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CustomUser.objects.all(),
        write_only=True, required=False
    )
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'topic',
            'topic_title',
            'sender',
            'sender_username',
            'content',
            'tagged_users',
            'tagged_users_ids',
            'created_at'
        ]
        read_only_fields = ['sender', 'tagged_users', 'created_at']
