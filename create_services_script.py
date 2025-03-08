"""
Script to create default service categories and services.
Run this script directly on the production server with:
docker-compose exec web python create_services_script.py
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthcare_project.settings')
django.setup()

# Import models after Django setup
from apps.services.models import Service, ServiceCategory

def create_default_data():
    print("Creating default service categories and services...")
    
    # Create default service categories
    default_categories = [
        {'name': 'Cardiology', 'description': 'Heart and cardiovascular system', 'icon': 'fa-heart'},
        {'name': 'Neurology', 'description': 'Brain, spinal cord, and nervous system', 'icon': 'fa-brain'},
        {'name': 'Orthopedics', 'description': 'Bones, joints, ligaments, tendons, and muscles', 'icon': 'fa-bone'},
        {'name': 'Pediatrics', 'description': 'Medical care for infants, children, and adolescents', 'icon': 'fa-child'},
        {'name': 'Oncology', 'description': 'Cancer diagnosis and treatment', 'icon': 'fa-ribbon'},
        {'name': 'Dermatology', 'description': 'Skin, hair, and nails', 'icon': 'fa-allergies'},
        {'name': 'Ophthalmology', 'description': 'Eye and vision care', 'icon': 'fa-eye'},
        {'name': 'Gynecology', 'description': 'Female reproductive health', 'icon': 'fa-venus'},
        {'name': 'Urology', 'description': 'Urinary tract and male reproductive health', 'icon': 'fa-mars'},
        {'name': 'Psychiatry', 'description': 'Mental health disorders', 'icon': 'fa-brain'},
        {'name': 'General Medicine', 'description': 'General healthcare services', 'icon': 'fa-stethoscope'},
        {'name': 'Specialized Care', 'description': 'Specialized healthcare services', 'icon': 'fa-heartbeat'},
    ]
    
    categories_created = 0
    for cat_data in default_categories:
        cat, created = ServiceCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'icon': cat_data.get('icon', '')
            }
        )
        if created:
            categories_created += 1
            print(f"Created service category: {cat.name}")
    
    # Get the first category for services that need a category
    default_category = ServiceCategory.objects.first()
    if not default_category and categories_created > 0:
        default_category = ServiceCategory.objects.first()
    
    # Create default services
    default_services = [
        {'name': 'General Consultation', 'description': 'General medical consultation', 'price': 150.00, 'duration': 30},
        {'name': 'Specialist Consultation', 'description': 'Consultation with a specialist', 'price': 250.00, 'duration': 45},
        {'name': 'Follow-up Appointment', 'description': 'Follow-up after previous consultation', 'price': 100.00, 'duration': 20},
        {'name': 'Annual Physical', 'description': 'Comprehensive annual physical examination', 'price': 300.00, 'duration': 60},
        {'name': 'Vaccination', 'description': 'Routine vaccination', 'price': 80.00, 'duration': 15},
        {'name': 'Blood Test', 'description': 'Standard blood panel', 'price': 120.00, 'duration': 15},
        {'name': 'X-Ray', 'description': 'X-ray imaging', 'price': 200.00, 'duration': 30},
        {'name': 'Ultrasound', 'description': 'Ultrasound imaging', 'price': 250.00, 'duration': 45},
        {'name': 'MRI Scan', 'description': 'Magnetic Resonance Imaging', 'price': 800.00, 'duration': 60},
        {'name': 'CT Scan', 'description': 'Computed Tomography scan', 'price': 700.00, 'duration': 45},
        {'name': 'Follow-up Visit', 'description': 'Follow-up appointment for existing patients', 'price': 100.00, 'duration': 20},
        {'name': 'Cardiac Assessment', 'description': 'Comprehensive heart health evaluation', 'price': 300.00, 'duration': 45},
        {'name': 'Diabetes Management', 'description': 'Diabetes care and management', 'price': 200.00, 'duration': 40},
    ]
    
    services_created = 0
    if default_category:
        for service_data in default_services:
            service, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'category': default_category,
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration_minutes': service_data['duration'],
                    'pricing_type': 'fixed'
                }
            )
            if created:
                services_created += 1
                print(f"Created service: {service.name}")
    else:
        print('No service category available. Cannot create services.')
    
    print(f'Created {categories_created} service categories and {services_created} services')

if __name__ == "__main__":
    create_default_data()
