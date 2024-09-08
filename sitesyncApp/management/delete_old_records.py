from django.core.management.base import BaseCommand
from your_app.models import Projects, Chat, Events  # Import your models

class Command(BaseCommand):
    help = 'Delete records that are older than 30 days'

    def handle(self, *args, **kwargs):
        Projects.objects.delete_old_records()
        Chat.objects.delete_old_records()
        Events.objects.delete_old_records()
        # Add other models as needed

        self.stdout.write(self.style.SUCCESS('Old records deleted successfully.'))
