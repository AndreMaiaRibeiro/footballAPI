from django.urls import path
from .views import player_search

urlpatterns = [
    path('players/search/', player_search, name='player-search'),
]
