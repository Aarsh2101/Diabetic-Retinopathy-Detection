from django import forms
from .models import *

class RetinaPhotoForm(forms.ModelForm):
    image = forms.ImageField(label=False, widget=forms.FileInput(attrs={'class': 'your-class-name'}))

    class Meta:
        model = RetinaPhoto
        fields = ['image',]

class CorrectLabelForm(forms.ModelForm):
    class Meta:
        model = CorrectLabel
        fields = ['correct_label', 'image_name']
        widgets = {
            'correct_label': forms.RadioSelect,
            'image_name': forms.HiddenInput() 
        }