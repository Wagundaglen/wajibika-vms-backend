# training/forms.py
from django import forms
from .models import TrainingCourse, TrainingModule, TrainingAssignment
from accounts.models import Volunteer
import logging

logger = logging.getLogger(__name__)

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
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Filter courses to only show active ones
        self.fields['course'].queryset = TrainingCourse.objects.filter(is_active=True)
        
        # Filter volunteers based on user role
        if user and (user.is_staff or user.role == 'Admin'):
            # Admins can see all volunteers
            self.fields['volunteer'].queryset = Volunteer.objects.filter(role='Volunteer')
        elif user and user.role == 'Coordinator':
            # Coordinators can only see volunteers in their team (if team model exists)
            try:
                from accounts.models import Team
                team_volunteers = Volunteer.objects.filter(team=user.team, role='Volunteer')
                self.fields['volunteer'].queryset = team_volunteers
            except:
                # If Team model doesn't exist, show all volunteers
                self.fields['volunteer'].queryset = Volunteer.objects.filter(role='Volunteer')
        else:
            # Other users can't assign training
            self.fields['volunteer'].queryset = Volunteer.objects.none()
        
        # Add a helpful label for the volunteer field
        self.fields['volunteer'].label = "Select Volunteer"
        
        # Set empty label for the dropdown
        self.fields['volunteer'].empty_label = "Choose a volunteer..."