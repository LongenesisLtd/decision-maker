def gte(a, b):
    try:
        return float(a) >= float(b)
    except (ValueError, TypeError):
        return False


def gt(a, b):
    try:
        return float(a) > float(b)
    except (ValueError, TypeError):
        return False


def lte(a, b):
    try:
        return float(a) <= float(b)
    except (ValueError, TypeError):
        return False


def lt(a, b):
    try:
        return float(a) < float(b)
    except (ValueError, TypeError):
        return False


# a - user answer (what)
# p - pattern (where)


def is_true(a, p):
    """Check if the answer is True."""
    if a == "certainly not the answer you are looking for":
        return False
    return bool(a) is True


def is_false(a, p):
    """Check if the answer is False."""
    if a == "certainly not the answer you are looking for":
        return False
    return bool(a) is False


def equals_func(a, p):
    """Check if two values are equal, with special handling for numeric types."""
    try:
        return float(a) == float(p)
    except (ValueError, TypeError):
        return f"{a}" == f"{p}"


exp_types = {
    "equals": lambda a, p: equals_func(a, p),
    "lt": lt,
    "lte": lte,
    "gt": gt,
    "gte": gte,
    "ne": lambda a, p: f"{a}" != f"{p}",
    "in_range": lambda a, p: p[0] <= a <= p[1],
    "not_in_range": lambda a, p: not (p[0] <= a <= p[1]),
    "in": lambda a, p: a in p,
    "contains_any_of": lambda a, p: any(item in a for item in p),
    "contains_none_of": lambda a, p: not any(item in a for item in p),
    "contains_all_of": lambda a, p: set(p).issubset(set(a)),
    "is_subset_of": lambda a, p: set(a).issubset(set(p)),
    "is_not_subset_of": lambda a, p: not set(a).issubset(set(p)),
    "is_subset": lambda a, p: set(a).issubset(set(p)),  # DEPRECATED SINCE 2022-21-10
    "is_not_subset": lambda a, p: not set(a).issubset(set(p)),  # DEPRECATED SINCE 2022-21-10
    "answer_exact": lambda a, p: a == p,  # DEPRECATED SINCE 2022-11-10
    "true": is_true,
    "false": is_false,
}
