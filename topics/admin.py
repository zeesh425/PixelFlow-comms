# topics/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Topic, CategoryRestriction, TopicRestriction
from users.models import CustomUser # Import CustomUser for clarity, though it might be implicitly available

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'get_topics_count', 'created_by', 'created_at', 'is_active'] # Added description, get_topics_count
    list_filter = ['is_active', 'created_at', 'created_by'] # Added created_by to filter
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by'] # created_by should be readonly after creation
    actions = ['activate_categories', 'deactivate_categories'] # New actions
    list_per_page = 20 # Add pagination limit

    def get_topics_count(self, obj):
        return obj.topics.count()
    get_topics_count.short_description = 'Topics Count'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def activate_categories(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories activated.')
    activate_categories.short_description = "Activate selected categories"

    def deactivate_categories(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories deactivated.')
    deactivate_categories.short_description = "Deactivate selected categories"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'created_by', 'total_messages', 'last_activity',
        'is_active', 'is_closed', 'is_pinned', 'is_locked', 'is_archived',
        'created_at'
    ]
    list_filter = [
        'is_active', 'is_closed', 'is_pinned', 'is_locked', 'is_archived',
        'category', 'created_by', 'created_at', 'last_activity' # Added created_by, last_activity
    ]
    search_fields = ['title', 'description', 'created_by__username', 'category__name'] # Can search by related fields
    readonly_fields = [
        'created_at', 'updated_at', 'last_activity', 'total_messages',
        'closed_by', 'closed_at', 'pinned_by', 'pinned_at',
        'locked_by', 'locked_at', 'archived_by', 'archived_at',
        'created_by' # created_by should be readonly after creation
    ]
    list_per_page = 20 # Add pagination limit

    fieldsets = [
        (None, {
            'fields': ['title', 'description', 'category', 'created_by']
        }),
        ('Topic Status', {
            'fields': [
                ('is_active',), # Grouped for better layout
                ('is_closed', 'closed_by', 'closed_at'),
                ('is_pinned', 'pinned_by', 'pinned_at'),
                ('is_locked', 'locked_by', 'locked_at'),
                ('is_archived', 'archived_by', 'archived_at'),
            ],
            'classes': ['wide', 'extrapretty'], # Django admin CSS classes
        }),
        ('Metrics & Timestamps', {
            'fields': ['total_messages', 'last_activity', 'created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]

    actions = [
        'activate_topics', 'deactivate_topics',
        'close_topics', 'reopen_topics',
        'pin_topics', 'unpin_topics',
        'lock_topics', 'unlock_topics',
        'archive_topics', 'unarchive_topics',
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # Custom actions for topic status
    def activate_topics(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} topics activated.')
    activate_topics.short_description = "Activate selected topics"

    def deactivate_topics(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} topics deactivated.')
    deactivate_topics.short_description = "Deactivate selected topics"

    def close_topics(self, request, queryset):
        queryset.update(is_closed=True, closed_by=request.user, closed_at=timezone.now())
        self.message_user(request, f'{queryset.count()} topics closed.')
    close_topics.short_description = "Close selected topics"

    def reopen_topics(self, request, queryset):
        queryset.update(is_closed=False, closed_by=None, closed_at=None)
        self.message_user(request, f'{queryset.count()} topics reopened.')
    reopen_topics.short_description = "Reopen selected topics"

    def pin_topics(self, request, queryset):
        queryset.update(is_pinned=True, pinned_by=request.user, pinned_at=timezone.now())
        self.message_user(request, f'{queryset.count()} topics pinned.')
    pin_topics.short_description = "Pin selected topics"

    def unpin_topics(self, request, queryset):
        queryset.update(is_pinned=False, pinned_by=None, pinned_at=None)
        self.message_user(request, f'{queryset.count()} topics unpinned.')
    unpin_topics.short_description = "Unpin selected topics"

    def lock_topics(self, request, queryset):
        queryset.update(is_locked=True, locked_by=request.user, locked_at=timezone.now())
        self.message_user(request, f'{queryset.count()} topics locked.')
    lock_topics.short_description = "Lock selected topics"

    def unlock_topics(self, request, queryset):
        queryset.update(is_locked=False, locked_by=None, locked_at=None)
        self.message_user(request, f'{queryset.count()} topics unlocked.')
    unlock_topics.short_description = "Unlock selected topics"

    def archive_topics(self, request, queryset):
        queryset.update(is_archived=True, archived_by=request.user, archived_at=timezone.now())
        self.message_user(request, f'{queryset.count()} topics archived.')
    archive_topics.short_description = "Archive selected topics"

    def unarchive_topics(self, request, queryset):
        queryset.update(is_archived=False, archived_by=None, archived_at=None)
        self.message_user(request, f'{queryset.count()} topics unarchived.')
    unarchive_topics.short_description = "Unarchive selected topics"



# Optional: Inlines for restrictions
class CategoryRestrictionInline(admin.TabularInline):
    model = CategoryRestriction
    extra = 1 # Number of empty forms to display
    fields = ('user', 'can_view', 'can_reply')
    readonly_fields = ('created_by', 'created_at') # Make these readonly in inline as well

class TopicRestrictionInline(admin.TabularInline):
    model = TopicRestriction
    extra = 1
    fields = ('user', 'can_view', 'can_reply')
    readonly_fields = ('created_by', 'created_at')

# Re-register CategoryAdmin and TopicAdmin to include inlines
# You'd typically add these inlines to the fieldsets or directly to the class
# For now, we'll keep them separate to demonstrate the inline classes.
# To use them, you would add `inlines = [CategoryRestrictionInline]` to CategoryAdmin
# and `inlines = [TopicRestrictionInline]` to TopicAdmin.

# Example of how to add inlines:
# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     # ... existing code ...
#     inlines = [CategoryRestrictionInline]
#     # ... existing code ...

# @admin.register(Topic)
# class TopicAdmin(admin.ModelAdmin):
#     # ... existing code ...
#     inlines = [TopicRestrictionInline]
#     # ... existing code ...


@admin.register(CategoryRestriction)
class CategoryRestrictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'can_view', 'can_reply', 'get_created_by_username', 'created_at'] # Added get_created_by_username
    list_filter = ['can_view', 'can_reply', 'created_at', 'created_by'] # Added created_by to filter
    search_fields = ['user__username', 'category__name', 'created_by__username'] # Added created_by search
    readonly_fields = ['created_at', 'created_by'] # created_by should be readonly
    list_per_page = 20 # Add pagination limit

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else 'N/A'
    get_created_by_username.short_description = 'Created By'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TopicRestriction)
class TopicRestrictionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'can_view', 'can_reply', 'get_created_by_username', 'created_at'] # Added get_created_by_username
    list_filter = ['can_view', 'can_reply', 'created_at', 'created_by'] # Added created_by to filter
    search_fields = ['user__username', 'topic__title', 'created_by__username'] # Added created_by search
    readonly_fields = ['created_at', 'created_by'] # created_by should be readonly
    list_per_page = 20 # Add pagination limit

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else 'N/A'
    get_created_by_username.short_description = 'Created By'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)