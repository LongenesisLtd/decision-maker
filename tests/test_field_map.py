from londec.field_map import FieldMap


def test_field_map_fields():
    fm = FieldMap(type_id="kind", created_at="ts", revoked_at="cancelled_at")
    assert fm.type_id == "kind"
    assert fm.created_at == "ts"
    assert fm.revoked_at == "cancelled_at"


def test_field_map_used_for_flat_lookup():
    fm = FieldMap(type_id="kind", created_at="ts", revoked_at="cancelled_at")
    event = {"kind": "purchase", "ts": "2026-01-01", "cancelled_at": None, "amount": 99}
    assert event.get(fm.type_id) == "purchase"
    assert event.get(fm.created_at) == "2026-01-01"
    assert event.get(fm.revoked_at) is None
