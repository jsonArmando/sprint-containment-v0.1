"""Capa 1: tripwire de secuencia sobre efectos. Sin Intent. Sin LLM.

v0.2: opera sobre `capability_class` (derivado de src/dst/outcome por el
proxy — ver taxonomy.py), no sobre `tool_id` (autodeclarado por el agente).

v0.3: `_windows()` existía en v0.2 pero `decide()` nunca la llamaba —
código muerto que se documentó como "ventanas reales" sin serlo. Un
revisor lo señaló. Aquí se usa para UNA cosa concreta y acotada: detectar
`fan_out_burst` (muchas llamadas iguales en una ventana corta). Las reglas
de secuencia (`scope_stretch`, `chain_fetch_then_hop`, `replay`) siguen
evaluándose sobre el episodio completo a propósito: un atacante que pacea
su cadena para separarla en el tiempo la evade igual si se la limita a una
ventana — ventanear esas reglas la haría MÁS fácil de evadir, no más
difícil. Ver `tests/test_layer1_windows.py::test_low_and_slow_spread_across_windows_evades_fan_out`
para la prueba explícita de que este límite existe y no está resuelto.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .taxonomy import capability_class

POLICY_PATH = Path(__file__).resolve().parents[1] / "policy" / "layer1_policy.yaml"


def _load_policy() -> dict:
    return yaml.safe_load(POLICY_PATH.read_text())


def _windows(effects: list[dict], size: float) -> list[list[dict]]:
    """Ventanas por `ts // size`. Simple y explícito a propósito — no es un
    motor de streaming de producción, es suficiente para episodios de
    laboratorio medidos en segundos."""
    if not effects:
        return []
    buckets: dict[int, list[dict]] = {}
    for e in effects:
        ts = float(e.get("ts", 0))
        bucket = int(ts // size) if size > 0 else 0
        buckets.setdefault(bucket, []).append(e)
    return [buckets[k] for k in sorted(buckets)]


def _fan_out(windows: list[list[dict]], policy: dict) -> bool:
    rule = policy["rules"].get("fan_out")
    if not rule:
        return False
    threshold = rule["same_dst_same_class_min_count"]
    for window in windows:
        counts: dict[tuple[str, str], int] = {}
        for e in window:
            if e.get("is_healthcheck"):
                continue
            key = (capability_class(e), e.get("dst"))
            counts[key] = counts.get(key, 0) + 1
        if any(c >= threshold for c in counts.values()):
            return True
    return False


def _replay(work: list[dict], policy: dict) -> bool:
    rule = policy["rules"]["replay_outside_retry"]
    seen: dict[str, int] = {}
    for e in work:
        key = f"{capability_class(e)}:{e.get('dst')}"
        n = int(e.get("retry_n") or 0)
        if (
            key in seen
            and n == rule["retry_n_equals"]
            and e.get("outcome") == rule["outcome"]
        ):
            return True
        seen[key] = n
    return False


def decide(effects: list[dict], policy: dict | None = None) -> dict:
    policy = policy or _load_policy()
    classes = [capability_class(e) for e in effects]

    work = [e for e, c in zip(effects, classes) if c != "healthcheck"]
    if not work and effects:
        return {"decision": "abstain", "reason": "healthcheck_only", "candidates": []}
    if not effects:
        return {"decision": "abstain", "reason": "no_effects", "candidates": []}

    work_classes = [capability_class(e) for e in work]
    candidates = []

    stretch_rule = policy["rules"]["scope_stretch"]
    if work_classes.count(stretch_rule["trigger_class"]) >= stretch_rule["min_count"]:
        candidates.append("allowlist_scope_stretch")

    chain_rule = policy["rules"]["chain_fetch_then_hop"]
    if all(c in work_classes for c in chain_rule["requires_classes"]):
        candidates.append("chain_fetch_then_hop")

    if _replay(work, policy):
        candidates.append("replay_outside_retry")

    windows = _windows(effects, policy.get("window_seconds", 5))
    if _fan_out(windows, policy):
        candidates.append("fan_out_burst")

    if candidates:
        return {"decision": "contain", "reason": "+".join(candidates), "candidates": candidates}
    return {"decision": "abstain", "reason": "no_sequence", "candidates": []}
