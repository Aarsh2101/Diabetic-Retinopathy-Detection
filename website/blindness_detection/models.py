from django.db import models

# Create your models here.
class RetinaPhoto(models.Model):
    image = models.ImageField(upload_to='retina_images/')
    
    def __str__(self):
        return self.image.name
