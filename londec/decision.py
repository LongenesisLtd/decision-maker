from typing import NamedTuple
import datetime


class Decision(NamedTuple):
    """The result of evaluating a condition.

    `satisfied` is always computed directly by whichever evaluator or
    combinator produced this `Decision` — never derived by comparing `when`
    to `now` after the fact.

    `when`, when present, means "since this date" if `satisfied` is True, or
    "predicted to become satisfied at this date" if `satisfied` is False.
    It is `None` whenever there's no meaningful date to report (a pure
    count-based check, or a genuine dead end with no way to predict a future
    resolution).
    """

    satisfied: bool
    when: datetime.datetime | None = None
