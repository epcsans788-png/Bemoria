from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from .models import HealthRecord, Medication

User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="E-mail")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class MedicationForm(forms.ModelForm):
    schedule_times = forms.CharField(
        label="Horários",
        required=False,
        help_text="Separe os horários por vírgula. Exemplo: 08:00, 20:00",
        widget=forms.TextInput(attrs={"placeholder": "08:00, 20:00"}),
    )

    class Meta:
        model = Medication
        fields = ("name", "dosage", "instructions")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Nome do medicamento"}),
            "dosage": forms.TextInput(attrs={"placeholder": "Ex.: 1 comprimido"}),
            "instructions": forms.Textarea(attrs={"rows": 3, "placeholder": "Instruções pessoais (opcional)"}),
        }

    def clean_schedule_times(self):
        raw = self.cleaned_data.get("schedule_times", "")
        times = []
        for value in raw.split(","):
            value = value.strip()
            if not value:
                continue
            try:
                times.append(datetime.strptime(value, "%H:%M").time())
            except ValueError as exc:
                raise forms.ValidationError("Use o formato de 24 horas HH:MM, por exemplo 08:00.") from exc
        if len(times) != len(set(times)):
            raise forms.ValidationError("Remova horários repetidos.")
        return times


class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ("kind", "title", "details", "occurred_on")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Consulta de rotina"}),
            "details": forms.Textarea(attrs={"rows": 4, "placeholder": "Anotações pessoais (opcional)"}),
            "occurred_on": forms.DateInput(attrs={"type": "date"}),
        }
