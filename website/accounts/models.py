# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class CustomUser(AbstractUser):
    affiliation = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/')

    def __str__(self):
        return self.username

class ZipFile(models.Model):
    file = models.FileField(upload_to='zip_files/', null=True, blank=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)