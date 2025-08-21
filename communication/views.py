from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q, Count
from .models import Notification, Announcement, Message, Event, CommunicationPreference
from .forms import AnnouncementForm, MessageForm, EventForm, CommunicationPreferenceForm

class DashboardView(LoginRequiredMixin, ListView):
    """Main dashboard view with role-specific content"""
    template_name = 'communication/dashboard.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user, is_read=False)[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get unread messages count
        context['unread_messages'] = Message.objects.filter(
            recipient=user, 
            is_read=False,
            is_deleted_by_recipient=False
        ).count()
        
        # Get upcoming events
        context['upcoming_events'] = Event.objects.filter(
            Q(attendees=user) | Q(is_public=True),
            start_time__gt=timezone.now()
        ).order_by('start_time')[:5]
        
        # Get announcements for user's role
        user_role = user.role
        context['announcements'] = Announcement.objects.filter(
            is_active=True,
            target_roles__contains=user_role
        ).order_by('-created_at')[:3]
        
        # Role-specific context
        if user.role == 'Admin':
            context['admin_stats'] = self.get_admin_stats()
        elif user.role == 'Coordinator':
            context['coordinator_stats'] = self.get_coordinator_stats()
            
        return context
    
    def get_admin_stats(self):
        return {
            'total_users': User.objects.count(),
            'total_events': Event.objects.count(),
            'pending_announcements': Announcement.objects.filter(is_active=False).count(),
        }
    
    def get_coordinator_stats(self):
        return {
            'my_events': Event.objects.filter(organizer=self.request.user).count(),
            'upcoming_my_events': Event.objects.filter(
                organizer=self.request.user,
                start_time__gt=timezone.now()
            ).count(),
        }

class NotificationListView(LoginRequiredMixin, ListView):
    """List all notifications for the current user"""
    model = Notification
    template_name = 'communication/notifications.html'
    context_object_name = 'notifications'
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class NotificationDetailView(LoginRequiredMixin, DetailView):
    """View a single notification and mark it as read"""
    model = Notification
    template_name = 'communication/notification_detail.html'
    
    def get_object(self):
        obj = super().get_object()
        if not obj.is_read and obj.recipient == self.request.user:
            obj.mark_as_read()
        return obj

class AnnouncementListView(LoginRequiredMixin, ListView):
    """List all announcements relevant to the user's role"""
    model = Announcement
    template_name = 'communication/announcements.html'
    context_object_name = 'announcements'
    
    def get_queryset(self):
        user_role = self.request.user.role
        return Announcement.objects.filter(
            is_active=True,
            target_roles__contains=user_role
        )

class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    """View a single announcement"""
    model = Announcement
    template_name = 'communication/announcement_detail.html'

class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new announcement (Admin/Coordinator only)"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'communication/announcement_form.html'
    
    def test_func(self):
        return self.request.user.role in ['Admin', 'Coordinator']
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        
        # Create notifications for targeted users
        self.create_announcement_notifications(form.instance)
        
        messages.success(self.request, "Announcement created successfully!")
        return response
    
    def create_announcement_notifications(self, announcement):
        target_roles = announcement.get_target_roles_list()
        recipients = User.objects.filter(role__in=target_roles)
        
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                title=f"New Announcement: {announcement.title}",
                message=announcement.content[:200] + "..." if len(announcement.content) > 200 else announcement.content,
                level='info',
                link=reverse('communication:announcement_detail', kwargs={'pk': announcement.pk})
            )

class MessageListView(LoginRequiredMixin, ListView):
    """List all messages for the current user"""
    model = Message
    template_name = 'communication/messages.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        return Message.objects.filter(
            Q(sender=self.request.user, is_deleted_by_sender=False) | 
            Q(recipient=self.request.user, is_deleted_by_recipient=False)
        ).distinct()

class MessageDetailView(LoginRequiredMixin, DetailView):
    """View a single message"""
    model = Message
    template_name = 'communication/message_detail.html'
    
    def get_object(self):
        obj = super().get_object()
        # Mark as read if recipient is viewing
        if obj.recipient == self.request.user and not obj.is_read:
            obj.mark_as_read()
        return obj

class MessageCreateView(LoginRequiredMixin, CreateView):
    """Create a new message"""
    model = Message
    form_class = MessageForm
    template_name = 'communication/message_form.html'
    
    def form_valid(self, form):
        form.instance.sender = self.request.user
        response = super().form_valid(form)
        
        # Create notification for recipient
        Notification.objects.create(
            recipient=form.instance.recipient,
            title=f"New Message: {form.instance.subject}",
            message=form.instance.body[:200] + "..." if len(form.instance.body) > 200 else form.instance.body,
            level='info',
            link=reverse('communication:message_detail', kwargs={'pk': form.instance.pk})
        )
        
        # Send email notification if enabled
        self.send_email_notification(form.instance)
        
        messages.success(self.request, "Message sent successfully!")
        return response
    
    def send_email_notification(self, message):
        try:
            recipient_prefs = CommunicationPreference.objects.get(user=message.recipient)
            if recipient_prefs.email_notifications:
                subject = f"New Message from {message.sender.get_full_name() or message.sender.username}"
                body = render_to_string('communication/email/message_notification.html', {
                    'message': message,
                    'user': message.recipient,
                    'site_url': settings.SITE_URL,
                })
                send_mail(
                    subject,
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [message.recipient.email],
                    html_message=body,
                    fail_silently=True,
                )
        except CommunicationPreference.DoesNotExist:
            pass

class EventListView(LoginRequiredMixin, ListView):
    """List all events"""
    model = Event
    template_name = 'communication/events.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return Event.objects.filter(
            Q(attendees=self.request.user) | Q(is_public=True)
        ).distinct()

class EventDetailView(LoginRequiredMixin, DetailView):
    """View a single event"""
    model = Event
    template_name = 'communication/event_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_attending'] = self.object.attendees.filter(pk=self.request.user.pk).exists()
        return context

class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new event (Admin/Coordinator only)"""
    model = Event
    form_class = EventForm
    template_name = 'communication/event_form.html'
    
    def test_func(self):
        return self.request.user.role in ['Admin', 'Coordinator']
    
    def form_valid(self, form):
        form.instance.organizer = self.request.user
        response = super().form_valid(form)
        
        # Create notifications for potential attendees
        self.create_event_notifications(form.instance)
        
        messages.success(self.request, "Event created successfully!")
        return response
    
    def create_event_notifications(self, event):
        # Notify all users about the new event
        recipients = User.objects.all()
        
        for recipient in recipients:
            Notification.objects.create(
                recipient=recipient,
                title=f"New Event: {event.title}",
                message=f"A new event has been scheduled: {event.title} on {event.start_time.strftime('%Y-%m-%d %H:%M')}",
                level='info',
                link=reverse('communication:event_detail', kwargs={'pk': event.pk})
            )

@login_required
def mark_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@login_required
def rsvp_event(request, pk, action):
    """RSVP to an event"""
    event = get_object_or_404(Event, pk=pk)
    
    if action == 'attend':
        event.attendees.add(request.user)
        messages.success(request, f"You are now attending {event.title}")
    elif action == 'decline':
        event.attendees.remove(request.user)
        messages.success(request, f"You are no longer attending {event.title}")
    
    return redirect('communication:event_detail', pk=pk)

@login_required
def communication_preferences(request):
    """Update communication preferences"""
    try:
        preferences = CommunicationPreference.objects.get(user=request.user)
    except CommunicationPreference.DoesNotExist:
        preferences = CommunicationPreference(user=request.user)
    
    if request.method == 'POST':
        form = CommunicationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, "Your communication preferences have been updated.")
            return redirect('communication:dashboard')
    else:
        form = CommunicationPreferenceForm(instance=preferences)
    
    return render(request, 'communication/preferences.html', {'form': form})