from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.urls import reverse
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
from .models import DoseLog, HealthRecord, MedicalDocument, Medication, MedicationSchedule

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password")

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MedicationScheduleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = MedicationSchedule
        fields = ("id", "time", "weekdays", "active")

    def validate_weekdays(self, weekdays):
        if not isinstance(weekdays, list) or any(type(day) is not int or day < 0 or day > 6 for day in weekdays):
            raise serializers.ValidationError("Use uma lista de dias da semana de 0 (segunda) a 6 (domingo).")
        if len(weekdays) != len(set(weekdays)):
            raise serializers.ValidationError("Remova os dias repetidos.")
        return weekdays


class MedicationSerializer(serializers.ModelSerializer):
    schedules = MedicationScheduleSerializer(many=True, required=False)

    class Meta:
        model = Medication
        fields = ("id", "name", "dosage", "instructions", "active", "created_at", "schedules")
        read_only_fields = ("id", "created_at")

    def validate_schedules(self, schedules):
        supplied_ids = [item["id"] for item in schedules if "id" in item]
        if self.instance is None and supplied_ids:
            raise serializers.ValidationError("IDs de horários só podem ser usados ao atualizar um medicamento.")
        if self.instance is not None:
            allowed_ids = set(self.instance.schedules.values_list("id", flat=True))
            if any(schedule_id not in allowed_ids for schedule_id in supplied_ids):
                raise serializers.ValidationError("Um dos horários não pertence a este medicamento.")
            if len(supplied_ids) != len(set(supplied_ids)):
                raise serializers.ValidationError("O mesmo horário foi informado mais de uma vez.")
        return schedules

    def create(self, validated_data):
        schedules = validated_data.pop("schedules", [])
        medication = Medication.objects.create(user=self.context["request"].user, **validated_data)
        MedicationSchedule.objects.bulk_create([MedicationSchedule(medication=medication, **item) for item in schedules])
        return medication

    def update(self, instance, validated_data):
        schedules = validated_data.pop("schedules", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if schedules is not None:
            retained_ids = []
            existing = {schedule.pk: schedule for schedule in instance.schedules.all()}
            for item in schedules:
                schedule_id = item.pop("id", None)
                if schedule_id is None:
                    schedule = MedicationSchedule.objects.create(medication=instance, **item)
                else:
                    schedule = existing[schedule_id]
                    for field, value in item.items():
                        setattr(schedule, field, value)
                    schedule.save()
                retained_ids.append(schedule.pk)
            # Preserve dose history for schedules removed from the active regimen.
            instance.schedules.exclude(pk__in=retained_ids).update(active=False)
        return instance


class DoseLogSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source="schedule.medication.name", read_only=True)

    class Meta:
        model = DoseLog
        fields = ("id", "schedule", "medication_name", "scheduled_for", "status", "recorded_at")
        read_only_fields = ("id", "recorded_at")

    def validate_schedule(self, schedule):
        if schedule.medication.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Horário não encontrado.")
        return schedule


class HealthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthRecord
        fields = ("id", "kind", "title", "details", "occurred_on", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        return HealthRecord.objects.create(user=self.context["request"].user, **validated_data)


class MedicalDocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = MedicalDocument
        fields = ("id", "title", "file", "download_url", "uploaded_at")
        read_only_fields = ("id", "download_url", "uploaded_at")

    def validate_file(self, uploaded):
        if uploaded.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("O arquivo deve ter no máximo 10 MB.")

        suffix = uploaded.name.lower().rsplit(".", 1)[-1] if "." in uploaded.name else ""
        try:
            if suffix == "pdf":
                if uploaded.read(5) != b"%PDF-":
                    raise serializers.ValidationError("O conteúdo não corresponde a um PDF válido.")
            elif suffix in {"jpg", "jpeg", "png"}:
                with Image.open(uploaded) as image:
                    expected_format = "JPEG" if suffix in {"jpg", "jpeg"} else "PNG"
                    if image.format != expected_format:
                        raise serializers.ValidationError("A extensão não corresponde ao formato da imagem.")
                    image.verify()
            else:
                raise serializers.ValidationError("Envie um arquivo PDF, JPG ou PNG.")
        except (UnidentifiedImageError, OSError) as exc:
            raise serializers.ValidationError("O arquivo de imagem está inválido.") from exc
        finally:
            uploaded.seek(0)
        return uploaded

    def get_download_url(self, obj) -> str:
        request = self.context.get("request")
        path = reverse("document-download", kwargs={"pk": obj.pk})
        return request.build_absolute_uri(path) if request else path

    def create(self, validated_data):
        return MedicalDocument.objects.create(user=self.context["request"].user, **validated_data)
