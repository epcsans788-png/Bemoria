import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from .models import MedicationSchedule

logger = logging.getLogger(__name__)


@shared_task
def queue_due_medication_reminders():
    """Find schedules due this minute; delivery channels can subscribe to this task later."""
    current = timezone.localtime()
    due = MedicationSchedule.objects.filter(
        active=True,
        medication__active=True,
        time__hour=current.hour,
        time__minute=current.minute,
    ).select_related("medication__user")
    reminders = [
        {
            "user_id": schedule.medication.user_id,
            "email": schedule.medication.user.email,
            "medication": schedule.medication.name,
            "dosage": schedule.medication.dosage,
            "time": schedule.time.strftime("%H:%M"),
        }
        for schedule in due
        if schedule.is_scheduled_for(current.date())
    ]
    for reminder in reminders:
        logger.info("Medication reminder due: user=%s medication=%s time=%s", reminder["user_id"], reminder["medication"], reminder["time"])
        if reminder["email"]:
            send_mail(
                subject=f"Lembrete Bemoria: {reminder['medication']} às {reminder['time']}",
                message=(
                    f"Olá! Este é um lembrete do Bemoria para conferir seu horário de "
                    f"{reminder['medication']} ({reminder['dosage']}) às {reminder['time']}.\n\n"
                    "Siga as orientações do profissional que acompanha você e registre a dose no seu checklist."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reminder["email"]],
                fail_silently=False,
            )
    return reminders
