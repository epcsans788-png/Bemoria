from django.contrib import admin
from .models import DoseLog, HealthRecord, MedicalDocument, Medication, MedicationSchedule

admin.site.register([Medication, MedicationSchedule, DoseLog, HealthRecord, MedicalDocument])
