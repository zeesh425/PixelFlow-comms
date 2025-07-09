from django.db import models
from django.utils import timezone
from users.models import CustomUser
from topics.models import Topic

class Message(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    tagged_users = models.ManyToManyField(CustomUser, blank=True, related_name='tagged_in_messages')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender.username} @ {self.topic.title} - {self.content[:30]}"
