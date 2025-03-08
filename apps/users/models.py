from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser to support multiple user types.
    """
    USER_TYPE_CHOICES = (
        ('healthcare_provider', 'Healthcare Provider'),
        ('company', 'Company'),
        ('government', 'Government'),
        ('researcher', 'Researcher'),
        ('patient', 'Patient'),
    )
    
    HEALTHCARE_PROVIDER_TYPE_CHOICES = (
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('admin', 'Admin'),
        ('clinic', 'Clinic/Hospital'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    national_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    healthcare_provider_type = models.CharField(
        max_length=10, 
        choices=HEALTHCARE_PROVIDER_TYPE_CHOICES,
        blank=True, 
        null=True
    )
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    terms_accepted = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_type})"


class UserProfile(models.Model):
    """
    User Profile model to store additional information about users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField(max_length=200, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
