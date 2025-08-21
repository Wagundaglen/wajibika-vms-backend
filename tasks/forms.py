from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Task, TaskCategory, TimeEntry

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'assigned_to', 
            'start_date', 'start_time', 'end_date', 'end_time',
            'location', 'skills_required', 'estimated_hours', 
            'priority', 'due_date'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'skills_required': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(
            role__in=['Volunteer', 'Coordinator']
        ).order_by('username')
        self.fields['assigned_to'].label = 'Assign To'
        self.fields['category'].empty_label = 'Select Category'
        
        # Set default due date to 7 days from now
        if not self.instance.pk:
            self.fields['due_date'].initial = timezone.now().date() + timezone.timedelta(days=7)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        due_date = cleaned_data.get('due_date')
        
        # Validate dates
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("End date cannot be before start date.")
        
        if start_date and due_date and start_date > due_date:
            raise forms.ValidationError("Due date cannot be before start date.")
        
        # Validate estimated hours
        estimated_hours = cleaned_data.get('estimated_hours')
        if estimated_hours and estimated_hours <= 0:
            raise forms.ValidationError("Estimated hours must be greater than 0.")
        
        return cleaned_data

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['task', 'date', 'hours', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hours': forms.NumberInput(attrs={'step': '0.25', 'class': 'form-control', 'min': '0.25'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter tasks to only show accepted tasks for this user
        if self.user:
            self.fields['task'].queryset = Task.objects.filter(
                assigned_to=self.user,
                acceptance_status='Accepted',
                status__in=['Pending', 'In Progress']
            ).order_by('start_date')
            self.fields['task'].label = 'Task'
        
        # Set default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()
    
    def clean(self):
        cleaned_data = super().clean()
        task = cleaned_data.get('task')
        date = cleaned_data.get('date')
        hours = cleaned_data.get('hours')
        
        # Validate date is not in the future
        if date and date > timezone.now().date():
            raise forms.ValidationError("You cannot log hours for future dates.")
        
        # Validate hours
        if hours and hours <= 0:
            raise forms.ValidationError("Hours must be greater than 0.")
        
        # Validate date is after task start date
        if task and date and task.start_date and date < task.start_date:
            raise forms.ValidationError("You cannot log hours before the task start date.")
        
        return cleaned_data

class TaskFilterForm(forms.Form):
    """Form for filtering tasks in the list view"""
    STATUS_CHOICES = [('', 'All Status')] + list(Task.ACCEPTANCE_CHOICES)
    PRIORITY_CHOICES = [('', 'All Priority')] + list(Task.PRIORITY_CHOICES)
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    search = forms.CharField(max_length=100, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        self.fields['priority'].widget.attrs.update({'class': 'form-select'})
        self.fields['search'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Search tasks...'
        })

class HoursFilterForm(forms.Form):
    """Form for filtering hours entries"""
    MONTH_CHOICES = [('', 'All Months')] + [
        (i, timezone.datetime(2024, i, 1).strftime('%B')) for i in range(1, 13)
    ]
    
    month = forms.ChoiceField(choices=MONTH_CHOICES, required=False)
    year = forms.ChoiceField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Generate year choices
        current_year = timezone.now().year
        year_choices = [('', 'All Years')] + [
            (year, str(year)) for year in range(current_year - 5, current_year + 1)
        ]
        self.fields['year'].choices = year_choices
        self.fields['year'].widget.attrs.update({'class': 'form-select'})
        self.fields['month'].widget.attrs.update({'class': 'form-select'})