from django.urls import path

from .views import ClinicalServicesView, GenomicServicesView
from .provider_views import (
    ProviderServiceListView, ProviderServiceCreateView, ProviderServiceUpdateView, ProviderServiceDeleteView,
    ProviderAppointmentListView, ProviderAppointmentDetailView, ProviderAppointmentUpdateView,
    ProviderAvailabilityListView, ProviderAvailabilityCreateView, ProviderAvailabilityUpdateView, ProviderAvailabilityDeleteView,
    ProviderDashboardView, ProviderReviewListView,
    ProviderServiceStatisticsView, ProviderPatientSearchView, ProviderPatientDetailView, MedicalNotesUpdateView,
    ProviderPatientRegisterView, ProviderScheduleAppointmentView,
    GetDoctorsByDepartmentView, GetServicesByDoctorAndDepartmentView
)
from .admin_views import (
    DoctorListView, DoctorDetailView, DoctorServicesView, DoctorAddServiceView, DoctorEditServiceView, DoctorDeleteServiceView,
    DoctorScheduleView, DoctorAddScheduleView, DoctorEditScheduleView, DoctorDeleteScheduleView, DoctorCreateView, DoctorUpdateView,
    DoctorDeleteView, DoctorReactivateView
)

urlpatterns = [
    # Existing service URLs
    path('clinical/', ClinicalServicesView.as_view(), name='clinical_services'),
    path('genomic/', GenomicServicesView.as_view(), name='genomic_services'),
    
    # Healthcare provider service URLs
    path('provider/dashboard/', ProviderDashboardView.as_view(), name='provider_dashboard'),
    
    # Provider services management
    path('provider/services/', ProviderServiceListView.as_view(), name='provider_services'),
    path('provider/services/add/', ProviderServiceCreateView.as_view(), name='provider_service_add'),
    path('provider/services/<int:pk>/update/', ProviderServiceUpdateView.as_view(), name='provider_service_update'),
    path('provider/services/<int:pk>/delete/', ProviderServiceDeleteView.as_view(), name='provider_service_delete'),
    path('provider/services/statistics/', ProviderServiceStatisticsView.as_view(), name='provider_service_statistics'),
    
    # Provider appointments management
    path('provider/appointments/', ProviderAppointmentListView.as_view(), name='provider_appointments'),
    path('provider/appointments/<int:pk>/', ProviderAppointmentDetailView.as_view(), name='provider_appointment_detail'),
    path('provider/appointments/<int:pk>/update/', ProviderAppointmentUpdateView.as_view(), name='provider_appointment_update'),
    path('provider/appointments/<int:pk>/medical-notes/', MedicalNotesUpdateView.as_view(), name='medical_notes_update'),
    
    # Provider availability management
    path('provider/availability/', ProviderAvailabilityListView.as_view(), name='provider_availability'),
    path('provider/availability/add/', ProviderAvailabilityCreateView.as_view(), name='provider_availability_add'),
    path('provider/availability/<int:pk>/update/', ProviderAvailabilityUpdateView.as_view(), name='provider_availability_update'),
    path('provider/availability/<int:pk>/delete/', ProviderAvailabilityDeleteView.as_view(), name='provider_availability_delete'),
    
    # Provider patient management
    path('provider/patients/search/', ProviderPatientSearchView.as_view(), name='provider_patient_search'),
    path('provider/patients/<int:pk>/', ProviderPatientDetailView.as_view(), name='provider_patient_detail'),
    path('provider/patients/register/', ProviderPatientRegisterView.as_view(), name='provider_patient_register'),
    
    # Schedule appointment - both with and without patient_id
    path('provider/schedule-appointment/', ProviderScheduleAppointmentView.as_view(), name='provider_schedule_appointment'),
    path('provider/patients/<int:patient_id>/schedule-appointment/', ProviderScheduleAppointmentView.as_view(), name='provider_schedule_appointment_for_patient'),

    # AJAX endpoints for appointment scheduling
    path('provider/api/doctors-by-department/', GetDoctorsByDepartmentView.as_view(), name='api_doctors_by_department'),
    path('provider/api/services-by-doctor-department/', GetServicesByDoctorAndDepartmentView.as_view(), name='api_services_by_doctor_department'),

    # Provider reviews
    path('provider/reviews/', ProviderReviewListView.as_view(), name='provider_reviews'),
]

# Admin URLs for doctor service management
urlpatterns += [
    path('admin/doctors/', DoctorListView.as_view(), name='admin_doctor_list'),
    path('admin/doctors/add/', DoctorCreateView.as_view(), name='admin_doctor_add'),
    path('admin/doctors/<int:pk>/', DoctorDetailView.as_view(), name='admin_doctor_detail'),
    path('admin/doctors/<int:pk>/edit/', DoctorUpdateView.as_view(), name='admin_doctor_edit'),
    path('admin/doctors/<int:pk>/delete/', DoctorDeleteView.as_view(), name='admin_doctor_delete'),
    path('admin/doctors/<int:pk>/reactivate/', DoctorReactivateView.as_view(), name='admin_doctor_reactivate'),
    path('admin/doctors/<int:pk>/services/', DoctorServicesView.as_view(), name='admin_doctor_services'),
    path('admin/doctors/<int:pk>/services/add/', DoctorAddServiceView.as_view(), name='admin_doctor_add_service'),
    path('admin/doctors/<int:pk>/services/<int:service_id>/edit/', DoctorEditServiceView.as_view(), name='admin_doctor_edit_service'),
    path('admin/doctors/<int:pk>/services/<int:service_id>/delete/', DoctorDeleteServiceView.as_view(), name='admin_doctor_delete_service'),
    path('admin/doctors/<int:pk>/schedule/', DoctorScheduleView.as_view(), name='admin_doctor_schedule'),
    path('admin/doctors/<int:pk>/schedule/add/', DoctorAddScheduleView.as_view(), name='admin_doctor_add_schedule'),
    path('admin/doctors/<int:pk>/schedule/<int:schedule_id>/edit/', DoctorEditScheduleView.as_view(), name='admin_doctor_edit_schedule'),
    path('admin/doctors/<int:pk>/schedule/<int:schedule_id>/delete/', DoctorDeleteScheduleView.as_view(), name='admin_doctor_delete_schedule'),
]
