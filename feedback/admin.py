from django.contrib import admin
from django.utils.html import format_html
from .models import Feedback, Survey, Question, SurveyResponse


# -------------------------------------------------
# Feedback Admin
# -------------------------------------------------
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'to_user',
        'display_sender',
        'category',
        'sentiment',
        'sentiment_colored',
        'status',
        'status_colored',
        'created_at',
        'anonymous',
    )
    list_filter = ('status', 'sentiment', 'category', 'anonymous', 'created_at')
    search_fields = ('message', 'to_user__username', 'from_user__username')
    list_editable = ('status', 'sentiment')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def display_sender(self, obj):
        return obj.from_user if obj.from_user else "Anonymous"
    display_sender.short_description = "From User"

    def status_colored(self, obj):
        colors = {
            'open': 'red',
            'reviewed': 'orange',
            'resolved': 'green'
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colored.short_description = "Status (Colored)"

    def sentiment_colored(self, obj):
        colors = {
            'positive': 'green',
            'neutral': 'gray',
            'negative': 'red'
        }
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            colors.get(obj.sentiment, 'black'),
            obj.get_sentiment_display()
        )
    sentiment_colored.short_description = "Sentiment (Colored)"


# -------------------------------------------------
# Survey Admin
# -------------------------------------------------
@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


# -------------------------------------------------
# Question Admin
# -------------------------------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'survey', 'question_type')
    list_filter = ('question_type', 'survey')
    search_fields = ('text',)
    ordering = ('id',)


# -------------------------------------------------
# Survey Response Admin
# -------------------------------------------------
@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'survey', 'status', 'submitted_at')  # ✅ fixed
    list_filter = ('status', 'survey', 'submitted_at')           # ✅ fixed
    search_fields = ('user__username', 'survey__title')
    ordering = ('-submitted_at',)                                # ✅ fixed
    date_hierarchy = 'submitted_at'                              # ✅ fixed
