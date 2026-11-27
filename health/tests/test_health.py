from datetime import date, datetime, time
from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from health.models import DoseLog, HealthCondition, HealthProfile, HealthRecord, MedicalClinic, MedicalDocument, Medication, MedicationSchedule
from health.tasks import queue_due_medication_reminders
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


class BemoriaWebFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bemoria-user", email="user@example.com", password="long-passphrase-123")
        self.other_user = User.objects.create_user(username="bemoria-other", email="other@example.com", password="long-passphrase-123")
        self.client = Client()
        self.client.force_login(self.user)

    def test_new_sections_render_for_authenticated_users(self):
        for path in ("/", "/perfil/", "/emergencia/", "/documentos/", "/saude/", "/clinicas/", "/historico/doses/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_profile_form_updates_user_and_health_information(self):
        response = self.client.post("/perfil/", {
            "first_name": "Beatriz", "last_name": "Lima", "email": "beatriz@example.com",
            "phone": "11999990000", "birth_date": "1990-04-10", "blood_type": "O+",
            "allergies": "Penicilina", "height_cm": "168", "weight_kg": "62.5",
            "emergency_contact_name": "Contato", "emergency_contact_phone": "11888880000",
            "emergency_notes": "Informação pessoal",
        })

        self.assertRedirects(response, "/perfil/")
        self.user.refresh_from_db()
        profile = self.user.health_profile
        self.assertEqual(self.user.first_name, "Beatriz")
        self.assertEqual(self.user.email, "beatriz@example.com")
        self.assertEqual(profile.blood_type, "O+")
        self.assertEqual(profile.allergies, "Penicilina")

    def test_profile_photo_and_documents_are_private(self):
        image_buffer = BytesIO()
        Image.new("RGB", (8, 8), "green").save(image_buffer, format="PNG")
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post("/perfil/", {
                "first_name": "", "last_name": "", "email": "user@example.com", "phone": "", "birth_date": "",
                "blood_type": "", "allergies": "", "height_cm": "", "weight_kg": "", "emergency_contact_name": "",
                "emergency_contact_phone": "", "emergency_notes": "",
                "profile_photo": SimpleUploadedFile("photo.png", image_buffer.getvalue(), content_type="image/png"),
            })
            self.assertRedirects(response, "/perfil/")
            self.assertTrue(self.user.health_profile.profile_photo.name)
            self.client.force_login(self.other_user)
            self.assertEqual(self.client.get("/perfil/foto/").status_code, 404)
            self.client.force_login(self.user)
            clear_response = self.client.post("/perfil/", {
                "first_name": "", "last_name": "", "email": "user@example.com", "phone": "", "birth_date": "",
                "blood_type": "", "allergies": "", "height_cm": "", "weight_kg": "", "emergency_contact_name": "",
                "emergency_contact_phone": "", "emergency_notes": "", "remove_profile_photo": "on",
            })
            self.assertRedirects(clear_response, "/perfil/")
            self.user.health_profile.refresh_from_db()
            self.assertFalse(self.user.health_profile.profile_photo)

    def test_document_upload_download_and_removal(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post("/documentos/", {"title": "Exame", "file": SimpleUploadedFile("exam.pdf", b"%PDF-1.4 contents", content_type="application/pdf")})
            self.assertRedirects(response, "/documentos/")
            document = MedicalDocument.objects.get(user=self.user)
            self.assertEqual(document.user_id, self.user.pk)
            other_client = Client()
            other_client.force_login(self.other_user)
            self.assertEqual(other_client.get(f"/documentos/{document.pk}/baixar/").status_code, 404)
            download = self.client.get(f"/documentos/{document.pk}/baixar/")
            self.assertEqual(download.status_code, 200)
            self.assertIn(b"%PDF-1.4", download.content)
            self.assertIn("attachment;", download["Content-Disposition"])
            self.assertRedirects(self.client.post(f"/documentos/{document.pk}/remover/"), "/documentos/")
            self.assertFalse(MedicalDocument.objects.filter(pk=document.pk).exists())

    def test_conditions_and_clinics_belong_only_to_their_owner(self):
        self.client.post("/saude/", {"name": "Acompanhamento pessoal", "notes": "Minha anotação", "diagnosed_on": "", "active": "on"})
        self.client.post("/clinicas/", {"name": "Clínica da família", "specialty": "", "phone": "", "address": "", "website": "", "notes": ""})
        self.assertTrue(HealthCondition.objects.filter(user=self.user).exists())
        self.assertTrue(MedicalClinic.objects.filter(user=self.user).exists())
        self.assertFalse(HealthCondition.objects.filter(user=self.other_user).exists())
        self.assertFalse(MedicalClinic.objects.filter(user=self.other_user).exists())

    def test_medication_edit_keeps_previous_dose_log(self):
        medication = Medication.objects.create(user=self.user, name="Exemplo", dosage="1 comprimido")
        schedule = MedicationSchedule.objects.create(medication=medication, time=time(8, 0))
        due = timezone.make_aware(datetime.combine(timezone.localdate(), schedule.time))
        dose = DoseLog.objects.create(schedule=schedule, scheduled_for=due, status=DoseLog.Status.TAKEN)

        response = self.client.post(f"/medicamentos/{medication.pk}/editar/", {
            "name": "Exemplo", "dosage": "2 comprimidos", "instructions": "Com água",
            "schedule_times": "09:00, 21:00", "schedule_weekdays": ["0", "2", "4"],
        })

        self.assertRedirects(response, "/medicamentos/")
        schedule.refresh_from_db()
        self.assertFalse(schedule.active)
        self.assertTrue(DoseLog.objects.filter(pk=dose.pk).exists())
        self.assertEqual(list(medication.schedules.filter(active=True).values_list("weekdays", flat=True)), [[0, 2, 4], [0, 2, 4]])

    def test_password_reset_sends_recovery_link(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post("/senha/esqueci/", {"email": self.user.email})
            self.assertRedirects(response, "/senha/enviado/")
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn("senha/redefinir/", mail.outbox[0].body)

    def test_profile_and_sensitive_areas_require_login(self):
        anonymous = Client()
        for path in ("/perfil/", "/emergencia/", "/documentos/", "/saude/", "/clinicas/", "/historico/doses/"):
            with self.subTest(path=path):
                self.assertEqual(anonymous.get(path).status_code, 302)

    def test_health_library_has_publicly_sourced_resources(self):
        response = self.client.get("/saude/")
        self.assertContains(response, "Ministério da Saúde")
        self.assertContains(response, "Canal Saúde")

    def test_checklist_can_record_a_dose_as_skipped_without_deleting_history(self):
        medication = Medication.objects.create(user=self.user, name="Dose", dosage="1")
        schedule = MedicationSchedule.objects.create(medication=medication, time=time(8, 0), weekdays=[])
        due = timezone.make_aware(datetime.combine(timezone.localdate(), schedule.time))
        DoseLog.objects.create(schedule=schedule, scheduled_for=due, status=DoseLog.Status.TAKEN)

        response = self.client.post(f"/medicamentos/horarios/{schedule.pk}/tomar/", {"taken": ""})

        self.assertRedirects(response, "/")
        log = DoseLog.objects.get(schedule=schedule, scheduled_for=due)
        self.assertEqual(log.status, DoseLog.Status.SKIPPED)


class MedicationReminderTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_due_scheduled_medication_sends_an_email_reminder(self):
        current = timezone.make_aware(datetime(2026, 11, 23, 8, 0))
        user = User.objects.create_user(username="reminder-user", email="reminder@example.com", password="long-passphrase-123")
        medication = Medication.objects.create(user=user, name="Remédio", dosage="1 dose")
        MedicationSchedule.objects.create(medication=medication, time=time(8, 0), weekdays=[])
        with patch("health.tasks.timezone.localtime", return_value=current):
            reminders = queue_due_medication_reminders.run()

        self.assertEqual(len(reminders), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Remédio", mail.outbox[0].subject)

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
