from django.core.management.base import BaseCommand
from recognition.models import Leaderboard, Team, Recognition
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Debug leaderboard updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeframe',
            type=str,
            choices=['weekly', 'monthly', 'all_time'],
            default='all_time',
            help='Timeframe to update'
        )
        parser.add_argument(
            '--team',
            type=str,
            help='Team name to update leaderboard for (default: system-wide)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        timeframe = options['timeframe']
        team_name = options['team']
        dry_run = options['dry_run']
        
        team = None
        if team_name:
            try:
                team = Team.objects.get(name=team_name)
                self.stdout.write(f"Updating leaderboard for team: {team.name}")
            except Team.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Team '{team_name}' does not exist"))
                return
        
        # Show current state
        self.stdout.write("\nCurrent leaderboard entries:")
        current_entries = Leaderboard.objects.filter(timeframe=timeframe, team=team)
        for entry in current_entries:
            self.stdout.write(f"  {entry.rank}. {entry.volunteer.username}: {entry.points} points")
        
        # Calculate new leaderboard
        self.stdout.write("\nCalculating new leaderboard...")
        recognitions = Recognition.objects.all()
        
        if timeframe == 'weekly':
            from datetime import timedelta
            from django.utils import timezone
            start_date = timezone.now() - timedelta(days=7)
            recognitions = recognitions.filter(created_at__gte=start_date)
        elif timeframe == 'monthly':
            from datetime import timedelta
            from django.utils import timezone
            start_date = timezone.now() - timedelta(days=30)
            recognitions = recognitions.filter(created_at__gte=start_date)
        
        if team:
            recognitions = recognitions.filter(team=team)
        
        volunteer_points = recognitions.values('volunteer').annotate(
            total_points=Sum('points')
        ).order_by('-total_points')
        
        self.stdout.write("\nNew leaderboard would be:")
        for rank, entry in enumerate(volunteer_points, 1):
            points = entry['total_points'] or 0
            self.stdout.write(f"  {rank}. Volunteer ID {entry['volunteer']}: {points} points")
        
        if dry_run:
            self.stdout.write("\nDry run - no changes made")
            return
        
        # Actually update
        try:
            result = Leaderboard.update_leaderboard(timeframe=timeframe, team=team)
            self.stdout.write(self.style.SUCCESS(f"\n{result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nError: {str(e)}"))
            import traceback
            traceback.print_exc()