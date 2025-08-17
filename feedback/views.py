from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView, UpdateView, TemplateView, ListView, DeleteView, DetailView
)
from django.urls import reverse_lazy
from django.forms import inlineformset_factory
from django.db import models  # Ensure this import is included
from .models import Feedback, Survey, SurveyResponse, Question
from .forms import (
    FeedbackForm,
    FeedbackResponseForm,
    AdminSurveyForm,
    SurveyResponseForm,
    QuestionForm,
)

# =====================================================
# Helper: role check for admin/coordinator
# =====================================================
def is_admin_or_coordinator(user):
    return getattr(user, "role", "").lower() in ["admin", "coordinator"] or user.is_staff

# =====================================================
# Submit Feedback (Volunteers)
# =====================================================
class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "feedback/feedback_form.html"
    success_url = reverse_lazy("feedback_dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.from_user = self.request.user
        form.instance.status = "open"
        messages.success(self.request, "✅ Your feedback has been submitted successfully.")
        return super().form_valid(form)

# =====================================================
# Feedback Detail (Volunteers + Admin/Coordinator)
# =====================================================
class FeedbackDetailView(LoginRequiredMixin, DetailView):
    model = Feedback
    template_name = "feedback/feedback_detail.html"
    context_object_name = "feedback"

    def dispatch(self, request, *args, **kwargs):
        feedback = self.get_object()
        if feedback.from_user == request.user or feedback.to_user == request.user or is_admin_or_coordinator(request.user):
            return super().dispatch(request, *args, **kwargs)
        messages.error(request, "⚠️ You are not authorised to view this feedback.")
        return redirect("feedback_dashboard")

# =====================================================
# Update Feedback
# =====================================================
class FeedbackUpdateView(LoginRequiredMixin, UpdateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "feedback/feedback_update.html"
    success_url = reverse_lazy("feedback_dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        feedback = self.get_object()
        if feedback.from_user == request.user and feedback.status != "open":
            messages.error(request, "⚠️ You can no longer edit this feedback as it has been reviewed/resolved.")
            return redirect("feedback_dashboard")
        elif not is_admin_or_coordinator(request.user):
            messages.error(request, "⚠️ You are not authorised to edit this feedback.")
            return redirect("feedback_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if is_admin_or_coordinator(self.request.user):
            form.instance.updated_by = self.request.user
        messages.success(self.request, "✏️ Feedback updated successfully.")
        return super().form_valid(form)

# =====================================================
# Respond to Feedback (Admin/Coordinator only)
# =====================================================
class FeedbackResponseView(LoginRequiredMixin, UpdateView):
    model = Feedback
    form_class = FeedbackResponseForm
    template_name = "feedback/feedback_response.html"
    success_url = reverse_lazy("feedback_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            messages.error(request, "⚠️ Only coordinators and admins can respond to feedback.")
            return redirect("feedback_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        if form.instance.status != "resolved":
            form.instance.status = "reviewed"
        messages.success(self.request, "💬 Response saved successfully.")
        return super().form_valid(form)

# =====================================================
# Mark Feedback as Resolved
# =====================================================
@login_required
def mark_feedback_resolved(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if is_admin_or_coordinator(request.user):
        feedback.mark_resolved(user=request.user)
        messages.success(request, "✅ Feedback marked as resolved.")
    else:
        messages.error(request, "⚠️ You are not authorised to resolve this feedback.")
    return redirect("feedback_dashboard")

# =====================================================
# Feedback Dashboard
# =====================================================
class FeedbackDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "feedback/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if is_admin_or_coordinator(self.request.user):
            context["feedbacks"] = Feedback.objects.all().order_by("-created_at")
            context["surveys"] = Survey.objects.all().order_by("-created_at")
            context["survey_responses"] = SurveyResponse.objects.select_related("survey", "user").order_by("-created_at")
        else:
            context["feedbacks"] = Feedback.objects.filter(
                models.Q(from_user=self.request.user) | models.Q(to_user=self.request.user)
            ).order_by("-created_at")
            context["surveys"] = Survey.objects.filter(assigned_users=self.request.user).order_by("-created_at")
            context["survey_responses"] = SurveyResponse.objects.filter(
                user=self.request.user
            ).select_related("survey").order_by("-created_at")
        return context

# =====================================================
# My Feedback
# =====================================================
class MyFeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/my_feedback.html"
    context_object_name = "feedbacks"

    def get_queryset(self):
        return Feedback.objects.filter(from_user=self.request.user).order_by("-created_at")

# =====================================================
# Delete Feedback
# =====================================================
@login_required
def delete_feedback(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)

    if feedback.from_user == request.user and feedback.status == "open":
        feedback.delete()
        messages.success(request, "🗑️ Feedback deleted successfully.")
    elif is_admin_or_coordinator(request.user):
        feedback.delete()
        messages.success(request, "🗑️ Feedback deleted successfully.")
    else:
        messages.error(request, "⚠️ You are not authorised to delete this feedback.")
    return redirect("feedback_dashboard")

# =====================================================
# Survey Management
# =====================================================
class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    form_class = AdminSurveyForm
    template_name = "feedback/survey_form.html"  # This renders the form
    success_url = reverse_lazy("survey_list")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            messages.error(request, "⚠️ Only admins/coordinators can create surveys.")
            return redirect("feedback_dashboard")
        
        # Allow access to the survey creation form
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "📝 Survey created successfully.")
        return super().form_valid(form)
# Create a formset for questions
QuestionFormSet = inlineformset_factory(Survey, Question, fields=('text', 'question_type'), extra=1)

class SurveyListView(LoginRequiredMixin, ListView):
    model = Survey
    template_name = "feedback/survey_list.html"
    context_object_name = "surveys"

    def get_queryset(self):
        if is_admin_or_coordinator(self.request.user):
            return Survey.objects.all().order_by("-created_at")
        return Survey.objects.filter(assigned_users=self.request.user).order_by("-created_at")

class SurveyDetailView(LoginRequiredMixin, TemplateView):
    template_name = "feedback/survey_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = get_object_or_404(Survey, pk=self.kwargs["pk"])
        context["survey"] = survey
        context["responses"] = SurveyResponse.objects.filter(survey=survey).select_related("user")
        return context

class SurveyUpdateView(LoginRequiredMixin, UpdateView):
    model = Survey
    form_class = AdminSurveyForm
    template_name = "feedback/survey_form.html"
    success_url = reverse_lazy("survey_list")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            messages.error(request, "⚠️ Only admins/coordinators can update surveys.")
            return redirect("feedback_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "✏️ Survey updated successfully.")
        return super().form_valid(form)

class SurveyDeleteView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = "feedback/survey_confirm_delete.html"
    success_url = reverse_lazy("survey_list")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            messages.error(request, "⚠️ Only admins/coordinators can delete surveys.")
            return redirect("feedback_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "🗑️ Survey deleted successfully.")
        return super().delete(request, *args, **kwargs)

# =====================================================
# Survey Thank You Page
# =====================================================
class SurveyThanksView(LoginRequiredMixin, TemplateView):
    template_name = "feedback/survey_thanks.html"

# =====================================================
# Submit Survey Response (Fixed q1, q2, rating)
# =====================================================
@login_required
def submit_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    if not survey.assigned_users.filter(pk=request.user.pk).exists():
        messages.error(request, "⚠️ You are not assigned to this survey.")
        return redirect("feedback_dashboard")

    response, _ = SurveyResponse.objects.get_or_create(
        survey=survey,
        user=request.user,
        defaults={"assigned_by": survey.created_by, "status": "pending"},
    )

    if request.method == "POST":
        form = SurveyResponseForm(request.POST, instance=response)
        if form.is_valid():
            resp = form.save(commit=False)
            resp.status = "completed"
            resp.save()
            messages.success(request, "✅ Your survey has been submitted successfully.")
            return redirect("survey_thanks")
    else:
        form = SurveyResponseForm(instance=response)

    return render(
        request,
        "feedback/survey_response_form.html",
        {"form": form, "survey": survey}
    )

# =====================================================
# My Feedback View (Added)
# =====================================================
class MyFeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/my_feedback.html"
    context_object_name = "feedbacks"

    def get_queryset(self):
        return Feedback.objects.filter(from_user=self.request.user).order_by("-created_at")

# =====================================================
# Question Management Views
# =====================================================
class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = "feedback/question_form.html"

    def form_valid(self, form):
        form.instance.survey = get_object_or_404(Survey, pk=self.kwargs['survey_pk'])
        messages.success(self.request, "✅ Question added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('survey_detail', kwargs={'pk': self.kwargs['survey_pk']})

class QuestionUpdateView(LoginRequiredMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "feedback/question_form.html"

    def get_success_url(self):
        return reverse_lazy('survey_detail', kwargs={'pk': self.object.survey.pk})

class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    model = Question

    def get_success_url(self):
        messages.success(self.request, "🗑️ Question deleted successfully.")
        return reverse_lazy('survey_detail', kwargs={'pk': self.object.survey.pk})

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)