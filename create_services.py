from apps.services.models import ServiceCategory, Service

def create_sample_services():
    # Create service categories
    general_medicine = ServiceCategory.objects.create(
        name='General Medicine',
        description='General healthcare services',
        icon='fa-stethoscope',
        is_active=True
    )
    
    specialized_care = ServiceCategory.objects.create(
        name='Specialized Care',
        description='Specialized healthcare services',
        icon='fa-heartbeat',
        is_active=True
    )
    
    # Create services for General Medicine
    Service.objects.create(
        category=general_medicine,
        name='General Consultation',
        description='Regular medical consultation',
        pricing_type='fixed',
        price=150,
        duration_minutes=30,
        is_active=True
    )
    
    Service.objects.create(
        category=general_medicine,
        name='Follow-up Visit',
        description='Follow-up appointment for existing patients',
        pricing_type='fixed',
        price=100,
        duration_minutes=20,
        is_active=True
    )
    
    # Create services for Specialized Care
    Service.objects.create(
        category=specialized_care,
        name='Cardiac Assessment',
        description='Comprehensive heart health evaluation',
        pricing_type='fixed',
        price=300,
        duration_minutes=45,
        is_active=True
    )
    
    Service.objects.create(
        category=specialized_care,
        name='Diabetes Management',
        description='Diabetes care and management',
        pricing_type='fixed',
        price=200,
        duration_minutes=40,
        is_active=True
    )
    
    print("Sample services created successfully!")

if __name__ == "__main__":
    create_sample_services()
