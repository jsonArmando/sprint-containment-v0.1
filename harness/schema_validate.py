"""C3 — Valida cada evento Observed contra el schema cerrado.

Implementación mínima sin dependencia de `jsonschema` (el harness debe correr
offline, en un runner de CI sin acceso a red). Solo aplica lo que C3 exige:
lista cerrada de campos + tipos básicos. No es un validador JSON Schema
general — es deliberadamente estrecho.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "observed.schema.v0_1.json"

_TYPE_MAP = {
    "number": (int, float),
    "string": str,
    "boolean": bool,
}


class SchemaViolation(AssertionError):
    pass


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def validate_event(event: dict, schema: dict | None = None) -> None:
    schema = schema or _load_schema()
    props = schema["properties"]
    required = schema.get("required", [])

    unknown = set(event) - set(props)
    if unknown:
        raise SchemaViolation(f"C3 FAIL: campo(s) no declarados en schema: {sorted(unknown)}")

    missing = [k for k in required if k not in event]
    if missing:
        raise SchemaViolation(f"C3 FAIL: falta(n) campo(s) requerido(s): {missing}")

    for key, value in event.items():
        expected = props[key]
        if "enum" in expected and value not in expected["enum"]:
            raise SchemaViolation(f"C3 FAIL: {key}={value!r} fuera de enum {expected['enum']}")
        py_type = _TYPE_MAP.get(expected.get("type"))
        if py_type and not isinstance(value, py_type):
            raise SchemaViolation(
                f"C3 FAIL: {key}={value!r} no es de tipo {expected['type']}"
            )


def validate_episode(effects: list[dict]) -> None:
    schema = _load_schema()
    for e in effects:
        validate_event(e, schema)
