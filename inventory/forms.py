from django import forms
from .models import Equipment, Record

class UploadFileForm(forms.Form):
    file = forms.FileField()

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'record', 'ref', 'sn', 'sn_rempl', 'reception_date', 'delivery_status', 'delivery_date', 'bl']
        widgets = {
            'reception_date': forms.DateInput(attrs={'type': 'date'}),
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'sn': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

class RecordForm(forms.ModelForm):
    class Meta:
        model = Record
        fields = ['name', 'reception_date']
        widgets = {
            'reception_date': forms.DateInput(attrs={'type': 'date'}),
        }