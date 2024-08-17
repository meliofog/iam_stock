from django.shortcuts import render, redirect, get_object_or_404
from .models import Record, Equipment
from .forms import EquipmentForm, UploadFileForm
import pandas as pd
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.urls import reverse
from django.db.models import Count
from io import BytesIO
from django.utils.dateparse import parse_date
import xlsxwriter
# Create your views here.

def home(request):
    form = UploadFileForm()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            df = pd.read_excel(excel_file)

            for index, row in df.iterrows():
                record_name = row['Dossier']
                equipment_name = row['Design.']
                ref = row['Ref']
                sn = row['SN']
                sn_rempl = row['SN Rempl']
                #reception_date = row['Date de récept']
                #delivery_status = row['Livraison']
                #delivery_date = row['Date Livraison']
                #bl = row['BL']
                #year = row['YEAR']
                #quarter = row['QUARTER']

                # Check if the record already exists
                record, created = Record.objects.get_or_create(name=record_name)

                # Check if the equipment with the same SN already exists
                existing_equipment = Equipment.objects.filter(sn=sn).first()

                if not existing_equipment:
                    # Create the equipment associated with the record
                    Equipment.objects.create(
                        name=equipment_name, 
                        record=record, 
                        ref=ref, 
                        sn=sn, 
                        sn_rempl=sn_rempl,
                        order_index=index + 1  # Assign order_index based on the row number
                    )
                else:
                    # Log or handle the case where the equipment already exists
                    print(f"Equipment with SN {sn} already exists and was not added.")

            return redirect('home')

    total_records = Record.objects.count()
    total_equipments = Equipment.objects.count()

    return render(request, 'inventory/home.html', {
        'form': form,
        'total_records': total_records,
        'total_equipments': total_equipments,
    })


def record_list(request):
    records = Record.objects.all()
    equipment_count = Equipment.objects.values('record__name').annotate(count=Count('id'))
    equipment_count_dict = {item['record__name']: item['count'] for item in equipment_count}

    return render(request, 'inventory/record_list.html', {'records': records, 'equipment_count': equipment_count_dict})


def equipment_list(request):
    # Get filters from GET parameters
    filter_record_id = request.GET.get('record')
    filter_sn = request.GET.get('sn', '')

    # Filter query
    equipments = Equipment.objects.all()
    if filter_record_id:
        equipments = equipments.filter(record_id=filter_record_id)
    if filter_sn:
        equipments = equipments.filter(sn__icontains=filter_sn)

    # Pagination
    paginator = Paginator(equipments, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all records for the filter dropdown
    records = Record.objects.all()

    context = {
        'equipments': page_obj,
        'records': records,
        'filter_record_id': filter_record_id,
        'filter_sn': filter_sn
    }
    return render(request, 'inventory/equipment_list.html', context)

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

def edit_equipment(request, pk):
    equipment = get_object_or_404(Equipment, pk=pk)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save(commit=False)
            # Update year and quarter based on reception_date
            if equipment.reception_date:
                equipment.year = equipment.reception_date.year
                quarter_mapping = {1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4'}
                equipment.quarter = quarter_mapping[(equipment.reception_date.month - 1) // 3 + 1]
            else:
                equipment.year = None
                equipment.quarter = None
            equipment.save()
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)

    return render(request, 'inventory/edit_equipment.html', {'form': form})

def update_equipment(request, id):
    equipment = get_object_or_404(Equipment, id=id)
    
    if request.method == 'POST':
        # Update fields manually
        equipment.name = request.POST.get('name')
        equipment.record_id = request.POST.get('record')
        equipment.ref = request.POST.get('ref')
        equipment.sn = request.POST.get('sn')
        equipment.sn_rempl = request.POST.get('sn_rempl')
        
        # Handle optional dates
        reception_date = request.POST.get('reception_date')
        delivery_date = request.POST.get('delivery_date')
        equipment.reception_date = reception_date if reception_date else None
        equipment.delivery_date = delivery_date if delivery_date else None
        
        equipment.delivery_status = request.POST.get('delivery_status')
        equipment.bl = request.POST.get('bl')
        equipment.year = request.POST.get('year')
        equipment.quarter = request.POST.get('quarter')
        equipment.save()
        
        return redirect('equipment_list')
    
    records = Record.objects.all()
    return render(request, 'inventory/edit_equipment.html', {
        'equipment': equipment,
        'records': records
    })

