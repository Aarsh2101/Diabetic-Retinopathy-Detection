# Register your models here.
from django.contrib import admin
from .models import *

admin.site.register(CanvasImage)
admin.site.register(RetinaPhoto)
admin.site.register(GradcamImage)
admin.site.register(CorrectLabel)
admin.site.register(Report)
admin.site.register(Patient)