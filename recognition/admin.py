from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

from .models import Recognition, Badge


@admin.register(Recognition)
class RecognitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient",  
        "recognition_type",
        "title",
        "points_awarded",
        "badge",
        "certificate_link",
        "date_awarded",
    )
    list_filter = ("recognition_type", "badge", "date_awarded")
    search_fields = (
        "volunteer__username",
        "volunteer__first_name",
        "volunteer__last_name",
        "title",
    )
    ordering = ("-date_awarded",)

    def recipient(self, obj):
        return obj.volunteer.get_full_name() or obj.volunteer.username
    recipient.admin_order_field = "volunteer__username"
    recipient.short_description = "Recipient"

    def certificate_link(self, obj):
        if obj.certificate:
            return format_html("<a href='{}' target='_blank'>📜 Download</a>", obj.certificate.url)
        return "-"
    certificate_link.short_description = "Certificate"

    # --- Admin Actions ---
    actions = ["award_bronze_badge", "award_silver_badge", "award_gold_badge"]

    def _assign_badge(self, request, queryset, badge_name, msg):
        badge, _ = Badge.objects.get_or_create(
            name=badge_name,
            defaults={"description": f"{badge_name} awarded for recognition."}
        )
        for recognition in queryset:
            recognition.badge = badge
            recognition.recognition_type = "badge"
            recognition.save()
        self.message_user(request, msg)

    def award_bronze_badge(self, request, queryset):
        self._assign_badge(request, queryset, "Bronze Volunteer", "🥉 Bronze badge awarded successfully.")
    award_bronze_badge.short_description = "Award Bronze Badge"

    def award_silver_badge(self, request, queryset):
        self._assign_badge(request, queryset, "Silver Volunteer", "🥈 Silver badge awarded successfully.")
    award_silver_badge.short_description = "Award Silver Badge"

    def award_gold_badge(self, request, queryset):
        self._assign_badge(request, queryset, "Gold Volunteer", "🥇 Gold badge awarded successfully.")
    award_gold_badge.short_description = "Award Gold Badge"


# --- Custom Dashboard Widget ---
class CustomAdminSite(AdminSite):
    site_header = "Volunteer Management System Admin"
    site_title = "VMS Admin"
    index_title = "Dashboard"

    def index(self, request, extra_context=None):
        # Aggregate recognition data
        total_points = Recognition.objects.aggregate(total=Sum("points_awarded"))["total"] or 0
        total_certificates = Recognition.objects.filter(recognition_type="certificate").count()
        total_badges = Recognition.objects.filter(recognition_type="badge").count()

        # Top 5 volunteers by points
        top_volunteers = (
            Recognition.objects.values(
                "volunteer__username",
                "volunteer__first_name",
                "volunteer__last_name",
            )
            .annotate(total_points=Sum("points_awarded"))
            .order_by("-total_points")[:5]
        )

        extra_context = extra_context or {}
        extra_context["total_points"] = total_points
        extra_context["total_certificates"] = total_certificates
        extra_context["total_badges"] = total_badges
        extra_context["top_volunteers"] = top_volunteers

        return TemplateResponse(request, "admin/custom_index.html", extra_context)


# Swap Django’s default admin site with our custom one
custom_admin_site = CustomAdminSite(name="custom_admin")
