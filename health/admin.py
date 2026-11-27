from django.contrib import admin
from .models import (
    DoseLog, EducationalResource, HealthCondition, HealthProfile, HealthRecord,
    MedicalClinic, MedicalDocument, Medication, MedicationSchedule,
)

admin.site.register([
    HealthProfile, Medication, MedicationSchedule, DoseLog, HealthRecord,
    MedicalDocument, HealthCondition, MedicalClinic, EducationalResource,
])
