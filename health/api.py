from pathlib import PurePosixPath
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
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
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer

    def get_queryset(self):
        return Medication.objects.filter(user=self.request.user).prefetch_related("schedules")


class DoseLogViewSet(viewsets.ModelViewSet):
    queryset = DoseLog.objects.all()
    serializer_class = DoseLogSerializer

    def get_queryset(self):
        return DoseLog.objects.filter(schedule__medication__user=self.request.user).select_related("schedule__medication")


class HealthRecordViewSet(viewsets.ModelViewSet):
    queryset = HealthRecord.objects.all()
    serializer_class = HealthRecordSerializer

    def get_queryset(self):
        return HealthRecord.objects.filter(user=self.request.user)


class MedicalDocumentViewSet(viewsets.ModelViewSet):
    queryset = MedicalDocument.objects.all()
    serializer_class = MedicalDocumentSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return MedicalDocument.objects.filter(user=self.request.user)


class MedicalDocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, pk):
        document = get_object_or_404(MedicalDocument, pk=pk, user=request.user)
        suffix = PurePosixPath(document.file.name).suffix.lower()
        content_type = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}[suffix]
        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=f"documento-{document.pk}{suffix}",
            content_type=content_type,
        )
