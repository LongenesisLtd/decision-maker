from typing import Callable
import datetime


def create_decision_maker(
    now: datetime.datetime | None = None,
) -> Callable[[dict, dict], bool | datetime.datetime]:
    """
    Create a decision maker instance with an optional current time.

    :param now: The current time to use for decision making, defaults to None.
    :return: An instance of DecisionMaker.
    """

    def evaluate_conditions(
        condition_tree: dict, context: dict
    ) -> bool | datetime.datetime:
        return False

    return evaluate_conditions
