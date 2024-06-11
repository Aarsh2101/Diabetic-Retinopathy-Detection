from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('predict', views.predict, name='predict'),
    path('results', views.results, name='results'),
    path('correct_prediction', views.correct_prediction, name='correct_prediction'),
    path('save_canvas_image', views.save_canvas_image, name='save_canvas_image'),
    path('team', views.team, name='team'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('update_submission/<int:submission_id>/', views.update_submission, name='update_submission'),
    path('update_submission/<int:submission_id>/update_submission', views.update_submission, name='update_submission_post'),
    path('update_canvas_image', views.update_canvas_image, name='save_canvas_image'),
]