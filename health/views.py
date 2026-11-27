from datetime import datetime
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .forms import (
    HealthConditionForm, HealthProfileForm, HealthRecordForm, MedicalClinicForm,
    MedicalDocumentForm, MedicationForm, RegistrationForm,
)
from .models import (
    DoseLog, EducationalResource, HealthCondition, HealthProfile, HealthRecord,
    MedicalClinic, MedicalDocument, Medication, MedicationSchedule,
)


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        HealthProfile.objects.get_or_create(user=user)
        return redirect("dashboard")
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    medications = request.user.medications.filter(active=True).prefetch_related("schedules")
    records = request.user.health_records.all()[:4]
    dose_rows = []
    for medication in medications:
        for schedule in medication.schedules.filter(active=True):
            if not schedule.is_scheduled_for(today):
                continue
            scheduled_for = timezone.make_aware(datetime.combine(today, schedule.time))
            dose_log = DoseLog.objects.filter(schedule=schedule, scheduled_for=scheduled_for).first()
            dose_rows.append({
                "medication": medication,
                "schedule": schedule,
                "taken": bool(dose_log and dose_log.status == DoseLog.Status.TAKEN),
                "skipped": bool(dose_log and dose_log.status == DoseLog.Status.SKIPPED),
            })
    dose_rows.sort(key=lambda row: row["schedule"].time)
    pending_count = sum(not row["taken"] for row in dose_rows)
    return render(request, "health/dashboard.html", {
        "medications": medications,
        "records": records,
        "today": today,
        "dose_rows": dose_rows,
        "pending_count": pending_count,
        "profile": HealthProfile.objects.filter(user=request.user).first(),
    })


@login_required
def medication_list(request):
    medications = request.user.medications.filter(active=True).prefetch_related("schedules")
    return render(request, "health/medication_list.html", {"medications": medications})


@login_required
def medication_create(request):
    form = MedicationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        medication = form.save(commit=False)
        medication.user = request.user
        medication.save()
        weekdays = [int(day) for day in form.cleaned_data["schedule_weekdays"]]
        for time in form.cleaned_data["schedule_times"]:
            MedicationSchedule.objects.create(medication=medication, time=time, weekdays=weekdays)
        messages.success(request, "Medicamento cadastrado.")
        return redirect("medication-list")
    return render(request, "health/medication_form.html", {"form": form, "page_title": "Adicionar medicamento"})


@login_required
def medication_update(request, pk):
    medication = get_object_or_404(Medication, pk=pk, user=request.user, active=True)
    form = MedicationForm(request.POST or None, instance=medication)
    if request.method == "POST" and form.is_valid():
        medication = form.save()
        # Keep old schedules attached to their dose history; a changed regimen gets new schedule rows.
        medication.schedules.filter(active=True).update(active=False)
        weekdays = [int(day) for day in form.cleaned_data["schedule_weekdays"]]
        MedicationSchedule.objects.bulk_create([
            MedicationSchedule(medication=medication, time=value, weekdays=weekdays)
            for value in form.cleaned_data["schedule_times"]
        ])
        messages.success(request, "Medicamento atualizado.")
        return redirect("medication-list")
    return render(request, "health/medication_form.html", {"form": form, "page_title": "Editar medicamento", "medication": medication})


@login_required
def medication_delete(request, pk):
    medication = get_object_or_404(Medication, pk=pk, user=request.user)
    if request.method == "POST":
        medication.active = False
        medication.save(update_fields=["active"])
        messages.success(request, "Medicamento removido da lista ativa.")
        return redirect("medication-list")
    return render(request, "health/medication_confirm_delete.html", {"medication": medication})


@login_required
def mark_dose_taken(request, schedule_id):
    if request.method != "POST":
        return redirect("dashboard")
    schedule = get_object_or_404(MedicationSchedule, pk=schedule_id, medication__user=request.user, active=True)
    scheduled_for = timezone.make_aware(datetime.combine(timezone.localdate(), schedule.time))
    if request.POST.get("taken") == "true":
        DoseLog.objects.update_or_create(
            schedule=schedule,
            scheduled_for=scheduled_for,
            defaults={"status": DoseLog.Status.TAKEN},
        )
    else:
        DoseLog.objects.update_or_create(
            schedule=schedule,
            scheduled_for=scheduled_for,
            defaults={"status": DoseLog.Status.SKIPPED},
        )
    return redirect("dashboard")


@login_required
def health_record_list(request):
    records = request.user.health_records.all()
    return render(request, "health/record_list.html", {"records": records})


@login_required
def health_record_create(request):
    form = HealthRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.user = request.user
        record.save()
        messages.success(request, "Registro adicionado ao seu histórico.")
        return redirect("record-list")
    return render(request, "health/record_form.html", {"form": form})


@login_required
def dose_history(request):
    logs = DoseLog.objects.filter(schedule__medication__user=request.user).select_related("schedule__medication")[:100]
    return render(request, "health/dose_history.html", {"logs": logs})


@login_required
def profile(request):
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    form = HealthProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Seu perfil foi atualizado.")
        return redirect("profile")
    return render(request, "health/profile.html", {"form": form, "profile": profile})


@login_required
def profile_photo(request):
    profile = get_object_or_404(HealthProfile, user=request.user)
    if not profile.profile_photo:
        raise Http404
    suffix = profile.profile_photo.name.lower().rsplit(".", 1)[-1]
    content_type = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(suffix, "application/octet-stream")
    with profile.profile_photo.open("rb") as photo:
        return HttpResponse(photo.read(), content_type=content_type)


@login_required
def emergency_card(request):
    profile, _ = HealthProfile.objects.get_or_create(user=request.user)
    return render(request, "health/emergency.html", {"profile": profile})


@login_required
def medical_document_list(request):
    form = MedicalDocumentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        document = form.save(commit=False)
        document.user = request.user
        document.save()
        messages.success(request, "Documento adicionado com acesso privado.")
        return redirect("document-list")
    documents = request.user.medical_documents.all()
    return render(request, "health/documents.html", {"form": form, "documents": documents})


@login_required
def medical_document_download(request, pk):
    document = get_object_or_404(MedicalDocument, pk=pk, user=request.user)
    suffix = document.file.name.lower().rsplit(".", 1)[-1]
    content_type = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(suffix, "application/octet-stream")
    with document.file.open("rb") as stored_file:
        response = HttpResponse(stored_file.read(), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="documento-{document.pk}.{suffix}"'
    return response


@login_required
def medical_document_delete(request, pk):
    document = get_object_or_404(MedicalDocument, pk=pk, user=request.user)
    if request.method == "POST":
        document.file.delete(save=False)
        document.delete()
        messages.success(request, "Documento removido.")
    return redirect("document-list")


@login_required
def health_area(request):
    conditions = request.user.health_conditions.filter(active=True)
    resources = EducationalResource.objects.filter(active=True)
    condition_form = HealthConditionForm()
    if request.method == "POST":
        condition_form = HealthConditionForm(request.POST)
        if condition_form.is_valid():
            condition = condition_form.save(commit=False)
            condition.user = request.user
            condition.save()
            messages.success(request, "Condição adicionada ao seu acompanhamento.")
            return redirect("health-area")
    return render(request, "health/health_area.html", {"conditions": conditions, "resources": resources, "form": condition_form})


@login_required
def health_condition_delete(request, pk):
    condition = get_object_or_404(HealthCondition, pk=pk, user=request.user)
    if request.method == "POST":
        condition.delete()
        messages.success(request, "Condição removida do acompanhamento.")
    return redirect("health-area")


@login_required
def clinic_list(request):
    form = MedicalClinicForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        clinic = form.save(commit=False)
        clinic.user = request.user
        clinic.save()
        messages.success(request, "Clínica adicionada à sua lista.")
        return redirect("clinic-list")
    query = request.GET.get("q", "").strip()
    clinics = request.user.medical_clinics.all()
    if query:
        clinics = clinics.filter(Q(name__icontains=query) | Q(specialty__icontains=query) | Q(address__icontains=query))
    return render(request, "health/clinics.html", {"clinics": clinics, "form": form, "query": query})


@login_required
def clinic_delete(request, pk):
    clinic = get_object_or_404(MedicalClinic, pk=pk, user=request.user)
    if request.method == "POST":
        clinic.delete()
        messages.success(request, "Clínica removida da sua lista.")
    return redirect("clinic-list")
