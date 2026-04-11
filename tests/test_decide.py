import datetime
import pytest
from zoneinfo import ZoneInfo
from londec import decide, FieldMap
from tests.conftest import FIELD_MAP, dt, make_event


class TestDecideNoType:
    def test_condition_without_type_returns_true(self):
        assert decide({"blank": True}, [], FIELD_MAP) is True

    def test_empty_condition_returns_true(self):
        assert decide({}, [], FIELD_MAP) is True


class TestDecideSurveyConditions:
    def test_event_happened(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        assert decide({"type": "event_happened", "activity_id": 1}, events, FIELD_MAP) == created_at

    def test_event_happened_no_submission(self):
        assert decide({"type": "event_happened", "activity_id": 1}, [], FIELD_MAP) is False

    def test_event_not_happened_true(self):
        assert decide({"type": "event_not_happened", "activity_id": 1}, [], FIELD_MAP) is True

    def test_event_not_happened_false(self):
        events = [make_event(1)]
        assert decide({"type": "event_not_happened", "activity_id": 1}, events, FIELD_MAP) is False

    def test_event_happened_exactly(self):
        events = [make_event(1, dt(i)) for i in range(1, 4)]
        assert decide({"type": "event_happened_exactly", "activity_id": 1, "x": 3}, events, FIELD_MAP) == dt(3)

    def test_event_happened_exactly_no_match(self):
        events = [make_event(1), make_event(1)]
        assert decide({"type": "event_happened_exactly", "activity_id": 1, "x": 3}, events, FIELD_MAP) is False

    def test_event_happened_fewer_than_true(self):
        events = [make_event(1), make_event(1)]
        assert decide({"type": "event_happened_fewer_than", "activity_id": 1, "x": 3}, events, FIELD_MAP) is True

    def test_event_happened_fewer_than_false(self):
        events = [make_event(1)] * 3
        assert decide({"type": "event_happened_fewer_than", "activity_id": 1, "x": 3}, events, FIELD_MAP) is False

    def test_event_happened_at_least_true(self):
        events = [make_event(1)] * 3
        assert decide({"type": "event_happened_at_least", "activity_id": 1, "x": 3}, events, FIELD_MAP) is True

    def test_event_happened_at_least_false(self):
        events = [make_event(1), make_event(1)]
        assert decide({"type": "event_happened_at_least", "activity_id": 1, "x": 3}, events, FIELD_MAP) is False

    def test_event_revoked_returns_revoked_at(self):
        revoked_at = dt(5)
        events = [make_event(1, consented_revoked_at=revoked_at)]
        assert decide({"type": "event_revoked", "activity_id": 1}, events, FIELD_MAP) == revoked_at

    def test_event_revoked_returns_false_when_not_revoked(self):
        events = [make_event(1)]
        assert decide({"type": "event_revoked", "activity_id": 1}, events, FIELD_MAP) is False


class TestDecideDelay:
    def test_delay_returns_target_date(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        expected = created_at + datetime.timedelta(days=7)
        assert decide({"type": "delay", "activity_id": 1, "days": 7}, events, FIELD_MAP) == expected

    def test_delay_returns_false_with_no_events(self):
        assert decide({"type": "delay", "activity_id": 1, "days": 7}, [], FIELD_MAP) is False


class TestDecidePayloadMatch:
    def test_exact_match(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, mood="good")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "mood", "answer": "good"}
        assert decide(condition, events, FIELD_MAP) == created_at

    def test_no_match(self):
        events = [make_event(1, mood="bad")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "mood", "answer": "good"}
        assert decide(condition, events, FIELD_MAP) is False

    def test_sub_type(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, score="10")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "score", "answer": "5", "sub_type": "gte"}
        assert decide(condition, events, FIELD_MAP) == created_at

    def test_without_activity_id(self):
        created_at = dt(2)
        events = [
            make_event(1, created_at=dt(1), risk="low"),
            make_event(2, created_at=created_at, risk="high"),
        ]
        condition = {"type": "payload_match", "key": "risk", "answer": "high"}
        assert decide(condition, events, FIELD_MAP) == created_at

    def test_seq_num_1(self):
        events = [make_event(1, created_at=dt(1), mood="old"), make_event(1, created_at=dt(2), mood="new")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "mood", "answer": "old", "seq_num": 1}
        assert decide(condition, events, FIELD_MAP) == dt(1)

    def test_seq_num_as_string(self):
        events = [make_event(1, created_at=dt(1), mood="old"), make_event(1, created_at=dt(2), mood="new")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "mood", "answer": "old", "seq_num": "1"}
        assert decide(condition, events, FIELD_MAP) == dt(1)

    def test_seq_num_out_of_range(self):
        events = [make_event(1, mood="yes")]
        condition = {"type": "payload_match", "activity_id": 1, "key": "mood", "answer": "yes", "seq_num": 5}
        assert decide(condition, events, FIELD_MAP) is False


class TestDecideLastEventTypeEquals:
    def test_most_recent_matches(self):
        events = [make_event(1, dt(1)), make_event(2, dt(2))]
        condition = {"type": "last_event_type_equals", "activity_id": 2, "seq_num": 0}
        assert decide(condition, events, FIELD_MAP) == dt(2)

    def test_most_recent_does_not_match(self):
        events = [make_event(1, dt(1)), make_event(2, dt(2))]
        condition = {"type": "last_event_type_equals", "activity_id": 1, "seq_num": 0}
        assert decide(condition, events, FIELD_MAP) is False


class TestDecideAvailableOnDateRange:
    def test_within_range(self):
        now = datetime.datetime(2025, 1, 20, tzinfo=ZoneInfo("UTC"))
        condition = {
            "type": "available_on_date_range",
            "start_date": "2025-01-15",
            "end_date": "2025-01-31",
            "timezone_offset": 0,
        }
        result = decide(condition, [], FIELD_MAP, now=now)
        assert result == datetime.datetime(2025, 1, 15, tzinfo=ZoneInfo("UTC"))

    def test_after_range(self):
        now = datetime.datetime(2025, 2, 1, 0, 1, tzinfo=ZoneInfo("UTC"))
        condition = {
            "type": "available_on_date_range",
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "timezone_offset": 0,
        }
        assert decide(condition, [], FIELD_MAP, now=now) is False


class TestDecideTakenRecently:
    def test_within_window(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        now = created_at + datetime.timedelta(days=3)
        condition = {"type": "is_taken_recently", "activity_id": 1, "duration_type": "days", "duration": 7}
        assert decide(condition, events, FIELD_MAP, now=now) == created_at

    def test_outside_window(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        now = created_at + datetime.timedelta(days=8)
        condition = {"type": "is_taken_recently", "activity_id": 1, "duration_type": "days", "duration": 7}
        assert decide(condition, events, FIELD_MAP, now=now) is False


class TestDecideLogicalOperators:
    def test_and_all_true(self):
        events = [make_event(1, dt(1)), make_event(2, dt(3))]
        condition = {
            "type": "AND",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == dt(3)

    def test_and_one_false(self):
        events = [make_event(1, dt(1))]
        condition = {
            "type": "AND",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, events, FIELD_MAP) is False

    def test_or_one_true(self):
        events = [make_event(1, dt(1))]
        condition = {
            "type": "OR",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == dt(1)

    def test_or_all_false(self):
        condition = {
            "type": "OR",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, [], FIELD_MAP) is False

    def test_min_and(self):
        events = [make_event(1, dt(1)), make_event(2, dt(5))]
        condition = {
            "type": "MIN_AND",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == dt(1)

    def test_max_or(self):
        events = [make_event(1, dt(1)), make_event(2, dt(5))]
        condition = {
            "type": "MAX_OR",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "event_happened", "activity_id": 2},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == dt(5)


class TestDecideWorkflows:
    def test_event_then_delay(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        condition = {
            "type": "AND",
            "list": [
                {"type": "event_happened", "activity_id": 1},
                {"type": "delay", "activity_id": 1, "days": 7},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == created_at + datetime.timedelta(days=7)

    def test_nested_or_inside_and(self):
        events = [make_event(1, dt(1)), make_event(3, dt(5))]
        condition = {
            "type": "AND",
            "list": [
                {
                    "type": "OR",
                    "list": [
                        {"type": "event_happened", "activity_id": 1},
                        {"type": "event_happened", "activity_id": 2},
                    ],
                },
                {"type": "event_happened", "activity_id": 3},
            ],
        }
        assert decide(condition, events, FIELD_MAP) == dt(5)

    def test_unknown_type_returns_none(self):
        assert decide({"type": "unknown_type"}, [], FIELD_MAP) is None
