from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from users.models import CustomUser


class Category(models.Model):
    """Department-based categories like Software, Marketing, etc."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='categories_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Permissions
    restricted_users = models.ManyToManyField(
        CustomUser, 
        through='CategoryRestriction', 
        through_fields=('category', 'user'),
        related_name='categories_restricted',
        blank=True
    )
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def can_user_view(self, user):
        """Check if user can view this category"""
        if user.is_admin():
            return True
        
        restriction = CategoryRestriction.objects.filter(
            category=self, 
            user=user
        ).first()
        
        if restriction:
            return restriction.can_view
        return True
    
    def can_user_reply(self, user):
        """Check if user can reply in this category"""
        if user.is_admin():
            return True
            
        restriction = CategoryRestriction.objects.filter(
            category=self, 
            user=user
        ).first()
        
        if restriction:
            return restriction.can_reply
        return True


class CategoryRestriction(models.Model):
    """Permissions for users on specific categories"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_reply = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='category_restrictions_created'
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['category', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name}"


class Topic(models.Model):
    """Individual discussion topics within categories"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='topics')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='topics_created')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Topic status
    is_active = models.BooleanField(default=True)
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='topics_closed'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    pinned_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='topics_pinned'
    )
    pinned_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='topics_locked'
    )
    locked_at = models.DateTimeField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_by = models.ForeignKey(    
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='topics_archived'
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Topic restrictions
    restricted_users = models.ManyToManyField(
        CustomUser, 
        through='TopicRestriction', 
        through_fields=('topic', 'user'),
        related_name='topics_restricted',
        blank=True
    )
    
    # Metrics
    total_messages = models.IntegerField(default=0)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.category.name} - {self.title}"
    
    
    def _has_permission(self, user, permission_field):
        # Superusers always have permission
        if user.is_superuser == user:
            return True
        
        # Check category permissions
        if permission_field == 'view' and not self.category.can_user_view(user):
            return False
        
        if permission_field == 'reply' and not self.category.can_user_reply(user):
            return False

        # Check if the user has any restriction entry
        restriction = TopicRestriction.objects.filter(topic=self, user=user).first()

        if not restriction:
            # No restriction set = default allow
            return True

        # Restriction exists; check specific permission
        return getattr(restriction, f"can_{permission_field}", False)


    def can_user_view(self, user):
        return self._has_permission(user, 'view')

    def can_user_reply(self, user):
        if self.is_closed:
            return False
        if self.is_locked:
            return False
        if self.is_archived:
            return False
        return self._has_permission(user, 'reply')


class TopicRestriction(models.Model):
    """Permissions for users on specific topics"""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    can_view = models.BooleanField(default=True)
    can_reply = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='topic_restrictions_created'
    )
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['topic', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.topic.title}"