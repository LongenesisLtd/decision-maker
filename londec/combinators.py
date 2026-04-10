import datetime


def _is_datetime(x: object) -> bool:
    return isinstance(x, datetime.datetime)


def all_or_date_max(a: list) -> bool | datetime.datetime:
    """AND combinator — returns False if any element is falsy, otherwise the max datetime."""
    if not all(a):
        return False
    datetimes = [i for i in a if _is_datetime(i)]
    if datetimes:
        return max(datetimes)
    return True


def all_or_date_min(a: list) -> bool | datetime.datetime:
    """AND (MIN) combinator — returns False if any element is falsy, otherwise the min datetime."""
    if not all(a):
        return False
    datetimes = [i for i in a if _is_datetime(i)]
    if datetimes:
        return min(datetimes)
    return True


def any_or_date_min(a: list) -> bool | datetime.datetime:
    """OR combinator — returns the min datetime of truthy elements, or True/False."""
    datetimes = [i for i in a if _is_datetime(i)]
    if datetimes:
        return min(datetimes)
    return any(a)


def any_or_date_max(a: list) -> bool | datetime.datetime:
    """OR (MAX) combinator — returns the max datetime of truthy elements, or True/False."""
    datetimes = [i for i in a if _is_datetime(i)]
    if datetimes:
        return max(datetimes)
    return any(a)
