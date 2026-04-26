from django import forms

from .models import Set


class SetUpdateForm(forms.ModelForm):
    """Form to validate inline edits to a Set."""

    class Meta:
        model = Set
        fields = ('reps', 'weight_kg', 'is_warmup', 'completed')