from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class HealthProfile(models.Model):
    BLOOD_GROUPS = [
        ("A+", "A+"), ("A-", "A−"), ("B+", "B+"), ("B-", "B−"),
        ("AB+", "AB+"), ("AB-", "AB−"), ("O+", "O+"), ("O-", "O−"),
        ("unknown", "Não sei"),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_profile")
    phone = models.CharField("telefone", max_length=30, blank=True)
    birth_date = models.DateField("data de nascimento", null=True, blank=True)
    blood_type = models.CharField("tipo sanguíneo", max_length=10, choices=BLOOD_GROUPS, blank=True)
    allergies = models.TextField("alergias", blank=True, help_text="Informe alergias conhecidas. Deixe em branco se não souber.")
    height_cm = models.DecimalField("altura (cm)", max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(300)])
    weight_kg = models.DecimalField("peso (kg)", max_digits=5, decimal_places=1, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(700)])
    emergency_contact_name = models.CharField("contato de emergência", max_length=120, blank=True)
    emergency_contact_phone = models.CharField("telefone de emergência", max_length=30, blank=True)
    emergency_notes = models.TextField("observações para emergência", blank=True)
    profile_photo = models.ImageField("foto de perfil", upload_to="profile-photos/%Y/%m/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de saúde"
        verbose_name_plural = "perfis de saúde"

    def __str__(self):
        return f"Perfil de {self.user}"

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


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

    def is_scheduled_for(self, day):
        """An empty weekdays list means every day; Python weekdays use Monday=0."""
        return self.active and (not self.weekdays or day.weekday() in self.weekdays)

    @property
    def weekday_labels(self):
        names = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
        return "Todos os dias" if not self.weekdays else ", ".join(names[day] for day in self.weekdays if 0 <= day <= 6)


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


class HealthCondition(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="health_conditions")
    name = models.CharField("condição", max_length=160)
    notes = models.TextField("anotações pessoais", blank=True)
    diagnosed_on = models.DateField("data informada", null=True, blank=True)
    active = models.BooleanField("acompanhar", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "condição de saúde"
        verbose_name_plural = "condições de saúde"

    def __str__(self):
        return self.name


class MedicalClinic(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="medical_clinics")
    name = models.CharField("nome", max_length=160)
    specialty = models.CharField("especialidade", max_length=120, blank=True)
    phone = models.CharField("telefone", max_length=30, blank=True)
    address = models.CharField("endereço", max_length=240, blank=True)
    website = models.URLField("site", blank=True)
    notes = models.TextField("anotações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "clínica"
        verbose_name_plural = "clínicas"

    def __str__(self):
        return self.name


class EducationalResource(models.Model):
    class Kind(models.TextChoices):
        ARTICLE = "article", "Artigo"
        VIDEO = "video", "Vídeo"

    title = models.CharField("título", max_length=180)
    topic = models.CharField("tema", max_length=120, blank=True)
    summary = models.TextField("resumo")
    kind = models.CharField("formato", max_length=10, choices=Kind.choices)
    source_name = models.CharField("fonte", max_length=120, blank=True)
    url = models.URLField("link", blank=True)
    read_minutes = models.PositiveSmallIntegerField("duração em minutos", null=True, blank=True)
    active = models.BooleanField("publicado", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["topic", "title"]
        verbose_name = "conteúdo educativo"
        verbose_name_plural = "conteúdos educativos"

    def __str__(self):
        return self.title
