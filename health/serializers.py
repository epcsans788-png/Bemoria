from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import DoseLog, HealthRecord, MedicalDocument, Medication, MedicationSchedule

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=10)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MedicationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationSchedule
        fields = ("id", "time", "weekdays", "active")


class MedicationSerializer(serializers.ModelSerializer):
    schedules = MedicationScheduleSerializer(many=True, required=False)

    class Meta:
        model = Medication
        fields = ("id", "name", "dosage", "instructions", "active", "created_at", "schedules")
        read_only_fields = ("id", "created_at")

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
            instance.schedules.all().delete()
            MedicationSchedule.objects.bulk_create([MedicationSchedule(medication=instance, **item) for item in schedules])
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
    class Meta:
        model = MedicalDocument
        fields = ("id", "title", "file", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")

    def create(self, validated_data):
        return MedicalDocument.objects.create(user=self.context["request"].user, **validated_data)
