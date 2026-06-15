# taskAssignmentApp/management/commands/check_missed_assignments.py

from datetime import timezone
from django.core.management.base import BaseCommand
from taskAssignmentApp.status_service import TaskAssignmentStatusService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for overdue assignments and mark them as missed'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (don\'t actually update)',
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.NOTICE('Checking for missed assignments...'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            
            from taskAssignmentApp.models import TaskAssignment
            now = timezone.now()
            
            overdue = TaskAssignment.objects.filter(
                status='scheduled',
                end_time__lt=now
            )
            
            self.stdout.write(f"Found {overdue.count()} overdue assignments that would be marked as missed:")
            for assignment in overdue[:10]:  # Show first 10
                self.stdout.write(f"  - Assignment #{assignment.id}: {assignment.task.name} for {assignment.user.full_name}")
            
            if overdue.count() > 10:
                self.stdout.write(f"  ... and {overdue.count() - 10} more")
        else:
            count = TaskAssignmentStatusService.check_for_missed_assignments()
            self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} assignments as missed'))