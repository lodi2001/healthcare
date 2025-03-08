from django.urls import path

from .views import (
    HealthcareProviderDashboardView,
    DoctorDashboardView,
    ClinicDashboardView,
    CompanyDashboardView,
    GovernmentDashboardView,
    ResearcherDashboardView,
    PatientDashboardView
)

urlpatterns = [
    path('healthcare-provider/', HealthcareProviderDashboardView.as_view(), name='healthcare_provider_dashboard'),
    path('doctor/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('clinic/', ClinicDashboardView.as_view(), name='clinic_dashboard'),
    path('company/', CompanyDashboardView.as_view(), name='company_dashboard'),
    path('government/', GovernmentDashboardView.as_view(), name='government_dashboard'),
    path('researcher/', ResearcherDashboardView.as_view(), name='researcher_dashboard'),
    path('patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
]
