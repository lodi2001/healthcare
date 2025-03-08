from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q

from apps.ehr.models import EHR, HealthPlan
from apps.genomics.models import GenomicData
from apps.reports.models import Report
from apps.users.models import User, UserProfile
from apps.services.models import ProviderService, Appointment

class BaseDashboardView(LoginRequiredMixin, TemplateView):
    """
    Base dashboard view with common functionality for all user types.
    """
    template_name = 'dashboard/base_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Common statistics for all dashboards
        context['total_users'] = User.objects.count()
        return context


class DoctorDashboardView(BaseDashboardView):
    """
    Dashboard view for individual doctors.
    """
    template_name = 'dashboard/doctor_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get doctor-specific statistics
        doctor = self.request.user
        
        # Count services offered by this doctor
        context['services_count'] = ProviderService.objects.filter(
            provider=doctor,
            is_available=True
        ).count()
        
        # Count appointments
        from datetime import datetime
        today = datetime.now().date()
        appointments = Appointment.objects.filter(provider_service__provider=doctor)
        
        context['total_appointments'] = appointments.count()
        context['completed_appointments'] = appointments.filter(
            status='completed'
        ).count()
        context['upcoming_appointments'] = appointments.filter(
            appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).count()
        
        # Get upcoming appointments for display
        context['upcoming_appointment_list'] = appointments.filter(
            appointment_date__gte=today,
            status__in=['scheduled', 'confirmed']
        ).order_by('appointment_date', 'start_time')[:5]
        
        return context


class ClinicDashboardView(BaseDashboardView):
    """
    Dashboard view for clinics/hospitals that manage multiple doctors.
    """
    template_name = 'dashboard/clinic_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Healthcare provider specific statistics
        context['visits'] = EHR.objects.aggregate(total=Count('visits'))['total'] or 0
        context['medications'] = 4  # Mock data
        context['lab_results'] = 15  # Mock data
        context['vaccinations'] = 20  # Mock data
        context['total_lookups'] = 11  # Mock data
        context['variants'] = 20  # Mock data
        context['reports'] = Report.objects.count()
        context['sequenced_samples'] = GenomicData.objects.aggregate(total=Count('sequenced_samples'))['total'] or 0
        
        # Get doctors associated with this clinic
        context['doctors'] = User.objects.filter(
            user_type='healthcare_provider',
            healthcare_provider_type='doctor'
        ).order_by('first_name')
        
        return context


class HealthcareProviderDashboardView(BaseDashboardView):
    """
    Dashboard view for healthcare providers.
    This view determines which specific dashboard to show based on provider type.
    """
    
    def get_template_names(self):
        user = self.request.user
        if user.user_type == 'healthcare_provider':
            if user.healthcare_provider_type == 'doctor':
                return ['dashboard/doctor_dashboard.html']
            elif user.healthcare_provider_type == 'clinic':
                return ['dashboard/clinic_dashboard.html']
        
        # Default to the original healthcare provider dashboard
        return ['dashboard/healthcare_provider_dashboard.html']


class CompanyDashboardView(BaseDashboardView):
    """
    Dashboard view for companies.
    """
    template_name = 'dashboard/company_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Company specific statistics
        context['market_reports'] = 15  # Mock data
        context['biotech_data'] = 30  # Mock data
        context['pharmaceutical_data'] = 25  # Mock data
        
        return context


class GovernmentDashboardView(BaseDashboardView):
    """
    Dashboard view for government users.
    """
    template_name = 'dashboard/government_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Government specific statistics
        context['national_health_statistics'] = 100  # Mock data
        context['regulatory_data'] = 50  # Mock data
        
        return context


class ResearcherDashboardView(BaseDashboardView):
    """
    Dashboard view for researchers.
    """
    template_name = 'dashboard/researcher_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Researcher specific statistics
        context['research_data'] = 75  # Mock data
        context['genomic_variants'] = 120  # Mock data
        context['research_reports'] = 30  # Mock data
        
        return context


class PatientDashboardView(BaseDashboardView):
    """
    Dashboard view for patients.
    """
    template_name = 'dashboard/patient_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Patient specific statistics
        try:
            patient_profile = UserProfile.objects.get(user=self.request.user)
            context['personal_health_records'] = EHR.objects.filter(patient=patient_profile).count()
            context['health_plans'] = HealthPlan.objects.filter(patient=patient_profile).count()
        except UserProfile.DoesNotExist:
            # Create a profile for the user if it doesn't exist
            patient_profile = UserProfile.objects.create(user=self.request.user)
            context['personal_health_records'] = 0
            context['health_plans'] = 0
        
        context['appointments'] = 3  # Mock data
        
        return context
