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
import urllib.parse


def scrape_club_squad(club_id, club_name):
    # Ensure the team exists in the database, or create it if necessary
    team, created = Team.objects.get_or_create(id=club_id, defaults={'name': club_name.replace('-', ' ')})

    # Fetch all players for this team
    players_in_db = Player.objects.filter(team=team)

    # If all players have stats in the database, return the current data without scraping
    if all(player.stats for player in players_in_db):
        print(f"Returning players data from the database for team {team.name}")
        return list(players_in_db.values())  # Return the players if their stats exist in the database

    # Proceed with scraping if stats are missing or no players are found
    print(f"Scraping players data for team {team.name}")
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

                # Check if the player already exists in the database and has stats
                player = Player.objects.filter(player_id=player_id, team=team).first()
                if player and player.stats:
                    # If the player already has stats, return them directly from the database
                    continue  # Skip scraping for this player if stats already exist

                # Extract player data from the page
                name_element = player_element.find_element(By.CLASS_NAME, "stats-card__player-name")
                player_name = name_element.text

                position = player_element.find_element(By.CLASS_NAME, "stats-card__player-position").text

                nationality = driver.execute_script(
                    "return arguments[0].innerText || arguments[0].textContent;",
                    player_element.find_element(By.CLASS_NAME, "stats-card__player-country")
                )

                flag_image_url = player_element.find_element(By.CLASS_NAME, "stats-card__flag-icon").get_attribute('src')
                image_url = player_element.find_element(By.CLASS_NAME, "statCardImg").get_attribute('src')

                # Save or update the player record in the database
                player, _ = Player.objects.update_or_create(
                    player_id=player_id,
                    team=team,
                    defaults={
                        'name': player_name,
                        'position': position,
                        'nationality': nationality,
                        'flag_image': flag_image_url,
                        'image': image_url,
                    }
                )

                # If scraping was done, also populate player stats if they don't exist
                if not player.stats:
                    stats = scrape_player_data(player_id, player_name)
                    player.stats = stats
                    player.save()

            except NoSuchElementException as e:
                print(f"Error extracting data for player with ID: {player_id}. Error: {e}")
    finally:
        driver.quit()

    # Return the updated list of players from the database
    return list(Player.objects.filter(team=team).values())






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



def scrape_player_stats(soup):
    stats = {}

    # First, scrape the top 4 stats: Appearances, Wins, Goals, Losses
    top_stats_section = soup.find('div', class_='player-stats__top-stats')
    if top_stats_section:
        top_stat_items = top_stats_section.find_all('div', class_='player-stats__top-stat')
        if top_stat_items:
            for top_stat in top_stat_items:
                stat_label = top_stat.find('span', class_='player-stats__top-stat-value').contents[0].strip()  # Get the stat label
                stat_value = top_stat.find('span', class_='allStatContainer').text.strip()  # Get the stat value
                stats[stat_label] = stat_value

    # Scrape stats from the main section (Goalkeeping, Defence, Attack, Discipline, Team Play)
    stats_section = soup.find('ul', class_='player-stats__stats-wrapper')
    if stats_section:
        for stat_item in stats_section.find_all('li', class_='player-stats__stat'):
            category_title = stat_item.find('div', class_='player-stats__stat-title').text.strip()
            for stat_value in stat_item.find_all('div', class_='player-stats__stat-value'):
                stat_name = stat_value.contents[0].strip()  # Get the stat name
                stat_number = stat_value.find('span', class_='allStatContainer').text.strip()  # Get the stat value
                stats[f"{category_title} - {stat_name}"] = stat_number

    return stats




def scrape_player_data(player_id, player_name):
    try:
        formatted_player_name = urllib.parse.quote(player_name.strip().replace('\n', '').replace(' ', '-').lower())

        player_url = f"https://www.premierleague.com/players/{player_id}/{formatted_player_name}/stats"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(player_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve page for {player_name}, status code: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Get nationality and flag
        nationality = soup.find('span', class_='player-overview__player-country').text.strip()
        flag_image = soup.find('img', class_='player-overview__flag-icon').get('src')

        # Locate the position inside the player overview section
        position_section = soup.find('section', class_='player-overview__side-widget')
        position_element = position_section.find('div', string="Position").find_next('div', class_='player-overview__info')

        if not position_element:
            print(f"Could not determine the position for player {player_name}.")
            return None

        position = position_element.get_text(strip=True).lower()
        print(f"Position for {player_name}: {position}")

        # Scrape the player's stats (Unified function for all positions)
        stats = scrape_player_stats(soup)

        return {
            'name': player_name,
            'position': position,
            'nationality': nationality,
            'flag_image': flag_image,
            'stats': stats
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
