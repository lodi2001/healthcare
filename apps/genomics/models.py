from django.db import models
from apps.users.models import UserProfile

class GenomicData(models.Model):
    """
    Genomic Data model to store patient genomic information.
    """
    patient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='genomic_data')
    variants = models.TextField()
    sequenced_samples = models.IntegerField(default=0)
    risk_alleles = models.TextField()
    date_analyzed = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Genomic Data for {self.patient.user.username}"
    
    class Meta:
        indexes = [
            models.Index(fields=['patient']),
        ]
        verbose_name_plural = "Genomic Data"
