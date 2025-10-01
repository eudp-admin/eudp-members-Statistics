from django import forms
from .models import Member

class MemberCreationForm(forms.ModelForm):
    class Meta:
        model = Member
        # An new member can fill these fields. Admin-only fields are excluded.
        fields = [
            'full_name', 'gender', 'date_of_birth', 'photo', 
            'phone_number', 'email', 'address_region', 'address_zone', 
            'address_woreda', 'address_kebele', 'education_level', 'profession',
            'membership_level' # Allow them to choose if they are a supporter or full member
        ]
        
        # To make the date field user-friendly with a calendar widget
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

# This is the correct placement for the second class
class MemberUpdateForm(forms.ModelForm):
    class Meta:
        model = Member
        # A member can update these fields. We exclude fields they shouldn't change.
        fields = [
            'full_name', 'date_of_birth', 'photo', 'email', 
            'address_region', 'address_zone', 'address_woreda', 
            'address_kebele', 'education_level', 'profession'
        ]
        
        # Make sure the date field still uses the calendar widget
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }