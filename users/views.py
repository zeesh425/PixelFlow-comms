from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.template.loader import render_to_string

# Import Django REST Framework components
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from topics.models import CategoryRestriction, TopicRestriction

# Import models and serializers from current app
from .models import CustomUser, Department, UserRegistrationRequest
from .forms import (
    UserRegistrationRequestForm, 
    CodeVerificationForm, 
    CustomLoginForm, 
    AdminApprovalForm
)
from .serializers import UserSummarySerializer

# Import models and serializers from other apps
# Ensure 'conversations' app is correctly set up and its models/serializers exist
try:
    from conversations.models import Message
    from conversations.serializers import MessageSerializer
    from topics.models import Topic, Category # Needed for related lookups if you query by topic/category
    # No direct import of TopicSerializer or CategorySerializer from 'topics' here,
    # as we're only using MessageSerializer to serialize 'recent_messages'.
    # If you needed full Topic/Category objects in the dashboard data, you'd import their serializers.
except ImportError as e:
    print(f"Warning: Failed to import models/serializers from 'conversations' or 'topics': {e}")
    Message = None
    # If Message or Topic models aren't found, set their serializers to None as well
    MessageSerializer = None
    Topic = None
    Category = None


def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_admin()


def register_request(request):
    """Handle user registration requests"""
    if request.method == 'POST':
        form = UserRegistrationRequestForm(request.POST)
        if form.is_valid():
            registration_request = form.save()
            messages.success(
                request, 
                'Registration request submitted successfully! '
                'Admin will review your request and send you a verification code.'
            )
            return redirect('registration_success')
    else:
        form = UserRegistrationRequestForm()
    
    return render(request, 'users/register_request.html', {'form': form})


def registration_success(request):
    """Show registration success page"""
    return render(request, 'users/registration_success.html')


def verify_code(request):
    """Handle code verification and password setup"""
    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            code = form.cleaned_data['one_time_code']
            password = form.cleaned_data['password']
            
            try:
                # Find the registration request
                reg_request = UserRegistrationRequest.objects.get(
                    username=username,
                    one_time_code=code,
                    status='approved'
                )
                
                # Check if code is still valid
                if not reg_request.is_code_valid():
                    messages.error(request, 'Verification code has expired. Please contact admin.')
                    return render(request, 'users/verify_code.html', {'form': form})
                
                # Create the user account
                user = CustomUser.objects.create_user(
                    username=reg_request.username,
                    email=reg_request.email,
                    first_name=reg_request.first_name,
                    last_name=reg_request.last_name,
                    password=password,
                    department=reg_request.department,
                    whatsapp_number=reg_request.whatsapp_number,
                    is_approved=True,
                    role='user'
                )
                
                # Clear the one-time code
                reg_request.one_time_code = ''
                reg_request.save()
                
                messages.success(request, 'Account created successfully! You can now login.')
                return redirect('login')
                
            except UserRegistrationRequest.DoesNotExist:
                messages.error(request, 'Invalid username or verification code.')
    else:
        form = CodeVerificationForm()
    
    return render(request, 'users/verify_code.html', {'form': form})


def user_login(request):
    """Handle user login"""
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user:

                if not user.is_approved and not user.is_superuser:
                    messages.error(request, 'Your account is not approved yet. Please contact admin.')
                    return render(request, 'users/login.html', {'form': form})

                login(request, user)

                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('dashboard')

            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def dashboard(request):
    """User dashboard"""
    return render(request, 'users/dashboard.html')


# @login_required
# @user_passes_test(is_admin)
# def admin_CRUD(request):
#     """Admin dashboard with all management options"""
#     pending_requests = UserRegistrationRequest.objects.filter(status='pending')
#     all_users = CustomUser.objects.all().order_by('-date_joined')
#     categories = Category.objects.all()
#     topics = Topic.objects.all().order_by('-created_at')
#     category_restrictions = CategoryRestriction.objects.all().select_related('category', 'user')
#     topic_restrictions = TopicRestriction.objects.all().select_related('topic', 'user')
    
#     return render(request, 'users/admin_CRUD.html', {
#         'pending_requests': pending_requests,
#         'all_users': all_users,
#         'categories': categories,
#         'topics': topics,
#         'category_restrictions': category_restrictions,
#         'topic_restrictions': topic_restrictions,
#     })



@login_required
@user_passes_test(is_admin) # Ensure only admins/staff can access
def admin_CRUD(request):
    try:
        # User Management Counts
        all_users_count = CustomUser.objects.count()
        approved_users_count = CustomUser.objects.filter(is_approved=True).count()
        active_users_count = CustomUser.objects.filter(is_active=True).count()
        admin_users_count = CustomUser.objects.filter(role='admin').count() # Or is_staff=True if that's your admin indicator

        # Pending Requests
        pending_requests = UserRegistrationRequest.objects.filter(status='pending').order_by('-created_at')

        # Categories Counts
        categories_count = Category.objects.count()
        active_categories_count = Category.objects.filter(is_active=True).count()

        # Topics Counts
        topics_count = Topic.objects.count()
        active_topics_count = Topic.objects.filter(is_active=True).count()
        closed_topics_count = Topic.objects.filter(is_closed=True).count()
        archived_topics_count = Topic.objects.filter(is_archived=True).count()

        # Permissions Counts
        category_restrictions_count = CategoryRestriction.objects.count()
        topic_restrictions_count = TopicRestriction.objects.count()

        context = {
            'all_users_count': all_users_count,
            'approved_users_count': approved_users_count,
            'active_users_count': active_users_count,
            'admin_users_count': admin_users_count,
            'pending_requests': pending_requests,
            'categories_count': categories_count,
            'active_categories_count': active_categories_count,
            'topics_count': topics_count,
            'active_topics_count': active_topics_count,
            'closed_topics_count': closed_topics_count,
            'archived_topics_count': archived_topics_count,
            'category_restrictions_count': category_restrictions_count,
            'topic_restrictions_count': topic_restrictions_count,
        }
    except Exception as e:
        messages.error(request, f"An error occurred while fetching admin data: {e}")
        context = {
            'all_users_count': 0, 'approved_users_count': 0, 'active_users_count': 0, 'admin_users_count': 0,
            'pending_requests': [], 'categories_count': 0, 'active_categories_count': 0,
            'topics_count': 0, 'active_topics_count': 0, 'closed_topics_count': 0, 'archived_topics_count': 0,
            'category_restrictions_count': 0, 'topic_restrictions_count': 0,
        }
    return render(request, 'users/admin_CRUD.html', context)



@login_required
@user_passes_test(is_admin)
def admin_approve_request(request, request_id):
    """Admin approve a registration request"""
    reg_request = get_object_or_404(UserRegistrationRequest, id=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            reg_request.approve_request(request.user)
            
            # ✅ Auto-generate one-time code
            code = reg_request.generate_one_time_code()
            messages.success(request, f'Registration request for {reg_request.username} approved.')
            messages.info(request, f'One-time code generated: {code}')
            messages.info(request, f'Send this code to {reg_request.whatsapp_number} or {reg_request.email}')

        elif action == 'reject':
            notes = request.POST.get('admin_notes', '')
            reg_request.reject_request(request.user, notes)
            messages.success(request, f'Registration request for {reg_request.username} rejected.')

        return redirect('admin_pending_requests')

    return render(request, 'users/admin_approve_request.html', {
        'reg_request': reg_request
    })


@login_required
@user_passes_test(is_admin)
def admin_all_requests(request):
    """Admin view to see all registration requests"""
    all_requests = UserRegistrationRequest.objects.all()
    return render(request, 'users/admin_all_requests.html', {
        'all_requests': all_requests
    })


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'users/profile.html')


# --- API Views (for frontend integration) ---

@api_view(['GET']) # Only allow GET requests
@permission_classes([IsAuthenticated]) # Ensure user is logged in
def dashboard_data_api_view(request):
    """
    API endpoint to provide data for the user's dashboard,
    including user summary and recent messages.
    """
    user = request.user
    
    # Serialize user's basic info
    user_summary_data = UserSummarySerializer(user).data

    recent_messages_data = []
    if Message and MessageSerializer: # Check if Message model and serializer were successfully imported
        # Fetch recent messages.
        # Given your frontend expects 'topic_title', 'sender_username', 'content', 'created_at'
        # for recent activity, and your MessageSerializer provides these,
        # we can fetch messages and serialize them directly.
        
        # This query fetches the 5 most recent messages overall.
        # You might want to filter this further based on user's departments,
        # topics they are members of, or messages they were tagged in.
        # For example, to get messages from topics the user can view:
        if Topic: # Ensure Topic model is available
            user_viewable_topics_ids = [t.id for t in Topic.objects.all() if t.can_user_view(user)]
            # Filter messages by topics the user can view
            recent_messages = Message.objects.filter(topic_id__in=user_viewable_topics_ids).order_by('-created_at')[:5]
        else: # Fallback if Topic model isn't available
            recent_messages = Message.objects.order_by('-created_at')[:5] 

        # Pass the request context to the serializer for methods like get_can_view/can_reply
        # (Though MessageSerializer doesn't directly use this, it's good practice for others)
        recent_messages_data = MessageSerializer(recent_messages, many=True, context={'request': request}).data
    else:
        print("Debug: Message model or MessageSerializer not available. Recent activity data will be empty.")


    return Response({
        'user_summary': user_summary_data,
        'recent_messages': recent_messages_data,
        # You can add more data here if needed for the dashboard (e.g., pending tasks, notifications)
    })


@csrf_exempt
def api_register_request(request):
    """API endpoint for registration requests"""
    if request.method == 'POST':
        form = UserRegistrationRequestForm(request.POST)
        if form.is_valid():
            registration_request = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Registration request submitted successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_verify_code(request):
    """API endpoint for code verification"""
    if request.method == 'POST':
        form = CodeVerificationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            code = form.cleaned_data['one_time_code']
            password = form.cleaned_data['password']
            
            try:
                reg_request = UserRegistrationRequest.objects.get(
                    username=username,
                    one_time_code=code,
                    status='approved'
                )
                
                if not reg_request.is_code_valid():
                    return JsonResponse({
                        'success': False,
                        'message': 'Verification code has expired.'
                    })
                
                user = CustomUser.objects.create_user(
                    username=reg_request.username,
                    email=reg_request.email,
                    first_name=reg_request.first_name,
                    last_name=reg_request.last_name,
                    password=password,
                    department=reg_request.department,
                    whatsapp_number=reg_request.whatsapp_number,
                    is_approved=True,
                    role='user'
                )
                
                reg_request.one_time_code = ''
                reg_request.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Account created successfully!'
                })
                
            except UserRegistrationRequest.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or verification code.'
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)