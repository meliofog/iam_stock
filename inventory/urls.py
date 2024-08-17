from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('equipments/', views.equipment_list, name='equipment_list'),
    path('records/', views.record_list, name='record_list'),
    path('download_record/<int:record_id>/', views.download_record, name='download_record'),
    path('delete_record/<int:record_id>/', views.delete_record, name='delete_record'),
    path('equipment/edit/<int:pk>/', views.edit_equipment, name='edit_equipment'),
    path('equipment/update/<int:id>/', views.update_equipment, name='update_equipment'),
]
