from django.conf import settings
from django.db import models


class Medication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medications")
    name = models.CharField("nome", max_length=160)
    dosage = models.CharField("dose", max_length=100)
    instructions = models.TextField("instruções", blank=True)
    active = models.BooleanField("em uso", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "medicamento"
        verbose_name_plural = "medicamentos"

    def __str__(self):
        return f"{self.name} · {self.dosage}"


class MedicationSchedule(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name="schedules")
    time = models.TimeField("horário")
    weekdays = models.JSONField("dias da semana", default=list, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["time"]

    def __str__(self):
        return f"{self.medication.name} às {self.time:%H:%M}"


class DoseLog(models.Model):
    class Status(models.TextChoices):
        TAKEN = "taken", "Tomado"
        SKIPPED = "skipped", "Não tomado"

    schedule = models.ForeignKey(MedicationSchedule, on_delete=models.CASCADE, related_name="dose_logs")
    scheduled_for = models.DateTimeField("previsto para")
    status = models.CharField(max_length=12, choices=Status.choices)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_for"]
        constraints = [models.UniqueConstraint(fields=["schedule", "scheduled_for"], name="unique_dose_per_schedule_time")]


class HealthRecord(models.Model):
    class Kind(models.TextChoices):
        CONSULTATION = "consultation", "Consulta"
        EXAM = "exam", "Exame"
        VACCINE = "vaccine", "Vacina"
        NOTE = "note", "Anotação"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_records")
    kind = models.CharField("tipo", max_length=20, choices=Kind.choices)
    title = models.CharField("título", max_length=180)
    details = models.TextField("detalhes", blank=True)
    occurred_on = models.DateField("data")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        verbose_name = "registro de saúde"
        verbose_name_plural = "registros de saúde"

    def __str__(self):
        return self.title


class MedicalDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medical_documents")
    title = models.CharField("nome do documento", max_length=180)
    file = models.FileField("arquivo", upload_to="medical-documents/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "documento médico"
        verbose_name_plural = "documentos médicos"
