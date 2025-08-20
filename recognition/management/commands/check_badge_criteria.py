from django.core.management.base import BaseCommand
from recognition.utils import BadgeCriteriaChecker

class Command(BaseCommand):
    help = 'Check badge criteria and assign badges automatically'

    def handle(self, *args, **options):
        assigned_count = BadgeCriteriaChecker.check_all_badges()
        
        if assigned_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully assigned {assigned_count} badges based on criteria'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No new badges assigned based on criteria'
                )
            )