from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('update_user_info/', views.update_user_info, name='update_user_info'),
    path('profile/', views.profile, name='profile'),
]