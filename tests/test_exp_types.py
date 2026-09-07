import pytest
from londec.exp_types import exp_types, gte, gt, lte, lt, is_true, is_false, equals_func


class TestNumericComparisons:
    def test_gte(self):
        assert gte("5", "5") is True
        assert gte("6", "5") is True
        assert gte("4", "5") is False

    def test_gte_non_numeric_returns_false(self):
        assert gte("abc", "5") is False
        assert gte(None, "5") is False

    def test_gt(self):
        assert gt("6", "5") is True
        assert gt("5", "5") is False

    def test_gt_non_numeric_returns_false(self):
        assert gt("abc", "5") is False

    def test_lte(self):
        assert lte("5", "5") is True
        assert lte("4", "5") is True
        assert lte("6", "5") is False

    def test_lte_non_numeric_returns_false(self):
        assert lte("abc", "5") is False

    def test_lt(self):
        assert lt("4", "5") is True
        assert lt("5", "5") is False

    def test_lt_non_numeric_returns_false(self):
        assert lt("abc", "5") is False


class TestIsTrue:
    def test_truthy_values(self):
        assert is_true("yes", None) is True
        assert is_true(1, None) is True
        assert is_true(True, None) is True

    def test_falsy_values(self):
        assert is_true("", None) is False
        assert is_true(0, None) is False
        assert is_true(False, None) is False

    def test_sentinel_missing_value_returns_false(self):
        assert is_true("certainly not the answer you are looking for", None) is False


class TestIsFalse:
    def test_falsy_values(self):
        assert is_false("", None) is True
        assert is_false(0, None) is True
        assert is_false(False, None) is True

    def test_truthy_values(self):
        assert is_false("yes", None) is False
        assert is_false(1, None) is False

    def test_sentinel_missing_value_returns_false(self):
        assert is_false("certainly not the answer you are looking for", None) is False


class TestEqualsFunc:
    def test_numeric_equality(self):
        assert equals_func("5", "5.0") is True
        assert equals_func("5", "6") is False

    def test_falls_back_to_string_equality_for_non_numeric(self):
        assert equals_func("yes", "yes") is True
        assert equals_func("yes", "no") is False


class TestExpTypesRegistry:
    def test_equals(self):
        assert exp_types["equals"]("5", "5.0") is True
        assert exp_types["equals"]("yes", "yes") is True
        assert exp_types["equals"]("yes", "no") is False

    def test_lt_lte_gt_gte(self):
        assert exp_types["lt"]("4", "5") is True
        assert exp_types["lte"]("5", "5") is True
        assert exp_types["gt"]("6", "5") is True
        assert exp_types["gte"]("5", "5") is True

    def test_ne(self):
        assert exp_types["ne"]("a", "b") is True
        assert exp_types["ne"]("a", "a") is False

    def test_in_range(self):
        assert exp_types["in_range"](5, [1, 10]) is True
        assert exp_types["in_range"](15, [1, 10]) is False

    def test_not_in_range(self):
        assert exp_types["not_in_range"](15, [1, 10]) is True
        assert exp_types["not_in_range"](5, [1, 10]) is False

    def test_in(self):
        assert exp_types["in"]("b", ["a", "b", "c"]) is True
        assert exp_types["in"]("z", ["a", "b", "c"]) is False

    def test_contains_any_of(self):
        assert exp_types["contains_any_of"](["a", "b"], ["b", "c"]) is True
        assert exp_types["contains_any_of"](["a"], ["b", "c"]) is False

    def test_contains_none_of(self):
        assert exp_types["contains_none_of"](["a"], ["b", "c"]) is True
        assert exp_types["contains_none_of"](["a", "b"], ["b", "c"]) is False

    def test_contains_all_of(self):
        assert exp_types["contains_all_of"](["a", "b", "c"], ["a", "b"]) is True
        assert exp_types["contains_all_of"](["a"], ["a", "b"]) is False

    def test_is_subset_of(self):
        assert exp_types["is_subset_of"](["a", "b"], ["a", "b", "c"]) is True
        assert exp_types["is_subset_of"](["a", "d"], ["a", "b", "c"]) is False

    def test_is_not_subset_of(self):
        assert exp_types["is_not_subset_of"](["a", "d"], ["a", "b", "c"]) is True
        assert exp_types["is_not_subset_of"](["a", "b"], ["a", "b", "c"]) is False

    def test_deprecated_is_subset_alias(self):
        assert exp_types["is_subset"](["a", "b"], ["a", "b", "c"]) is True

    def test_deprecated_is_not_subset_alias(self):
        assert exp_types["is_not_subset"](["a", "d"], ["a", "b", "c"]) is True

    def test_deprecated_answer_exact(self):
        assert exp_types["answer_exact"]("yes", "yes") is True
        assert exp_types["answer_exact"]("yes", "no") is False

    def test_true(self):
        assert exp_types["true"]("yes", None) is True
        assert exp_types["true"]("", None) is False

    def test_false(self):
        assert exp_types["false"]("", None) is True
        assert exp_types["false"]("yes", None) is False
