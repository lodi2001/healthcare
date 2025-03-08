from django.db import models
from apps.users.models import UserProfile

class Report(models.Model):
    """
    Report model to store various types of reports.
    """
    REPORT_TYPE_CHOICES = (
        ('genomic', 'Genomic'),
        ('clinical', 'Clinical'),
        ('patient', 'Patient'),
    )
    
    STATUS_CHOICES = (
        ('done', 'Done'),
        ('waiting_approval', 'Waiting Approval'),
    )
    
    report_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reports')
    type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date = models.DateField()
    content = models.TextField()
    
    def __str__(self):
        return f"Report {self.report_id} - {self.type} - {self.status}"
    
    class Meta:
        indexes = [
            models.Index(fields=['report_id']),
            models.Index(fields=['patient']),
            models.Index(fields=['type']),
            models.Index(fields=['status']),
        ]
