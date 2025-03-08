from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.views.generic import TemplateView, CreateView, FormView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib import messages

from .models import User, UserProfile
from .forms import UserRegistrationForm, UserLoginForm

class UserTypeSelectionView(TemplateView):
    """
    View to display the user type selection page.
    """
    template_name = 'users/user_type_selection.html'


class UserRegistrationView(CreateView):
    """
    View to handle user registration.
    """
    model = User
    form_class = UserRegistrationForm
    template_name = 'users/registration.html'
    success_url = reverse_lazy('login')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user_type'] = self.kwargs.get('user_type')
        return kwargs
    
    def form_valid(self, form):
        # The form's save method now handles UserProfile creation
        user = form.save()
        messages.success(self.request, 'Registration successful. You can now log in.')
        return super().form_valid(form)


class CustomLoginView(LoginView):
    """
    Custom login view to handle user login and redirect to appropriate dashboard.
    """
    form_class = UserLoginForm
    template_name = 'users/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass user_type to context if it's in GET parameters
        if 'user_type' in self.request.GET:
            context['user_type'] = self.request.GET.get('user_type')
        return context
    
    def form_valid(self, form):
        """Set user_type from form data if it was passed in the request"""
        user = form.get_user()
        # If user_type is passed in the form and the user's type is not set, update it
        user_type = self.request.POST.get('user_type')
        if user_type and not user.user_type:
            user.user_type = user_type
            user.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        """
        Determine the appropriate dashboard URL based on user type.
        """
        user_type = self.request.user.user_type
        dashboard_urls = {
            'healthcare_provider': 'healthcare_provider_dashboard',
            'patient': 'patient_dashboard',
            'company': 'company_dashboard',
            'government': 'government_dashboard',
            'researcher': 'researcher_dashboard'
        }
        
        # Default to home if user_type is empty or not recognized
        if not user_type or user_type not in dashboard_urls:
            return reverse_lazy('home')
        
        # Special handling for healthcare providers based on their specific type
        if user_type == 'healthcare_provider':
            provider_type = self.request.user.healthcare_provider_type
            if provider_type == 'doctor':
                return reverse_lazy('doctor_dashboard')
            elif provider_type == 'clinic':
                return reverse_lazy('clinic_dashboard')
        
        return reverse_lazy(dashboard_urls[user_type])
