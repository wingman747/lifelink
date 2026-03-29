from django import forms
from django.contrib.auth.models import User
from .models import HospitalBloodBankVerification, InstitutionUser

class InstitutionRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    password_confirm = forms.CharField(widget=forms.PasswordInput())
    
    class Meta:
        model = InstitutionUser
        fields = ['institution', 'designation']
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        
        institution = cleaned_data.get('institution')
        if institution and not institution.is_verified:
            raise forms.ValidationError("Your institution has not been verified yet. Please contact admin.")
        
        return cleaned_data