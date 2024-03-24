from django import forms
from .models import RetinaPhoto

class RetinaPhotoForm(forms.ModelForm):
    image = forms.ImageField(label=False, widget=forms.FileInput(attrs={'class': 'your-class-name'}))

    class Meta:
        model = RetinaPhoto
        fields = ['image',]

class CorrectLabelForm(forms.Form):
    LABEL_CHOICES = [
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        # Add more choices as needed
    ]
    correct_label = forms.ChoiceField(choices=LABEL_CHOICES, widget=forms.RadioSelect)