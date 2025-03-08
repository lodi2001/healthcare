from django.db import models
from apps.users.models import UserProfile

class EHR(models.Model):
    """
    Electronic Health Record model to store patient health information.
    """
    patient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='ehr_records')
    visits = models.IntegerField(default=0)
    medications = models.TextField(blank=True)
    lab_results = models.TextField(blank=True)
    vaccinations = models.TextField(blank=True)
    report_id = models.CharField(max_length=20, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EHR for {self.patient.user.username} - {self.report_id}"

    class Meta:
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['report_id']),
        ]


class HealthPlan(models.Model):
    """
    Health Plan model to store patient health plans and alerts.
    """
    SEVERITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    ALERT_TYPE_CHOICES = (
        ('blood_glucose', 'Blood Glucose'),
        ('pulse_rate', 'Pulse Rate'),
        ('blood_pressure', 'Blood Pressure'),
        ('cholesterol', 'Cholesterol'),
        ('other', 'Other'),
    )
    
    patient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='health_plans')
    plan_details = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Health Plan for {self.patient.user.username} - {self.alert_type}"
