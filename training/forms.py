# training/forms.py

from django import forms
from .models import TrainingCourse, TrainingModule, TrainingAssignment
from accounts.models import Volunteer  # Removed Role and Team imports

class TrainingCourseForm(forms.ModelForm):
    class Meta:
        model = TrainingCourse
        fields = ['title', 'description', 'duration', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class TrainingModuleForm(forms.ModelForm):
    class Meta:
        model = TrainingModule
        fields = ['title', 'content', 'order', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class TrainingAssignmentForm(forms.ModelForm):
    class Meta:
        model = TrainingAssignment
        fields = ['volunteer', 'course', 'due_date']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['volunteer'].queryset = Volunteer.objects.all()
        self.fields['course'].queryset = TrainingCourse.objects.filter(is_active=True)