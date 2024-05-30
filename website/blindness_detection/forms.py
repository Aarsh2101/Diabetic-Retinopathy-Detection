from django import forms
from .models import *

class RetinaPhotoForm(forms.ModelForm):
    name = forms.CharField(label='Name', max_length=30, required=False)
    gender = forms.ChoiceField(label='Gender', widget=forms.RadioSelect, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], required=False)
    dob = forms.DateField(label='DOB', widget=forms.SelectDateWidget(years=range(1925, 2023), attrs={'class': 'dob-select'}), required=False)
    location = forms.CharField(label='Location', max_length=50, required=False)
    image = forms.ImageField(label='Fundus Image', widget=forms.FileInput(attrs={'class': 'your-class-name'}), required=True)

    class Meta:
        model = RetinaPhoto
        fields = ['name', 'gender', 'dob', 'location', 'image']

class CorrectLabelForm(forms.ModelForm):
    class Meta:
        model = CorrectLabel
        fields = ['correct_label']
        widgets = {
            'correct_label': forms.RadioSelect
        }