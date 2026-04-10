import datetime
import pytest
from zoneinfo import ZoneInfo
from londec.combinators import all_or_date_max, all_or_date_min, any_or_date_min, any_or_date_max


def dt(day):
    return datetime.datetime(2025, 1, day, 12, 0, tzinfo=ZoneInfo("UTC"))


class TestAllOrDateMax:
    def test_all_true_no_datetimes(self):
        assert all_or_date_max([True, True]) is True

    def test_any_false_returns_false(self):
        assert all_or_date_max([True, False]) is False

    def test_all_false_returns_false(self):
        assert all_or_date_max([False, False]) is False

    def test_returns_max_datetime(self):
        assert all_or_date_max([dt(1), dt(3), dt(2)]) == dt(3)

    def test_mixed_bool_and_datetime(self):
        assert all_or_date_max([True, dt(5)]) == dt(5)

    def test_false_with_datetimes_returns_false(self):
        assert all_or_date_max([dt(1), False]) is False


class TestAllOrDateMin:
    def test_all_true_no_datetimes(self):
        assert all_or_date_min([True, True]) is True

    def test_any_false_returns_false(self):
        assert all_or_date_min([True, False]) is False

    def test_returns_min_datetime(self):
        assert all_or_date_min([dt(1), dt(3), dt(2)]) == dt(1)

    def test_mixed_bool_and_datetime(self):
        assert all_or_date_min([True, dt(5)]) == dt(5)


class TestAnyOrDateMin:
    def test_all_false_returns_false(self):
        assert any_or_date_min([False, False]) is False

    def test_any_true_returns_true(self):
        assert any_or_date_min([False, True]) is True

    def test_returns_min_datetime(self):
        assert any_or_date_min([dt(1), dt(3)]) == dt(1)

    def test_false_with_datetimes_returns_min(self):
        assert any_or_date_min([False, dt(5), dt(2)]) == dt(2)


class TestAnyOrDateMax:
    def test_all_false_returns_false(self):
        assert any_or_date_max([False, False]) is False

    def test_any_true_returns_true(self):
        assert any_or_date_max([False, True]) is True

    def test_returns_max_datetime(self):
        assert any_or_date_max([dt(1), dt(3)]) == dt(3)

    def test_false_with_datetimes_returns_max(self):
        assert any_or_date_max([False, dt(5), dt(2)]) == dt(5)
