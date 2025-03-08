from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import ProviderService, AvailabilitySchedule, Appointment, ServiceReview, DoctorSchedule

# Import User model for DoctorForm
User = get_user_model()

class ProviderServiceForm(forms.ModelForm):
    """
    Form for healthcare providers to add or update services they offer
    """
    class Meta:
        model = ProviderService
        fields = ['service', 'custom_price', 'custom_duration', 'is_available']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'custom_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'custom_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = self.fields['service'].queryset.filter(is_active=True)
        self.fields['service'].label_from_instance = lambda obj: f"{obj.category.name} - {obj.name}"


class AvailabilityScheduleForm(forms.ModelForm):
    """
    Form for healthcare providers to add or update their availability schedule
    """
    class Meta:
        model = AvailabilitySchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("End time must be after start time"))
        
        return cleaned_data


class AppointmentForm(forms.ModelForm):
    """
    Form for patients to book appointments with healthcare providers
    """
    # Add fields for doctor and department selection
    doctor = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Doctor"),
        empty_label=_("Select a doctor")
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Department"),
        empty_label=_("Select a department")
    )
    
    class Meta:
        model = Appointment
        fields = ['provider_service', 'appointment_date', 'start_time', 'notes']
        widgets = {
            'provider_service': forms.Select(attrs={'class': 'form-select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)
        
        from apps.users.models import User
        from .models import ServiceCategory
        
        # Set up the doctor and department querysets
        self.fields['doctor'].queryset = User.objects.filter(user_type='healthcare_provider', is_active=True)
        self.fields['department'].queryset = ServiceCategory.objects.filter(is_active=True)
        
        if self.provider:
            # Use a broader queryset to allow for dynamic service selection
            self.fields['provider_service'].queryset = ProviderService.objects.filter(
                is_available=True
            ).select_related('service', 'service__category')
            
            # Update the label_from_instance to include category name and ensure SAR currency
            self.fields['provider_service'].label_from_instance = lambda obj: f"{obj.service.category.name} - {obj.service.name} ({obj.price_display}, {obj.duration_display})"
            
            # Add empty label for the dropdown
            self.fields['provider_service'].empty_label = _("Select a service")
            
            # Pre-select the current provider in the doctor dropdown
            self.initial['doctor'] = self.provider
    
    def clean(self):
        cleaned_data = super().clean()
        provider_service = cleaned_data.get('provider_service')
        appointment_date = cleaned_data.get('appointment_date')
        start_time = cleaned_data.get('start_time')
        
        if provider_service and appointment_date and start_time:
            # Debug information
            print("Checking availability for:")
            print(f"Provider: {provider_service.provider}")
            print(f"Date: {appointment_date} (weekday: {appointment_date.weekday()})")
            print(f"Start time: {start_time}")
            
            # Check if the provider is available at the selected time
            day_of_week = appointment_date.weekday()
            availability = AvailabilitySchedule.objects.filter(
                provider=provider_service.provider,
                day_of_week=day_of_week,
                start_time__lte=start_time,
                end_time__gt=start_time,
                is_active=True
            )
            
            # Debug availability results
            print(f"Availability query: {availability.query}")
            print(f"Availability found: {availability.exists()}")
            if availability.exists():
                for avail in availability:
                    print(f"Available slot: {avail.day_of_week} from {avail.start_time} to {avail.end_time}")
            
            if not availability.exists():
                # Instead of raising an error, let's make it more flexible for providers
                if self.provider and self.provider == provider_service.provider:
                    # If the current user is the provider, allow them to schedule outside availability
                    print("Provider is scheduling their own appointment - bypassing availability check")
                else:
                    raise forms.ValidationError(_("The healthcare provider is not available at the selected time"))
            
            # Calculate end time based on service duration
            duration = provider_service.custom_duration or provider_service.service.duration_minutes or 30
            from datetime import datetime, timedelta
            start_datetime = datetime.combine(appointment_date, start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)
            end_time = end_datetime.time()
            
            # Debug end time calculation
            print(f"Service duration: {duration} minutes")
            print(f"Calculated end time: {end_time}")
            
            # Check for overlapping appointments
            overlapping_query = Appointment.objects.filter(
                provider_service__provider=provider_service.provider,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed'],
            ).filter(
                (models.Q(start_time__lt=end_time) & models.Q(end_time__gt=start_time))
            )
            
            # Exclude the current appointment if we're editing an existing one
            if self.instance and self.instance.pk:
                overlapping_query = overlapping_query.exclude(pk=self.instance.pk)
            
            # Debug overlapping appointments
            print(f"Overlapping query: {overlapping_query.query}")
            print(f"Overlapping appointments found: {overlapping_query.exists()}")
            if overlapping_query.exists():
                for appt in overlapping_query:
                    print(f"Overlapping appointment: {appt.id} from {appt.start_time} to {appt.end_time}")
            
            if overlapping_query.exists():
                # Always prevent overlapping appointments, even for providers
                overlapping_appts = list(overlapping_query)
                if len(overlapping_appts) == 1:
                    appt = overlapping_appts[0]
                    patient_name = appt.patient.get_full_name()
                    error_msg = _(f"This time slot overlaps with an existing appointment for {patient_name} from {appt.start_time.strftime('%H:%M')} to {appt.end_time.strftime('%H:%M')}. Please select a different time.")
                else:
                    error_msg = _(f"This time slot overlaps with {len(overlapping_appts)} existing appointments. Please select a different time.")
                
                raise forms.ValidationError(error_msg)
            
            # Set end_time in the cleaned data
            cleaned_data['end_time'] = end_time
        
        return cleaned_data


class ServiceReviewForm(forms.ModelForm):
    """
    Form for patients to review healthcare services they received
    """
    class Meta:
        model = ServiceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'rating-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Share your experience with this service')}),
        }


class AppointmentStatusForm(forms.ModelForm):
    """
    Form for healthcare providers to update appointment status
    """
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MedicalNotesForm(forms.ModelForm):
    """
    Form for healthcare providers to update medical notes for appointments
    """
    medical_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': _('Enter detailed medical notes about the patient visit')
        }),
        required=False
    )
    
    class Meta:
        model = Appointment
        fields = ['medical_notes']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add a label to the medical_notes field
        self.fields['medical_notes'].label = _("Medical Notes")


class DoctorScheduleForm(forms.ModelForm):
    """
    Form for managing doctor schedules
    """
    class Meta:
        model = DoctorSchedule
        fields = ['day_of_week', 'start_time', 'end_time', 'is_active']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("End time must be after start time"))
        
        return cleaned_data


class DoctorServiceForm(forms.ModelForm):
    """
    Form for adding or editing doctor services
    """
    service = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Service"),
        empty_label=_("Select a service")
    )
    
    class Meta:
        model = ProviderService
        fields = ['service', 'custom_price', 'custom_duration', 'is_available']
        widgets = {
            'custom_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'custom_duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '5', 'step': '5'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        from .models import Service
        
        # Get all active services
        self.fields['service'].queryset = Service.objects.filter(is_active=True)
        
        # Update the label_from_instance to include category name
        self.fields['service'].label_from_instance = lambda obj: f"{obj.category.name} - {obj.name}"
        
        # If this is an edit form and we have an instance, pre-select the service
        if self.instance and self.instance.pk:
            self.fields['service'].initial = self.instance.service


class DoctorForm(forms.ModelForm):
    """
    Form for adding or editing doctor information
    """
    # Define common medical specialties
    SPECIALTY_CHOICES = [
        ('', 'Select Specialty'),
        ('Allergy and Immunology', 'Allergy and Immunology'),
        ('Anesthesiology', 'Anesthesiology'),
        ('Cardiology', 'Cardiology'),
        ('Dermatology', 'Dermatology'),
        ('Emergency Medicine', 'Emergency Medicine'),
        ('Endocrinology', 'Endocrinology'),
        ('Family Medicine', 'Family Medicine'),
        ('Gastroenterology', 'Gastroenterology'),
        ('General Surgery', 'General Surgery'),
        ('Geriatric Medicine', 'Geriatric Medicine'),
        ('Gynecology', 'Gynecology'),
        ('Hematology', 'Hematology'),
        ('Infectious Disease', 'Infectious Disease'),
        ('Internal Medicine', 'Internal Medicine'),
        ('Medical Genetics', 'Medical Genetics'),
        ('Nephrology', 'Nephrology'),
        ('Neurology', 'Neurology'),
        ('Neurosurgery', 'Neurosurgery'),
        ('Obstetrics and Gynecology', 'Obstetrics and Gynecology'),
        ('Oncology', 'Oncology'),
        ('Ophthalmology', 'Ophthalmology'),
        ('Orthopedic Surgery', 'Orthopedic Surgery'),
        ('Otolaryngology', 'Otolaryngology'),
        ('Pathology', 'Pathology'),
        ('Pediatrics', 'Pediatrics'),
        ('Physical Medicine', 'Physical Medicine'),
        ('Plastic Surgery', 'Plastic Surgery'),
        ('Psychiatry', 'Psychiatry'),
        ('Pulmonology', 'Pulmonology'),
        ('Radiology', 'Radiology'),
        ('Rheumatology', 'Rheumatology'),
        ('Sports Medicine', 'Sports Medicine'),
        ('Thoracic Surgery', 'Thoracic Surgery'),
        ('Urology', 'Urology'),
        ('Vascular Surgery', 'Vascular Surgery'),
    ]
    
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=30,
        required=True
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=30,
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=20,
        required=False
    )
    national_id = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=20,
        required=True,
        label="National ID/(IQAMA)"
    )
    specialty = forms.ChoiceField(
        choices=SPECIALTY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    department = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label="Select Department"
    )
    qualifications = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
    years_of_experience = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        required=False
    )
    license_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=50,
        required=False
    )
    languages = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        max_length=100,
        required=False,
        help_text="Comma separated list of languages"
    )
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=False
    )
    is_active = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        initial=True
    )
    profile_image = forms.ImageField(
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'national_id',
            'specialty', 'department', 'qualifications', 
            'years_of_experience', 'license_number', 'languages', 
            'bio', 'is_active', 'profile_image'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ServiceCategory
        
        # Set up the department queryset
        self.fields['department'].queryset = ServiceCategory.objects.filter(is_active=True)
