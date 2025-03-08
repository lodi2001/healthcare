import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_project.settings')
django.setup()

from apps.services.models import Service, ServiceCategory, ProviderService
from apps.users.models import User
from django.db.models import Count

def cleanup_services():
    print("Cleaning up duplicate services...")
    # Find duplicate services
    duplicates = Service.objects.values('name', 'category').annotate(count=Count('id')).filter(count__gt=1)
    
    for dup in duplicates:
        # Get all services with this name and category except the first one
        services = Service.objects.filter(name=dup['name'], category_id=dup['category']).order_by('id')[1:]
        print(f"Removing {len(services)} duplicate(s) of {dup['name']}")
        
        # Delete the duplicates
        for service in services:
            service.delete()

def create_provider_services():
    print("Creating provider services...")
    # Get all providers
    providers = User.objects.filter(user_type='provider')
    
    if not providers.exists():
        print("No providers found in the system. Please create a provider first.")
        return
    
    # Get all services
    services = Service.objects.all()
    
    for provider in providers:
        print(f"Setting up services for provider: {provider.username}")
        for service in services:
            # Check if this provider-service link already exists
            provider_service, created = ProviderService.objects.get_or_create(
                provider=provider,
                service=service,
                defaults={
                    'is_available': True
                }
            )
            if created:
                print(f"  - Linked service: {service.name}")

if __name__ == "__main__":
    cleanup_services()
    create_provider_services()
    print("Done!")
