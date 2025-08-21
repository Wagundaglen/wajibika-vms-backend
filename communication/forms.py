from django import forms
from .models import Announcement, Message, Event, CommunicationPreference
from django.contrib.auth import get_user_model

User = get_user_model()

class AnnouncementForm(forms.ModelForm):
    target_roles = forms.MultipleChoiceField(
        choices=Announcement._meta.get_field('target_roles').choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select which roles should see this announcement"
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'target_roles', 'is_active', 'requires_acknowledgment']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select the recipient"
    )
    
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }

class EventForm(forms.ModelForm):
    attendees = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select specific attendees (leave empty for public event)"
    )
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time', 'is_public', 'attendees']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class CommunicationPreferenceForm(forms.ModelForm):
    class Meta:
        model = CommunicationPreference
        fields = [
            'email_notifications', 
            'sms_notifications', 
            'in_app_notifications',
            'event_reminders',
            'announcement_alerts',
            'message_alerts'
        ]
        widgets = {
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'event_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'announcement_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }