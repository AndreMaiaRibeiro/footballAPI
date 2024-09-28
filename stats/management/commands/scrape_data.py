from django.core.management.base import BaseCommand
from stats.scrape import scrape_team_data, scrape_club_squad, scrape_player_list, scrape_player_data

class Command(BaseCommand):
    help = 'Scrape and update teams, players, and player stats data daily'

    def handle(self, *args, **kwargs):
        # Scrape all teams
        teams = scrape_team_data()

        # Scrape the squad for each team
        for team in teams:
            self.stdout.write(f"Updating squad for {team['name']}")
            scrape_club_squad(team['id'], team['name'])

        # Scrape player list
        self.stdout.write("Updating player list")
        players = scrape_player_list()

        # Scrape detailed stats for each player
        for player in players:
            self.stdout.write(f"Updating player stats for {player['name']}")
            scrape_player_data(player['id'], player['name'])

        self.stdout.write(self.style.SUCCESS('Successfully updated team, player, and stats data.'))
