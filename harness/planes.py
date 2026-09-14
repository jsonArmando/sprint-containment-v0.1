"""C1 + C8 — Tres planos como procesos/canales distintos, con ACL real.

Intent:        escribe el agente + planner del harness. NADIE del observador
               lo lee.
Observed:      escribe harness/proxy/red. Lee el observador.
Control plane: escribe el operador humano. El agente NO puede invocar
               set_policy y quedar etiquetado como `source: user` (C8).
               Cualquier intento queda registrado como denegado, con el
               actor real, no reescrito.

Este módulo es intencionalmente pequeño: la propiedad que certifica no es
"cuánta lógica tiene", es "el agente no puede escribir aquí ni disfrazarse".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import time


class ControlPlaneDenied(PermissionError):
    """El actor no tiene autoridad de operador sobre el control plane."""


@dataclass
class ControlPlane:
    audit_log: list[dict] = field(default_factory=list)
    _policy: dict = field(default_factory=dict)

    def set_policy(self, actor_role: str, actor_id: str, payload: dict) -> dict:
        """Solo `operator` puede escribir política. `agent` es rechazado y
        registrado como intento de auto-promoción (C8), nunca como `source: user`.
        """
        if actor_role != "operator":
            entry = {
                "ts": time(),
                "event": "control_plane_denied",
                "actor_role": actor_role,
                "actor_id": actor_id,
                "reason": "agent_cannot_personify_operator",
            }
            self.audit_log.append(entry)
            raise ControlPlaneDenied(
                f"actor_role={actor_role!r} no puede escribir en control plane"
            )
        entry = {
            "ts": time(),
            "event": "policy_set",
            "actor_role": actor_role,
            "actor_id": actor_id,
            "payload": payload,
        }
        self.audit_log.append(entry)
        self._policy.update(payload)
        return dict(self._policy)

    def current_policy(self) -> dict:
        return dict(self._policy)


class IntentStore:
    """Solo el agente y el planner del harness escriben. El observador NUNCA
    obtiene un canal de lectura de esta clase — no expone `read()` genérico,
    solo un helper de contraste explícito para pruebas offline (C0/C5).
    """

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def write(self, actor_role: str, payload: dict) -> None:
        if actor_role not in {"agent", "harness_planner"}:
            raise PermissionError(f"actor_role={actor_role!r} no puede escribir Intent")
        self._entries.append(payload)

    def contrast_only_snapshot(self) -> list[dict]:
        """Uso exclusivo en Corrida A (intent_on) para contraste. Nunca se
        pasa al observador de adecuación (C0)."""
        return list(self._entries)


class ObservedStore:
    """Escriben harness/proxy/red. Lee el observador. No acepta claves de
    Intent — reutiliza assert_frontier como guardia de escritura, no solo
    de auditoría posterior."""

    def __init__(self) -> None:
        from .frontier import assert_frontier

        self._assert_frontier = assert_frontier
        self._effects: list[dict] = []

    def write(self, writer_role: str, effect: dict) -> None:
        if writer_role not in {"harness", "proxy", "network"}:
            raise PermissionError(f"writer_role={writer_role!r} no puede escribir Observed")
        self._assert_frontier({"effect": effect})
        self._effects.append(effect)

    def read(self, reader_role: str) -> list[dict]:
        if reader_role != "observer":
            raise PermissionError(f"reader_role={reader_role!r} no puede leer Observed")
        return list(self._effects)
