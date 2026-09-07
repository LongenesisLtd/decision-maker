import datetime
import pytest
from zoneinfo import ZoneInfo
from londec.combinators import all_or_date_max, all_or_date_min, any_or_date_min, any_or_date_max
from londec.decision import Decision


def dt(day):
    return datetime.datetime(2025, 1, day, 12, 0, tzinfo=ZoneInfo("UTC"))


class TestAllOrDateMax:
    def test_all_satisfied_no_whens(self):
        assert all_or_date_max([Decision(True), Decision(True)]) == Decision(True, None)

    def test_one_unsatisfied_returns_unsatisfied(self):
        assert all_or_date_max([Decision(True), Decision(False)]) == Decision(False, None)

    def test_all_unsatisfied_returns_unsatisfied(self):
        assert all_or_date_max([Decision(False), Decision(False)]) == Decision(False, None)

    def test_returns_max_when_among_satisfied(self):
        result = all_or_date_max([Decision(True, dt(1)), Decision(True, dt(3)), Decision(True, dt(2))])
        assert result == Decision(True, dt(3))

    def test_mixed_satisfied_with_and_without_when(self):
        result = all_or_date_max([Decision(True), Decision(True, dt(5))])
        assert result == Decision(True, dt(5))

    def test_unsatisfied_with_prediction_reports_max_unresolved_when(self):
        """A future delay threshold reports its resolution date, but stays unsatisfied."""
        result = all_or_date_max([Decision(True, dt(1)), Decision(False, dt(5))])
        assert result == Decision(False, dt(5))
        assert result.satisfied is False

    def test_unresolved_with_no_when_blocks_prediction(self):
        result = all_or_date_max([Decision(False, dt(5)), Decision(False, None)])
        assert result == Decision(False, None)


class TestAllOrDateMin:
    def test_all_satisfied_no_whens(self):
        assert all_or_date_min([Decision(True), Decision(True)]) == Decision(True, None)

    def test_one_unsatisfied_returns_unsatisfied(self):
        assert all_or_date_min([Decision(True), Decision(False)]) == Decision(False, None)

    def test_returns_min_when_among_satisfied(self):
        result = all_or_date_min([Decision(True, dt(1)), Decision(True, dt(3)), Decision(True, dt(2))])
        assert result == Decision(True, dt(1))

    def test_mixed_satisfied_with_and_without_when(self):
        result = all_or_date_min([Decision(True), Decision(True, dt(5))])
        assert result == Decision(True, dt(5))

    def test_resolution_instant_matches_and_not_min(self):
        """MIN_AND's boolean resolution is identical to AND's — max of unresolved whens."""
        result = all_or_date_min([Decision(True, dt(1)), Decision(False, dt(5))])
        assert result == Decision(False, dt(5))


class TestAnyOrDateMin:
    def test_all_unsatisfied_returns_unsatisfied(self):
        assert any_or_date_min([Decision(False), Decision(False)]) == Decision(False, None)

    def test_any_satisfied_returns_satisfied(self):
        assert any_or_date_min([Decision(False), Decision(True)]) == Decision(True, None)

    def test_returns_min_when_among_satisfied(self):
        result = any_or_date_min([Decision(True, dt(1)), Decision(True, dt(3))])
        assert result == Decision(True, dt(1))

    def test_unsatisfied_children_report_min_when_as_prediction(self):
        result = any_or_date_min([Decision(False), Decision(False, dt(5)), Decision(False, dt(2))])
        assert result == Decision(False, dt(2))

    def test_ignores_unsatisfied_whens_when_satisfied(self):
        """Only satisfied children's whens count once the OR is satisfied."""
        result = any_or_date_min([Decision(True, dt(3)), Decision(False, dt(1))])
        assert result == Decision(True, dt(3))


class TestAnyOrDateMax:
    def test_all_unsatisfied_returns_unsatisfied(self):
        assert any_or_date_max([Decision(False), Decision(False)]) == Decision(False, None)

    def test_any_satisfied_returns_satisfied(self):
        assert any_or_date_max([Decision(False), Decision(True)]) == Decision(True, None)

    def test_returns_max_when_among_satisfied(self):
        result = any_or_date_max([Decision(True, dt(1)), Decision(True, dt(3))])
        assert result == Decision(True, dt(3))

    def test_resolution_instant_matches_or_not_max(self):
        """MAX_OR's boolean resolution is identical to OR's — min of unresolved whens."""
        result = any_or_date_max([Decision(False), Decision(False, dt(5)), Decision(False, dt(2))])
        assert result == Decision(False, dt(2))
