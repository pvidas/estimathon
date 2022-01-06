from django.urls import path

from . import views

app_name = 'games'
urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:game_slug>/', views.dashboard, name='dashboard'),
    path('<slug:game_slug>/register', views.register, name='register'),
    path('<slug:game_slug>/scoreboard', views.scoreboard, name='scoreboard'),
]