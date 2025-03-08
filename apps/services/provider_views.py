from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    ServiceCategory, 
    Service, 
    ProviderService, 
    Appointment, 
    AvailabilitySchedule,
    ServiceReview
)
from .forms import ProviderServiceForm, AvailabilityScheduleForm, MedicalNotesForm, AppointmentForm
from apps.users.models import User, UserProfile


class ProviderRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only healthcare providers can access the view
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'healthcare_provider'


class ProviderServiceListView(LoginRequiredMixin, ProviderRequiredMixin, ListView):
    """
    View to list all services offered by the healthcare provider
    """
    model = ProviderService
    template_name = 'services/provider/service_list.html'
    context_object_name = 'provider_services'
    
    def get_queryset(self):
        return ProviderService.objects.filter(provider=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.filter(is_active=True)
        return context


class ProviderServiceCreateView(LoginRequiredMixin, ProviderRequiredMixin, CreateView):
    """
    View to add a new service to the healthcare provider's offerings
    """
    model = ProviderService
    form_class = ProviderServiceForm
    template_name = 'services/provider/service_form.html'
    success_url = reverse_lazy('provider_services')
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        
        # Check if the provider already offers this service
        service = form.cleaned_data.get('service')
        if ProviderService.objects.filter(provider=self.request.user, service=service).exists():
            messages.error(self.request, _("You already offer this service. You can edit the existing service instead."))
            return self.form_invalid(form)
        
        messages.success(self.request, _("Service added successfully"))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Add New Service")
        context['categories'] = ServiceCategory.objects.filter(is_active=True)
        return context


class ProviderServiceUpdateView(LoginRequiredMixin, ProviderRequiredMixin, UpdateView):
    """
    View to update an existing service offered by the healthcare provider
    """
    model = ProviderService
    form_class = ProviderServiceForm
    template_name = 'services/provider/service_form.html'
    success_url = reverse_lazy('provider_services')
    
    def get_queryset(self):
        return ProviderService.objects.filter(provider=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _("Service updated successfully"))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Update Service")
        return context


class ProviderServiceDeleteView(LoginRequiredMixin, ProviderRequiredMixin, DeleteView):
    """
    View to delete a service from the healthcare provider's offerings
    """
    model = ProviderService
    template_name = 'services/provider/service_confirm_delete.html'
    success_url = reverse_lazy('provider_services')
    
    def get_queryset(self):
        return ProviderService.objects.filter(provider=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Service removed successfully"))
        return super().delete(request, *args, **kwargs)


class ProviderAppointmentListView(LoginRequiredMixin, ProviderRequiredMixin, ListView):
    """
    View to list all appointments for the healthcare provider
    """
    model = Appointment
    template_name = 'services/provider/appointment_list.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        status = self.request.GET.get('status', None)
        date_from = self.request.GET.get('date_from', None)
        date_to = self.request.GET.get('date_to', None)
        
        queryset = Appointment.objects.filter(provider_service__provider=self.request.user)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Appointment.STATUS_CHOICES
        
        # Count appointments by status
        status_counts = {}
        for status, label in Appointment.STATUS_CHOICES:
            count = self.get_queryset().filter(status=status).count()
            status_counts[status] = count
        
        context['status_counts'] = status_counts
        return context


class ProviderAppointmentDetailView(LoginRequiredMixin, ProviderRequiredMixin, DetailView):
    """
    View to show details of a specific appointment
    """
    model = Appointment
    template_name = 'services/provider/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.filter(provider_service__provider=self.request.user)


class ProviderAppointmentUpdateView(LoginRequiredMixin, ProviderRequiredMixin, UpdateView):
    """
    View to update the status of an appointment
    """
    model = Appointment
    fields = ['status', 'notes']
    template_name = 'services/provider/appointment_update.html'
    
    def get_queryset(self):
        return Appointment.objects.filter(provider_service__provider=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('provider_appointment_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, _("Appointment updated successfully"))
        return super().form_valid(form)


class ProviderAvailabilityListView(LoginRequiredMixin, ProviderRequiredMixin, ListView):
    """
    View to list all availability schedules for the healthcare provider
    """
    model = AvailabilitySchedule
    template_name = 'services/provider/availability_list.html'
    context_object_name = 'schedules'
    
    def get_queryset(self):
        return AvailabilitySchedule.objects.filter(provider=self.request.user).order_by('day_of_week', 'start_time')


class ProviderAvailabilityCreateView(LoginRequiredMixin, ProviderRequiredMixin, CreateView):
    """
    View to add a new availability schedule
    """
    model = AvailabilitySchedule
    form_class = AvailabilityScheduleForm
    template_name = 'services/provider/availability_form.html'
    success_url = reverse_lazy('provider_availability')
    
    def form_valid(self, form):
        form.instance.provider = self.request.user
        
        # Check if an availability schedule with the same attributes already exists
        existing_schedule = AvailabilitySchedule.objects.filter(
            provider=self.request.user,
            day_of_week=form.instance.day_of_week,
            start_time=form.instance.start_time,
            end_time=form.instance.end_time
        ).first()
        
        if existing_schedule:
            # If it exists but is not active, just reactivate it
            if not existing_schedule.is_active:
                existing_schedule.is_active = True
                existing_schedule.save()
                messages.success(self.request, _("Availability schedule reactivated successfully"))
                return HttpResponseRedirect(self.success_url)
            else:
                # If it exists and is already active, show an error
                messages.error(
                    self.request, 
                    _("An availability schedule for this day and time range already exists")
                )
                return self.form_invalid(form)
        
        messages.success(self.request, _("Availability schedule added successfully"))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Add Availability Schedule")
        return context


class ProviderAvailabilityUpdateView(LoginRequiredMixin, ProviderRequiredMixin, UpdateView):
    """
    View to update an existing availability schedule
    """
    model = AvailabilitySchedule
    form_class = AvailabilityScheduleForm
    template_name = 'services/provider/availability_form.html'
    success_url = reverse_lazy('provider_availability')
    
    def get_queryset(self):
        return AvailabilitySchedule.objects.filter(provider=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _("Availability schedule updated successfully"))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Update Availability Schedule")
        return context


class ProviderAvailabilityDeleteView(LoginRequiredMixin, ProviderRequiredMixin, DeleteView):
    """
    View to delete an availability schedule
    """
    model = AvailabilitySchedule
    template_name = 'services/provider/availability_confirm_delete.html'
    success_url = reverse_lazy('provider_availability')
    
    def get_queryset(self):
        return AvailabilitySchedule.objects.filter(provider=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Availability schedule removed successfully"))
        return super().delete(request, *args, **kwargs)


class ProviderDashboardView(LoginRequiredMixin, ProviderRequiredMixin, View):
    """
    View for the healthcare provider dashboard
    """
    def get(self, request, *args, **kwargs):
        # Get upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            provider_service__provider=request.user,
            status__in=['scheduled', 'confirmed'],
            appointment_date__gte=timezone.now().date()
        ).order_by('appointment_date', 'start_time')[:5]
        
        # Get service statistics - optimize by using annotations and aggregations
        services = ProviderService.objects.filter(provider=request.user)
        
        # Get all appointment counts in a single query using annotations
        from django.db.models import Count, Q, F
        
        services_with_stats = services.annotate(
            appointments_count=Count('appointments'),
            completed_count=Count('appointments', filter=Q(appointments__status='completed')),
        )
        
        # Get average ratings in a single query
        from django.db.models.functions import Coalesce
        
        service_ids = services.values_list('id', flat=True)
        avg_ratings = ServiceReview.objects.filter(
            appointment__provider_service_id__in=service_ids
        ).values('appointment__provider_service').annotate(
            avg_rating=Coalesce(Avg('rating'), 0.0)
        ).values_list('appointment__provider_service', 'avg_rating')
        
        # Convert to dictionary for easy lookup
        ratings_dict = dict(avg_ratings)
        
        service_stats = []
        for service in services_with_stats:
            service_stats.append({
                'service': service,
                'appointments_count': service.appointments_count,
                'completed_count': service.completed_count,
                'avg_rating': ratings_dict.get(service.id, 0)
            })
        
        # Get appointment counts by status in a single query
        status_counts = {}
        appointment_counts = Appointment.objects.filter(
            provider_service__provider=request.user
        ).values('status').annotate(
            count=Count('id')
        )
        
        # Initialize all status counts to 0
        for status, label in Appointment.STATUS_CHOICES:
            status_counts[status] = 0
            
        # Update with actual counts
        for item in appointment_counts:
            status_counts[item['status']] = item['count']
        
        # Get total services and appointments in a more efficient way
        total_services = services.count()
        total_appointments = sum(status_counts.values())
        
        # Get completed and upcoming appointments counts
        completed_appointments = status_counts.get('completed', 0)
        upcoming_appointments_count = status_counts.get('scheduled', 0) + status_counts.get('confirmed', 0)
        
        context = {
            'upcoming_appointments': upcoming_appointments,
            'service_stats': service_stats,
            'status_counts': status_counts,
            'total_services': total_services,
            'total_appointments': total_appointments,
            'completed_appointments': completed_appointments,
            'upcoming_appointments_count': upcoming_appointments_count,
            'services_count': total_services
        }
        
        return render(request, 'dashboard/doctor_dashboard.html', context)


class ProviderReviewListView(LoginRequiredMixin, ProviderRequiredMixin, ListView):
    """
    View to list all reviews for the healthcare provider's services
    """
    model = ServiceReview
    template_name = 'services/provider/review_list.html'
    context_object_name = 'reviews'
    
    def get_queryset(self):
        return ServiceReview.objects.filter(appointment__provider_service__provider=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate average rating
        avg_rating = self.get_queryset().aggregate(Avg('rating'))['rating__avg'] or 0
        context['avg_rating'] = avg_rating
        
        # Count reviews by rating
        rating_counts = {}
        for i in range(1, 6):
            count = self.get_queryset().filter(rating=i).count()
            rating_counts[i] = count
        
        context['rating_counts'] = rating_counts
        context['total_reviews'] = self.get_queryset().count()
        
        return context


class ProviderServiceStatisticsView(LoginRequiredMixin, ProviderRequiredMixin, View):
    """
    View to display statistics about the healthcare provider's services
    """
    def get(self, request, *args, **kwargs):
        # Get date range for filtering
        date_from = request.GET.get('date_from', None)
        date_to = request.GET.get('date_to', None)
        
        if not date_from:
            # Default to last 30 days
            date_from = (timezone.now() - timedelta(days=30)).date()
        
        if not date_to:
            date_to = timezone.now().date()
            
        # Get provider services
        provider_services = ProviderService.objects.filter(provider=request.user)
        
        # Get appointments for the provider in the date range
        appointments = Appointment.objects.filter(
            provider_service__provider=request.user,
            appointment_date__gte=date_from,
            appointment_date__lte=date_to
        )
        
        # Calculate statistics for the new template
        analyzed_reports = 40  # Example data
        number_of_requests = 35  # Example data
        total_reports = 15  # Example data
        
        # Get recent reports (using appointments as example data)
        recent_reports = appointments.order_by('-created_at')[:4]
        
        # Convert to the format needed for the template
        report_lookups = []
        for i, report in enumerate(recent_reports):
            status = "Done" if i == 0 else "Waiting Approval"
            report_type = ["Genomic", "Clinical", "Patient", "Genomic"][i % 4]
            report_date = report.appointment_date.strftime('%d/%m/%Y')
            
            report_lookups.append({
                'id': f"3455{6000 + i}",
                'date': report_date,
                'type': report_type,
                'status': status
            })
            
        # If we don't have enough reports, add some dummy data
        while len(report_lookups) < 4:
            i = len(report_lookups)
            status = "Done" if i == 0 else "Waiting Approval"
            report_type = ["Genomic", "Clinical", "Patient", "Genomic"][i % 4]
            
            report_lookups.append({
                'id': f"3455{6000 + i}",
                'date': f"{28-i*7}/11/2024",
                'type': report_type,
                'status': status
            })
        
        context = {
            'analyzed_reports': analyzed_reports,
            'number_of_requests': number_of_requests,
            'total_reports': total_reports,
            'report_lookups': report_lookups,
            'date_from': date_from,
            'date_to': date_to
        }
        
        return render(request, 'services/provider/service_statistics.html', context)


class ProviderPatientSearchView(LoginRequiredMixin, ProviderRequiredMixin, View):
    """
    View to search for patients
    """
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        patients = []
        
        if query:
            # Search for patients by name, email, or national ID
            patients = User.objects.filter(
                user_type='patient'
            ).filter(
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query) | 
                Q(email__icontains=query) | 
                Q(national_id__icontains=query)
            )[:20]  # Limit to 20 results
            
        context = {
            'query': query,
            'patients': patients
        }
        
        return render(request, 'services/provider/patient_search.html', context)


class ProviderPatientDetailView(LoginRequiredMixin, ProviderRequiredMixin, DetailView):
    """
    View to show patient details and appointment history
    """
    model = User
    template_name = 'services/provider/patient_detail.html'
    context_object_name = 'patient'
    
    def get_queryset(self):
        return User.objects.filter(user_type='patient')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        
        try:
            # Get appointments between the patient and the provider
            appointments = Appointment.objects.filter(
                patient=patient,
                provider_service__provider=self.request.user
            ).order_by('-appointment_date', '-start_time')
            
            context['appointments'] = appointments
            
            # Get the latest appointment
            latest_appointment = appointments.first()
            context['latest_appointment'] = latest_appointment
        except Exception as e:
            # Handle the case where the Appointment table doesn't exist yet
            context['appointments'] = []
            context['latest_appointment'] = None
            context['appointment_error'] = str(e)
        
        return context


class MedicalNotesUpdateView(LoginRequiredMixin, ProviderRequiredMixin, UpdateView):
    """
    View to update medical notes for an appointment
    """
    model = Appointment
    form_class = MedicalNotesForm
    template_name = 'services/provider/medical_notes_form.html'
    
    def get_queryset(self):
        # Only allow providers to update their own appointments
        provider_services = ProviderService.objects.filter(provider=self.request.user)
        return Appointment.objects.filter(provider_service__in=provider_services)
    
    def get_success_url(self):
        return reverse_lazy('provider_appointment_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, _('Medical notes updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appointment'] = self.object
        return context


class ProviderPatientRegisterView(LoginRequiredMixin, ProviderRequiredMixin, CreateView):
    """
    View for healthcare providers to register new patients
    """
    from apps.users.forms import PatientRegistrationForm
    form_class = PatientRegistrationForm
    template_name = 'services/provider/patient_register.html'
    success_url = reverse_lazy('provider_patient_search')
    
    def form_valid(self, form):
        # Don't call form.save() directly to avoid UserProfile creation issues
        user = form.save(commit=False)
        
        # Set user type to patient
        user.user_type = 'patient'
        
        # Generate username based on national ID
        user.username = f"patient_{user.national_id}"
        
        # Generate a random password
        import uuid
        random_password = uuid.uuid4().hex[:8]
        user.set_password(random_password)
        
        # Save the user
        user.save()
        
        # Check if UserProfile already exists
        from apps.users.models import UserProfile
        try:
            UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            # Only create if it doesn't exist
            UserProfile.objects.create(user=user)
        
        # Store the generated password for display
        form.generated_password = random_password
        
        # Display success message with patient details
        messages.success(
            self.request, 
            _(f'Patient {user.get_full_name()} registered successfully with National ID: {user.national_id}. '
              f'Temporary password: {random_password}')
        )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Register New Patient')
        return context


class ProviderScheduleAppointmentView(LoginRequiredMixin, ProviderRequiredMixin, CreateView):
    """
    View for healthcare providers to schedule appointments for patients
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'services/provider/schedule_appointment.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Get the patient if patient_id is provided, otherwise set to None
        patient_id = self.kwargs.get('patient_id')
        self.patient = None
        if patient_id:
            self.patient = get_object_or_404(User, pk=patient_id, user_type='patient')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['provider'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        appointment = form.save(commit=False)
        
        # Debug information
        print("Form data:", self.request.POST)
        print("Provider service ID:", self.request.POST.get('provider_service'))
        print("Doctor ID:", self.request.POST.get('doctor'))
        print("Department ID:", self.request.POST.get('department'))
        
        # If we're creating an appointment without a pre-selected patient,
        # get the patient from the form
        if self.patient:
            appointment.patient = self.patient
        else:
            patient_id = self.request.POST.get('patient')
            if patient_id:
                try:
                    appointment.patient = User.objects.get(id=patient_id, user_type='patient')
                except User.DoesNotExist:
                    messages.error(self.request, _("The selected patient does not exist."))
                    return self.form_invalid(form)
            else:
                messages.error(self.request, _("Please select a patient for the appointment."))
                return self.form_invalid(form)
        
        # Get the provider service based on selected doctor and service
        provider_service_id = self.request.POST.get('provider_service')
        
        # If provider_service_id is provided directly, use it
        if provider_service_id:
            try:
                provider_service = ProviderService.objects.filter(id=provider_service_id).select_related('service').first()
                if not provider_service:
                    messages.error(self.request, _("The selected service is not available."))
                    return self.form_invalid(form)
                
                appointment.provider_service = provider_service
                
                # Calculate end time based on service duration
                duration = provider_service.custom_duration or provider_service.service.duration_minutes or 30
                from datetime import datetime, timedelta
                start_datetime = datetime.combine(appointment.appointment_date, appointment.start_time)
                end_datetime = start_datetime + timedelta(minutes=duration)
                appointment.end_time = end_datetime.time()
                
                print(f"Setting appointment end time to {appointment.end_time} based on duration {duration}")
                
                # Double-check for overlapping appointments before saving
                from django.db.models import Q
                overlapping = Appointment.objects.filter(
                    provider_service__provider=provider_service.provider,
                    appointment_date=appointment.appointment_date,
                    status__in=['scheduled', 'confirmed'],
                ).filter(
                    (Q(start_time__lt=appointment.end_time) & Q(end_time__gt=appointment.start_time))
                )
                
                # Exclude the current appointment if we're editing an existing one
                if appointment.pk:
                    overlapping = overlapping.exclude(pk=appointment.pk)
                
                if overlapping.exists():
                    overlapping_appts = list(overlapping)
                    if len(overlapping_appts) == 1:
                        appt = overlapping_appts[0]
                        patient_name = appt.patient.get_full_name()
                        error_msg = _(f"This time slot overlaps with an existing appointment for {patient_name} from {appt.start_time.strftime('%H:%M')} to {appt.end_time.strftime('%H:%M')}. Please select a different time.")
                    else:
                        error_msg = _(f"This time slot overlaps with {len(overlapping_appts)} existing appointments. Please select a different time.")
                    
                    messages.error(self.request, error_msg)
                    return self.form_invalid(form)
                
            except Exception as e:
                messages.error(self.request, _(f"Error scheduling appointment: {str(e)}"))
                return self.form_invalid(form)
        else:
            messages.error(self.request, _("Please select a service."))
            return self.form_invalid(form)
        
        appointment.status = 'confirmed'  # Automatically confirm appointments created by providers
        appointment.save()
        
        messages.success(
            self.request,
            _(f'Appointment scheduled successfully for {appointment.patient.get_full_name()} on '
              f'{appointment.appointment_date} at {appointment.start_time}')
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        if self.patient:
            return reverse_lazy('provider_patient_detail', kwargs={'pk': self.patient.pk})
        else:
            return reverse_lazy('provider_appointments')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patient'] = self.patient
        
        # Add provider services to the context
        from apps.services.models import ProviderService, ServiceCategory
        from apps.users.models import User
        
        # Get all healthcare providers
        context['doctors'] = User.objects.filter(
            user_type='healthcare_provider',
            is_active=True
        ).order_by('last_name', 'first_name')
        
        # Get all service categories (departments)
        context['departments'] = ServiceCategory.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Get provider services with related data
        context['provider_services'] = ProviderService.objects.filter(
            is_available=True
        ).select_related(
            'provider', 
            'service', 
            'service__category'
        )
        
        # If no patient is pre-selected, add a list of patients to the context
        if not self.patient:
            context['patients'] = User.objects.filter(user_type='patient')
        
        return context


class GetDoctorsByDepartmentView(LoginRequiredMixin, ProviderRequiredMixin, View):
    """
    AJAX view to get doctors filtered by department
    """
    def get(self, request, *args, **kwargs):
        department_id = request.GET.get('department_id')
        if not department_id:
            return JsonResponse({'error': 'Department ID is required'}, status=400)
        
        try:
            # Find all provider services in this department
            provider_services = ProviderService.objects.filter(
                service__category_id=department_id,
                is_available=True
            ).values_list('provider_id', flat=True).distinct()
            
            # Get the doctors who offer these services
            doctors = User.objects.filter(
                id__in=provider_services,
                user_type='healthcare_provider',
                is_active=True
            ).values('id', 'first_name', 'last_name')
            
            # Get specialty for each doctor from their profile
            doctor_list = []
            for doctor in doctors:
                profile = UserProfile.objects.filter(user_id=doctor['id']).first()
                specialty = None
                if profile and profile.metadata:
                    specialty = profile.metadata.get('specialty', 'General')
                
                doctor_list.append({
                    'id': doctor['id'],
                    'name': f"{doctor['first_name']} {doctor['last_name']}",
                    'specialty': specialty or 'General'
                })
            
            return JsonResponse({'doctors': doctor_list})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class GetServicesByDoctorAndDepartmentView(LoginRequiredMixin, ProviderRequiredMixin, View):
    """
    AJAX view to get services filtered by doctor and department
    """
    def get(self, request, *args, **kwargs):
        doctor_id = request.GET.get('doctor_id')
        department_id = request.GET.get('department_id')
        
        if not doctor_id or not department_id:
            return JsonResponse({'error': 'Doctor ID and Department ID are required'}, status=400)
        
        try:
            # Find all provider services offered by this doctor in this department
            provider_services = ProviderService.objects.filter(
                provider_id=doctor_id,
                service__category_id=department_id,
                is_available=True
            ).select_related('service', 'service__category')
            
            services = [{
                'id': ps.id,
                'name': ps.service.name,
                'category_id': ps.service.category.id,
                'category_name': ps.service.category.name,
                'doctor_id': ps.provider_id,
                'price': ps.price_display,
                'duration': ps.duration_display
            } for ps in provider_services]
            
            return JsonResponse({'services': services})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
