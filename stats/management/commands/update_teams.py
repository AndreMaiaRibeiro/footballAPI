from django.core.management.base import BaseCommand
from stats.models import Team, Player
from stats.scrape import scrape_team_data, scrape_club_squad, scrape_player_data

class Command(BaseCommand):
    help = 'Scrape and update teams and players data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting team and player data update...")

        # Step 1: Scrape all team data
        teams = scrape_team_data()

        # Step 2: Update team data in the database
        for team_data in teams:
            self.stdout.write(f"Updating team: {team_data['name']}")
            team, created = Team.objects.update_or_create(
                id=team_data['id'],
                defaults={
                    'name': team_data['name'],
                    'crest': team_data['logo']
                }
            )

            # Step 3: Scrape the squad data for each team
            self.stdout.write(f"Updating squad for team: {team_data['name']}")
            club_name = team_data['name'].replace(' ', '-').lower()
            players_data = scrape_club_squad(team_data['id'], club_name)

            # Step 4: Update player data and scrape stats if necessary
            if players_data:
                for player_data in players_data:
                    self.stdout.write(f"Updating player: {player_data['name']}")
                    player, created = Player.objects.update_or_create(
                        player_id=player_data['id'],
                        team=team,
                        defaults={
                            'name': player_data['name'],
                            'position': player_data['position'],
                            'nationality': player_data['nationality'],
                            'image': player_data['image'],
                            'flag_image': player_data['flag_image'],
                        }
                    )

                    # Step 5: If player has no stats, scrape the player's individual stats
                    if not player.stats:
                        self.stdout.write(f"Scraping stats for player: {player_data['name']}")
                        player_stats = scrape_player_data(player.player_id, player.name)
                        if player_stats:
                            player.stats = player_stats['stats']
                            player.save()

            else:
                self.stdout.write(f"Failed to retrieve player data for {team_data['name']}")

        self.stdout.write(self.style.SUCCESS("Successfully updated team and player data."))
