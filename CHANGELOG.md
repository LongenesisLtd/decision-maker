# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project is in `0.x`; per common `0.x` convention, a breaking change is
released as a minor version bump rather than a major one.

## [0.2.1] - 2026-09-07

### Added

- Test suite reaches 100% line coverage: added `tests/test_exp_types.py`
  (covering every `sub_type` expression evaluator, including numeric-parse
  fallback and sentinel-value branches), plus tests for `_key_match`'s
  unknown-`sub_type` and exception-handling paths and the wall-clock
  `datetime.now(UTC)` fallback in `delay_passed`, `available_on_date_range`,
  and `taken_recently` when `now` isn't passed in. No behavior changes.

## [0.2.0] - 2026-09-07

### Changed

- **Breaking:** `decide()` — and every leaf evaluator and combinator — now
  returns an explicit `Decision(satisfied: bool, when: datetime | None)`
  NamedTuple instead of `bool | datetime`. `satisfied` is always computed
  directly by whichever evaluator or combinator produced it, never inferred
  by comparing `when` to `now` after the fact. `when`, when present, means
  "since this date" if satisfied, or "predicted to become satisfied at this
  date" if not.

### Fixed

- `delay_passed()` and `available_on_date_range()` previously returned a
  future datetime unconditionally, with no comparison against `now`. Since
  Python datetimes are always truthy, every `AND`/`OR` combinator — and any
  caller doing `bool(decide(...))` — treated a condition that legitimately
  wasn't due yet as satisfied. `delay_passed()` now takes `now` and compares
  the computed threshold against it directly.

## [0.1.0] - 2026-08-21

Initial public release.

### Added

- `decide()`: evaluate tree-structured, JSON-serializable conditions against
  an ordered history of flat event dicts.
- `FieldMap`: maps three semantic roles (`type_id`, `created_at`,
  `revoked_at`) onto your own event dicts' key names.
- Leaf evaluators: `event_happened`, `event_not_happened`,
  `event_happened_exactly`, `event_happened_fewer_than`,
  `event_happened_at_least`, `event_revoked`, `delay`, `payload_match`,
  `last_event_type_equals`, `available_on_date_range`, `is_taken_recently`.
- Combinators: `AND`/`MAX_AND`, `MIN_AND`, `OR`/`MIN_OR`, `MAX_OR`, composing
  to arbitrary tree depth.
- `sub_type` expression evaluators for `payload_match` (`equals`, `ne`,
  `gt`/`gte`, `lt`/`lte`, `in`, `in_range`/`not_in_range`,
  `contains_any_of`/`contains_none_of`/`contains_all_of`,
  `is_subset_of`/`is_not_subset_of`, `true`/`false`).

[0.2.1]: https://github.com/LongenesisLtd/decision-maker/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/LongenesisLtd/decision-maker/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LongenesisLtd/decision-maker/releases/tag/v0.1.0
