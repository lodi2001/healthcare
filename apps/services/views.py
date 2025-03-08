from django.shortcuts import render
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
import pandas as pd
import json

from apps.users.models import User, UserProfile
from apps.ehr.models import EHR
from apps.genomics.models import GenomicData

class ClinicalServicesView(LoginRequiredMixin, View):
    """
    View to handle clinical services.
    """
    def get(self, request, *args, **kwargs):
        return render(request, 'services/clinical_services.html')
    
    def post(self, request, *args, **kwargs):
        service_type = request.POST.get('service_type')
        patient_id = request.POST.get('patient_id')
        
        try:
            patient = User.objects.get(national_id=patient_id, user_type='patient')
            try:
                patient_profile = UserProfile.objects.get(user=patient)
            except UserProfile.DoesNotExist:
                # Create a profile for the user if it doesn't exist
                patient_profile = UserProfile.objects.create(user=patient)
            
            if service_type == 'patient_journey':
                result = self.search_patient_journey(patient_profile)
            elif service_type == 'procedures':
                result = self.check_procedures(patient_profile)
            elif service_type == 'therapy_plan':
                result = self.recommend_therapy_plan(patient_profile)
            elif service_type == 'medication_compliance':
                result = self.check_medication_compliance(patient_profile)
            else:
                result = {'error': 'Invalid service type'}
                
            return JsonResponse(result)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    def search_patient_journey(self, patient_profile):
        """
        Search patient journey and return results.
        """
        # Mock data for patient journey
        journey = {
            'visits': [
                {'date': '2024-01-15', 'doctor': 'Dr. Smith', 'reason': 'Annual checkup'},
                {'date': '2024-02-20', 'doctor': 'Dr. Johnson', 'reason': 'Flu symptoms'},
                {'date': '2024-03-10', 'doctor': 'Dr. Williams', 'reason': 'Follow-up'}
            ],
            'treatments': [
                {'date': '2024-01-15', 'treatment': 'Vitamin D prescription'},
                {'date': '2024-02-20', 'treatment': 'Antiviral medication'}
            ]
        }
        return {'success': True, 'journey': journey}
    
    def check_procedures(self, patient_profile):
        """
        Check procedures for patient.
        """
        # Mock data for procedures
        procedures = [
            {'date': '2024-01-15', 'procedure': 'Blood test', 'status': 'Completed'},
            {'date': '2024-02-20', 'procedure': 'X-ray', 'status': 'Completed'},
            {'date': '2024-04-05', 'procedure': 'MRI', 'status': 'Scheduled'}
        ]
        return {'success': True, 'procedures': procedures}
    
    def recommend_therapy_plan(self, patient_profile):
        """
        Recommend therapy plan for patient.
        """
        # Mock data for therapy plan
        therapy_plan = {
            'diagnosis': 'Mild hypertension',
            'recommendations': [
                'Regular exercise (30 minutes daily)',
                'Low sodium diet',
                'Stress management techniques',
                'Blood pressure monitoring twice weekly'
            ],
            'medications': [
                {'name': 'Lisinopril', 'dosage': '10mg', 'frequency': 'Once daily'},
                {'name': 'Hydrochlorothiazide', 'dosage': '12.5mg', 'frequency': 'Once daily'}
            ]
        }
        return {'success': True, 'therapy_plan': therapy_plan}
    
    def check_medication_compliance(self, patient_profile):
        """
        Check medication compliance for patient.
        """
        # Mock data for medication compliance
        compliance = {
            'overall_compliance': '85%',
            'medications': [
                {'name': 'Lisinopril', 'compliance': '90%', 'last_refill': '2024-02-15'},
                {'name': 'Hydrochlorothiazide', 'compliance': '80%', 'last_refill': '2024-02-15'}
            ],
            'recommendations': [
                'Set daily medication reminders',
                'Use a pill organizer',
                'Schedule regular follow-up appointments'
            ]
        }
        return {'success': True, 'compliance': compliance}


class GenomicServicesView(LoginRequiredMixin, View):
    """
    View to handle genomic services.
    """
    def get(self, request, *args, **kwargs):
        return render(request, 'services/genomic_services.html')
    
    def post(self, request, *args, **kwargs):
        service_type = request.POST.get('service_type')
        patient_id = request.POST.get('patient_id')
        
        try:
            patient = User.objects.get(national_id=patient_id, user_type='patient')
            try:
                patient_profile = UserProfile.objects.get(user=patient)
            except UserProfile.DoesNotExist:
                # Create a profile for the user if it doesn't exist
                patient_profile = UserProfile.objects.create(user=patient)
            
            if service_type == 'genomic_variants':
                result = self.check_genomic_variants(patient_profile)
            elif service_type == 'risk_alleles':
                result = self.check_risk_alleles(patient_profile)
            elif service_type == 'drug_gene_interaction':
                result = self.drug_gene_interaction(patient_profile)
            elif service_type == 'dose_adjustment':
                result = self.dose_adjustment(patient_profile)
            else:
                result = {'error': 'Invalid service type'}
                
            return JsonResponse(result)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    def check_genomic_variants(self, patient_profile):
        """
        Check genomic variants for patient.
        """
        # Mock data for genomic variants
        variants = [
            {'gene': 'BRCA1', 'variant': 'rs28897696', 'significance': 'Pathogenic'},
            {'gene': 'MTHFR', 'variant': 'rs1801133', 'significance': 'Benign'},
            {'gene': 'CYP2C19', 'variant': 'rs4244285', 'significance': 'Likely pathogenic'}
        ]
        return {'success': True, 'variants': variants}
    
    def check_risk_alleles(self, patient_profile):
        """
        Check risk alleles for patient.
        """
        # Mock data for risk alleles
        risk_alleles = [
            {'condition': 'Type 2 Diabetes', 'gene': 'TCF7L2', 'risk': 'Moderate'},
            {'condition': 'Coronary Artery Disease', 'gene': 'CDKN2B-AS1', 'risk': 'Low'},
            {'condition': 'Alzheimer\'s Disease', 'gene': 'APOE', 'risk': 'High'}
        ]
        return {'success': True, 'risk_alleles': risk_alleles}
    
    def drug_gene_interaction(self, patient_profile):
        """
        Check drug-gene interactions for patient.
        """
        # Mock data for drug-gene interactions
        interactions = [
            {'drug': 'Clopidogrel', 'gene': 'CYP2C19', 'effect': 'Reduced metabolism', 'recommendation': 'Consider alternative antiplatelet therapy'},
            {'drug': 'Simvastatin', 'gene': 'SLCO1B1', 'effect': 'Increased risk of myopathy', 'recommendation': 'Lower dose or alternative statin'},
            {'drug': 'Warfarin', 'gene': 'VKORC1', 'effect': 'Increased sensitivity', 'recommendation': 'Reduce initial dose'}
        ]
        return {'success': True, 'interactions': interactions}
    
    def dose_adjustment(self, patient_profile):
        """
        Calculate dose adjustment based on genomic data.
        """
        # Mock data for dose adjustment
        adjustments = [
            {'drug': 'Warfarin', 'standard_dose': '5mg daily', 'adjusted_dose': '3mg daily', 'reason': 'VKORC1 variant'},
            {'drug': 'Azathioprine', 'standard_dose': '2mg/kg daily', 'adjusted_dose': '1mg/kg daily', 'reason': 'TPMT variant'},
            {'drug': 'Simvastatin', 'standard_dose': '40mg daily', 'adjusted_dose': '20mg daily', 'reason': 'SLCO1B1 variant'}
        ]
        return {'success': True, 'adjustments': adjustments}
