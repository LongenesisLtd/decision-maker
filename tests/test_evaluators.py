import datetime
import pytest
from zoneinfo import ZoneInfo
from londec.evaluators import (
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
from tests.conftest import FIELD_MAP, dt, make_event


class TestEventHappened:
    def test_returns_created_at_when_event_exists(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        assert event_happened(1, events, FIELD_MAP) == created_at

    def test_returns_false_when_no_matching_event(self):
        assert event_happened(1, [], FIELD_MAP) is False

    def test_ignores_revoked_events(self):
        events = [make_event(1, consented_revoked_at=dt(2))]
        assert event_happened(1, events, FIELD_MAP) is False

    def test_returns_last_created_at_when_multiple(self):
        events = [make_event(1, created_at=dt(1)), make_event(1, created_at=dt(3))]
        assert event_happened(1, events, FIELD_MAP) == dt(3)


class TestEventNotHappened:
    def test_returns_true_when_no_event(self):
        assert event_not_happened(1, [], FIELD_MAP) is True

    def test_returns_false_when_event_exists(self):
        events = [make_event(1)]
        assert event_not_happened(1, events, FIELD_MAP) is False

    def test_returns_true_when_only_revoked_events(self):
        events = [make_event(1, consented_revoked_at=dt(2))]
        assert event_not_happened(1, events, FIELD_MAP) is True


class TestEventHappenedExactly:
    def test_returns_created_at_on_exact_count(self):
        events = [make_event(1, dt(1)), make_event(1, dt(2)), make_event(1, dt(3))]
        assert event_happened_exactly(1, 3, events, FIELD_MAP) == dt(3)

    def test_returns_false_when_count_differs(self):
        events = [make_event(1, dt(1)), make_event(1, dt(2))]
        assert event_happened_exactly(1, 3, events, FIELD_MAP) is False

    def test_returns_false_when_no_events(self):
        assert event_happened_exactly(1, 1, [], FIELD_MAP) is False


class TestEventHappenedFewerThan:
    def test_true_when_fewer(self):
        events = [make_event(1), make_event(1)]
        assert event_happened_fewer_than(1, 3, events, FIELD_MAP) is True

    def test_false_when_equal(self):
        events = [make_event(1), make_event(1), make_event(1)]
        assert event_happened_fewer_than(1, 3, events, FIELD_MAP) is False

    def test_false_when_more(self):
        events = [make_event(1)] * 4
        assert event_happened_fewer_than(1, 3, events, FIELD_MAP) is False


class TestEventHappenedAtLeast:
    def test_true_when_equal(self):
        events = [make_event(1)] * 3
        assert event_happened_at_least(1, 3, events, FIELD_MAP) is True

    def test_true_when_more(self):
        events = [make_event(1)] * 5
        assert event_happened_at_least(1, 3, events, FIELD_MAP) is True

    def test_false_when_fewer(self):
        events = [make_event(1), make_event(1)]
        assert event_happened_at_least(1, 3, events, FIELD_MAP) is False


class TestEventRevoked:
    def test_returns_revoked_at(self):
        revoked_at = dt(5)
        events = [make_event(1, consented_revoked_at=revoked_at)]
        assert event_revoked(1, events, FIELD_MAP) == revoked_at

    def test_returns_false_when_not_revoked(self):
        events = [make_event(1)]
        assert event_revoked(1, events, FIELD_MAP) is False

    def test_returns_false_when_no_events(self):
        assert event_revoked(1, [], FIELD_MAP) is False

    def test_returns_last_revoked_at_when_multiple(self):
        events = [
            make_event(1, consented_revoked_at=dt(2)),
            make_event(1, consented_revoked_at=dt(5)),
        ]
        assert event_revoked(1, events, FIELD_MAP) == dt(5)


class TestDelayPassed:
    def test_returns_target_datetime(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        expected = created_at + datetime.timedelta(days=7)
        assert delay_passed(1, 7, events, FIELD_MAP) == expected

    def test_returns_false_when_no_event(self):
        assert delay_passed(1, 7, [], FIELD_MAP) is False


class TestPayloadMatch:
    def test_exact_match_returns_created_at(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, q="yes")]
        assert payload_match("q", "yes", {}, events, FIELD_MAP, type_id=1) == created_at

    def test_no_match_returns_false(self):
        events = [make_event(1, q="no")]
        assert payload_match("q", "yes", {}, events, FIELD_MAP, type_id=1) is False

    def test_missing_key_returns_false(self):
        events = [make_event(1, other="yes")]
        assert payload_match("q", "yes", {}, events, FIELD_MAP, type_id=1) is False

    def test_no_event_returns_false(self):
        assert payload_match("q", "yes", {}, [], FIELD_MAP, type_id=1) is False

    def test_none_answer_match(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, q=None)]
        assert payload_match("q", None, {}, events, FIELD_MAP, type_id=1) == created_at

    def test_sub_type_gt(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, score="10")]
        assert payload_match("score", "5", {"sub_type": "gt"}, events, FIELD_MAP, type_id=1) == created_at

    def test_sub_type_gt_fails(self):
        events = [make_event(1, score="3")]
        assert payload_match("score", "5", {"sub_type": "gt"}, events, FIELD_MAP, type_id=1) is False

    def test_ignores_revoked_event(self):
        events = [make_event(1, q="yes", consented_revoked_at=dt(2))]
        assert payload_match("q", "yes", {}, events, FIELD_MAP, type_id=1) is False

    def test_uses_most_recent_event(self):
        newer = dt(3)
        events = [
            make_event(1, created_at=dt(1), q="old"),
            make_event(1, created_at=newer, q="new"),
        ]
        assert payload_match("q", "new", {}, events, FIELD_MAP, type_id=1) == newer

    def test_no_type_id_checks_last_event_of_any_type(self):
        created_at = dt(2)
        events = [
            make_event(1, created_at=dt(1), total="5"),
            make_event(2, created_at=created_at, total="10"),
        ]
        assert payload_match("total", "10", {}, events, FIELD_MAP) == created_at

    def test_no_type_id_ignores_revoked(self):
        events = [
            make_event(1, created_at=dt(1), total="5"),
            make_event(2, created_at=dt(2), total="10", consented_revoked_at=dt(3)),
        ]
        assert payload_match("total", "5", {}, events, FIELD_MAP) == dt(1)

    def test_no_events_with_no_type_id_returns_false(self):
        assert payload_match("total", "10", {}, [], FIELD_MAP) is False


class TestPayloadMatchSeqNum:
    def test_seq_num_0_is_most_recent(self):
        events = [make_event(1, created_at=dt(1), q="old"), make_event(1, created_at=dt(2), q="new")]
        assert payload_match("q", "new", {}, events, FIELD_MAP, type_id=1, seq_num=0) == dt(2)

    def test_seq_num_1_is_second_most_recent(self):
        events = [make_event(1, created_at=dt(1), q="old"), make_event(1, created_at=dt(2), q="new")]
        assert payload_match("q", "old", {}, events, FIELD_MAP, type_id=1, seq_num=1) == dt(1)

    def test_seq_num_out_of_range_returns_false(self):
        events = [make_event(1, q="yes")]
        assert payload_match("q", "yes", {}, events, FIELD_MAP, type_id=1, seq_num=5) is False

    def test_seq_num_skips_revoked_events(self):
        events = [
            make_event(1, created_at=dt(1), q="a"),
            make_event(1, created_at=dt(2), q="b", consented_revoked_at=dt(3)),
            make_event(1, created_at=dt(4), q="c"),
        ]
        assert payload_match("q", "c", {}, events, FIELD_MAP, type_id=1, seq_num=0) == dt(4)
        assert payload_match("q", "a", {}, events, FIELD_MAP, type_id=1, seq_num=1) == dt(1)

    def test_seq_num_1_without_type_id(self):
        events = [
            make_event(1, created_at=dt(1), total="5"),
            make_event(2, created_at=dt(2), total="10"),
        ]
        assert payload_match("total", "5", {}, events, FIELD_MAP, seq_num=1) == dt(1)


class TestLastEventTypeEquals:
    def test_most_recent_matches(self):
        events = [make_event(1, dt(1)), make_event(2, dt(2))]
        assert last_event_type_equals(2, 0, events, FIELD_MAP) == dt(2)

    def test_most_recent_does_not_match(self):
        events = [make_event(1, dt(1)), make_event(2, dt(2))]
        assert last_event_type_equals(1, 0, events, FIELD_MAP) is False

    def test_second_most_recent(self):
        events = [make_event(1, dt(1)), make_event(2, dt(2))]
        assert last_event_type_equals(1, 1, events, FIELD_MAP) == dt(1)

    def test_index_out_of_range_returns_false(self):
        events = [make_event(1)]
        assert last_event_type_equals(1, 5, events, FIELD_MAP) is False

    def test_no_events_returns_false(self):
        assert last_event_type_equals(1, 0, [], FIELD_MAP) is False


class TestAvailableOnDateRange:
    def test_within_range_returns_start_date(self):
        start = "2025-01-10"
        end = "2025-01-31"
        now = datetime.datetime(2025, 1, 15, tzinfo=ZoneInfo("UTC"))
        result = available_on_date_range(start, end, 0, now)
        assert result == datetime.datetime(2025, 1, 10, tzinfo=ZoneInfo("UTC"))

    def test_before_range_returns_start_date(self):
        start = "2025-01-15"
        end = "2025-01-31"
        now = datetime.datetime(2025, 1, 5, tzinfo=ZoneInfo("UTC"))
        result = available_on_date_range(start, end, 0, now)
        assert result == datetime.datetime(2025, 1, 15, tzinfo=ZoneInfo("UTC"))

    def test_after_range_returns_false(self):
        start = "2025-01-01"
        end = "2025-01-10"
        now = datetime.datetime(2025, 1, 20, tzinfo=ZoneInfo("UTC"))
        assert available_on_date_range(start, end, 0, now) is False

    def test_no_start_date_returns_true(self):
        end = "2025-12-31"
        now = datetime.datetime(2025, 6, 1, tzinfo=ZoneInfo("UTC"))
        assert available_on_date_range(None, end, 0, now) is True

    def test_no_end_date_always_available(self):
        start = "2025-01-01"
        now = datetime.datetime(2030, 1, 1, tzinfo=ZoneInfo("UTC"))
        result = available_on_date_range(start, None, 0, now)
        assert result == datetime.datetime(2025, 1, 1, tzinfo=ZoneInfo("UTC"))

    def test_timezone_offset_applied(self):
        now = datetime.datetime(2025, 1, 15, tzinfo=ZoneInfo("UTC"))
        result = available_on_date_range("2025-01-10", None, 120, now)
        expected = datetime.datetime(2025, 1, 10, 2, 0, tzinfo=ZoneInfo("UTC"))
        assert result == expected


class TestTakenRecently:
    def test_taken_within_window_returns_created_at(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        now = created_at + datetime.timedelta(days=3)
        assert taken_recently(1, "days", 7, events, FIELD_MAP, now) == created_at

    def test_taken_outside_window_returns_false(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        now = created_at + datetime.timedelta(days=8)
        assert taken_recently(1, "days", 7, events, FIELD_MAP, now) is False

    def test_hours_duration_type(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at)]
        now = created_at + datetime.timedelta(hours=2)
        assert taken_recently(1, "hours", 3, events, FIELD_MAP, now) == created_at

    def test_no_events_returns_false(self):
        assert taken_recently(1, "days", 7, [], FIELD_MAP) is False

    def test_ignores_revoked_events(self):
        created_at = dt(1)
        events = [make_event(1, created_at=created_at, consented_revoked_at=dt(2))]
        now = created_at + datetime.timedelta(days=1)
        assert taken_recently(1, "days", 7, events, FIELD_MAP, now) is False
