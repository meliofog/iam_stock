from django.db import models
from django.utils import timezone

class Record(models.Model):
    name = models.CharField(max_length=255)
    reception_date = models.DateField(blank=True, null=True)
    quarter = models.CharField(max_length=2, blank=True, null=True)  # Adding the quarter field

    @property
    def items_count(self):
        return self.equipment.count()

    @property
    def status(self):
        in_progress_count = self.equipment.filter(delivery_status='InProgress').count()
        if in_progress_count == 0:
            return 'closed'
        return f'{in_progress_count} items left'

    @property
    def repair_duration(self):
        if self.reception_date:
            return (timezone.now().date() - self.reception_date).days
        return 0

    @property
    def message(self):
        if 75 <= self.repair_duration <= 90:
            days_left = 91 - self.repair_duration
            return f'You have {days_left} days before penalty.'
        elif self.repair_duration > 90:
            return 'Penalty issued!'
        return None

    def save(self, *args, **kwargs):
        # Automatically update the quarter based on reception_date
        if self.reception_date:
            quarter_mapping = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
            self.quarter = quarter_mapping[(self.reception_date.month - 1) // 3 + 1]
        else:
            self.quarter = None  # Set quarter to None if reception_date is not set
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    record = models.ForeignKey(Record, related_name='equipment', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    ref = models.CharField(max_length=255, blank=True, null=True)
    sn = models.CharField(max_length=255, blank=True, null=True)
    sn_rempl = models.CharField(max_length=255, blank=True, null=True)
    reception_date = models.DateField(blank=True, null=True)
    delivery_status = models.CharField(
        max_length=50,
        choices=[('Delivered', 'Delivered'), ('InProgress', 'InProgress')],
        default='InProgress'
    )
    delivery_date = models.DateField(blank=True, null=True)
    bl = models.CharField(
        max_length=3,
        choices=[('yes', 'Yes'), ('no', 'No')],
        default='no'
    )
    year = models.PositiveIntegerField(blank=True, null=True)
    quarter = models.CharField(max_length=2, blank=True, null=True)
    order_index = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        # Automatically update year and quarter based on reception_date
        if self.reception_date:
            self.year = self.reception_date.year
            quarter_mapping = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
            self.quarter = quarter_mapping[(self.reception_date.month - 1) // 3 + 1]
        else:
            self.year = None
            self.quarter = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
