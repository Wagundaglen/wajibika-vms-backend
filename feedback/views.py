from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, TemplateView, ListView
from django.urls import reverse_lazy
from django.db import models
from .models import Feedback
from .forms import FeedbackForm, FeedbackResponseForm


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
        # Attach logged-in volunteer
        form.instance.from_user = self.request.user
        form.instance.status = "open"
        messages.success(self.request, "✅ Your feedback has been submitted successfully.")
        return super().form_valid(form)


# =====================================================
# Update Feedback (Volunteers & Admin/Coordinator)
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
        role = getattr(request.user, "role", None)

        # Volunteers can only edit their own feedback if it's still open
        if feedback.from_user == request.user:
            if feedback.status != "open":
                messages.error(request, "⚠️ You can no longer edit this feedback as it has been reviewed/resolved.")
                return redirect("feedback_dashboard")

        # Admins/Coordinators can edit anytime
        elif role not in ["Admin", "Coordinator"]:
            messages.error(request, "⚠️ You are not authorised to edit this feedback.")
            return redirect("feedback_dashboard")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Track admin/coordinator updates
        if getattr(self.request.user, "role", None) in ["Admin", "Coordinator"]:
            form.instance.updated_by = self.request.user

        messages.success(self.request, "✏️ Feedback updated successfully.")
        return super().form_valid(form)


# =====================================================
# Respond to Feedback (Admin/Coordinator only)
# =====================================================
class FeedbackResponseView(LoginRequiredMixin, UpdateView):   # ✅ renamed to match urls.py
    model = Feedback
    form_class = FeedbackResponseForm
    template_name = "feedback/feedback_response.html"
    success_url = reverse_lazy("feedback_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if getattr(request.user, "role", None) not in ["Admin", "Coordinator"]:
            messages.error(request, "⚠️ Only coordinators and admins can respond to feedback.")
            return redirect("feedback_dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        # Mark as reviewed if not already resolved
        if form.instance.status != "resolved":
            form.instance.status = "reviewed"
        messages.success(self.request, "💬 Response saved successfully.")
        return super().form_valid(form)


# =====================================================
# Mark Feedback as Resolved (Admin/Coordinator)
# =====================================================
@login_required
def mark_feedback_resolved(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if getattr(request.user, "role", None) in ["Admin", "Coordinator"]:
        feedback.status = "resolved"
        feedback.updated_by = request.user
        feedback.save(update_fields=["status", "updated_by"])   # ✅ fixed (was wrongly setting a DateTimeField object)
        messages.success(request, "✅ Feedback marked as resolved.")
    else:
        messages.error(request, "⚠️ You are not authorised to resolve this feedback.")
    return redirect("feedback_dashboard")


# =====================================================
# Feedback Dashboard (Admin/Coordinator = all feedbacks, Volunteer = own)
# =====================================================
class FeedbackDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "feedback/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = getattr(self.request.user, "role", None)

        if role in ["Admin", "Coordinator"]:
            context["feedbacks"] = Feedback.objects.all().order_by("-created_at")
        else:
            context["feedbacks"] = Feedback.objects.filter(
                models.Q(from_user=self.request.user) | models.Q(to_user=self.request.user)
            ).order_by("-created_at")
        return context


# =====================================================
# My Feedback (Volunteer only)
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
    role = getattr(request.user, "role", None)

    if feedback.from_user == request.user and feedback.status == "open":
        feedback.delete()
        messages.success(request, "🗑️ Feedback deleted successfully.")
    elif role in ["Admin", "Coordinator"]:
        feedback.delete()
        messages.success(request, "🗑️ Feedback deleted successfully.")
    else:
        messages.error(request, "⚠️ You are not authorised to delete this feedback.")
    return redirect("feedback_dashboard")
