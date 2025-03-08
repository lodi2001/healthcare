from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta

# Create your models here.

class ServiceCategory(models.Model):
    """
    Model to represent service categories offered by healthcare providers
    """
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("Icon Class"), max_length=50, blank=True, help_text="Font Awesome icon class")
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Service Category")
        verbose_name_plural = _("Service Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Model to represent healthcare services offered by providers
    """
    PRICING_TYPE_CHOICES = (
        ('fixed', _('Fixed Price')),
        ('range', _('Price Range')),
        ('variable', _('Variable Price')),
        ('free', _('Free')),
    )

    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    name = models.CharField(_("Service Name"), max_length=200)
    description = models.TextField(_("Description"))
    pricing_type = models.CharField(_("Pricing Type"), max_length=20, choices=PRICING_TYPE_CHOICES, default='fixed')
    price = models.DecimalField(_("Price (SAR)"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_min = models.DecimalField(_("Minimum Price (SAR)"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_max = models.DecimalField(_("Maximum Price (SAR)"), max_digits=10, decimal_places=2, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(_("Duration (minutes)"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    @property
    def price_display(self):
        if self.pricing_type == 'fixed' and self.price:
            return f"{self.price} SAR"
        elif self.pricing_type == 'range' and self.price_min and self.price_max:
            return f"{self.price_min} - {self.price_max} SAR"
        elif self.pricing_type == 'free':
            return _("Free")
        else:
            return _("Variable")


class ProviderService(models.Model):
    """
    Model to link healthcare providers with the services they offer
    """
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="offered_services")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="providers")
    custom_price = models.DecimalField(_("Custom Price (SAR)"), max_digits=10, decimal_places=2, null=True, blank=True)
    custom_duration = models.PositiveIntegerField(_("Custom Duration (minutes)"), null=True, blank=True)
    is_available = models.BooleanField(_("Available"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Provider Service")
        verbose_name_plural = _("Provider Services")
        unique_together = ('provider', 'service')

    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.service.name}"

    @property
    def price_display(self):
        if self.custom_price:
            return f"{self.custom_price} SAR"
        return self.service.price_display

    @property
    def duration_display(self):
        if self.custom_duration:
            return f"{self.custom_duration} minutes"
        elif self.service.duration_minutes:
            return f"{self.service.duration_minutes} minutes"
        return _("Variable")


class Appointment(models.Model):
    """
    Model to represent service appointments between patients and providers
    """
    STATUS_CHOICES = (
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    )

    provider_service = models.ForeignKey(ProviderService, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appointments")
    appointment_date = models.DateField(_("Appointment Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(_("Notes"), blank=True)
    medical_notes = models.TextField(_("Medical Notes"), blank=True, help_text=_("Private notes for healthcare providers"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Appointment")
        verbose_name_plural = _("Appointments")
        ordering = ["appointment_date", "start_time"]

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.provider_service.service.name} - {self.appointment_date}"


class AvailabilitySchedule(models.Model):
    """
    Model to represent provider availability for scheduling appointments
    """
    DAY_CHOICES = (
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    )

    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_schedules")
    day_of_week = models.IntegerField(_("Day of Week"), choices=DAY_CHOICES)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Availability Schedule")
        verbose_name_plural = _("Availability Schedules")
        ordering = ["day_of_week", "start_time"]
        unique_together = ('provider', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.provider.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


class ServiceReview(models.Model):
    """
    Model to represent patient reviews for provider services
    """
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField(_("Rating"), choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(_("Comment"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Service Review")
        verbose_name_plural = _("Service Reviews")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.appointment.patient.get_full_name()} for {self.appointment.provider_service.service.name}"


class DoctorSchedule(models.Model):
    """Model to track doctor availability schedules"""
    DAYS_OF_WEEK = [
        ('Monday', _('Monday')),
        ('Tuesday', _('Tuesday')),
        ('Wednesday', _('Wednesday')),
        ('Thursday', _('Thursday')),
        ('Friday', _('Friday')),
        ('Saturday', _('Saturday')),
        ('Sunday', _('Sunday')),
    ]
    
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                              related_name='schedules', limit_choices_to={'user_type': 'healthcare_provider'})
    day_of_week = models.CharField(_('Day of Week'), max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    is_active = models.BooleanField(_('Active'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Doctor Schedule')
        verbose_name_plural = _('Doctor Schedules')
        ordering = ['day_of_week', 'start_time']
        unique_together = [['doctor', 'day_of_week', 'start_time']]
    
    def __str__(self):
        return f"{self.doctor.get_full_name()} - {self.day_of_week} ({self.start_time} - {self.end_time})"
    
    def clean(self):
        """Validate that end_time is after start_time and no overlapping schedules exist"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError(_('End time must be after start time'))
        
        # Check for overlapping schedules
        overlapping = DoctorSchedule.objects.filter(
            doctor=self.doctor,
            day_of_week=self.day_of_week,
            is_active=True
        ).exclude(pk=self.pk)
        
        for schedule in overlapping:
            # Check if new schedule overlaps with existing schedule
            if (self.start_time <= schedule.end_time and self.end_time >= schedule.start_time):
                raise ValidationError(_(
                    'This schedule overlaps with an existing schedule: '
                    f'{schedule.start_time} - {schedule.end_time}'
                ))
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Calculate the duration of the schedule in minutes"""
        if not self.start_time or not self.end_time:
            return 0
        
        start_datetime = datetime.combine(date.today(), self.start_time)
        end_datetime = datetime.combine(date.today(), self.end_time)
        
        if end_datetime < start_datetime:  # Handle overnight schedules
            end_datetime += timedelta(days=1)
            
        duration = end_datetime - start_datetime
        return duration.seconds // 60
