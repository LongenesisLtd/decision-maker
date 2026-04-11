import datetime

from .combinators import all_or_date_max, all_or_date_min, any_or_date_min, any_or_date_max
from .evaluators import (
    event_happened,
    event_not_happened,
    event_happened_exactly,
    event_happened_fewer_than,
    event_happened_at_least,
    event_revoked,
    delay_passed,
    payload_match,
    last_event_type_equals,
    available_on_date_range,
    taken_recently,
)
from .field_map import FieldMap


def decide(
    condition: dict,
    events: list[dict],
    field_map: FieldMap,
    now: datetime.datetime | None = None,
) -> bool | datetime.datetime:
    """Evaluate a condition tree against an ordered history of events.

    Returns False if the condition is not satisfied, or the datetime it was
    first satisfied (enabling callers to schedule follow-up actions).
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)

    if "type" not in condition:
        return True

    def _recurse(c):
        return decide(c, events, field_map, now)

    match condition["type"]:
        case "event_happened":
            return event_happened(condition["activity_id"], events, field_map)

        case "event_not_happened":
            return event_not_happened(condition["activity_id"], events, field_map)

        case "event_happened_exactly":
            return event_happened_exactly(condition["activity_id"], condition["x"], events, field_map)

        case "event_happened_fewer_than":
            return event_happened_fewer_than(condition["activity_id"], condition["x"], events, field_map)

        case "event_happened_at_least":
            return event_happened_at_least(condition["activity_id"], condition["x"], events, field_map)

        case "event_revoked":
            return event_revoked(condition["activity_id"], events, field_map)

        case "delay":
            return delay_passed(condition["activity_id"], condition["days"], events, field_map)

        case "payload_match":
            return payload_match(
                condition["key"],
                condition.get("answer"),
                condition,
                events,
                field_map,
                type_id=condition.get("activity_id"),
                seq_num=int(condition.get("seq_num", 0)),
            )

        case "last_event_type_equals":
            return last_event_type_equals(
                condition["activity_id"],
                condition["seq_num"],
                events,
                field_map,
            )

        case "available_on_date_range":
            return available_on_date_range(
                condition.get("start_date"),
                condition.get("end_date"),
                condition["timezone_offset"],
                now,
            )

        case "is_taken_recently":
            return taken_recently(
                condition["activity_id"],
                condition["duration_type"],
                condition["duration"],
                events,
                field_map,
                now,
            )

        case "AND" | "MAX_AND":
            return all_or_date_max([_recurse(c) for c in condition["list"]])

        case "OR" | "MIN_OR":
            return any_or_date_min([_recurse(c) for c in condition["list"]])

        case "MIN_AND":
            return all_or_date_min([_recurse(c) for c in condition["list"]])

        case "MAX_OR":
            return any_or_date_max([_recurse(c) for c in condition["list"]])

        case _:
            return None
