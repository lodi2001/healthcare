from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, F, Sum, Prefetch
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.db import transaction

from apps.users.models import User, UserProfile
from .models import (
    ServiceCategory, Service, ProviderService, 
    Appointment, DoctorSchedule
)
from .forms import ProviderServiceForm, DoctorScheduleForm, DoctorForm


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin access"""
    def test_func(self):
        # Allow access for staff, superusers, admins, providers, and healthcare_providers
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or 
            self.request.user.is_superuser or
            self.request.user.user_type in ['admin', 'provider', 'healthcare_provider']
        )


class DoctorListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all doctors"""
    model = User
    template_name = 'services/admin/doctor_list.html'
    context_object_name = 'doctors'
    
    def get_queryset(self):
        queryset = User.objects.filter(
            user_type='healthcare_provider',
            healthcare_provider_type='doctor'
        )
        
        # Apply filters
        department = self.request.GET.get('department')
        status = self.request.GET.get('status', 'active')  # Default to active doctors
        
        # Filter by active status
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        # If status is 'all', don't filter by is_active
        
        if department:
            # Filter doctors who offer services in this department
            queryset = queryset.filter(
                offered_services__service__category_id=department
            ).distinct()
        
        return queryset.annotate(
            service_count=Count('offered_services', distinct=True)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all departments
        context['departments'] = ServiceCategory.objects.filter(is_active=True)
        
        # Pass the current status filter to the template
        context['current_status'] = self.request.GET.get('status', 'active')
        
        return context


class DoctorDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """View to show doctor details"""
    model = User
    template_name = 'services/admin/doctor_detail.html'
    context_object_name = 'doctor'
    
    def get_queryset(self):
        return User.objects.filter(user_type__in=['healthcare_provider', 'provider'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.get_object()
        
        # Get doctor services
        context['doctor_services'] = ProviderService.objects.filter(
            provider=doctor
        ).select_related('service', 'service__category')
        
        # Get doctor schedules
        context['doctor_schedules'] = DoctorSchedule.objects.filter(
            doctor=doctor,
            is_active=True
        )
        
        # Get upcoming appointments
        context['upcoming_appointments'] = Appointment.objects.filter(
            provider_service__provider=doctor,
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        ).select_related('patient', 'provider_service', 'provider_service__service')
        
        return context


class DoctorCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new doctor"""
    model = User
    form_class = DoctorForm
    template_name = 'services/admin/doctor_form.html'
    success_url = reverse_lazy('admin_doctor_list')
    
    def form_valid(self, form):
        # Set user type to healthcare_provider
        form.instance.user_type = 'healthcare_provider'
        form.instance.healthcare_provider_type = 'doctor'
        
        # Generate a username from email
        email = form.cleaned_data.get('email')
        username = email.split('@')[0]
        
        # Check if username exists, if so, add a number
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        form.instance.username = username
        
        # Set department if selected
        department = form.cleaned_data.get('department')
        if department:
            form.instance.department = department
        
        # Check if national_id is unique
        national_id = form.cleaned_data.get('national_id')
        if User.objects.filter(national_id=national_id).exists():
            form.add_error('national_id', _("This National ID is already in use by another user."))
            return self.form_invalid(form)
        
        # Set a temporary password - can be changed later
        form.instance.set_password('TemporaryPassword123')
        
        # Save the user first
        response = super().form_valid(form)
        
        # Now save the specialty and other fields to the user's profile
        user_profile, created = UserProfile.objects.get_or_create(user=self.object)
        
        # Store specialty and other doctor-specific fields in profile metadata
        specialty = form.cleaned_data.get('specialty')
        qualifications = form.cleaned_data.get('qualifications')
        years_of_experience = form.cleaned_data.get('years_of_experience')
        license_number = form.cleaned_data.get('license_number')
        languages = form.cleaned_data.get('languages')
        bio = form.cleaned_data.get('bio')
        
        # Create a JSON field to store doctor-specific data
        doctor_data = {
            'specialty': specialty,
            'qualifications': qualifications,
            'years_of_experience': years_of_experience,
            'license_number': license_number,
            'languages': languages,
            'bio': bio
        }
        
        # Store the data in the profile
        user_profile.metadata = doctor_data
        
        # Handle profile image
        profile_image = form.cleaned_data.get('profile_image')
        if profile_image:
            user_profile.profile_image = profile_image
            
        user_profile.save()
        
        messages.success(self.request, _(f"Doctor created successfully. Temporary password: TemporaryPassword123"))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Doctor')
        context['submit_text'] = _('Create Doctor')
        return context


class DoctorUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """View to update a doctor"""
    model = User
    form_class = DoctorForm
    template_name = 'services/admin/doctor_form.html'
    success_url = reverse_lazy('admin_doctor_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Get doctor-specific data from profile
        try:
            profile = self.object.profile
            if profile.metadata:
                # Pre-fill form fields with data from profile metadata
                if 'specialty' in profile.metadata:
                    form.fields['specialty'].initial = profile.metadata.get('specialty')
                if 'qualifications' in profile.metadata:
                    form.fields['qualifications'].initial = profile.metadata.get('qualifications')
                if 'years_of_experience' in profile.metadata:
                    form.fields['years_of_experience'].initial = profile.metadata.get('years_of_experience')
                if 'license_number' in profile.metadata:
                    form.fields['license_number'].initial = profile.metadata.get('license_number')
                if 'languages' in profile.metadata:
                    form.fields['languages'].initial = profile.metadata.get('languages')
                if 'bio' in profile.metadata:
                    form.fields['bio'].initial = profile.metadata.get('bio')
        except UserProfile.DoesNotExist:
            pass
            
        return form
    
    def form_valid(self, form):
        # Get the current national_id before saving
        current_national_id = self.object.national_id
        
        # Check if national_id is being changed
        new_national_id = form.cleaned_data.get('national_id')
        
        # If national_id is being changed and the new one already exists, raise validation error
        if new_national_id and new_national_id != current_national_id:
            if User.objects.filter(national_id=new_national_id).exclude(pk=self.object.pk).exists():
                form.add_error('national_id', _("This National ID is already in use by another user."))
                return self.form_invalid(form)
        
        # If national_id is empty, keep the current one
        if not new_national_id:
            form.instance.national_id = current_national_id
        
        response = super().form_valid(form)
        
        # Update doctor-specific fields in profile
        user_profile, created = UserProfile.objects.get_or_create(user=self.object)
        
        # Get doctor-specific data from form
        specialty = form.cleaned_data.get('specialty')
        qualifications = form.cleaned_data.get('qualifications')
        years_of_experience = form.cleaned_data.get('years_of_experience')
        license_number = form.cleaned_data.get('license_number')
        languages = form.cleaned_data.get('languages')
        bio = form.cleaned_data.get('bio')
        
        # Create or update metadata
        metadata = user_profile.metadata or {}
        metadata.update({
            'specialty': specialty,
            'qualifications': qualifications,
            'years_of_experience': years_of_experience,
            'license_number': license_number,
            'languages': languages,
            'bio': bio
        })
        
        # Save updated metadata
        user_profile.metadata = metadata
        
        # Handle profile image
        profile_image = form.cleaned_data.get('profile_image')
        if profile_image:
            user_profile.profile_image = profile_image
            
        user_profile.save()
        
        messages.success(self.request, _("Doctor updated successfully."))
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Doctor')
        context['submit_text'] = _('Update Doctor')
        context['action'] = 'Update'
        context['doctor'] = self.object
        return context


class DoctorDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to delete a doctor (soft deletion)"""
    
    def get(self, request, pk):
        try:
            # Get the doctor by ID
            doctor = get_object_or_404(User, pk=pk)
            
            # Check if the doctor is actually a doctor
            if doctor.user_type != 'healthcare_provider' or doctor.healthcare_provider_type != 'doctor':
                messages.error(request, _("The selected user is not a doctor."))
                return redirect('admin_doctor_list')
            
            # Implement soft deletion
            doctor.is_active = False
            
            # Store deletion info in metadata
            if not hasattr(doctor, 'profile') or not doctor.profile:
                # Create profile if it doesn't exist
                UserProfile.objects.create(user=doctor, metadata={
                    'deleted': True,
                    'deleted_at': timezone.now().isoformat(),
                    'deleted_by': request.user.id
                })
            else:
                # Update existing profile metadata
                metadata = doctor.profile.metadata or {}
                metadata.update({
                    'deleted': True,
                    'deleted_at': timezone.now().isoformat(),
                    'deleted_by': request.user.id
                })
                doctor.profile.metadata = metadata
                doctor.profile.save()
            
            # Save the doctor with updated status
            doctor.save()
            
            # Log the action
            messages.success(request, _("Doctor deactivated successfully."))
            
        except User.DoesNotExist:
            messages.error(request, _("Doctor not found."))
        except Exception as e:
            messages.error(request, _("Error deactivating doctor: {}").format(str(e)))
        
        return redirect('admin_doctor_list')


class DoctorReactivateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to reactivate a doctor (reverse soft deletion)"""
    
    def get(self, request, pk):
        try:
            # Get the doctor by ID
            doctor = get_object_or_404(User, pk=pk)
            
            # Check if the doctor is actually a doctor
            if doctor.user_type != 'healthcare_provider' or doctor.healthcare_provider_type != 'doctor':
                messages.error(request, _("The selected user is not a doctor."))
                return redirect('admin_doctor_list')
            
            # Check if doctor is already active
            if doctor.is_active:
                messages.info(request, _("This doctor is already active."))
                return redirect('admin_doctor_list')
            
            # Reactivate the doctor
            doctor.is_active = True
            
            # Update metadata to reflect reactivation
            if hasattr(doctor, 'profile') and doctor.profile:
                metadata = doctor.profile.metadata or {}
                metadata.update({
                    'deleted': False,
                    'reactivated_at': timezone.now().isoformat(),
                    'reactivated_by': request.user.id
                })
                doctor.profile.metadata = metadata
                doctor.profile.save()
            
            # Save the doctor with updated status
            doctor.save()
            
            # Log the action
            messages.success(request, _("Doctor reactivated successfully."))
            
        except User.DoesNotExist:
            messages.error(request, _("Doctor not found."))
        except Exception as e:
            messages.error(request, _("Error reactivating doctor: {}").format(str(e)))
        
        return redirect('admin_doctor_list')


class DoctorServicesView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to manage doctor services"""
    template_name = 'services/admin/doctor_services.html'
    
    def get(self, request, pk):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        # Get doctor services
        doctor_services = ProviderService.objects.filter(
            provider=doctor
        ).select_related('service', 'service__category')
        
        # Get active services count
        active_services = doctor_services.filter(is_available=True).count()
        
        # Get unique departments
        departments = set(service.service.category for service in doctor_services)
        
        # Get doctor schedules
        schedule_days = DoctorSchedule.objects.filter(
            doctor=doctor,
            is_active=True
        )
        
        # Get all service categories with their services
        categories = ServiceCategory.objects.filter(
            is_active=True
        ).prefetch_related('services')
        
        return render(request, self.template_name, {
            'doctor': doctor,
            'doctor_services': doctor_services,
            'active_services': active_services,
            'departments': departments,
            'schedule_days': schedule_days,
            'categories': categories,
        })


class DoctorAddServiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to add a service to a doctor"""
    
    def post(self, request, pk):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        service_id = request.POST.get('service')
        price = request.POST.get('custom_price')
        duration = request.POST.get('custom_duration')
        is_available = request.POST.get('is_available') == 'on'
        
        if not service_id or not price or not duration:
            messages.error(request, _("Please fill in all required fields."))
            return redirect('admin_doctor_services', pk=doctor.id)
        
        try:
            service = Service.objects.get(id=service_id)
            
            # Check if the doctor already offers this service
            if ProviderService.objects.filter(provider=doctor, service=service).exists():
                messages.error(request, _("This doctor already offers this service."))
                return redirect('admin_doctor_services', pk=doctor.id)
            
            # Create the provider service
            provider_service = ProviderService.objects.create(
                provider=doctor,
                service=service,
                custom_price=price,
                custom_duration=duration,
                is_available=is_available
            )
            
            messages.success(request, _("Service added successfully."))
            
        except Service.DoesNotExist:
            messages.error(request, _("The selected service does not exist."))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_services', pk=doctor.id)


class DoctorEditServiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to edit a doctor's service"""
    
    def post(self, request, pk, service_id):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        provider_service = get_object_or_404(ProviderService, id=service_id, provider=doctor)
        
        service_id = request.POST.get('service')
        price = request.POST.get('custom_price')
        duration = request.POST.get('custom_duration')
        is_available = request.POST.get('is_available') == 'on'
        
        if not service_id or not price or not duration:
            messages.error(request, _("Please fill in all required fields."))
            return redirect('admin_doctor_services', pk=doctor.id)
        
        try:
            service = Service.objects.get(id=service_id)
            
            # Check if the doctor already offers this service (if changing service)
            if service != provider_service.service and ProviderService.objects.filter(
                provider=doctor, service=service
            ).exists():
                messages.error(request, _("This doctor already offers this service."))
                return redirect('admin_doctor_services', pk=doctor.id)
            
            # Update the provider service
            provider_service.service = service
            provider_service.custom_price = price
            provider_service.custom_duration = duration
            provider_service.is_available = is_available
            provider_service.save()
            
            messages.success(request, _("Service updated successfully."))
            
        except Service.DoesNotExist:
            messages.error(request, _("The selected service does not exist."))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_services', pk=doctor.id)


class DoctorDeleteServiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to delete a doctor's service"""
    
    def post(self, request, pk, service_id):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        provider_service = get_object_or_404(ProviderService, id=service_id, provider=doctor)
        
        # Check if there are any appointments for this service
        appointments = Appointment.objects.filter(
            provider_service=provider_service,
            appointment_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        )
        
        if appointments.exists():
            messages.error(
                request, 
                _("Cannot delete this service as there are upcoming appointments scheduled for it.")
            )
            return redirect('admin_doctor_services', pk=doctor.id)
        
        try:
            provider_service.delete()
            messages.success(request, _("Service deleted successfully."))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_services', pk=doctor.id)


class DoctorScheduleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to manage doctor schedules"""
    template_name = 'services/admin/doctor_schedule.html'
    
    def get(self, request, pk):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        # Get doctor services
        doctor_services = ProviderService.objects.filter(
            provider=doctor
        ).select_related('service', 'service__category')
        
        # Get doctor schedules grouped by day
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            is_active=True
        ).order_by('day_of_week', 'start_time')
        
        # Group schedules by day
        schedule_days = {}
        for day, _ in DoctorSchedule.DAYS_OF_WEEK:
            schedule_days[day] = []
        
        for schedule in schedules:
            schedule_days[schedule.day_of_week].append(schedule)
        
        # Calculate total hours
        total_hours = sum(schedule.duration_minutes for schedule in schedules) / 60
        
        return render(request, self.template_name, {
            'doctor': doctor,
            'doctor_services': doctor_services,
            'schedule_days': schedule_days,
            'total_hours': round(total_hours, 1)
        })


class DoctorAddScheduleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to add a schedule for a doctor"""
    
    def post(self, request, pk):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if not day_of_week or not start_time or not end_time:
            messages.error(request, _("Please fill in all required fields."))
            return redirect('admin_doctor_schedule', pk=doctor.id)
        
        try:
            # Create the doctor schedule
            schedule = DoctorSchedule(
                doctor=doctor,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time
            )
            
            # This will call clean() which validates time and checks for overlaps
            schedule.save()
            
            messages.success(request, _("Schedule added successfully."))
            
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_schedule', pk=doctor.id)


class DoctorEditScheduleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to edit a doctor's schedule"""
    
    def post(self, request, pk, schedule_id):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        schedule = get_object_or_404(DoctorSchedule, id=schedule_id, doctor=doctor)
        
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if not day_of_week or not start_time or not end_time:
            messages.error(request, _("Please fill in all required fields."))
            return redirect('admin_doctor_schedule', pk=doctor.id)
        
        try:
            # Update the schedule
            schedule.day_of_week = day_of_week
            schedule.start_time = start_time
            schedule.end_time = end_time
            
            # This will call clean() which validates time and checks for overlaps
            schedule.save()
            
            messages.success(request, _("Schedule updated successfully."))
            
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_schedule', pk=doctor.id)


class DoctorDeleteScheduleView(LoginRequiredMixin, AdminRequiredMixin, View):
    """View to delete a doctor's schedule"""
    
    def post(self, request, pk, schedule_id):
        # Get the doctor by ID
        doctor = get_object_or_404(User, pk=pk)
        
        # Check if the doctor is a healthcare provider or a doctor within a provider
        if doctor.user_type not in ['healthcare_provider', 'provider']:
            # If the user is not a healthcare provider, check if they have a healthcare_provider_type
            if not doctor.healthcare_provider_type:
                messages.error(request, _("The selected user is not a healthcare provider."))
                return redirect('admin_doctor_list')
        
        schedule = get_object_or_404(DoctorSchedule, id=schedule_id, doctor=doctor)
        
        try:
            # Instead of deleting, mark as inactive
            schedule.is_active = False
            schedule.save()
            
            messages.success(request, _("Schedule deleted successfully."))
            
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin_doctor_schedule', pk=doctor.id)
