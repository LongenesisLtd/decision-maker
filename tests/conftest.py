import datetime
from zoneinfo import ZoneInfo
from londec import FieldMap


FIELD_MAP = FieldMap(
    type_id="activity_id",
    created_at="created_at",
    revoked_at="consented_revoked_at",
)


def dt(year=2025, month=1, day=1, hour=12, minute=0):
    return datetime.datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("UTC"))


def make_event(
    activity_id,
    created_at=None,
    consented_revoked_at=None,
    **data,
):
    return {
        "activity_id": activity_id,
        "created_at": created_at or dt(),
        "consented_revoked_at": consented_revoked_at,
        **data,
    }
