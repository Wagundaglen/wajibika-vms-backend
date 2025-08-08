from django.contrib import admin
from django.utils.html import format_html
from .models import Recognition


@admin.register(Recognition)
class RecognitionAdmin(admin.ModelAdmin):
    list_display = (
        'recipient',
        'title',
        'recognition_type',
        'badge',
        'points_awarded',
        'date_awarded',
        'certificate_link',  # New column
    )
    list_filter = ('recognition_type', 'badge', 'date_awarded')
    search_fields = ('recipient__username', 'title', 'badge', 'description')
    readonly_fields = ('date_awarded',)

    fieldsets = (
        ("Recipient Info", {
            "fields": ('recipient', 'recognition_type')
        }),
        ("Recognition Details", {
            "fields": ('title', 'description', 'points_awarded', 'badge', 'certificate')
        }),
        ("Timestamps", {
            "fields": ('date_awarded',)
        }),
    )

    def certificate_link(self, obj):
        if obj.certificate:
            return format_html(
                '<a href="{}" target="_blank">📄 Download</a>',
                obj.certificate.url
            )
        return "-"
    certificate_link.short_description = "Certificate"
