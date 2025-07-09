from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from users.models import CustomUser
from django.utils import timezone
from django.db.models import Q

from .models import Category, Topic, CategoryRestriction, TopicRestriction
from .serializers import (
    CategorySerializer, CategoryCreateSerializer,
    TopicSerializer, TopicCreateSerializer, TopicListSerializer,
    CategoryRestrictionSerializer, CategoryRestrictionCreateSerializer,
    TopicRestrictionSerializer, TopicRestrictionCreateSerializer
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission: Admins can do anything, others can only read"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_admin()


class IsAdminUser(permissions.BasePermission):
    """Custom permission: Only admins can access"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing categories"""
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    
    def get_queryset(self):
        """Filter categories based on user permissions"""
        user = self.request.user
        if user.is_admin():
            return Category.objects.filter(is_active=True)
        
        # For regular users, filter out categories they can't view
        queryset = Category.objects.filter(is_active=True)
        accessible_categories = []
        
        for category in queryset:
            if category.can_user_view(user):
                accessible_categories.append(category.id)
        
        return queryset.filter(id__in=accessible_categories)
    
    def get_serializer_class(self):
        """Use different serializer for create/update"""
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryCreateSerializer
        return CategorySerializer
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Get all topics in a category"""
        category = self.get_object()
        
        # Check if user can view this category
        if not category.can_user_view(request.user):
            return Response(
                {'error': 'You do not have permission to view this category'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get topics user can view
        topics = category.topics.filter(is_active=True)
        accessible_topics = []
        
        for topic in topics:
            if topic.can_user_view(request.user):
                accessible_topics.append(topic.id)
        
        filtered_topics = topics.filter(id__in=accessible_topics)
        serializer = TopicListSerializer(filtered_topics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restrict_user(self, request, pk=None):
        """Restrict a user's access to this category"""
        category = self.get_object()
        serializer = CategoryRestrictionCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Check if restriction already exists
            existing = CategoryRestriction.objects.filter(
                category=category,
                user_id=request.data.get('user_id')
            ).first()
            
            if existing:
                return Response(
                    {'error': 'Restriction already exists for this user'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            restriction = serializer.save()
            return Response(
                CategoryRestrictionSerializer(restriction).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def restrictions(self, request, pk=None):
        """Get all restrictions for this category"""
        category = self.get_object()
        restrictions = CategoryRestriction.objects.filter(category=category)
        serializer = CategoryRestrictionSerializer(restrictions, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ModelViewSet):
    """ViewSet for managing topics"""
    serializer_class = TopicSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter topics based on user permissions and an optional category filter
        from query parameters.
        """
        user = self.request.user
        
        # Start with all active topics
        queryset = Topic.objects.filter(is_active=True)
        
        # Apply user-specific filtering (admin vs. regular user permissions)
        if user.is_admin():
            # Admins can see all active topics
            pass
        else:
            # Regular users: hide archived topics and apply user-specific view permissions
            queryset = queryset.filter(is_archived=False)
            
            # This permission check can be inefficient for large datasets.
            # For better performance, consider using Django's Q objects or
            # optimizing the `can_user_view` method to use database queries.
            accessible_topics_ids = [
                topic.id for topic in queryset if topic.can_user_view(user)
            ]
            queryset = queryset.filter(id__in=accessible_topics_ids)

        # *** Crucial Fix: Filter by category if 'category' ID is provided in query parameters ***
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                # Ensure the category exists and is active
                category = Category.objects.get(id=category_id, is_active=True)
                
                # Check if the user has permission to view this specific category
                # If not, return an empty queryset for security
                if not category.can_user_view(user):
                    return Topic.objects.none() # Return no topics if category is not viewable
                
                # Filter the topics by the validated category
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                # If the requested category ID does not exist, return an empty queryset
                # This prevents showing unrelated topics when an invalid category is requested.
                return Topic.objects.none()
        
        return queryset

        
        # Regular users: hide archived topics
        queryset = queryset.filter(is_archived=False)
        
        # For regular users, filter based on permissions
        accessible_topics = [
        topic.id for topic in queryset if topic.can_user_view(user)
    ]

        return queryset.filter(id__in=accessible_topics)

    
    def get_serializer_class(self):
        """Use different serializer for create"""
        if self.action == 'create':
            return TopicCreateSerializer
        elif self.action == 'list':
            return TopicListSerializer
        return TopicSerializer
    
    def perform_create(self, serializer):
        """Create topic and check permissions"""
        topic = serializer.save()
        return topic
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def close(self, request, pk=None):
        """Close a topic (admin only)"""
        topic = self.get_object()
        
        if topic.is_closed:
            return Response(
                {'error': 'Topic is already closed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        topic.is_closed = True
        topic.closed_by = request.user
        topic.closed_at = timezone.now()
        topic.save()
        
        serializer = TopicSerializer(topic, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reopen(self, request, pk=None):
        """Reopen a closed topic (admin only)"""
        topic = self.get_object()
        
        if not topic.is_closed:
            return Response(
                {'error': 'Topic is not closed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        topic.is_closed = False
        topic.closed_by = None
        topic.closed_at = None
        topic.save()
        
        serializer = TopicSerializer(topic, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def restrict_user(self, request, pk=None):
        """Restrict a user's access to this topic"""
        topic = self.get_object()
        serializer = TopicRestrictionCreateSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Check if restriction already exists
            existing = TopicRestriction.objects.filter(
                topic=topic,
                user_id=request.data.get('user_id')
            ).first()
            
            if existing:
                return Response(
                    {'error': 'Restriction already exists for this user'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            restriction = serializer.save()
            return Response(
                TopicRestrictionSerializer(restriction).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminUser])
    def restrictions(self, request, pk=None):
        """Get all restrictions for this topic"""
        topic = self.get_object()
        restrictions = TopicRestriction.objects.filter(topic=topic)
        serializer = TopicRestrictionSerializer(restrictions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search topics by title or description"""
        query = request.query_params.get('q', '')
        category_id = request.query_params.get('category', '')
        
        if not query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start with user's accessible topics
        queryset = self.get_queryset()
        
        # Filter by search query
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
        
        # Filter by category if specified
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                if category.can_user_view(request.user):
                    queryset = queryset.filter(category=category)
                else:
                    return Response(
                        {'error': 'You do not have permission to view this category'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Category.DoesNotExist:
                return Response(
                    {'error': 'Category not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = TopicListSerializer(queryset, many=True)
        return Response(serializer.data)


class CategoryRestrictionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing category restrictions (admin only)"""
    serializer_class = CategoryRestrictionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return CategoryRestriction.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CategoryRestrictionCreateSerializer
        return CategoryRestrictionSerializer


class TopicRestrictionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing topic restrictions (admin only)"""
    serializer_class = TopicRestrictionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return TopicRestriction.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TopicRestrictionCreateSerializer
        return TopicRestrictionSerializer