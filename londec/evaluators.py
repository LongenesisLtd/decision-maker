import datetime
import logging
from zoneinfo import ZoneInfo

from mathjson_solver import MathJSONException

from .exp_types import exp_types
from .field_map import FieldMap

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _events_of_type(events: list[dict], type_id, field_map: FieldMap) -> list[dict]:
    return [e for e in events if e.get(field_map.type_id) == type_id]


def _active_events_of_type(events: list[dict], type_id, field_map: FieldMap) -> list[dict]:
    """Events matching type_id that have not been revoked."""
    return [
        e for e in _events_of_type(events, type_id, field_map)
        if e.get(field_map.revoked_at) is None
    ]


def _active_events(events: list[dict], field_map: FieldMap) -> list[dict]:
    """All non-revoked events regardless of type."""
    return [e for e in events if e.get(field_map.revoked_at) is None]


def _last_created_at(events: list[dict], type_id, field_map: FieldMap) -> datetime.datetime | None:
    active = _active_events_of_type(events, type_id, field_map)
    if active:
        return active[-1].get(field_map.created_at)
    return None


def _times_happened(events: list[dict], type_id, field_map: FieldMap) -> int:
    return len(_active_events_of_type(events, type_id, field_map))


def _event_at(active: list[dict], seq_num: int) -> dict | None:
    """Return the event at position seq_num (0 = most recent) from an already-filtered list."""
    try:
        return list(reversed(active))[seq_num]
    except IndexError:
        return None


def _key_match(
    event: dict,
    key: str,
    answer,
    condition: dict,
    field_map: FieldMap,
) -> bool | datetime.datetime:
    """Check whether a key/answer matches in the flat event dict."""
    created_at = event.get(field_map.created_at)

    if "sub_type" in condition:
        try:
            sub_type = condition["sub_type"]
            if sub_type not in exp_types:
                return False
            value = event.get(key, "certainly not the answer you are looking for")
            if exp_types[sub_type](value, answer):
                return created_at
            return False
        except MathJSONException as e:
            logger.debug(f"key match failed: {e}")
            return False
        except Exception as e:
            logger.error(e)
            return False
    else:
        if key not in event:
            return False
        if event.get(key) == answer:
            return created_at
        return False


# ---------------------------------------------------------------------------
# Leaf evaluators
# ---------------------------------------------------------------------------

def event_happened(
    type_id, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    created_at = _last_created_at(events, type_id, field_map)
    return created_at if created_at else False


def event_not_happened(type_id, events: list[dict], field_map: FieldMap) -> bool:
    return _times_happened(events, type_id, field_map) == 0


def event_happened_exactly(
    type_id, x: int, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    last_created_at = _last_created_at(events, type_id, field_map)
    if last_created_at and _times_happened(events, type_id, field_map) == x:
        return last_created_at
    return False


def event_happened_fewer_than(
    type_id, x: int, events: list[dict], field_map: FieldMap
) -> bool:
    return _times_happened(events, type_id, field_map) < x


def event_happened_at_least(
    type_id, x: int, events: list[dict], field_map: FieldMap
) -> bool:
    return _times_happened(events, type_id, field_map) >= x


def event_revoked(
    type_id, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    revoked = [
        e for e in _events_of_type(events, type_id, field_map)
        if e.get(field_map.revoked_at) is not None
    ]
    if not revoked:
        return False
    return revoked[-1].get(field_map.revoked_at)


def delay_passed(
    type_id, delay_days: int, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    """Return the datetime when the delay will have passed, or False if no event exists."""
    last_created_at = _last_created_at(events, type_id, field_map)
    if last_created_at:
        return last_created_at + datetime.timedelta(days=delay_days)
    return False


def payload_match(
    key: str,
    answer,
    condition: dict,
    events: list[dict],
    field_map: FieldMap,
    type_id=None,
    seq_num: int = 0,
) -> bool | datetime.datetime:
    """Match a key/answer against a flat event dict.

    If type_id is given, only events of that type are considered.
    If type_id is None, all non-revoked events are considered.
    """
    active = (
        _active_events_of_type(events, type_id, field_map)
        if type_id is not None
        else _active_events(events, field_map)
    )
    event = _event_at(active, seq_num)
    if event is None:
        return False
    return _key_match(event, key, answer, condition, field_map)


def last_event_type_equals(
    type_id, seq_num: int, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    """Return created_at if the nth-most-recent event (0 = most recent) matches type_id."""
    events_reversed = list(reversed(events))
    try:
        event = events_reversed[seq_num]
        if event.get(field_map.type_id) == type_id:
            return event.get(field_map.created_at)
        return False
    except IndexError:
        return False


def available_on_date_range(
    start_date: str | None,
    end_date: str | None,
    timezone_offset: int,
    now: datetime.datetime | None = None,
) -> bool | datetime.datetime:
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    s_dt = None
    end_ok = True

    if start_date:
        dt = datetime.datetime.fromisoformat(start_date)
        s_dt = (
            datetime.datetime(dt.year, dt.month, dt.day, tzinfo=ZoneInfo("UTC"))
            + datetime.timedelta(minutes=timezone_offset)
        )

    if end_date:
        dt = datetime.datetime.fromisoformat(end_date)
        e_dt = (
            datetime.datetime(dt.year, dt.month, dt.day, tzinfo=ZoneInfo("UTC"))
            + datetime.timedelta(hours=24)
            + datetime.timedelta(minutes=timezone_offset)
        )
        end_ok = now <= e_dt

    if end_ok:
        if not s_dt:
            return True
        return s_dt
    return False


def taken_recently(
    type_id,
    duration_type: str,
    duration: int,
    events: list[dict],
    field_map: FieldMap,
    now: datetime.datetime | None = None,
) -> bool | datetime.datetime:
    active = _active_events_of_type(events, type_id, field_map)
    if not active:
        return False

    last_created_at = active[-1].get(field_map.created_at)

    if duration_type == "days":
        delta = datetime.timedelta(days=duration)
    else:
        delta = datetime.timedelta(hours=duration)

    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    if now <= last_created_at + delta:
        return last_created_at
    return False
