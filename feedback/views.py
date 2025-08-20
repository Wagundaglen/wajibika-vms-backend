from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Count, Avg, Q, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse_lazy
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
        
        return context

class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback/feedback_form.html'
    success_url = reverse_lazy('feedback:feedback_list')
    
    def form_valid(self, form):
        feedback = form.save(commit=False)
        
        # Set user if not anonymous
        if not feedback.is_anonymous:
            feedback.user = self.request.user
        
        # Auto-detect sentiment (simplified)
        feedback.sentiment = self.detect_sentiment(feedback.message)
        
        feedback.save()
        
        messages.success(self.request, 'Your feedback has been submitted successfully!')
        return super().form_valid(form)
    
    def detect_sentiment(self, text):
        """Simple sentiment detection based on keywords"""
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'poor', 'worst']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

class FeedbackResponseCreateView(LoginRequiredMixin, CreateView):
    model = FeedbackResponse
    form_class = FeedbackResponseForm
    template_name = 'feedback/response_form.html'
    
    def form_valid(self, form):
        response = form.save(commit=False)
        response.responder = self.request.user
        response.feedback_id = self.kwargs['feedback_id']
        response.save()
        
        # Update feedback status if resolved
        feedback = response.feedback
        if feedback.status != 'resolved':
            feedback.status = 'in_progress'
            feedback.save()
        
        messages.success(self.request, 'Your response has been added!')
        return redirect('feedback:feedback_detail', pk=feedback.pk)

@login_required
def vote_feedback(request, feedback_id):
    feedback = get_object_or_404(Feedback, pk=feedback_id)
    vote_type = request.POST.get('vote_type')
    
    if vote_type in ['up', 'down']:
        FeedbackVote.objects.update_or_create(
            feedback=feedback,
            user=request.user,
            defaults={'vote_type': vote_type}
        )
        
        return JsonResponse({
            'success': True,
            'upvotes': feedback.votes.filter(vote_type='up').count(),
            'downvotes': feedback.votes.filter(vote_type='down').count()
        })
    
    return JsonResponse({'success': False})

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