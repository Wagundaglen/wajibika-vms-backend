from django.contrib import admin
from django.utils.html import format_html
from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'to_user',
        'display_sender',
        'category',
        'sentiment',  # raw editable
        'sentiment_colored',  # colored badge
        'status',  # raw editable
        'status_colored',  # colored badge
        'created_at',
        'anonymous',
    )
    list_filter = ('status', 'sentiment', 'category', 'anonymous', 'created_at')
    search_fields = ('message', 'to_user__username', 'from_user__username')
    list_editable = ('status', 'sentiment')
    ordering = ('-created_at',)  # newest first
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
