# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()

class VolunteerRegistrationForm(UserCreationForm):
    phone = forms.CharField(required=False, help_text="Enter phone number with country code")
    skills = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    role = forms.ChoiceField(choices=[
        ('Volunteer', 'Volunteer'),
        ('Admin', 'Admin'),
        ('Coordinator', 'Coordinator'),
    ])

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'skills', 'role', 'password1', 'password2']


class EditProfileForm(forms.ModelForm):
    """Form for editing an existing user's profile."""
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'skills', 'role', 'bio', 'address',
            'date_of_birth', 'profile_picture'
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 3}),
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
