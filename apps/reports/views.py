from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Report
from apps.users.models import User, UserProfile

class ReportListView(LoginRequiredMixin, ListView):
    """
    View to display a list of reports.
    """
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        
        # Filter reports based on user type
        if user.user_type == 'patient':
            # Patients can only see their own reports
            try:
                patient_profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                # Create a profile for the user if it doesn't exist
                patient_profile = UserProfile.objects.create(user=user)
            return Report.objects.filter(patient=patient_profile).order_by('-date')
        elif user.user_type == 'healthcare_provider':
            # Healthcare providers can see all reports
            return Report.objects.all().order_by('-date')
        elif user.user_type == 'researcher':
            # Researchers can see genomic reports
            return Report.objects.filter(type='genomic').order_by('-date')
        else:
            # Other user types can see reports based on their permissions
            return Report.objects.all().order_by('-date')


class ReportDetailView(LoginRequiredMixin, DetailView):
    """
    View to display report details.
    """
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    
    def get_object(self):
        report_id = self.kwargs.get('report_id')
        return get_object_or_404(Report, report_id=report_id)


class ReportCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new report.
    """
    model = Report
    template_name = 'reports/report_create.html'
    fields = ['patient', 'type', 'status', 'date', 'content']
    success_url = reverse_lazy('report_list')
    
    def form_valid(self, form):
        # Generate a unique report ID
        import uuid
        form.instance.report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"
        return super().form_valid(form)


def search_report(request):
    """
    Function to search for a report by ID.
    """
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        
        try:
            report = Report.objects.get(report_id=report_id)
            
            # Check if user has permission to view this report
            user = request.user
            if user.user_type == 'patient':
                try:
                    patient_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    # Create a profile for the user if it doesn't exist
                    patient_profile = UserProfile.objects.create(user=user)
                
                if report.patient != patient_profile:
                    return JsonResponse({'error': 'You do not have permission to view this report'})
            
            # Return report data
            report_data = {
                'report_id': report.report_id,
                'patient_name': f"{report.patient.user.first_name} {report.patient.user.last_name}",
                'type': report.get_type_display(),
                'status': report.get_status_display(),
                'date': report.date.strftime('%Y-%m-%d'),
                'content': report.content
            }
            
            return JsonResponse({'success': True, 'report': report_data})
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})


@login_required
def approve_report(request, report_id):
    """
    Function to approve a report.
    """
    # Only healthcare providers can approve reports
    if request.user.user_type != 'healthcare_provider':
        messages.error(request, 'You do not have permission to approve reports.')
        return redirect('report_list')
    
    report = get_object_or_404(Report, report_id=report_id)
    
    # Check if report is waiting for approval
    if report.status != 'waiting_approval':
        messages.error(request, 'This report is not waiting for approval.')
        return redirect('report_detail', report_id=report_id)
    
    # Update report status
    report.status = 'done'
    report.save()
    
    messages.success(request, f'Report {report_id} has been approved successfully.')
    return redirect('report_detail', report_id=report_id)
