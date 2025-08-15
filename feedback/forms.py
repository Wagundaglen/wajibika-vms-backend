from django import forms
from .models import Feedback
from .utils import analyze_sentiment

class FeedbackForm(forms.ModelForm):
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
        # Attach the logged-in user if not anonymous
        if self.user and not feedback.anonymous:
            feedback.from_user = self.user
        # Auto sentiment analysis
        if not feedback.sentiment or ('message' in getattr(self, 'changed_data', [])):
            feedback.sentiment = analyze_sentiment(feedback.message or "")
        if commit:
            feedback.save()
        return feedback


class FeedbackResponseForm(forms.ModelForm):
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
