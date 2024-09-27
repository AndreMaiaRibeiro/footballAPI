from collections import defaultdict
from django.shortcuts import render
from django.core.cache import cache
import requests
from django.conf import settings

def cache_premier_league_squads():
    headers = {'X-Auth-Token': settings.FOOTBALL_API_KEY}
    teams_url = f"{settings.FOOTBALL_API_URL}/competitions/PL/teams"
    teams_response = requests.get(teams_url, headers=headers)

    if teams_response.status_code == 200:
        teams = teams_response.json().get('teams', [])
        all_players = []

        for team in teams:
            squad_url = f"{settings.FOOTBALL_API_URL}/teams/{team['id']}"
            squad_response = requests.get(squad_url, headers=headers)

            if squad_response.status_code == 200:
                squad = squad_response.json().get('squad', [])
                all_players.extend(squad)

        cache.set('premier_league_players', all_players, timeout=86400)

def player_search(request):
    query = request.GET.get('q', '').lower()
    players = cache.get('premier_league_players')

    # Fetch players if not in cache
    if not players:
        cache_premier_league_squads()
        players = cache.get('premier_league_players')

    if not players:
        return render(request, 'player_search.html', {'players': [], 'query': query})

    # Filter players based on the search query
    filtered_players = [player for player in players if query in player.get('name', '').lower()]

    return render(request, 'player_search.html', {'players': filtered_players, 'query': query})
