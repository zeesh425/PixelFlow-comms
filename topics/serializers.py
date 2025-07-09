from rest_framework import serializers
from django.contrib.auth.models import User
from users.models import CustomUser
from .models import Category, Topic, CategoryRestriction, TopicRestriction


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    department_name = serializers.CharField(source='get_department_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'department_name']


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer with permissions"""
    created_by = UserBasicSerializer(read_only=True)
    topics_count = serializers.SerializerMethodField()
    can_view = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'created_by', 'created_at', 
            'updated_at', 'is_active', 'topics_count', 'can_view', 'can_reply'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_topics_count(self, obj):
        """Get count of active topics in this category"""
        return obj.topics.filter(is_active=True).count()
    
    def get_can_view(self, obj):
        """Check if current user can view this category"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_view(request.user)
        return False
    
    def get_can_reply(self, obj):
        """Check if current user can reply in this category"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_reply(request.user)
        return False


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']

    def validate_name(self, value):
        """Validate that category name is unique"""
        if Category.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Category with this name already exists")
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class TopicSerializer(serializers.ModelSerializer):
    """Topic serializer with permissions"""
    created_by = UserBasicSerializer(read_only=True)
    closed_by = UserBasicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    can_view = serializers.SerializerMethodField()
    can_reply = serializers.SerializerMethodField()
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'description', 'category', 'created_by', 
            'created_at', 'updated_at', 'is_active', 'is_closed', 
            'closed_by', 'closed_at', 'total_messages', 'last_activity',
            'can_view', 'can_reply'
        ]
        read_only_fields = [
            'created_by', 'created_at', 'updated_at', 'closed_by', 
            'closed_at', 'total_messages', 'last_activity'
        ]
    
    def get_can_view(self, obj):
        """Check if current user can view this topic"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_view(request.user)
        return False
    
    def get_can_reply(self, obj):
        """Check if current user can reply to this topic"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_user_reply(request.user)
        return False


class TopicCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating topics"""
    category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Topic
        fields = ['title', 'description', 'category_id']
    
    def validate_category_id(self, value):
        """Validate that category exists and user can create topics in it"""
        try:
            category = Category.objects.get(id=value, is_active=True)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found or inactive")
        
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if not category.can_user_reply(request.user):
                raise serializers.ValidationError("You don't have permission to create topics in this category")
        
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        category_id = validated_data.pop('category_id')
        category = Category.objects.get(id=category_id)
        
        topic = Topic.objects.create(
            category=category,
            created_by=request.user,
            **validated_data
        )
        return topic


class TopicListSerializer(serializers.ModelSerializer):
    """Simplified topic serializer for listing"""
    created_by = UserBasicSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'category_name','description', 'created_by', 'created_at',
            'is_closed', 'total_messages', 'last_activity'
        ]


class CategoryRestrictionSerializer(serializers.ModelSerializer):
    """Serializer for category restrictions"""
    user = UserBasicSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CategoryRestriction
        fields = [
            'id', 'category', 'user', 'can_view', 'can_reply',
            'created_by', 'created_at'
        ]


class CategoryRestrictionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating category restrictions"""
    user_id = serializers.IntegerField(write_only=True)
    category_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CategoryRestriction
        fields = ['user_id', 'category_id', 'can_view', 'can_reply']
    
    def validate(self, data):
        """Validate user and category exist"""

        request = self.context.get('request')
        user_id = data['user_id']

        if request.user.id == user_id:
            raise serializers.ValidationError("You cannot restrict yourself")
    
        try:
            CustomUser.objects.get(id=data['user_id'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        try:
            Category.objects.get(id=data['category_id'])
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        user_id = validated_data.pop('user_id')
        category_id = validated_data.pop('category_id')
        
        user = CustomUser.objects.get(id=user_id)
        category = Category.objects.get(id=category_id)
        
        restriction = CategoryRestriction.objects.create(
            user=user,
            category=category,
            created_by=request.user,
            **validated_data
        )
        return restriction


class TopicRestrictionSerializer(serializers.ModelSerializer):
    """Serializer for topic restrictions"""
    user = UserBasicSerializer(read_only=True)
    topic = TopicSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = TopicRestriction
        fields = [
            'id', 'topic', 'user', 'can_view', 'can_reply',
            'created_by', 'created_at'
        ]


class TopicRestrictionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating topic restrictions"""
    user_id = serializers.IntegerField(write_only=True)
    topic_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TopicRestriction
        fields = ['user_id', 'topic_id', 'can_view', 'can_reply']
    
    def validate(self, data):
        """Validate user and topic exist"""

        request = self.context.get('request')
        user_id = data['user_id']

        if request.user.id == user_id:
            raise serializers.ValidationError("You cannot restrict yourself")
        
        try:
            CustomUser.objects.get(id=data['user_id'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        try:
            Topic.objects.get(id=data['topic_id'])
        except Topic.DoesNotExist:
            raise serializers.ValidationError("Topic not found")
        
        return data
    
    def create(self, validated_data):
        request = self.context.get('request')
        user_id = validated_data.pop('user_id')
        topic_id = validated_data.pop('topic_id')
        
        user = CustomUser.objects.get(id=user_id)
        topic = Topic.objects.get(id=topic_id)
        
        restriction = TopicRestriction.objects.create(
            user=user,
            topic=topic,
            created_by=request.user,
            **validated_data
        )
        return restriction