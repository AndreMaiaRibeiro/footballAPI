from .models import Team, Player

from django.core.cache import cache
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_club_squad(club_id, club_name):
    team, created = Team.objects.get_or_create(id=club_id, defaults={'name': club_name.replace('-', ' ')})

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    base_url = f"https://www.premierleague.com/clubs/{club_id}/{club_name}/squad"
    driver.get(base_url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "stats-card")))
        player_elements = driver.find_elements(By.CLASS_NAME, "stats-card")

        for player_element in player_elements:
            try:
                player_id = player_element.get_attribute("data-player-id")
                first_name = player_element.find_element(By.CLASS_NAME, "stats-card__player-first").text
                last_name = player_element.find_element(By.CLASS_NAME, "stats-card__player-last").text
                name = f"{first_name} {last_name}"
                position = player_element.find_element(By.CLASS_NAME, "stats-card__player-position").text
                nationality = player_element.find_element(By.CLASS_NAME, "stats-card__flag-icon").get_attribute("alt")
                image_url = player_element.find_element(By.CLASS_NAME, "statCardImg").get_attribute('src')

                Player.objects.update_or_create(
                    player_id=player_id,
                    team=team,
                    defaults={
                        'name': name,
                        'position': position,
                        'nationality': nationality,
                        'image': image_url,
                    }
                )
            except NoSuchElementException as e:
                print(f"Error extracting player details: {e}")
    finally:
        driver.quit()


def scrape_player_list():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    base_url = "https://www.premierleague.com/players"
    driver.get(base_url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "player__name")))

    players = []
    player_elements = driver.find_elements(By.CLASS_NAME, "player__name")

    for player_element in player_elements:
        href = player_element.get_attribute('href')
        if href:
            player_id = href.split('/')[4]
            player_name = href.split('/')[5]
            img_tag = player_element.find_element(By.TAG_NAME, 'img')
            player_image_url = img_tag.get_attribute('src')

            players.append({
                'id': player_id,
                'name': player_name,
                'image': player_image_url
            })

    driver.quit()
    return players



def scrape_player_data(player_id, player_name):
    try:
        player_url = f"https://www.premierleague.com/players/{player_id}/{player_name}/stats"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(player_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve page for {player_name}, status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        player_name = soup.find('div', class_='playerDetails').find('h1').text.strip()
        stats = soup.find_all('span', class_='allStatContainer')
        stats_data = {stat['data-stat']: stat.text.strip() for stat in stats}

        return {
            'name': player_name,
            'stats': stats_data
        }
    except Exception as e:
        print(f"Error fetching player data for {player_name}: {e}")
        return None


def scrape_team_data():
    cached_teams = cache.get('team_data')
    if cached_teams:
        return cached_teams

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    base_url = "https://www.premierleague.com/clubs"
    driver.get(base_url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.clubIndex.col-12")))
        team_container = driver.find_element(By.CSS_SELECTOR, "div.clubIndex.col-12")
        team_elements = team_container.find_elements(By.CLASS_NAME, "club-card-wrapper")

        teams = []
        for team_element in team_elements[:20]:
            link = team_element.find_element(By.TAG_NAME, "a")
            href = link.get_attribute('href')
            team_id = href.split('/')[4]
            team_name = href.split('/')[5]
            img_tag = team_element.find_element(By.TAG_NAME, "img")
            team_logo_url = img_tag.get_attribute('srcset').split(",")[-1].split(" ")[0] if img_tag else ""

            teams.append({
                'id': team_id,
                'name': team_name.replace('-', ' '),
                'logo': team_logo_url
            })

            # Save team in the database
            Team.objects.update_or_create(id=team_id, defaults={'name': team_name.replace('-', ' '), 'crest': team_logo_url})

        cache.set('team_data', teams, 60 * 60 * 24)
        return teams
    finally:
        driver.quit()
