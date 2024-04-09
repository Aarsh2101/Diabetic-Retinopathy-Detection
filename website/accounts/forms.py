from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=True) 
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    affiliation = forms.CharField(max_length=100, required=True)

    class Meta:
        model = CustomUser 
        fields = ("profile_picture", "username", "first_name", "last_name", "affiliation", "email", "password1", "password2")  
        
    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.affiliation = self.cleaned_data['affiliation']
        user.profile_picture = self.cleaned_data['profile_picture']
        if commit:
            user.save()
        return user