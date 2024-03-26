from django.db import models
from django.conf import settings

# Create your models here.
class RetinaPhoto(models.Model):
    image = models.ImageField(upload_to='retina_images/')
    
    def __str__(self):
        return self.image.name

class GradcamImage(models.Model):
    image = models.ImageField(upload_to='retina_gradcam_images/')
    
    def __str__(self):
        return self.image.name

class CanvasImage(models.Model):
    image = models.ImageField(upload_to='canvas_images/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='canvas_images')

class CorrectLabel(models.Model):
    LABEL_CHOICES = [
        ('No DR', 'No DR'),
        ('Mild DR', 'Mild DR'),
        ('Moderate DR', 'Moderate DR'),
        ('Severe DR', 'Severe DR'),
        ('Proliferative DR', 'Proliferative DR'),
        # Add more choices as needed
    ]
    correct_label = models.CharField(max_length=100, choices=LABEL_CHOICES, default='No DR')
    image_name = models.CharField(max_length=255)