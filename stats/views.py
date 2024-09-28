from collections import defaultdict
from django.shortcuts import render
from django.core.cache import cache
import requests
from django.conf import settings
from bs4 import BeautifulSoup
from django.http import JsonResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . import scrape



def player_detail(request, player_id, player_name):
    player_data = scrape.scrape_player_data(player_id, player_name)  # Fetch the player data
    
    if player_data is None:
        return JsonResponse({'error': f"No data found for player {player_name}"}, status=404)
    
    return JsonResponse(player_data, safe=False)


def index(request):
    return render(request, 'home.html')


def teams_list(request):
    teams = scrape.scrape_team_data()  # Use the new scraper to get team data
    return render(request, 'teams.html', {'teams': teams})

def team_detail(request, team_id):
    teams = scrape.scrape_team_data()  # Get team data
    
    # Ensure that the team_id is being compared as a string
    team = next((team for team in teams if str(team['id']) == str(team_id)), None)
    
    if not team:
        return JsonResponse({'error': 'Team not found'}, status=404)
    
    # Scrape players for the selected team
    club_name = team['name'].replace(' ', '-')  # Format club name for the URL
    players = scrape.scrape_club_squad(team_id, club_name)  # Get players from the scraper
    
    # Render the team details and player list in the template
    return render(request, 'teamdetails.html', {'team': team, 'players': players})


def player_search(request):
    query = request.GET.get('q', '').lower()

    # Scrape player list from the Premier League website
    players = scrape.scrape_player_list()  # Scraper replaces the cache retrieval
    print(players)

    if not players:
        return render(request, 'player_search.html', {'players': [], 'query': query})

    # Filter players based on the search query
    filtered_players = [player for player in players if query in player.get('name', '').lower()]

    return render(request, 'player_search.html', {'players': filtered_players, 'query': query})

