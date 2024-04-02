from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('predict', views.predict, name='predict'),
    path('correct_prediction', views.correct_prediction, name='correct_prediction'),
    path('save_canvas_image', views.save_canvas_image, name='save_canvas_image'),
    path('team', views.team, name='team'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('update_submission/<int:submission_id>/', views.update_submission, name='update_submission'),
]