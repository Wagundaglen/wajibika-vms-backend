from django import forms
from .models import Feedback, FeedbackResponse, FeedbackCategory

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'is_anonymous', 'anonymous_name', 'anonymous_email',
            'category', 'feedback_type', 'title', 'message', 'priority'
        ]
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # safely pop the request so it doesn’t break BaseModelForm
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = FeedbackCategory.objects.all()
        self.fields['category'].empty_label = "Select a category"

        self.fields['anonymous_name'].required = False
        self.fields['anonymous_email'].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_anonymous = cleaned_data.get('is_anonymous')
        anonymous_name = cleaned_data.get('anonymous_name')

        if is_anonymous and not anonymous_name:
            raise forms.ValidationError(
                "Please provide a name for anonymous feedback."
            )
        return cleaned_data

class FeedbackResponseForm(forms.ModelForm):
    class Meta:
        model = FeedbackResponse
        fields = ['message', 'is_internal']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }