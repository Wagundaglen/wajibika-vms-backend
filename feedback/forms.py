from django import forms
from .models import Feedback, Survey, SurveyResponse, Question
from .utils import analyze_sentiment

# ======================================================
# FEEDBACK FORMS
# ======================================================
class FeedbackForm(forms.ModelForm):
    """Volunteer submits feedback to Admin/Coordinator."""
    class Meta:
        model = Feedback
        fields = ['to_user', 'category', 'message', 'anonymous']
        widgets = {
            'to_user': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your feedback here...'
            }),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        feedback = super().save(commit=False)
        # Link logged-in user unless anonymous
        if self.user and not feedback.anonymous:
            feedback.from_user = self.user
        # Auto-run sentiment analysis on message
        if not feedback.sentiment or ('message' in getattr(self, 'changed_data', [])):
            feedback.sentiment = analyze_sentiment(feedback.message or "")
        if commit:
            feedback.save()
        return feedback


class FeedbackResponseForm(forms.ModelForm):
    """Admin/Coordinator responds to feedback."""
    class Meta:
        model = Feedback
        fields = ['status', 'response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'response': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a reply or resolution notes...'
            }),
        }


# ======================================================
# SURVEY FORMS
# ======================================================

class AdminSurveyForm(forms.ModelForm):
    """Admin/Coordinator creates a new survey (CRUD)."""
    class Meta:
        model = Survey
        fields = [
            'title', 'description', 'instructions',
            'category', 'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter survey title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Brief description of this survey...'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Provide instructions for participants (optional)...'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category (e.g., Feedback, Research, Training)'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 'type': 'datetime-local'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SurveyResponseForm(forms.ModelForm):
    """Volunteer submits responses to a survey with fixed Q1, Q2, and rating."""
    class Meta:
        model = SurveyResponse
        fields = ['q1', 'q2', 'rating']
        widgets = {
            'q1': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Answer question 1...'
            }),
            'q2': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Answer question 2...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'placeholder': 'Rate 1 (Poor) to 5 (Excellent)'
            }),
        }


# ======================================================
# QUESTION FORM
# ======================================================
class QuestionForm(forms.ModelForm):
    """Admin/Coordinator creates a new question for a survey."""
    required = forms.BooleanField(required=False)  # Ensure this line exists

    class Meta:
        model = Question
        fields = ['text', 'question_type', 'required']  # Include 'required'
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter question text'
            }),
            'question_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }