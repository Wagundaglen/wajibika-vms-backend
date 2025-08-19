from django import forms
from django.contrib.auth import get_user_model
from .models import Feedback, FeedbackResponse, Survey, SurveyResponse, Question, SurveyAnswer
from .utils import analyze_sentiment

User = get_user_model()


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
        # Auto-run sentiment analysis
        if not feedback.sentiment or ('message' in getattr(self, 'changed_data', [])):
            feedback.sentiment = analyze_sentiment(feedback.message or "")
        if commit:
            feedback.save()
        return feedback


class FeedbackResponseForm(forms.ModelForm):
    """Admin/Coordinator adds a threaded response to feedback."""
    class Meta:
        model = FeedbackResponse
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
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


# ✅ Alias for backward compatibility with views.py
class SurveyForm(AdminSurveyForm):
    """Alias of AdminSurveyForm so imports won't break."""
    pass


class DynamicSurveyResponseForm(forms.Form):
    """
    Volunteer submits responses dynamically based on Survey Questions.
    Builds fields at runtime depending on the linked survey questions.
    """
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey')
        super().__init__(*args, **kwargs)

        for question in survey.questions.all():
            field_name = f"question_{question.id}"

            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.required,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 3,
                        'placeholder': 'Your answer...'
                    })
                )

            elif question.question_type == 'multiple_choice':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.required,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': 'Enter your choice...'
                    })
                )

            elif question.question_type == 'rating':
                self.fields[field_name] = forms.IntegerField(
                    label=question.text,
                    required=question.required,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': 1,
                        'max': 5,
                        'placeholder': 'Rate 1 (Poor) to 5 (Excellent)'
                    })
                )


# ======================================================
# QUESTION FORM
# ======================================================
class QuestionForm(forms.ModelForm):
    """Admin/Coordinator creates a new question for a survey."""
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'required']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter question text'
            }),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
        }


# ======================================================
# SEND SURVEY FORM (UPDATED)
# ======================================================

SEND_TO_CHOICES = [
    ("all", "All Volunteers"),
    ("specific", "Specific Volunteers"),
]

class SendSurveyForm(forms.Form):
    survey = forms.ModelChoiceField(
        queryset=Survey.objects.all(),
        label="Survey",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    send_to = forms.ChoiceField(
        choices=SEND_TO_CHOICES,
        widget=forms.RadioSelect,
        label="Send To"
    )

    volunteers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="Volunteer"),
        required=False,
        label="Select Volunteers",
        widget=forms.SelectMultiple(attrs={"class": "form-select"})
    )