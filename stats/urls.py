from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Front page
    path('teams/', views.teams_list, name='teams_list'),  # Team list
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),  # Team details
    path('player/<int:player_id>/<str:player_name>/', views.player_detail, name='player_detail'),
    path('search/', views.player_search, name='player_search'),  # Player search
]