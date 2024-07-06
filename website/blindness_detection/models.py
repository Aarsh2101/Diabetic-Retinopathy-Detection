from django.db import models
from django.conf import settings

# Create your models here.
class RetinaPhoto(models.Model):
    image = models.ImageField(upload_to='retina_images/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.image.name

class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    dob = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='retina_images/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

class GradcamImage(models.Model):
    image = models.ImageField(upload_to='retina_gradcam_images/')
    retina_photo = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='gradcam_image')
    
    def __str__(self):
        return self.image.name

class CanvasImage(models.Model):
    image = models.ImageField(upload_to='canvas_images/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='canvas_images')
    retina_photo = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='canvas_image')


class CorrectLabel(models.Model):
    LABEL_CHOICES = [
        ('No Diabetic Retinopathy', 'No Diabetic Retinopathy'),
        ('Mild Diabetic Retinopathy', 'Mild Diabetic Retinopathy'),
        ('Moderate Diabetic Retinopathy', 'Moderate Diabetic Retinopathy'),
        ('Severe Diabetic Retinopathy', 'Severe Diabetic Retinopathy'),
        ('Proliferative Diabetic Retinopathy', 'Proliferative Diabetic Retinopathy'),
        # Add more choices as needed
    ]
    correct_label = models.CharField(max_length=100, choices=LABEL_CHOICES, default='No Diabetic Retinopathy')
    retina_photo = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='correct_label')

class Report(models.Model):
    file = models.FileField(upload_to='reports/')
    retina_photo = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='report')
    created_at = models.DateTimeField(auto_now_add=True)