import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.schema_validate import SchemaViolation, validate_event


def test_valid_event_passes():
    validate_event({"ts": 1, "src": "harness", "dst": "x:443", "outcome": "allow"})


def test_unknown_field_is_c3_fail():
    with pytest.raises(SchemaViolation, match="C3 FAIL"):
        validate_event({"ts": 1, "src": "a", "dst": "b", "outcome": "allow", "plan": ["leak"]})


def test_free_reasoning_field_is_c3_fail():
    with pytest.raises(SchemaViolation):
        validate_event({"ts": 1, "src": "a", "dst": "b", "outcome": "allow", "reasoning": "why not"})


def test_missing_required_field_is_c3_fail():
    with pytest.raises(SchemaViolation):
        validate_event({"src": "a", "dst": "b", "outcome": "allow"})


def test_bad_enum_value_is_c3_fail():
    with pytest.raises(SchemaViolation):
        validate_event({"ts": 1, "src": "a", "dst": "b", "outcome": "maybe"})
