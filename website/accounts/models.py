# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    affiliation = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/')

    def __str__(self):
        return self.username