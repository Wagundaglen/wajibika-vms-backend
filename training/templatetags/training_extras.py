from django import template

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filter a queryset by status"""
    return queryset.filter(status=status)

@register.filter
def filter_completed(queryset):
    """Filter a queryset by is_completed=True"""
    return queryset.filter(is_completed=True)