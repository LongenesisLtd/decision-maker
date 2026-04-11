from dataclasses import dataclass


@dataclass
class FieldMap:
    """Maps semantic roles to key names in a flat event dict.

    All referenced keys must exist at the root level of the event dict.
    Callers are responsible for flattening nested structures before
    passing events to londec.
    """

    type_id: str
    created_at: str
    revoked_at: str
