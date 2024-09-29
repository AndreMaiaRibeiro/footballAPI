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
from .models import Team, Player 


def player_detail(request, player_id, player_name):
    try:
        # Check if the player exists in the database
        player = Player.objects.filter(player_id=player_id).first()

        if player and player.stats and player.nationality != 'Unknown' and player.flag_image:
            # Use the existing player data without modifying the image
            player_data = {
                'name': player.name,
                'position': player.position,
                'nationality': player.nationality,
                'flag_image': player.flag_image,
                'stats': player.stats
            }
        else:
            # Scrape player data if missing or incomplete
            player_data = scrape.scrape_player_data(player_id, player_name)

            if player_data is None:
                return JsonResponse({'error': f"No data found for player {player_name}"}, status=404)

            # Save or update player data in the database, but don't update the image
            if player:
                player.name = player_data['name']
                player.position = player_data['position']
                player.nationality = player_data.get('nationality', player.nationality)
                player.flag_image = player_data.get('flag_image', player.flag_image)
                player.stats = player_data['stats']
                player.save()
            else:
                Player.objects.create(
                    player_id=player_id,
                    name=player_data['name'],
                    position=player_data['position'],
                    nationality=player_data.get('nationality', 'Unknown'),
                    image=player_data.get('image', 'https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png'),
                    flag_image=player_data.get('flag_image', ''),
                    stats=player_data['stats']
                )

        # Fetch the image directly from the database
        player_image = player.image if player else 'https://resources.premierleague.com/premierleague/photos/players/110x140/Photo-Missing.png'

        # Render player data and the image separately to the HTML template
        context = {
            'player': player_data,
            'image': player_image  # Pass the image directly
        }
        return render(request, 'playerdetails.html', context)

    except Exception as e:
        print(f"Error fetching player details: {e}")
        return JsonResponse({'error': 'Internal Server Error'}, status=500)




def index(request):
    return render(request, 'home.html')


def teams_list(request):
    teams = scrape.scrape_team_data()  # Use the new scraper to get team data
    return render(request, 'teams.html', {'teams': teams})

def team_detail(request, team_id):
    try:
        # Check if the team exists in the database
        team = Team.objects.get(id=team_id)

        # Check if players for this team exist in the database
        players = Player.objects.filter(team=team)

        # If no players found, run the scrape function to get them
        if not players.exists():
            # Scrape players for the selected team
            club_name = team.name.replace(' ', '-')  # Format club name for the URL
            players_data = scrape.scrape_club_squad(team_id, club_name)  # Get players from the scraper

            # Save the scraped players to the database
            for player_data in players_data:
                Player.objects.create(
                    player_id=player_data['id'],
                    name=player_data['name'],
                    position=player_data['position'],
                    nationality=player_data['nationality'],
                    image=player_data['image'],
                    flag_image=player_data['flag_image'],  # Assuming flag_image is stored
                    team=team
                )

            # Fetch the newly saved players
            players = Player.objects.filter(team=team)

    except Team.DoesNotExist:
        # If team not found in the database, scrape the data and save it
        teams_data = scrape.scrape_team_data()

        # Find the team from the scraped data
        team_data = next((team for team in teams_data if str(team['id']) == str(team_id)), None)

        if not team_data:
            return JsonResponse({'error': 'Team not found'}, status=404)

        # Save the team to the database
        team = Team.objects.create(
            id=team_data['id'],
            name=team_data['name'],
            logo=team_data['logo']
        )

        # Scrape players for the selected team
        club_name = team.name.replace(' ', '-')  # Format club name for the URL
        players_data = scrape.scrape_club_squad(team_id, club_name)  # Get players from the scraper

        # Save the scraped players to the database
        for player_data in players_data:
            Player.objects.create(
                player_id=player_data['id'],
                name=player_data['name'],
                position=player_data['position'],
                nationality=player_data['nationality'],
                image=player_data['image'],
                flag_image=player_data['flag_image'],  # Assuming flag_image is stored
                team=team
            )

        # Fetch the newly saved players
        players = Player.objects.filter(team=team)

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

