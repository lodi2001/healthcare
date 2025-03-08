from django.core.management.base import BaseCommand
from django.db import transaction
from apps.services.models import ServiceCategory, Service, ProviderService
from apps.users.models import User

class Command(BaseCommand):
    help = 'Set up sample services and link them to providers'

    @transaction.atomic
    def handle(self, *args, **options):
        # Create service categories
        self.stdout.write('Creating service categories...')
        general_medicine, created = ServiceCategory.objects.get_or_create(
            name='General Medicine',
            defaults={
                'description': 'General healthcare services',
                'icon': 'fa-stethoscope',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {general_medicine.name}'))
        
        specialized_care, created = ServiceCategory.objects.get_or_create(
            name='Specialized Care',
            defaults={
                'description': 'Specialized healthcare services',
                'icon': 'fa-heartbeat',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created category: {specialized_care.name}'))
        
        # Create services for General Medicine
        self.stdout.write('Creating services...')
        services = [
            {
                'category': general_medicine,
                'name': 'General Consultation',
                'description': 'Regular medical consultation',
                'pricing_type': 'fixed',
                'price': 150,
                'duration_minutes': 30,
                'is_active': True
            },
            {
                'category': general_medicine,
                'name': 'Follow-up Visit',
                'description': 'Follow-up appointment for existing patients',
                'pricing_type': 'fixed',
                'price': 100,
                'duration_minutes': 20,
                'is_active': True
            },
            {
                'category': specialized_care,
                'name': 'Cardiac Assessment',
                'description': 'Comprehensive heart health evaluation',
                'pricing_type': 'fixed',
                'price': 300,
                'duration_minutes': 45,
                'is_active': True
            },
            {
                'category': specialized_care,
                'name': 'Diabetes Management',
                'description': 'Diabetes care and management',
                'pricing_type': 'fixed',
                'price': 200,
                'duration_minutes': 40,
                'is_active': True
            }
        ]
        
        created_services = []
        for service_data in services:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                category=service_data['category'],
                defaults={
                    'description': service_data['description'],
                    'pricing_type': service_data['pricing_type'],
                    'price': service_data['price'],
                    'duration_minutes': service_data['duration_minutes'],
                    'is_active': service_data['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))
            created_services.append(service)
        
        # Link services to providers
        self.stdout.write('Linking services to providers...')
        providers = User.objects.filter(user_type='provider')
        
        if not providers.exists():
            self.stdout.write(self.style.WARNING('No providers found in the system. Please create a provider first.'))
            return
        
        for provider in providers:
            for service in created_services:
                provider_service, created = ProviderService.objects.get_or_create(
                    provider=provider,
                    service=service,
                    defaults={
                        'is_available': True
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Linked service {service.name} to provider {provider.username}'))
        
        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))
