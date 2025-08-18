from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    CreateView, ListView, UpdateView, DetailView, DeleteView, TemplateView
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import HttpResponseForbidden
from .models import Feedback, FeedbackResponse, Survey, Question, SurveyResponse
from .forms import FeedbackForm, FeedbackResponseForm, SurveyForm, QuestionForm, SendSurveyForm
from django.contrib.auth import get_user_model
from .models import Volunteer

User = get_user_model()


# -------------------------------------------------
# Role helpers
# -------------------------------------------------
def is_admin(user):
    return user.is_staff and user.is_superuser

def is_coordinator(user):
    return user.is_staff and not user.is_superuser

def is_admin_or_coordinator(user):
    return user.is_staff


# -------------------------------------------------
# Feedback CRUD
# -------------------------------------------------
@method_decorator(login_required, name="dispatch")
class FeedbackCreateView(CreateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "feedback/feedback_form.html"
    success_url = reverse_lazy("feedback:my_feedback")

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        messages.success(self.request, "Feedback submitted successfully.")
        return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class MyFeedbackListView(LoginRequiredMixin, ListView):
    model = Feedback
    template_name = "feedback/my_feedback.html"
    context_object_name = "feedbacks"

    def get_queryset(self):
        # show only feedback submitted by the logged-in user
        return Feedback.objects.filter(from_user=self.request.user)

@method_decorator(login_required, name="dispatch")
class FeedbackDashboardView(TemplateView):
    template_name = "feedback/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Feedbacks submitted by the logged-in user (volunteer)
        context["my_feedbacks"] = Feedback.objects.filter(from_user=user)

        # Feedbacks assigned to this user (if coordinator/admin)
        context["assigned_feedbacks"] = Feedback.objects.filter(to_user=user)

        # Surveys assigned to this user
        context["my_surveys"] = Survey.objects.filter(assigned_users=user)

        return context



@method_decorator(login_required, name="dispatch")
class FeedbackDetailView(DetailView):
    model = Feedback
    template_name = "feedback/feedback_detail.html"
    context_object_name = "feedback"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feedback = self.object
        context["responses"] = FeedbackResponse.objects.filter(feedback=feedback)
        if is_admin_or_coordinator(self.request.user):
            context["response_form"] = FeedbackResponseForm()
        return context

    def post(self, request, *args, **kwargs):
        """Allow admin/coordinator to submit a response inline"""
        self.object = self.get_object()
        if not is_admin_or_coordinator(request.user):
            messages.error(request, "You are not allowed to respond.")
            return redirect("feedback:feedback_detail", pk=self.object.pk)

        form = FeedbackResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.feedback = self.object
            response.responded_by = request.user
            response.save()
            messages.success(request, "Response added successfully.")
            return redirect("feedback:feedback_detail", pk=self.object.pk)

        context = self.get_context_data()
        context["response_form"] = form
        return self.render_to_response(context)


@method_decorator(login_required, name="dispatch")
class FeedbackResponseView(CreateView):
    model = FeedbackResponse
    form_class = FeedbackResponseForm
    template_name = "feedback/feedback_response_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            return HttpResponseForbidden("You are not allowed to respond to feedback.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feedback"] = get_object_or_404(Feedback, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        feedback = get_object_or_404(Feedback, pk=self.kwargs["pk"])
        form.instance.feedback = feedback
        form.instance.responded_by = self.request.user
        messages.success(self.request, "Response added successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("feedback:feedback_detail", kwargs={"pk": self.kwargs["pk"]})


@method_decorator(login_required, name="dispatch")
class FeedbackUpdateView(UpdateView):
    model = Feedback
    form_class = FeedbackForm
    template_name = "feedback/feedback_form.html"

    def dispatch(self, request, *args, **kwargs):
        feedback = self.get_object()
        if not (is_admin(request.user) or request.user == feedback.submitted_by):
            return HttpResponseForbidden("Not allowed to edit this feedback.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("feedback:feedback_detail", kwargs={"pk": self.object.pk})


@method_decorator(login_required, name="dispatch")
class FeedbackDeleteView(DeleteView):
    model = Feedback
    template_name = "feedback/feedback_confirm_delete.html"
    success_url = reverse_lazy("feedback:feedback_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return HttpResponseForbidden("Only admins can delete feedback.")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Feedback deleted successfully.")
        return super().delete(request, *args, **kwargs)


@login_required
def mark_feedback_resolved(request, pk):
    feedback = get_object_or_404(Feedback, pk=pk)
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("You are not allowed to resolve feedback.")
    feedback.status = "resolved"
    feedback.save()
    messages.success(request, "Feedback marked as resolved.")
    return redirect("feedback:feedback_detail", pk=pk)


# -------------------------------------------------
# Survey CRUD
# -------------------------------------------------
@method_decorator(login_required, name="dispatch")
class SurveyListView(ListView):
    model = Survey
    template_name = "feedback/survey_list.html"
    context_object_name = "surveys"

    def get_queryset(self):
        if is_admin_or_coordinator(self.request.user):
            return Survey.objects.all()
        # Volunteers only see surveys assigned to them
        return Survey.objects.filter(surveyresponse__user=self.request.user).distinct()


@method_decorator(login_required, name="dispatch")
class SurveyCreateView(CreateView):
    model = Survey
    form_class = SurveyForm
    template_name = "feedback/survey_form.html"
    success_url = reverse_lazy("feedback:survey_list")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            return HttpResponseForbidden("Not allowed to create surveys.")
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class AssignedSurveyListView(ListView):
    model = Survey
    template_name = "feedback/assigned_surveys.html"
    context_object_name = "surveys"

    def get_queryset(self):
        # Assuming Survey model has a ManyToManyField "assigned_users"
        return Survey.objects.filter(assigned_users=self.request.user)


@method_decorator(login_required, name="dispatch")
class SurveyDetailView(DetailView):
    model = Survey
    template_name = "feedback/survey_detail.html"
    context_object_name = "survey"

@method_decorator(login_required, name="dispatch")
class SurveyResponseDetailView(DetailView):
    model = SurveyResponse
    template_name = "feedback/survey_response_detail.html"
    context_object_name = "response"

@method_decorator(login_required, name="dispatch")
class SurveyThanksView(TemplateView):
    template_name = "feedback/survey_thanks.html"

@method_decorator(login_required, name="dispatch")
class SurveyUpdateView(UpdateView):
    model = Survey
    form_class = SurveyForm
    template_name = "feedback/survey_form.html"
    success_url = reverse_lazy("feedback:survey_list")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            return HttpResponseForbidden("Not allowed to update surveys.")
        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class SurveyDeleteView(DeleteView):
    model = Survey
    template_name = "feedback/survey_confirm_delete.html"
    success_url = reverse_lazy("feedback:feedback_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return HttpResponseForbidden("Only admins can delete surveys.")
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Survey deleted successfully.")
        return super().delete(request, *args, **kwargs)


# -------------------------------------------------
# Questions (Admin/Coordinator only)
# -------------------------------------------------
@login_required
def add_question(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if not is_admin_or_coordinator(request.user):
        return HttpResponseForbidden("Not allowed to add questions.")

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.survey = survey
            question.save()
            messages.success(request, "Question added successfully.")
            return redirect("feedback:survey_detail", pk=survey.id)
    else:
        form = QuestionForm()

    return render(request, "feedback/question_form.html", {"form": form, "survey": survey})


@method_decorator(login_required, name="dispatch")
class QuestionUpdateView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = "feedback/question_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            return HttpResponseForbidden("Not allowed to update questions.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("feedback:survey_detail", kwargs={"pk": self.object.survey.pk})


@method_decorator(login_required, name="dispatch")
class QuestionDeleteView(DeleteView):
    model = Question
    template_name = "feedback/question_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_or_coordinator(request.user):
            return HttpResponseForbidden("Not allowed to delete questions.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("feedback:survey_detail", kwargs={"pk": self.object.survey.pk})


# -------------------------------------------------
# Survey Sending (Admin/Coordinator)
# -------------------------------------------------
@login_required
def send_survey(request):
    if request.method == "POST":
        form = SendSurveyForm(request.POST)
        if form.is_valid():
            survey = form.cleaned_data["survey"]
            send_to = request.POST.get("send_to")
            selected_volunteers = form.cleaned_data["volunteers"]

            # Decide recipients
            if send_to == "all":
                volunteers = User.objects.filter(role="Volunteer")
            else:
                volunteers = selected_volunteers

            count = 0
            for volunteer in volunteers:
                # Assign to ManyToMany field
                if volunteer not in survey.assigned_users.all():
                    survey.assigned_users.add(volunteer)

                    # Also create a SurveyResponse tracker
                    SurveyResponse.objects.get_or_create(
                        survey=survey,
                        user=volunteer,
                        defaults={"assigned_by": request.user}
                    )
                    count += 1

            messages.success(
                request,
                f"Survey '{survey.title}' sent to {count} volunteers."
            )
            return redirect("feedback:survey_list")
    else:
        form = SendSurveyForm()

    return render(request, "feedback/send_survey.html", {"form": form})



# -------------------------------------------------
# Survey Participation (Volunteers)
# -------------------------------------------------
@login_required
def submit_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)

    # 🚫 Block Admins and Coordinators from submitting
    if is_admin_or_coordinator(request.user):
        messages.warning(request, "Admins and Coordinators cannot submit surveys. You may only view results.")
        return redirect("feedback:survey_detail", pk=survey.pk)

    # ✅ Ensure volunteer is assigned this survey
    survey_response = SurveyResponse.objects.filter(user=request.user, survey=survey).first()
    if not survey_response:
        return HttpResponseForbidden("You were not assigned this survey.")

    if request.method == "POST":
        # Delete old answers if re-submitting
        survey_response.answers.all().delete()

        # Save answers
        for q in survey.questions.all():
            answer_text = request.POST.get(f"question_{q.id}", "").strip()
            if answer_text:  # Save only if answered
                survey_response.answers.create(
                    question=q,
                    answer_text=answer_text
                )

        survey_response.submitted_at = timezone.now()
        survey_response.save()

        messages.success(request, "Survey submitted successfully!")
        return redirect("feedback:survey_thanks")

    return render(request, "feedback/survey_submit.html", {"survey": survey})
