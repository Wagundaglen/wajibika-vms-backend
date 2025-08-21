# feedback/templatetags/feedback_extras.py

from django import template

register = template.Library()

@register.filter
def count_votes(queryset, vote_type):
    return queryset.filter(vote_type=vote_type).count()