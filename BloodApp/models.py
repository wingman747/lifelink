from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class HospitalBloodBankVerification(models.Model):
    """Model to store verified hospitals and blood banks"""
    INSTITUTION_TYPES = [
        ('hospital', 'Hospital'),
        ('blood_bank', 'Blood Bank'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPES)
    registration_number = models.CharField(max_length=50, unique=True)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    license_document = models.FileField(upload_to='licenses/')
    is_verified = models.BooleanField(default=False)
    verified_by = models.CharField(max_length=100, blank=True)
    verified_on = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reason_for_rejection = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('name', 'institution_type')
    
    def __str__(self):
        return f"{self.name} ({self.get_institution_type_display()})"


class InstitutionUser(models.Model):
    """Link users to their verified institution"""
    institution = models.ForeignKey(HospitalBloodBankVerification, on_delete=models.CASCADE)
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    designation = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} - {self.institution.name}"