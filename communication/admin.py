from django.contrib import admin
from .models import Notification, Announcement, Message, Event, CommunicationPreference

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'level', 'is_read', 'created_at')
    list_filter = ('level', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    actions = [mark_as_read]

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'priority', 'target_roles', 'is_active', 'created_at')
    list_filter = ('priority', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()
    date_hierarchy = 'created_at'
    
    def get_target_roles_display(self, obj):
        return ", ".join(obj.get_target_roles_list())
    get_target_roles_display.short_description = 'Target Roles'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set author on creation
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'recipient', 'is_read', 'timestamp')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('subject', 'body', 'sender__username', 'recipient__username')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} messages marked as read.")
    mark_as_read.short_description = "Mark selected as read"
    
    actions = [mark_as_read]

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_time', 'end_time', 'is_public', 'reminder_sent')
    list_filter = ('is_public', 'reminder_sent', 'start_time')
    search_fields = ('title', 'description', 'location', 'organizer__username')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('attendees',)
    date_hierarchy = 'start_time'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set organizer on creation
            obj.organizer = request.user
        super().save_model(request, obj, form, change)

@admin.register(CommunicationPreference)
class CommunicationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications', 'in_app_notifications')
    list_filter = ('email_notifications', 'sms_notifications', 'in_app_notifications')
    search_fields = ('user__username', 'user__email')