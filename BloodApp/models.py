from django.db import models
from django.utils import timezone

class BloodRequest(models.Model):
    """Hospital requests blood from Blood Bank"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('fulfilled', 'Fulfilled'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ]
    
    URGENCY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High - Critical'),
    ]
    
    # Relationships
    hospital = models.ForeignKey('Hospital', on_delete=models.CASCADE, related_name='blood_requests')
    blood_bank = models.ForeignKey('BloodBank', on_delete=models.CASCADE, related_name='received_requests')
    
    # Request Details
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPE_CHOICES)
    units_required = models.IntegerField(help_text="Number of units")
    urgency_level = models.CharField(max_length=20, choices=URGENCY_CHOICES, default='medium')
    
    # Status & Timeline
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Response Details
    approved_by = models.ForeignKey('BloodBankStaff', null=True, blank=True, on_delete=models.SET_NULL)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    units_approved = models.IntegerField(null=True, blank=True)
    units_fulfilled = models.IntegerField(default=0)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    
    rejection_reason = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-urgency_level', '-created_at']  # ← Added urgency sorting
        verbose_name_plural = 'Blood Requests'
    
    def __str__(self):
        return f"{self.hospital.name} - {self.blood_type} ({self.get_status_display()})"
    
    def approve(self, staff, units_approved, remarks=''):
        """Blood bank approves request"""
        if units_approved <= 0:
            raise ValueError("Units approved must be greater than 0")
        
        self.status = 'approved'
        self.approved_by = staff
        self.approved_at = timezone.now()
        self.units_approved = units_approved
        self.remarks = remarks
        self.save()
        
        # Create notification
        BloodRequestNotification.objects.create(
            request=self,
            notification_type='approved',
            message=f"Approved for {units_approved} units of {self.blood_type}"
        )
    
    def fulfill(self, units_given):
        """Blood bank fulfills the request"""
        if units_given <= 0:
            raise ValueError("Units given must be greater than 0")
        
        if units_given > self.units_approved:
            raise ValueError(f"Cannot give more than approved ({self.units_approved})")
        
        self.units_fulfilled = units_given
        self.status = 'fulfilled'
        self.fulfilled_at = timezone.now()
        self.save()
        
        # Update blood bank inventory
        self.blood_bank.inventory.reduce_inventory(self.blood_type, units_given)
        
        # Create notification
        BloodRequestNotification.objects.create(
            request=self,
            notification_type='fulfilled',
            message=f"Fulfilled with {units_given} units of {self.blood_type}"
        )
    
    def reject(self, reason):
        """Blood bank rejects request"""
        if not reason:
            raise ValueError("Rejection reason is required")
        
        self.status = 'rejected'
        self.rejection_reason = reason
        self.save()
        
        # Create notification
        BloodRequestNotification.objects.create(
            request=self,
            notification_type='rejected',
            message=f"Rejected: {reason}"
        )


class BloodRequestNotification(models.Model):
    """Tracks all notifications for blood requests"""
    
    NOTIFICATION_TYPES = [
        ('created', 'Request Created'),
        ('approved', 'Request Approved'),
        ('fulfilled', 'Request Fulfilled'),
        ('rejected', 'Request Rejected'),
        ('cancelled', 'Request Cancelled'),
    ]
    
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request} - {self.get_notification_type_display()}"


class BloodInventory(models.Model):
    """Track blood inventory in blood banks"""
    
    blood_bank = models.OneToOneField('BloodBank', on_delete=models.CASCADE, related_name='inventory')
    
    O_positive = models.IntegerField(default=0)
    O_negative = models.IntegerField(default=0)
    A_positive = models.IntegerField(default=0)
    A_negative = models.IntegerField(default=0)
    B_positive = models.IntegerField(default=0)
    B_negative = models.IntegerField(default=0)
    AB_positive = models.IntegerField(default=0)
    AB_negative = models.IntegerField(default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    def get_inventory_dict(self):
        """Return inventory as dictionary"""
        return {
            'O+': self.O_positive,
            'O-': self.O_negative,
            'A+': self.A_positive,
            'A-': self.A_negative,
            'B+': self.B_positive,
            'B-': self.B_negative,
            'AB+': self.AB_positive,
            'AB-': self.AB_negative,
        }
    
    def get_available_units(self, blood_type):
        """Get available units for specific blood type"""
        field_map = {
            'O+': 'O_positive',
            'O-': 'O_negative',
            'A+': 'A_positive',
            'A-': 'A_negative',
            'B+': 'B_positive',
            'B-': 'B_negative',
            'AB+': 'AB_positive',
            'AB-': 'AB_negative',
        }
        return getattr(self, field_map.get(blood_type), 0)
    
    def reduce_inventory(self, blood_type, units):
        """Reduce inventory after fulfilling request"""
        field_map = {
            'O+': 'O_positive',
            'O-': 'O_negative',
            'A+': 'A_positive',
            'A-': 'A_negative',
            'B+': 'B_positive',
            'B-': 'B_negative',
            'AB+': 'AB_positive',
            'AB-': 'AB_negative',
        }
        field = field_map.get(blood_type)
        if not field:
            raise ValueError(f"Invalid blood type: {blood_type}")
        
        current = getattr(self, field)
        setattr(self, field, max(0, current - units))
        self.save()
    
    def __str__(self):
        return f"Inventory - {self.blood_bank.name}"