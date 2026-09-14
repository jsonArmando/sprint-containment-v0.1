"""Capa 2 (opcional, C5): correlador acotado + respuesta graduada.

v0.2 calculaba `confidence` pero nada la usaba — un revisor lo señaló:
"tomar decisiones de contención perimetral duras basándose en inferencias
de baja confianza es un suicidio técnico". Tenía razón: v0.2 nunca hacía
eso porque `run.py` ignoraba la confianza por completo, no porque hubiera
una política. Ahora `graduate_response()` es esa política, explícita y
testeada: una sola señal nunca produce aislamiento perimetral duro por sí
sola.

Sigue recibiendo SOLO `candidates` (strings de nombre de regla) y un
resumen de efectos — `correlate()` corre `assert_frontier` sobre su propia
entrada antes de decidir nada.
"""
from __future__ import annotations

from .frontier import assert_frontier


def correlate(candidates: list[str], effect_summary: dict) -> dict:
    assert_frontier({"candidates": candidates, "effect_summary": effect_summary})

    n = len(candidates)
    if n >= 2:
        return {"decision": "contain", "confidence": "high", "basis": candidates}
    if n == 1:
        return {"decision": "contain", "confidence": "low", "basis": candidates}
    return {"decision": "abstain", "confidence": "n/a", "basis": []}


def graduate_response(layer1_decision: str, layer2_result: dict) -> str:
    """Política explícita confianza -> acción:

    - Capa 1 abstiene -> abstain. Capa 2 no escala lo que Capa 1 no señaló.
    - >=2 señales independientes corroborándose (confidence=high) -> contain
      (aislamiento perimetral duro, ver harness/actuator.py::isolate).
    - Exactamente 1 señal (confidence=low) -> contain_soft (señal reforzada
      / rate-limit, ver harness/actuator.py::soft_signal). NO aísla nada.
      Una sola regla disparando puede ser ruido; corroborar antes de
      pagar el costo de disponibilidad de un isolate.
    """
    if layer1_decision != "contain":
        return "abstain"
    if layer2_result["confidence"] == "high":
        return "contain"
    if layer2_result["confidence"] == "low":
        return "contain_soft"
    return "abstain"
