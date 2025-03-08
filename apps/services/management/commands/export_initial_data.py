from django.core.management.base import BaseCommand
import json
from apps.services.models import Service, ServiceCategory
from django.core import serializers


class Command(BaseCommand):
    help = 'Export services and service categories data to JSON fixtures'

    def handle(self, *args, **options):
        # Export services
        services = Service.objects.all()
        services_data = serializers.serialize('json', services)
        
        with open('fixtures/services.json', 'w') as f:
            f.write(services_data)
            self.stdout.write(self.style.SUCCESS(f'Exported {services.count()} services'))
        
        # Export service categories
        categories = ServiceCategory.objects.all()
        categories_data = serializers.serialize('json', categories)
        
        with open('fixtures/service_categories.json', 'w') as f:
            f.write(categories_data)
            self.stdout.write(self.style.SUCCESS(f'Exported {categories.count()} service categories'))
        
        self.stdout.write(self.style.SUCCESS('Data export complete. Files saved to fixtures/services.json and fixtures/service_categories.json'))
