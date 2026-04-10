import datetime
import logging
from zoneinfo import ZoneInfo

from mathjson_solver import MathJSONException

from .exp_types import exp_types
from .field_map import FieldMap, resolve

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _events_of_type(events: list[dict], type_id, field_map: FieldMap) -> list[dict]:
    return [
        e for e in events
        if resolve(e, field_map.type_id, field_map.separator) == type_id
    ]


def _active_events_of_type(events: list[dict], type_id, field_map: FieldMap) -> list[dict]:
    """Events matching type_id that have not been revoked."""
    return [
        e for e in _events_of_type(events, type_id, field_map)
        if resolve(e, field_map.revoked_at, field_map.separator) is None
    ]


def _last_created_at(events: list[dict], type_id, field_map: FieldMap) -> datetime.datetime | None:
    active = _active_events_of_type(events, type_id, field_map)
    if active:
        return resolve(active[-1], field_map.created_at, field_map.separator)
    return None


def _times_happened(events: list[dict], type_id, field_map: FieldMap) -> int:
    return len(_active_events_of_type(events, type_id, field_map))


def _match_in_payload(
    event: dict,
    question: str,
    answer,
    condition: dict,
    field_map: FieldMap,
    payload_name: str,
) -> bool | datetime.datetime:
    """Check whether a question/answer matches within the named payload namespace."""
    payload_path = field_map.payloads[payload_name]
    payload = resolve(event, payload_path, field_map.separator) or {}
    created_at = resolve(event, field_map.created_at, field_map.separator)

    if "sub_type" in condition:
        try:
            sub_type = condition["sub_type"]
            if sub_type not in exp_types:
                return False
            value = payload.get(question, "certainly not the answer you are looking for")
            if exp_types[sub_type](value, answer):
                return created_at
            return False
        except MathJSONException as e:
            logger.debug(f"payload match failed: {e}")
            return False
        except Exception as e:
            logger.error(e)
            return False
    else:
        if question not in payload:
            return False
        if payload.get(question) == answer:
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
        if resolve(e, field_map.revoked_at, field_map.separator) is not None
    ]
    if not revoked:
        return False
    return resolve(revoked[-1], field_map.revoked_at, field_map.separator)


def delay_passed(
    type_id, delay_days: int, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    """Return the datetime when the delay will have passed, or False if no event exists."""
    last_created_at = _last_created_at(events, type_id, field_map)
    if last_created_at:
        return last_created_at + datetime.timedelta(days=delay_days)
    return False


def _event_at(active: list[dict], seq_num: int) -> dict | None:
    """Return the event at position seq_num (0 = most recent) from an already-filtered list."""
    try:
        return list(reversed(active))[seq_num]
    except IndexError:
        return None


def payload_match_data(
    type_id,
    question: str,
    answer,
    condition: dict,
    events: list[dict],
    field_map: FieldMap,
    seq_num: int = 0,
) -> bool | datetime.datetime:
    active = _active_events_of_type(events, type_id, field_map)
    event = _event_at(active, seq_num)
    if event is None:
        return False
    return _match_in_payload(event, question, answer, condition, field_map, "data")


def payload_match_derived(
    question: str,
    answer,
    condition: dict,
    events: list[dict],
    field_map: FieldMap,
    type_id=None,
    seq_num: int = 0,
) -> bool | datetime.datetime:
    """Match against the derived payload at seq_num.

    If type_id is given, only events of that type are considered.
    If type_id is None, all non-revoked events are considered — the caller
    (adapter) is responsible for merging all derived sources into the payload.
    """
    if type_id is not None:
        active = _active_events_of_type(events, type_id, field_map)
    else:
        active = [
            e for e in events
            if resolve(e, field_map.revoked_at, field_map.separator) is None
        ]
    event = _event_at(active, seq_num)
    if event is None:
        return False
    return _match_in_payload(event, question, answer, condition, field_map, "derived")


def last_event_type_equals(
    type_id, seq_num: int, events: list[dict], field_map: FieldMap
) -> bool | datetime.datetime:
    """Return created_at if the nth-most-recent event (0 = most recent) matches type_id."""
    events_reversed = list(reversed(events))
    try:
        event = events_reversed[seq_num]
        if resolve(event, field_map.type_id, field_map.separator) == type_id:
            return resolve(event, field_map.created_at, field_map.separator)
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

    last_created_at = resolve(active[-1], field_map.created_at, field_map.separator)

    if duration_type == "days":
        delta = datetime.timedelta(days=duration)
    else:
        delta = datetime.timedelta(hours=duration)

    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    if now <= last_created_at + delta:
        return last_created_at
    return False
