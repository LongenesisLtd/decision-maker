import pytest
from londec.field_map import FieldMap, resolve


def test_resolve_top_level_key():
    assert resolve({"a": 1}, "a") == 1


def test_resolve_nested_key():
    assert resolve({"a": {"b": 2}}, "a.b") == 2


def test_resolve_deeply_nested():
    assert resolve({"a": {"b": {"c": 3}}}, "a.b.c") == 3


def test_resolve_missing_key_returns_none():
    assert resolve({"a": 1}, "b") is None


def test_resolve_missing_intermediate_returns_none():
    assert resolve({"a": 1}, "a.b") is None


def test_resolve_non_dict_intermediate_returns_none():
    assert resolve({"a": "string"}, "a.b") is None


def test_resolve_custom_separator():
    assert resolve({"a": {"b": 99}}, "a::b", separator="::") == 99


def test_resolve_none_value_is_returned():
    assert resolve({"a": None}, "a") is None


def test_field_map_defaults():
    fm = FieldMap(
        type_id="activity_id",
        created_at="created_at",
        revoked_at="consented_revoked_at",
        payloads={"data": "stuff.answers_json", "derived": "_derived"},
    )
    assert fm.separator == "."
