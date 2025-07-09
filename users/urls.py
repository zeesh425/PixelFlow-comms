from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # User registration workflow
    path('register/', views.register_request, name='register_request'),
    path('registration-success/', views.registration_success, name='registration_success'),
    path('verify-code/', views.verify_code, name='verify_code'),
    
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    
    # User dashboard and profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Admin views
    path('admin/admin_operations/', views.admin_CRUD, name='admin_CRUD'),
    path('admin/all-requests/', views.admin_all_requests, name='admin_all_requests'),
    path('admin/approve-request/<int:request_id>/', views.admin_approve_request, name='admin_approve_request'),
    # path('admin/generate-code/<int:request_id>/', views.admin_generate_code, name='admin_generate_code'),
    
    # API endpoints
    path('api/register/', views.api_register_request, name='api_register_request'),
    path('api/verify-code/', views.api_verify_code, name='api_verify_code'),
    path('api/dashboard-data/', views.dashboard_data_api_view, name='api_dashboard_data'),
]