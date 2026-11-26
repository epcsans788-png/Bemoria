from datetime import date, datetime, time
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from health.models import DoseLog, HealthRecord, MedicalDocument, Medication, MedicationSchedule
from health.serializers import MedicalDocumentSerializer, MedicationSerializer


User = get_user_model()


class MedicationScheduleLogicTests(SimpleTestCase):
    def test_empty_weekdays_means_every_day_and_configured_days_are_respected(self):
        schedule = MedicationSchedule(time=time(8, 0), weekdays=[])
        self.assertTrue(schedule.is_scheduled_for(date(2026, 11, 23)))  # Monday

        schedule.weekdays = [0, 2, 4]
        self.assertTrue(schedule.is_scheduled_for(date(2026, 11, 23)))
        self.assertFalse(schedule.is_scheduled_for(date(2026, 11, 24)))

class MedicationScheduleHistoryTests(TestCase):
    def test_deactivating_schedule_does_not_delete_dose_history(self):
        user = User.objects.create_user(username="schedule-owner", password="long-passphrase-123")
        medication = Medication.objects.create(user=user, name="Example", dosage="1")
        schedule = MedicationSchedule.objects.create(medication=medication, time=time(8, 0))
        scheduled_for = timezone.make_aware(datetime.combine(timezone.localdate(), schedule.time))
        dose = DoseLog.objects.create(schedule=schedule, scheduled_for=scheduled_for, status=DoseLog.Status.TAKEN)
        request = SimpleNamespace(user=user)
        serializer = MedicationSerializer(
            medication,
            data={"schedules": []},
            partial=True,
            context={"request": request},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        schedule.refresh_from_db()
        self.assertFalse(schedule.active)
        self.assertTrue(DoseLog.objects.filter(pk=dose.pk).exists())


class UserDataIsolationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="long-passphrase-123")
        self.other_user = User.objects.create_user(username="other", password="long-passphrase-123")
        Medication.objects.create(user=self.owner, name="Owner medication", dosage="1")
        Medication.objects.create(user=self.other_user, name="Other medication", dosage="1")
        HealthRecord.objects.create(
            user=self.owner,
            kind=HealthRecord.Kind.NOTE,
            title="Owner note",
            occurred_on=date(2026, 11, 1),
        )
        self.client = APIClient()
        self.client.force_authenticate(self.owner)

    def test_api_lists_only_the_authenticated_users_medications(self):
        response = self.client.get("/api/medications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["Owner medication"])

    def test_api_lists_only_the_authenticated_users_records(self):
        response = self.client.get("/api/records/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["title"] for item in response.data], ["Owner note"])

    def test_document_download_is_scoped_to_owner(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                document = MedicalDocument.objects.create(user=self.other_user, title="Private")
                document.file.save(
                    "private.pdf",
                    SimpleUploadedFile("private.pdf", b"%PDF-1.4 private test content", content_type="application/pdf"),
                )
                response = self.client.get(f"/api/documents/{document.pk}/download/")

                self.assertEqual(response.status_code, 404)


class MedicalDocumentValidationTests(SimpleTestCase):
    def test_rejects_unsupported_document_type(self):
        uploaded = SimpleUploadedFile("script.exe", b"not a document", content_type="application/octet-stream")
        serializer = MedicalDocumentSerializer(data={"title": "Invalid", "file": uploaded})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_rejects_pdf_with_invalid_signature(self):
        uploaded = SimpleUploadedFile("fake.pdf", b"not really a PDF", content_type="application/pdf")
        serializer = MedicalDocumentSerializer(data={"title": "Invalid", "file": uploaded})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_rejects_oversized_file(self):
        uploaded = SimpleUploadedFile("large.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024), content_type="application/pdf")
        serializer = MedicalDocumentSerializer(data={"title": "Large", "file": uploaded})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)
