import logging

from celery import shared_task
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
    ).select_related("medication")
    reminders = [
        {"user_id": schedule.medication.user_id, "medication": schedule.medication.name, "time": schedule.time.strftime("%H:%M")}
        for schedule in due
        if schedule.is_scheduled_for(current.date())
    ]
    for reminder in reminders:
        logger.info("Medication reminder due: user=%s medication=%s time=%s", reminder["user_id"], reminder["medication"], reminder["time"])
    return reminders
