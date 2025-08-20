from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import RecognitionProfile, Team, Badge, Recognition, PointsLog, Leaderboard
from .utils import update_leaderboard

@admin.register(RecognitionProfile)
class RecognitionProfileAdmin(admin.ModelAdmin):
    list_display = ['volunteer_info', 'role', 'team', 'total_points', 'join_date', 'recognition_count']
    list_filter = ['team', 'volunteer__role', 'join_date']
    search_fields = ['volunteer__username', 'volunteer__email', 'volunteer__first_name', 'volunteer__last_name']
    readonly_fields = ['join_date']
    
    def volunteer_info(self, obj):
        return format_html(
            '<b>{}</b><br>{}<br>{}',
            obj.volunteer.get_full_name() or obj.volunteer.username,
            obj.volunteer.email,
            obj.volunteer.phone or "No phone"
        )
    volunteer_info.short_description = "Volunteer"
    
    def role(self, obj):
        return obj.volunteer.role
    role.short_description = "Role"
    role.admin_order_field = 'volunteer__role'
    
    def recognition_count(self, obj):
        return obj.volunteer.recognitions_received.count()
    recognition_count.short_description = "Recognitions"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer', 'team')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'member_count', 'total_points', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def member_count(self, obj):
        return obj.recognitionprofile_set.count()
    member_count.short_description = "Members"
    
    def total_points(self, obj):
        total = RecognitionProfile.objects.filter(team=obj).aggregate(
            total=Sum('total_points')
        )['total'] or 0
        return total
    total_points.short_description = "Total Points"

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'scope', 'points_value', 'team', 'award_count', 'created_by', 'created_at']
    list_filter = ['scope', 'team', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def award_count(self, obj):
        return obj.recognition_set.count()
    award_count.short_description = "Times Awarded"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('team', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Recognition)
class RecognitionAdmin(admin.ModelAdmin):
    list_display = ['volunteer_info', 'giver_info', 'badge', 'points', 'team', 'created_at', 'message_preview']
    list_filter = ['team', 'created_at', 'badge', 'volunteer__role', 'giver__role']
    search_fields = [
        'volunteer__username', 'giver__username', 
        'volunteer__first_name', 'volunteer__last_name',
        'giver__first_name', 'giver__last_name',
        'message'
    ]
    readonly_fields = ['created_at']
    
    def volunteer_info(self, obj):
        return format_html(
            '<b>{}</b><br>{}',
            obj.volunteer.get_full_name() or obj.volunteer.username,
            obj.volunteer.role
        )
    volunteer_info.short_description = "Volunteer"
    
    def giver_info(self, obj):
        return format_html(
            '<b>{}</b><br>{}',
            obj.giver.get_full_name() or obj.giver.username,
            obj.giver.role
        )
    giver_info.short_description = "Given By"
    
    def message_preview(self, obj):
        if obj.message:
            return (obj.message[:50] + '...') if len(obj.message) > 50 else obj.message
        return "-"
    message_preview.short_description = "Message"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'volunteer', 'giver', 'badge', 'team'
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Limit volunteer choices based on user role
        if db_field.name == "volunteer" and not request.user.is_superuser:
            if request.user.role == 'Coordinator':
                # Coordinators can only recognize volunteers in their team
                try:
                    team = request.user.recognitionprofile.team
                    kwargs["queryset"] = RecognitionProfile.objects.filter(team=team)
                except:
                    pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        # Set team based on volunteer's team
        if not obj.team and obj.volunteer:
            try:
                obj.team = obj.volunteer.recognitionprofile.team
            except RecognitionProfile.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

@admin.register(PointsLog)
class PointsLogAdmin(admin.ModelAdmin):
    list_display = ['volunteer_info', 'points', 'activity', 'timestamp', 'recognition_badge']
    list_filter = ['timestamp', 'volunteer__role']
    search_fields = ['volunteer__username', 'activity']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def volunteer_info(self, obj):
        return format_html(
            '<b>{}</b><br>{}',
            obj.volunteer.get_full_name() or obj.volunteer.username,
            obj.volunteer.role
        )
    volunteer_info.short_description = "Volunteer"
    
    def recognition_badge(self, obj):
        if obj.related_recognition and obj.related_recognition.badge:
            return obj.related_recognition.badge.name
        return "-"
    recognition_badge.short_description = "Badge"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'volunteer', 'related_recognition', 'related_recognition__badge'
        )

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['volunteer_info', 'rank', 'points', 'timeframe', 'team', 'calculated_at']
    list_filter = ['timeframe', 'team', 'volunteer__role']
    search_fields = ['volunteer__username', 'volunteer__first_name', 'volunteer__last_name']
    readonly_fields = ['calculated_at']
    
    actions = ['update_weekly', 'update_monthly', 'update_all_time', 'update_all_for_team']
    
    def volunteer_info(self, obj):
        return format_html(
            '<b>{}</b><br>{}',
            obj.volunteer.get_full_name() or obj.volunteer.username,
            obj.volunteer.role
        )
    volunteer_info.short_description = "Volunteer"
    
    def update_weekly(self, request, queryset):
        """Update weekly leaderboard"""
        try:
            result = update_leaderboard(timeframe='weekly')
            if result['success']:
                self.message_user(
                    request, 
                    f"Weekly leaderboard updated: Deleted {result['deleted']}, Created {result['created']}", 
                    level='success'
                )
            else:
                self.message_user(
                    request, 
                    f"Error updating weekly leaderboard: {result['error']}", 
                    level='error'
                )
        except Exception as e:
            self.message_user(request, f"Error updating weekly leaderboard: {str(e)}", level='error')
    update_weekly.short_description = "Update weekly leaderboard"
    
    def update_monthly(self, request, queryset):
        """Update monthly leaderboard"""
        try:
            result = update_leaderboard(timeframe='monthly')
            if result['success']:
                self.message_user(
                    request, 
                    f"Monthly leaderboard updated: Deleted {result['deleted']}, Created {result['created']}", 
                    level='success'
                )
            else:
                self.message_user(
                    request, 
                    f"Error updating monthly leaderboard: {result['error']}", 
                    level='error'
                )
        except Exception as e:
            self.message_user(request, f"Error updating monthly leaderboard: {str(e)}", level='error')
    update_monthly.short_description = "Update monthly leaderboard"
    
    def update_all_time(self, request, queryset):
        """Update all-time leaderboard"""
        try:
            result = update_leaderboard(timeframe='all_time')
            if result['success']:
                self.message_user(
                    request, 
                    f"All-time leaderboard updated: Deleted {result['deleted']}, Created {result['created']}", 
                    level='success'
                )
            else:
                self.message_user(
                    request, 
                    f"Error updating all-time leaderboard: {result['error']}", 
                    level='error'
                )
        except Exception as e:
            self.message_user(request, f"Error updating all-time leaderboard: {str(e)}", level='error')
    update_all_time.short_description = "Update all-time leaderboard"
    
    def update_all_for_team(self, request, queryset):
        """Update all timeframes for selected teams"""
        updated = 0
        errors = []
        
        for team in queryset:
            try:
                for timeframe in ['weekly', 'monthly', 'all_time']:
                    result = update_leaderboard(timeframe, team)
                    if not result['success']:
                        errors.append(f"Team {team.name}: {result['error']}")
                updated += 1
            except Exception as e:
                errors.append(f"Team {team.name}: {str(e)}")
        
        if updated:
            self.message_user(request, f"Successfully updated leaderboards for {updated} teams", level='success')
        if errors:
            self.message_user(request, f"Errors occurred: {'; '.join(errors)}", level='error')
    update_all_for_team.short_description = "Update all leaderboards for selected teams"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('volunteer', 'team')
    
    def has_add_permission(self, request):
        # Don't allow manual creation of leaderboard entries
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow manual changes to leaderboard entries
        return False

# Admin site customization
admin.site.site_header = "Wajibika Initiative Administration"
admin.site.site_title = "Wajibika Admin Portal"
admin.site.index_title = "Welcome to Wajibika Volunteer Management System"