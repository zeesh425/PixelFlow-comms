from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'topics', views.TopicViewSet, basename='topic')
router.register(r'category-restrictions', views.CategoryRestrictionViewSet, basename='category-restriction')
router.register(r'topic-restrictions', views.TopicRestrictionViewSet, basename='topic-restriction')

urlpatterns = [
    path('', include(router.urls)),
]