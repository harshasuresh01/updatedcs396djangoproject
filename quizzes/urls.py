from django.urls import path
from . import views
from .views import create_quiz, quiz_list

urlpatterns = [
    path('list/', views.quiz_list, name='quiz_list'),
    path('create/', create_quiz, name='create_quiz'),
    path('detail/<str:quiz_title>/', views.quiz_detail, name='quiz_detail'),


]
