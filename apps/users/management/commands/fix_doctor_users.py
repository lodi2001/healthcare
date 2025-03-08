from django.core.management.base import BaseCommand
from apps.users.models import User


class Command(BaseCommand):
    help = 'Fixes healthcare provider users who should be doctors but have no healthcare_provider_type set'

    def handle(self, *args, **options):
        # Find healthcare provider users without a provider type
        users_to_fix = User.objects.filter(
            user_type='healthcare_provider',
            healthcare_provider_type__isnull=True
        )
        
        fixed_count = 0
        for user in users_to_fix:
            # Check if username suggests they're a doctor
            if 'dr' in user.username.lower() or 'doctor' in user.username.lower():
                user.healthcare_provider_type = 'doctor'
                user.save()
                fixed_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'Fixed user {user.username}: Set healthcare_provider_type to "doctor"'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'User {user.username} is a healthcare provider but has no provider type'
                ))
        
        # Also check for users who might be doctors but have the wrong user_type
        potential_doctors = User.objects.filter(
            healthcare_provider_type='doctor',
            user_type__isnull=True
        )
        
        for user in potential_doctors:
            user.user_type = 'healthcare_provider'
            user.save()
            fixed_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Fixed user {user.username}: Set user_type to "healthcare_provider"'
            ))
        
        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS('No users needed fixing'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} users'))
