# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html # Import for potential formatting
from .models import CustomUser, Department, UserRegistrationRequest

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    ordering = ['name']
    list_per_page = 20 # Add pagination limit

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Add custom fields to the user admin
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('department', 'whatsapp_number', 'role', 'is_approved')
        }),
        ('Timestamps', { # New fieldset for metadata
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',), # Make it collapsible
        }),
    )

    list_display = [
        'username', 'email', 'first_name', 'last_name', 'department',
        'role', 'is_approved', 'is_active', 'is_staff', 'is_superuser' # Added is_staff, is_superuser
    ]
    list_filter = ['role', 'is_approved', 'department', 'is_active', 'is_staff', 'is_superuser'] # Added is_staff, is_superuser
    search_fields = ['username', 'email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at'] # Added readonly fields
    actions = ['approve_users', 'make_admin', 'make_user', 'deactivate_users', 'activate_users'] # Added new actions
    list_per_page = 20 # Add pagination limit

    def approve_users(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} users approved successfully.')
    approve_users.short_description = "Approve selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated successfully.')
    deactivate_users.short_description = "Deactivate selected users"

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated successfully.')
    activate_users.short_description = "Activate selected users"

    def make_admin(self, request, queryset):
        updated = queryset.update(role='admin', is_staff=True) # Make staff for admin role
        self.message_user(request, f'{updated} users made admin.')
    make_admin.short_description = "Make selected users admin"

    def make_user(self, request, queryset):
        updated = queryset.update(role='user', is_staff=False) # Remove staff for regular user
        self.message_user(request, f'{updated} users made regular user.')
    make_user.short_description = "Make selected users regular user"


@admin.register(UserRegistrationRequest)
class UserRegistrationRequestAdmin(admin.ModelAdmin):
    list_display = [
        'username', 'first_name', 'last_name', 'email',
        'department', 'whatsapp_number', 'status', 'get_reviewed_by', 'reviewed_at',
        'get_code_status', 'created_at',
    ]
    list_filter = ['status', 'department', 'created_at', 'reviewed_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'whatsapp_number']
    readonly_fields = [
        'one_time_code', 'code_generated_at', 'code_expires_at',
        'reviewed_by', 'reviewed_at', 'created_at', 'updated_at' # Added reviewed_by, reviewed_at, created_at, updated_at
    ]
    list_per_page = 20 # Add pagination limit

    fieldsets = [
        ('User Information', {
            'fields': ['first_name', 'last_name', 'username', 'email', 'department', 'whatsapp_number']
        }),
        ('Request Status & Review', { # Renamed for clarity
            'fields': ['status', 'reviewed_by', 'reviewed_at', 'admin_notes']
        }),
        ('One-Time Code Details', { # Renamed for clarity
            'fields': ['one_time_code', 'code_generated_at', 'code_expires_at'],
            'classes': ['collapse']
        }),
        ('Timestamps', { # New fieldset for metadata
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    ]

    actions = ['approve_selected_requests', 'reject_selected_requests', 'generate_codes_for_approved'] # Renamed actions for clarity

    def get_reviewed_by(self, obj):
        return obj.reviewed_by.username if obj.reviewed_by else 'N/A'
    get_reviewed_by.short_description = 'Reviewed By'

    def get_code_status(self, obj):
        if obj.one_time_code and obj.is_code_valid():
            return format_html('<span style="color: green;">Valid (Expires: {})</span>', obj.code_expires_at.strftime("%Y-%m-%d %H:%M"))
        elif obj.one_time_code and not obj.is_code_valid():
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return 'No Code'
    get_code_status.short_description = 'Code Status'

    def approve_selected_requests(self, request, queryset):
        updated_count = 0
        for req in queryset.filter(status='pending'):
            # 1. Approve the request
            req.approve_request(request.user) # This sets status to 'approved' and reviewed_by/at

            # 2. Create the CustomUser instance
            try:
                CustomUser.objects.create_user(
                    username=req.username,
                    email=req.email,
                    first_name=req.first_name,
                    last_name=req.last_name,
                    department=req.department,
                    whatsapp_number=req.whatsapp_number,
                    is_approved=True, # User is approved upon creation from request
                    is_active=True,   # Also activate the user
                )
                updated_count += 1
            except Exception as e:
                self.message_user(request, f'Failed to create user {req.username}: {e}', level='error')
                # Optionally revert the request status if user creation fails
                req.status = 'pending'
                req.save()
        if updated_count > 0:
            self.message_user(request, f'{updated_count} registration requests approved and users created.')
        else:
            self.message_user(request, 'No pending requests were selected or could be approved.', level='warning')
    approve_selected_requests.short_description = "Approve selected requests and create users"

    def reject_selected_requests(self, request, queryset):
        updated = 0
        for obj in queryset.filter(status='pending'):
            obj.reject_request(request.user, notes="Rejected by admin action.") # Add a default note
            updated += 1
        if updated > 0:
            self.message_user(request, f'{updated} requests rejected.')
        else:
            self.message_user(request, 'No pending requests were selected or could be rejected.', level='warning')
    reject_selected_requests.short_description = "Reject selected requests"

    def generate_codes_for_approved(self, request, queryset):
        updated = 0
        for obj in queryset.filter(status='approved'): # Only generate for approved requests
            if not obj.one_time_code or not obj.is_code_valid(): # Only generate if no code or expired
                obj.generate_one_time_code()
                updated += 1
            else:
                self.message_user(request, f'Code for {obj.username} is already valid.', level='warning')
        if updated > 0:
            self.message_user(request, f'{updated} one-time codes generated/refreshed for approved requests.')
        else:
            self.message_user(request, 'No approved requests needed new one-time codes.', level='warning')
    generate_codes_for_approved.short_description = "Generate/Refresh one-time codes for approved requests"

    # Remove action_buttons as we're relying on standard admin actions
    # def action_buttons(self, obj):
    #     if obj.status == 'pending':
    #         # This would require a custom admin view to handle a single action
    #         # For simplicity, relying on the admin actions for approve/reject.
    #         return format_html('<span style="color: grey;">Use Admin Actions</span>')
    #     return '-'
    # action_buttons.short_description = 'Actions'