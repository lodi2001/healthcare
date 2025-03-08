from django.core.management.base import BaseCommand
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Import services and service categories data from JSON fixtures'

    def handle(self, *args, **options):
        fixtures_dir = 'fixtures'
        
        # Check if fixtures directory exists
        if not os.path.exists(fixtures_dir):
            self.stdout.write(self.style.WARNING(f'Directory {fixtures_dir} does not exist. Creating it.'))
            os.makedirs(fixtures_dir)
            self.stdout.write(self.style.SUCCESS(f'Created directory {fixtures_dir}'))
            self.stdout.write(self.style.WARNING('No fixture files found. Please run export_initial_data first.'))
            return
        
        # Check if fixture files exist
        services_file = os.path.join(fixtures_dir, 'services.json')
        categories_file = os.path.join(fixtures_dir, 'service_categories.json')
        
        if not os.path.exists(services_file):
            self.stdout.write(self.style.WARNING(f'File {services_file} does not exist. Skipping services import.'))
        else:
            # Load services data
            call_command('loaddata', services_file)
            self.stdout.write(self.style.SUCCESS(f'Imported services data from {services_file}'))
        
        if not os.path.exists(categories_file):
            self.stdout.write(self.style.WARNING(f'File {categories_file} does not exist. Skipping service categories import.'))
        else:
            # Load service categories data
            call_command('loaddata', categories_file)
            self.stdout.write(self.style.SUCCESS(f'Imported service categories data from {categories_file}'))
        
        self.stdout.write(self.style.SUCCESS('Data import complete.'))
