from django.shortcuts import render, redirect, get_object_or_404
from .models import Record, Equipment
from .forms import UploadFileForm
import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Count
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from io import BytesIO
import xlsxwriter
# Create your views here.

def record_list(request):
    records = Record.objects.all()
    equipment_count = Equipment.objects.values('record__name').annotate(count=Count('id'))
    equipment_count_dict = {item['record__name']: item['count'] for item in equipment_count}

    return render(request, 'inventory/record_list.html', {'records': records, 'equipment_count': equipment_count_dict})

def equipment_list(request):
    # Handle file upload
    form = UploadFileForm()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)

            for _, row in df.iterrows():
                record_name = row['Dossier']
                equipment_name = row['Design.']
                ref = row['Ref']
                sn = row['SN']
                sn_rempl = row['SN Rempl']
                reception_date = row['Reception date']
                delivery_status = row['Delivery status']
                delivery_date = row['Delivery date']
                bl = row['BL']
                year = row['YEAR']
                quarter = row['QUARTER']

                # Check if the record already exists
                record, created = Record.objects.get_or_create(name=record_name)

                # Create the equipment associated with the record
                Equipment.objects.create(
                    name=equipment_name, 
                    record=record, 
                    ref=ref, 
                    sn=sn, 
                    sn_rempl=sn_rempl,
                    reception_date=reception_date,
                    delivery_status=delivery_status,
                    delivery_date=delivery_date,
                    bl=bl,
                    year=year,
                    quarter=quarter
                )

            # Redirect or show success message
            return redirect('equipment_list')

    # Filtering and Pagination
    filter_record_id = request.GET.get('record')
    equipments = Equipment.objects.all()
    if filter_record_id:
        equipments = equipments.filter(record_id=filter_record_id)
    
    paginator = Paginator(equipments, 10)  # Show 10 equipments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/equipment_list.html', {
        'equipments': page_obj,
        'form': form,
        'records': Record.objects.all(),  # Ensure records are available for filtering
        'filter_record_id': filter_record_id  # Current filter record ID
    })

def download_record(request, record_id):
    record = get_object_or_404(Record, pk=record_id)
    equipments = Equipment.objects.filter(record=record)

    # Create Excel file
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#0000FF',
        'font_color': '#FFFFFF',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    yellow_header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#FFFF00',  # Yellow color for YEAR and QUARTER headers
        'font_color': '#000000',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })
    cell_format = workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True
    })

    # Add column headers with formatting
    headers = ['Name', 'Ref', 'SN', 'SN Rempl', 'Reception Date', 'Delivery Status', 'Delivery Date', 'BL', 'Year', 'Quarter']
    for col, header in enumerate(headers):
        if header in ['Year', 'Quarter']:
            worksheet.write(0, col, header, yellow_header_format)
        else:
            worksheet.write(0, col, header, header_format)

    # Add data rows with formatting
    for row_num, equipment in enumerate(equipments, start=1):
        worksheet.write(row_num, 0, equipment.name, cell_format)
        worksheet.write(row_num, 1, equipment.ref or '', cell_format)
        worksheet.write(row_num, 2, equipment.sn or '', cell_format)
        worksheet.write(row_num, 3, equipment.sn_rempl or '', cell_format)
        worksheet.write(row_num, 4, equipment.reception_date.strftime('%Y-%m-%d') if equipment.reception_date else '', cell_format)
        worksheet.write(row_num, 5, equipment.delivery_status or '', cell_format)
        worksheet.write(row_num, 6, equipment.delivery_date.strftime('%Y-%m-%d') if equipment.delivery_date else '', cell_format)
        worksheet.write(row_num, 7, equipment.bl or '', cell_format)
        worksheet.write(row_num, 8, equipment.year or '', cell_format)  # Apply cell_format to YEAR
        worksheet.write(row_num, 9, equipment.quarter or '', cell_format)  # Apply cell_format to QUARTER

    # Set column width for better readability
    worksheet.set_column('A:J', 20)

    workbook.close()
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{record.name}_data.xlsx"'
    return response

def delete_record(request, record_id):
    record = get_object_or_404(Record, pk=record_id)
    
    if request.method == 'POST':
        record.delete()
        return redirect('record_list')

    return render(request, 'records/confirm_delete.html', {'record': record})