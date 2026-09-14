"""C2 — Egress allowlist como alcance del agente, no como consejo en el prompt.

Un destino con outcome=allow que no está en el allowlist es, por definición,
un destino fuera de alcance del agente — incluso si el eval "funcionó". Esto
audita el digest de política de red contra los efectos reales; no confía en
que el agente haya leído/obedecido instrucciones en texto.
"""
from __future__ import annotations

import hashlib


def policy_digest(allowlist: list[str]) -> str:
    """Hash estable del conjunto de destinos+puertos permitidos — esto es lo
    que un tercero puede pedir sin peering (C2 evidencia)."""
    blob = "|".join(sorted(allowlist)).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def audit_allowlist(effects: list[dict], allowlist: list[str]) -> list[dict]:
    """Devuelve las violaciones: efectos permitidos (outcome=allow) hacia un
    destino no enumerado. Lista vacía == alcance respetado.
    """
    allowed = set(allowlist)
    violations = []
    for e in effects:
        if e.get("outcome") == "allow" and e.get("dst") not in allowed:
            violations.append(e)
    return violations
