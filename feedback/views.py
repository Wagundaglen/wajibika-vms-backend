from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Feedback
from .forms import FeedbackForm, FeedbackResponseForm

# Volunteer create feedback
class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = 'feedback/feedback_form.html'
    success_url = reverse_lazy('my_feedback')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Your feedback has been submitted successfully.")
        return super().form_valid(form)


# Volunteer view their feedback
class MyFeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = 'feedback/my_feedback_list.html'
    context_object_name = 'feedback_list'
    paginate_by = 10

    def get_queryset(self):
        return Feedback.objects.filter(from_user=self.request.user).order_by('-created_at')


# Admin/Coordinator dashboard
class FeedbackDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Feedback
    template_name = 'feedback/dashboard.html'
    context_object_name = 'feedback_list'
    paginate_by = 15

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name__in=['Coordinator']).exists()

    def get_queryset(self):
        qs = Feedback.objects.all().order_by('-created_at')
        status_filter = self.request.GET.get('status', '').strip()
        category_filter = self.request.GET.get('category', '').strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category=category_filter)
        return qs


# Update feedback status or reply
class FeedbackUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Feedback
    form_class = FeedbackResponseForm
    template_name = 'feedback/feedback_update.html'
    success_url = reverse_lazy('feedback_dashboard')

    def test_func(self):
        return self.request.user.is_staff or self.request.user.groups.filter(name__in=['Coordinator']).exists()

    def form_valid(self, form):
        messages.success(self.request, "Feedback updated successfully.")
        return super().form_valid(form)
