from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MessageViewSet

router = DefaultRouter()
router.register(r'messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
# This file defines the URL routing for the conversations app, specifically for the MessageViewSet.
# It uses Django REST Framework's DefaultRouter to automatically generate the URL patterns for the MessageViewSet.
# The `messages` endpoint will handle all CRUD operations for messages in the conversations app.