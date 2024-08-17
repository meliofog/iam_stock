from django.db import models

class Record(models.Model):
    name = models.CharField(max_length=255)

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
