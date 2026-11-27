from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.files.uploadedfile import UploadedFile
from datetime import datetime
from django.utils import timezone
from PIL import Image, UnidentifiedImageError
from .models import HealthCondition, HealthProfile, HealthRecord, MedicalClinic, MedicalDocument, Medication

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
    WEEKDAYS = [("0", "Seg"), ("1", "Ter"), ("2", "Qua"), ("3", "Qui"), ("4", "Sex"), ("5", "Sáb"), ("6", "Dom")]
    schedule_times = forms.CharField(
        label="Horários",
        required=False,
        help_text="Separe os horários por vírgula. Exemplo: 08:00, 20:00",
        widget=forms.TextInput(attrs={"placeholder": "08:00, 20:00"}),
    )
    schedule_weekdays = forms.MultipleChoiceField(
        label="Dias da semana", choices=WEEKDAYS, required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Se nenhum dia for selecionado, o horário vale todos os dias.",
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
        if not times:
            raise forms.ValidationError("Informe pelo menos um horário para o medicamento.")
        return times

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            schedules = list(self.instance.schedules.filter(active=True))
            self.fields["schedule_times"].initial = ", ".join(item.time.strftime("%H:%M") for item in schedules)
            self.fields["schedule_weekdays"].initial = [str(day) for day in (schedules[0].weekdays if schedules else [])]


class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ("kind", "title", "details", "occurred_on")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex.: Consulta de rotina"}),
            "details": forms.Textarea(attrs={"rows": 4, "placeholder": "Anotações pessoais (opcional)"}),
            "occurred_on": forms.DateInput(attrs={"type": "date"}),
        }


class HealthProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome", max_length=150, required=False)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail")
    remove_profile_photo = forms.BooleanField(label="Remover foto atual", required=False)

    class Meta:
        model = HealthProfile
        fields = (
            "phone", "birth_date", "blood_type", "allergies", "height_cm", "weight_kg",
            "emergency_contact_name", "emergency_contact_phone", "emergency_notes", "profile_photo",
        )
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "allergies": forms.Textarea(attrs={"rows": 3, "placeholder": "Informe alergias conhecidas ou deixe em branco."}),
            "emergency_notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Informações que você quer deixar acessíveis em uma emergência."}),
            "profile_photo": forms.FileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields["first_name"].initial = user.first_name
        self.fields["last_name"].initial = user.last_name
        self.fields["email"].initial = user.email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get("profile_photo")
        if not isinstance(photo, UploadedFile):
            return photo
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError("A foto deve ter no máximo 5 MB.")
        try:
            with Image.open(photo) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise forms.ValidationError("Envie uma foto JPG, PNG ou WebP.")
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise forms.ValidationError("A imagem enviada está inválida.") from exc
        finally:
            photo.seek(0)
        return photo

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date and birth_date > timezone.localdate():
            raise forms.ValidationError("A data de nascimento não pode estar no futuro.")
        return birth_date

    def save(self, commit=True):
        old_file = self.instance.profile_photo if self.instance.pk and self.instance.profile_photo else None
        old_photo = old_file.name if old_file else ""
        uploaded_photo = self.cleaned_data.get("profile_photo")
        has_new_photo = isinstance(uploaded_photo, UploadedFile)
        profile = super().save(commit=False)
        if self.cleaned_data.get("remove_profile_photo") and not has_new_photo:
            profile.profile_photo = ""
        self.user.first_name = self.cleaned_data["first_name"]
        self.user.last_name = self.cleaned_data["last_name"]
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save(update_fields=["first_name", "last_name", "email"])
            profile.save()
            if old_photo and profile.profile_photo.name != old_photo:
                old_file.delete(save=False)
        return profile


class MedicalDocumentForm(forms.ModelForm):
    class Meta:
        model = MedicalDocument
        fields = ("title", "file")
        widgets = {"file": forms.FileInput(attrs={"accept": ".pdf,.jpg,.jpeg,.png"})}

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > 10 * 1024 * 1024:
            raise forms.ValidationError("O arquivo deve ter no máximo 10 MB.")
        suffix = uploaded.name.lower().rsplit(".", 1)[-1] if "." in uploaded.name else ""
        try:
            if suffix == "pdf":
                if uploaded.read(5) != b"%PDF-":
                    raise forms.ValidationError("O conteúdo não corresponde a um PDF válido.")
            elif suffix in {"jpg", "jpeg", "png"}:
                with Image.open(uploaded) as image:
                    expected = "JPEG" if suffix in {"jpg", "jpeg"} else "PNG"
                    if image.format != expected:
                        raise forms.ValidationError("A extensão não corresponde ao formato da imagem.")
                    image.verify()
            else:
                raise forms.ValidationError("Envie um arquivo PDF, JPG ou PNG.")
        except (UnidentifiedImageError, OSError) as exc:
            raise forms.ValidationError("O arquivo de imagem está inválido.") from exc
        finally:
            uploaded.seek(0)
        return uploaded


class HealthConditionForm(forms.ModelForm):
    class Meta:
        model = HealthCondition
        fields = ("name", "notes", "diagnosed_on", "active")
        widgets = {"diagnosed_on": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 3})}


class MedicalClinicForm(forms.ModelForm):
    website = forms.URLField(label="Site", required=False, assume_scheme="https")

    class Meta:
        model = MedicalClinic
        fields = ("name", "specialty", "phone", "address", "website", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
