from datetime import datetime
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import redirect, render
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .forms import HealthRecordForm, MedicationForm, RegistrationForm
from .models import DoseLog, HealthRecord, Medication, MedicationSchedule


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
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
            dose_rows.append({"medication": medication, "schedule": schedule, "taken": bool(dose_log and dose_log.status == DoseLog.Status.TAKEN)})
    dose_rows.sort(key=lambda row: row["schedule"].time)
    return render(request, "health/dashboard.html", {
        "medications": medications,
        "records": records,
        "today": today,
        "dose_rows": dose_rows,
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
        for time in form.cleaned_data["schedule_times"]:
            MedicationSchedule.objects.create(medication=medication, time=time)
        messages.success(request, "Medicamento cadastrado.")
        return redirect("medication-list")
    return render(request, "health/medication_form.html", {"form": form})


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
        DoseLog.objects.filter(schedule=schedule, scheduled_for=scheduled_for).delete()
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
