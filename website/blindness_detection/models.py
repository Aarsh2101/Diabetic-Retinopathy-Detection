from django.db import models
from django.conf import settings

# Create your models here.
class RetinaPhoto(models.Model):
    image = models.ImageField(upload_to='retina_images/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.image.name

class GradcamImage(models.Model):
    image = models.ImageField(upload_to='retina_gradcam_images/')
    retina_photo = models.OneToOneField('RetinaPhoto', on_delete=models.CASCADE, related_name='gradcam_image')
    
    def __str__(self):
        return self.image.name

class CanvasImage(models.Model):
    image = models.ImageField(upload_to='canvas_images/')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='canvas_images')
    retina_photo = models.OneToOneField('RetinaPhoto', on_delete=models.CASCADE, related_name='canvas_image')


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
    retina_photo = models.OneToOneField('RetinaPhoto', on_delete=models.CASCADE, related_name='correct_label')

class ZipFile(models.Model):
    # name = models.CharField(max_length=100, null=True, blank=True)
    file = models.FileField(upload_to='zip_files/', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    # def __str__(self):
    #     return self.file.name