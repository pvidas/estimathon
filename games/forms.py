from django import forms

from .models import Team, Submission


class TeamRegistrationForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['team_name']


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['question', 'interval_lower_bound', 'interval_upper_bound']
        widgets = {
            'interval_lower_bound': forms.TextInput,
            'interval_upper_bound': forms.TextInput,
        }
        labels = {
            'interval_lower_bound': 'Min',
            'interval_upper_bound': 'Max',
        }