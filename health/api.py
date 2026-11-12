from rest_framework import generics, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from .models import DoseLog, HealthRecord, MedicalDocument, Medication
from .serializers import (
    DoseLogSerializer,
    HealthRecordSerializer,
    MedicalDocumentSerializer,
    MedicationSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []


class MedicationViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationSerializer

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user).prefetch_related("schedules")


class DoseLogViewSet(viewsets.ModelViewSet):
    serializer_class = DoseLogSerializer

    def get_queryset(self):
        return DoseLog.objects.filter(schedule__medication__user=self.request.user).select_related("schedule__medication")


class HealthRecordViewSet(viewsets.ModelViewSet):
    serializer_class = HealthRecordSerializer

    def get_queryset(self):
        return HealthRecord.objects.filter(user=self.request.user)


class MedicalDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalDocumentSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user)
