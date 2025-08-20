from django.core.management.base import BaseCommand
from recognition.models import Leaderboard, Team, Recognition
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from django.db import transaction

class Command(BaseCommand):
    help = 'Update leaderboards for all timeframes and teams'

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeframe',
            type=str,
            choices=['weekly', 'monthly', 'all_time'],
            help='Update specific timeframe (default: all)'
        )
        parser.add_argument(
            '--team',
            type=str,
            help='Update leaderboard for specific team (default: all teams)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating'
        )

    def handle(self, *args, **options):
        timeframe = options['timeframe']
        team_name = options['team']
        verbose = options['verbose']
        dry_run = options['dry_run']

        # Determine which timeframes to update
        timeframes = [timeframe] if timeframe else ['weekly', 'monthly', 'all_time']

        # Get teams to update
        if team_name:
            try:
                teams = [Team.objects.get(name=team_name)]
            except Team.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Team '{team_name}' not found"))
                return
        else:
            teams = Team.objects.all()
            # Include None for system-wide leaderboards
            teams = list(teams) + [None]

        total_updates = 0
        errors = []

        for team in teams:
            team_name_str = team.name if team else "System-wide"
            if verbose:
                self.stdout.write(f"\nProcessing {team_name_str}...")

            for tf in timeframes:
                try:
                    if verbose:
                        self.stdout.write(f"  Updating {tf} leaderboard...")
                    
                    # Calculate date range based on timeframe
                    now = timezone.now()
                    if tf == 'weekly':
                        start_date = now - timedelta(days=7)
                    elif tf == 'monthly':
                        start_date = now - timedelta(days=30)
                    else:
                        start_date = None
                    
                    # Filter recognitions
                    recognitions = Recognition.objects.all()
                    if start_date:
                        recognitions = recognitions.filter(created_at__gte=start_date)
                    if team:
                        recognitions = recognitions.filter(team=team)
                    
                    # Calculate points for each volunteer
                    volunteer_points = recognitions.values('volunteer').annotate(
                        total_points=Sum('points')
                    ).order_by('-total_points')
                    
                    if verbose:
                        self.stdout.write(f"    Found {len(volunteer_points)} volunteers with points")
                    
                    if not dry_run:
                        # Use transaction to ensure atomicity
                        with transaction.atomic():
                            # Clear existing leaderboard entries
                            deleted_count, _ = Leaderboard.objects.filter(
                                timeframe=tf, 
                                team=team
                            ).delete()
                            
                            # Create new leaderboard entries
                            created_count = 0
                            for rank, entry in enumerate(volunteer_points, 1):
                                Leaderboard.objects.create(
                                    volunteer_id=entry['volunteer'],
                                    points=entry['total_points'] or 0,
                                    rank=rank,
                                    timeframe=tf,
                                    team=team
                                )
                                created_count += 1
                            
                            total_updates += 1
                            
                            if verbose:
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"    {tf}: Deleted {deleted_count}, Created {created_count}"
                                    )
                                )
                    else:
                        # For dry run, just show what would happen
                        if verbose:
                            self.stdout.write(f"    Would create {len(volunteer_points)} entries")
                
                except Exception as e:
                    error_msg = f"Error updating {tf} leaderboard for {team_name_str}: {str(e)}"
                    errors.append(error_msg)
                    if verbose:
                        self.stdout.write(self.style.ERROR(f"    {error_msg}"))

        # Summary
        if dry_run:
            self.stdout.write(f"\nDry run completed. No changes made.")
        else:
            self.stdout.write(f"\nSummary:")
            self.stdout.write(f"  Total updates: {total_updates}")
            if errors:
                self.stdout.write(f"  Errors: {len(errors)}")
                for error in errors:
                    self.stdout.write(self.style.ERROR(f"    {error}"))
            else:
                self.stdout.write(self.style.SUCCESS("  All updates completed successfully"))