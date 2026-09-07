from .decision import Decision


def all_or_date_max(children: list[Decision]) -> Decision:
    """AND — satisfied once every child is; reports the LATEST since-date."""
    if all(c.satisfied for c in children):
        whens = [c.when for c in children if c.when is not None]
        return Decision(True, max(whens) if whens else None)
    unresolved = [c for c in children if not c.satisfied]
    if any(c.when is None for c in unresolved):
        return Decision(False, when=None)  # a genuine dead end blocks any prediction
    return Decision(False, when=max(c.when for c in unresolved))


def all_or_date_min(children: list[Decision]) -> Decision:
    """MIN_AND — same resolution as AND; reports the EARLIEST since-date."""
    if all(c.satisfied for c in children):
        whens = [c.when for c in children if c.when is not None]
        return Decision(True, min(whens) if whens else None)
    unresolved = [c for c in children if not c.satisfied]
    if any(c.when is None for c in unresolved):
        return Decision(False, when=None)
    return Decision(False, when=max(c.when for c in unresolved))  # resolution instant unchanged


def any_or_date_min(children: list[Decision]) -> Decision:
    """OR — satisfied once any child is; reports the EARLIEST since-date."""
    if any(c.satisfied for c in children):
        whens = [c.when for c in children if c.satisfied and c.when is not None]
        return Decision(True, min(whens) if whens else None)
    whens = [c.when for c in children if c.when is not None]
    return Decision(False, min(whens) if whens else None)


def any_or_date_max(children: list[Decision]) -> Decision:
    """MAX_OR — same resolution as OR; reports the LATEST since-date."""
    if any(c.satisfied for c in children):
        whens = [c.when for c in children if c.satisfied and c.when is not None]
        return Decision(True, max(whens) if whens else None)
    whens = [c.when for c in children if c.when is not None]
    return Decision(False, min(whens) if whens else None)  # resolution instant unchanged
