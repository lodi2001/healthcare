from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class HomeView(LoginRequiredMixin, TemplateView):
    """
    Home view that redirects to the appropriate dashboard based on user type.
    """
    template_name = 'core/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        # If user is authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            user_type = request.user.user_type
            if user_type == 'healthcare_provider':
                return redirect('healthcare_provider_dashboard')
            elif user_type == 'patient':
                return redirect('patient_dashboard')
            elif user_type == 'company':
                return redirect('company_dashboard')
            elif user_type == 'government':
                return redirect('government_dashboard')
            elif user_type == 'researcher':
                return redirect('researcher_dashboard')
        
        # If not authenticated or no matching user type, proceed with normal view
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
