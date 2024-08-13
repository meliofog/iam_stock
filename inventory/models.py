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
    delivery_status = models.CharField(max_length=255, blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    bl = models.CharField(max_length=255, blank=True, null=True)
    year = models.PositiveIntegerField(blank=True, null=True)
    quarter = models.CharField(max_length=2, blank=True, null=True)
    order_index = models.PositiveIntegerField()  # New field to store row order

    def __str__(self):
        return self.name
