from datetime import datetime, time as time_cls, timedelta
import re

from django.utils import timezone

from .models import Booking

MAX_BOOKING_DAYS_AHEAD = 7

_DAY_MAP = {
    'Пн': 0,
    'Вт': 1,
    'Ср': 2,
    'Чт': 3,
    'Пт': 4,
    'Сб': 5,
    'Вс': 6,
}

_RANGE_RE = re.compile(
    r'(?:(?P<days>Пн–Пт|Пн–Сб|Пн–Вс|Сб–Вс|Ежедневно|Пн\s*[-–]\s*Пт|Пн\s*[-–]\s*Сб|Пн\s*[-–]\s*Вс|Сб\s*[-–]\s*Вс)\s*·\s*)?'
    r'(?P<start>\d{1,2}:\d{2})\s*[–-]\s*(?P<end>\d{1,2}:\d{2})'
)


def parse_time_slot(value):
    value = (value or '').strip()
    for fmt in ('%H:%M', '%H:%M:%S'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue
    hour, minute = map(int, value.split(':', 1))
    return time_cls(hour=hour, minute=minute)


def _format_time(value):
    return value.strftime('%H:%M')


def booking_is_expired(booking, now=None):
    now = now or timezone.localtime(timezone.now())
    booking_date = booking.booking_date

    if booking_date < now.date():
        return True
    if booking_date > now.date():
        return False

    try:
        slot_time = parse_time_slot(booking.time_slot)
    except Exception:
        return False

    return (slot_time.hour, slot_time.minute) <= (now.hour, now.minute)


def expire_stale_bookings(profile=None):
    qs = Booking.objects.filter(status=Booking.STATUS_ACTIVE)
    if profile is not None:
        qs = qs.filter(profile=profile)

    now = timezone.localtime(timezone.now())
    expired_ids = []
    for booking in qs.only('id', 'booking_date', 'time_slot'):
        if booking_is_expired(booking, now=now):
            expired_ids.append(booking.id)

    if expired_ids:
        Booking.objects.filter(id__in=expired_ids).update(status=Booking.STATUS_EXPIRED)

    return len(expired_ids)


def booking_date_bounds():
    today = timezone.localdate()
    return today, today + timedelta(days=MAX_BOOKING_DAYS_AHEAD)


def is_bookable_date(booking_date):
    today, max_date = booking_date_bounds()
    return today <= booking_date <= max_date


def _parse_days(days_raw):
    days_raw = (days_raw or '').strip().replace('—', '–').replace('-', '–')
    if not days_raw or days_raw == 'Ежедневно':
        return set(range(7))

    for key, idx in _DAY_MAP.items():
        if days_raw == key:
            return {idx}

    if '–' in days_raw:
        start, end = [part.strip() for part in days_raw.split('–', 1)]
        if start in _DAY_MAP and end in _DAY_MAP:
            a, b = _DAY_MAP[start], _DAY_MAP[end]
            if a <= b:
                return set(range(a, b + 1))
            return set(list(range(a, 7)) + list(range(0, b + 1)))

    return set(range(7))


def _time_range_slots(start_time, end_time, step_minutes):
    start_dt = datetime.combine(timezone.localdate(), start_time)
    end_dt = datetime.combine(timezone.localdate(), end_time)

    if end_dt < start_dt:
        return []

    step_minutes = max(int(step_minutes or 60), 1)
    slots = []
    cursor = start_dt
    while cursor <= end_dt:
        slots.append(_format_time(cursor.time()))
        cursor += timedelta(minutes=step_minutes)

    return slots


def _parse_window_from_hours(working_hours, fallback_start=None, fallback_end=None):
    value = (working_hours or '').strip()
    match = _RANGE_RE.search(value)
    if match:
        try:
            start_time = parse_time_slot(match.group('start'))
            end_time = parse_time_slot(match.group('end'))
        except Exception:
            start_time = parse_time_slot(fallback_start or '11:00')
            end_time = parse_time_slot(fallback_end or '21:00')
        return start_time, end_time, _parse_days(match.group('days'))

    start_time = parse_time_slot(fallback_start or '11:00')
    end_time = parse_time_slot(fallback_end or '21:00')
    return start_time, end_time, set(range(7))


def available_time_slots(
    default_slots,
    occupied_slots,
    booking_date=None,
    today=None,
    allow_future_dates=False,
    working_hours=None,
    work_start_time=None,
    work_end_time=None,
    slot_step_minutes=60,
):
    start_time, end_time, allowed_days = _parse_window_from_hours(
        working_hours,
        fallback_start=work_start_time,
        fallback_end=work_end_time,
    )
    slots = _time_range_slots(start_time, end_time, slot_step_minutes)
    if not slots:
        slots = [slot for slot, _ in default_slots]

    slots = [slot for slot in slots if slot not in occupied_slots]

    if booking_date is None:
        return slots

    today = today or timezone.localdate()
    if booking_date < today or booking_date > today + timedelta(days=MAX_BOOKING_DAYS_AHEAD):
        return []

    if not allow_future_dates and booking_date != today:
        return []

    if booking_date.weekday() not in allowed_days:
        return []

    if booking_date == today:
        now = timezone.localtime(timezone.now()).time()
        slots = [slot for slot in slots if tuple(map(int, slot.split(':', 1))) > (now.hour, now.minute)]

    return slots
