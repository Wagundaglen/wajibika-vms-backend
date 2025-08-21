from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Feedback, FeedbackCategory, FeedbackResponse, FeedbackVote, FeedbackAnalytics
from .forms import FeedbackForm, FeedbackResponseForm


class FeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'feedback/feedback_list.html'
    context_object_name = 'feedback_list'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'category', 'assigned_to')
        
        # Filter based on user role
        if self.request.user.role == 'Volunteer':
            # Volunteers see only their own feedback
            queryset = queryset.filter(user=self.request.user)
        elif self.request.user.role == 'Coordinator':
            # Coordinators see feedback from their team
            queryset = queryset.filter(
                Q(user__profile__team=self.request.user.profile.team) |
                Q(assigned_to=self.request.user)
            )
        
        # Apply filters
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        sentiment_filter = self.request.GET.get('sentiment')
        if sentiment_filter:
            queryset = queryset.filter(sentiment=sentiment_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Feedback.STATUS_CHOICES
        context['sentiment_choices'] = Feedback.SENTIMENT_CHOICES
        
        # Add user's feedback
        if self.request.user.is_authenticated:
            context['user_feedback'] = Feedback.objects.filter(user=self.request.user).order_by('-created_at')
        
        return context


class FeedbackDetailView(LoginRequiredMixin, DetailView):
    model = Feedback
    template_name = 'feedback/feedback_detail.html'
    context_object_name = 'feedback'
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'user', 'category', 'assigned_to'
        ).prefetch_related('responses', 'votes')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has voted
        if self.request.user.is_authenticated:
            user_vote = FeedbackVote.objects.filter(
                feedback=self.object,
                user=self.request.user
            ).first()
            context['user_vote'] = user_vote
        
        # Get similar feedback
        context['similar_feedback'] = Feedback.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:5]
        
        # Add vote counts
        context['upvotes_count'] = self.object.votes.filter(vote_type='up').count()
        context['downvotes_count'] = self.object.votes.filter(vote_type='down').count()
        
        return context


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback/feedback_form.html'
    success_url = reverse_lazy('feedback:feedback_list')
    
    def get_form_kwargs(self):
        """Pass request to form for custom validation"""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_initial(self):
        """Set initial values for the form"""
        initial = super().get_initial()
        # Set initial user if not anonymous
        if not self.request.GET.get('anonymous', 'false').lower() == 'true':
            initial['user'] = self.request.user
        return initial
    
    def get_context_data(self, **kwargs):
        """Add additional context to the template"""
        context = super().get_context_data(**kwargs)
        context['categories'] = FeedbackCategory.objects.all()
        context['is_anonymous'] = self.request.GET.get('anonymous', 'false').lower() == 'true'
        return context
    
    def form_valid(self, form):
        """Process valid form submission"""
        try:
            feedback = form.save(commit=False)
            
            # Handle user assignment
            if not feedback.is_anonymous:
                feedback.user = self.request.user
                # Clear anonymous fields if not anonymous
                feedback.anonymous_name = ""
                feedback.anonymous_email = ""
            else:
                # Validate anonymous fields
                if not feedback.anonymous_name:
                    form.add_error('anonymous_name', 'Name is required for anonymous feedback')
                    return self.form_invalid(form)
                
                if not feedback.anonymous_email:
                    form.add_error('anonymous_email', 'Email is required for anonymous feedback')
                    return self.form_invalid(form)
                
                # Clear user field if anonymous
                feedback.user = None
            
            # Auto-detect sentiment
            feedback.sentiment = self.detect_sentiment(feedback.message)
            
            # Set initial status
            feedback.status = 'open'
            
            # Save the feedback
            feedback.save()
            
            # Handle categories if they exist in the form
            if 'category' in form.cleaned_data and form.cleaned_data['category']:
                feedback.category = form.cleaned_data['category']
                feedback.save()
            
            # Send notification to administrators
            self.send_admin_notification(feedback)
            
            messages.success(self.request, 'Your feedback has been submitted successfully!')
            return super().form_valid(form)
        
        except Exception as e:
            messages.error(self.request, f'An error occurred while submitting your feedback: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)
    
    def detect_sentiment(self, text):
        """Enhanced sentiment detection with more keywords and context"""
        if not text:
            return 'neutral'
        
        # Extended word lists with weights
        positive_words = {
            'good': 1, 'great': 2, 'excellent': 3, 'amazing': 3, 'wonderful': 3, 
            'fantastic': 3, 'love': 3, 'like': 1, 'awesome': 3, 'brilliant': 3,
            'outstanding': 3, 'superb': 3, 'marvelous': 3, 'exceptional': 3,
            'perfect': 3, 'satisfied': 2, 'happy': 2, 'pleased': 2, 'delighted': 3,
            'thank': 1, 'thanks': 1, 'appreciate': 2, 'helpful': 2, 'useful': 2
        }
        
        negative_words = {
            'bad': 1, 'terrible': 3, 'awful': 3, 'hate': 3, 'dislike': 2, 
            'poor': 2, 'worst': 3, 'horrible': 3, 'disgusting': 3, 'annoying': 2,
            'frustrating': 3, 'disappointing': 3, 'unhappy': 2, 'sad': 2,
            'angry': 3, 'upset': 2, 'dissatisfied': 3, 'displeased': 2,
            'useless': 3, 'waste': 2, 'problem': 2, 'issue': 1, 'fail': 2
        }
        
        text_lower = text.lower()
        
        # Calculate weighted scores
        positive_score = sum(positive_words.get(word, 0) for word in positive_words if word in text_lower)
        negative_score = sum(negative_words.get(word, 0) for word in negative_words if word in text_lower)
        
        # Consider negations
        negations = ['not', 'no', 'never', "n't", 'none', 'nobody', 'nothing', 'neither', 'nor']
        negation_count = sum(1 for neg in negations if neg in text_lower)
        
        # Adjust scores based on negations
        if negation_count > 0:
            positive_score *= 0.5
            negative_score *= 1.5
        
        # Determine sentiment
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def send_admin_notification(self, feedback):
        """Send notification to administrators about new feedback"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.contrib.auth.models import User
            from communication.models import Notification
            
            # Get admin users
            admin_users = User.objects.filter(
                models.Q(is_staff=True) | 
                models.Q(role='Admin') | 
                models.Q(role='Coordinator')
            ).distinct()
            
            # Create in-app notifications
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    message=f"📝 New feedback submitted: {feedback.title}",
                    category="feedback",
                    link=f"/feedback/{feedback.pk}/"
                )
            
            # Send email notifications
            subject = f"New Feedback Submitted: {feedback.title}"
            message = f"""
            New feedback has been submitted on {feedback.created_at.strftime('%B %d, %Y at %I:%M %p')}
            
            Title: {feedback.title}
            Sentiment: {feedback.get_sentiment_display()}
            Priority: {feedback.get_priority_display()}
            
            Message:
            {feedback.message}
            
            Submitted by: {feedback.anonymous_name or feedback.user.get_full_name() or feedback.user.username}
            
            Please review and respond as needed.
            
            View feedback: {self.request.build_absolute_uri(f'/feedback/{feedback.pk}/')}
            """
            
            admin_emails = [admin.email for admin in admin_users if admin.email]
            if admin_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            # Log the error but don't stop the process
            print(f"Error sending admin notification: {e}")

class FeedbackResponseCreateView(LoginRequiredMixin, CreateView):
    model = FeedbackResponse
    form_class = FeedbackResponseForm
    template_name = 'feedback/response_form.html'
    
    def form_valid(self, form):
        response = form.save(commit=False)
        response.responder = self.request.user
        
        # Get feedback ID from kwargs - try both possible parameter names
        feedback_id = self.kwargs.get('feedback_id') or self.kwargs.get('pk')
        if not feedback_id:
            messages.error(self.request, 'Feedback ID is missing.')
            return self.form_invalid(form)
            
        response.feedback_id = feedback_id
        response.save()
        
        # Update feedback status if resolved
        feedback = response.feedback
        if feedback.status != 'resolved':
            feedback.status = 'in_progress'
            feedback.save()
        
        # Send notification to feedback submitter if not internal note
        if not response.is_internal and feedback.user:
            self.send_response_notification(response)
        
        messages.success(self.request, 'Your response has been added!')
        return redirect('feedback:feedback_detail', pk=feedback.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get feedback ID from kwargs - try both possible parameter names
        feedback_id = self.kwargs.get('feedback_id') or self.kwargs.get('pk')
        if feedback_id:
            context['feedback'] = get_object_or_404(Feedback, pk=feedback_id)
        return context
    
    def send_response_notification(self, response):
        """Send notification to feedback submitter about new response"""
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from communication.models import Notification
            
            feedback = response.feedback
            
            # Create in-app notification
            Notification.objects.create(
                recipient=feedback.user,
                message=f"💬 New response to your feedback: {feedback.title}",
                category="feedback",
                link=f"/feedback/{feedback.pk}/"
            )
            
            # Send email notification
            subject = f"Response to Your Feedback: {feedback.title}"
            message = f"""
            Dear {feedback.user.get_full_name() or feedback.user.username},
            
            There has been a new response to your feedback titled "{feedback.title}".
            
            Response:
            {response.message}
            
            You can view the full conversation here:
            {self.request.build_absolute_uri(f'/feedback/{feedback.pk}/')}
            
            Thank you for your feedback.
            
            Wajibika Initiative Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [feedback.user.email],
                fail_silently=True,
            )
        except Exception as e:
            # Log the error but don't stop the process
            print(f"Error sending response notification: {e}")


@login_required
@require_POST
def vote_feedback(request, feedback_id):
    """Handle AJAX voting on feedback"""
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        vote_type = data.get('vote_type')
        
        if vote_type not in ['up', 'down']:
            return JsonResponse({'success': False, 'message': 'Invalid vote type'})
        
        # Remove any existing vote from this user
        FeedbackVote.objects.filter(feedback=feedback, user=request.user).delete()
        
        # Create new vote
        FeedbackVote.objects.create(
            feedback=feedback,
            user=request.user,
            vote_type=vote_type
        )
        
        # Count votes
        upvotes = FeedbackVote.objects.filter(feedback=feedback, vote_type='up').count()
        downvotes = FeedbackVote.objects.filter(feedback=feedback, vote_type='down').count()
        
        return JsonResponse({
            'success': True,
            'upvotes': upvotes,
            'downvotes': downvotes
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def feedback_dashboard(request):
    """Dashboard for staff to view feedback analytics"""
    if request.user.role not in ['Admin', 'Coordinator']:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('feedback:feedback_list')
    
    # Get basic stats
    total_feedback = Feedback.objects.count()
    open_feedback = Feedback.objects.filter(status='open').count()
    resolved_this_week = Feedback.objects.filter(
        status='resolved',
        resolved_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    # Get sentiment distribution
    sentiment_data = Feedback.objects.values('sentiment').annotate(
        count=Count('id')
    )
    
    # Get category distribution
    category_data = Feedback.objects.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get recent feedback
    recent_feedback = Feedback.objects.select_related('user').order_by('-created_at')[:10]
    
    # Get top categories
    top_categories = category_data[:5]
    
    # Get resolution time stats
    resolved_feedback = Feedback.objects.filter(
        status='resolved',
        resolved_at__isnull=False
    ).annotate(
        resolution_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=DurationField()
        )
    )
    
    avg_resolution_time = resolved_feedback.aggregate(
        avg_time=Avg('resolution_time')
    )['avg_time']
    
    # Calculate average resolution time in days and hours
    avg_resolution_hours = None
    if avg_resolution_time:
        total_seconds = avg_resolution_time.total_seconds()
        avg_resolution_hours = {
            'days': int(total_seconds // 86400),
            'hours': int((total_seconds % 86400) // 3600)
        }
    
    # Get all categories for filter dropdown
    categories = FeedbackCategory.objects.all()
    
    # Get status and sentiment choices
    status_choices = Feedback.STATUS_CHOICES
    sentiment_choices = Feedback.SENTIMENT_CHOICES
    
    # Calculate counts for dashboard stats
    pending_response_count = Feedback.objects.filter(
        status__in=['open', 'in_progress']
    ).count()
    
    resolved_this_week_count = Feedback.objects.filter(
        status='resolved',
        resolved_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).count()
    
    total_feedback_count = Feedback.objects.count()
    
    context = {
        'total_feedback': total_feedback,
        'open_feedback': open_feedback,
        'resolved_this_week': resolved_this_week,
        'sentiment_data': sentiment_data,
        'category_data': category_data,
        'recent_feedback': recent_feedback,
        'top_categories': top_categories,
        'avg_resolution_time': avg_resolution_time,
        'avg_resolution_hours': avg_resolution_hours,
        'categories': categories,
        'status_choices': status_choices,
        'sentiment_choices': sentiment_choices,
        'pending_response_count': pending_response_count,
        'resolved_this_week_count': resolved_this_week_count,
        'total_feedback_count': total_feedback_count,
    }
    
    return render(request, 'feedback/dashboard.html', context)