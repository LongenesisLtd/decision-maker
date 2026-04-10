from dataclasses import dataclass, field


@dataclass
class FieldMap:
    """Describes which keys (or key paths) in each event dict carry the values londec needs."""

    type_id: str
    created_at: str
    revoked_at: str
    payloads: dict[str, str]
    separator: str = "."


def resolve(event: dict, path: str, separator: str = "."):
    """Walk a dot-separated (or custom-separator) path through a nested dict.

    Returns None on any missing key or non-dict intermediate value.
    """
    value = event
    for key in path.split(separator):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value
