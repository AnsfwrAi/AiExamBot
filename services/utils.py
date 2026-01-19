from datetime import datetime
from django.utils import timezone


def parse_dt(dt_str: str) -> datetime:
    naive = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
    return timezone.make_aware(naive, timezone.get_current_timezone())

