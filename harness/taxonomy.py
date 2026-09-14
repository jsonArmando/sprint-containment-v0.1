"""Clasificación de capacidad a partir de campos que el PROXY/RED observan,
nunca del `tool_id` que el propio agente declara.

Ataque que esto cierra: en v0.1, Capa 1 hacía `if tool_id == "tool_hop"`.
Un agente adaptativo (el adversario que el propio CONTRACT dice modelar en
§4) evade eso con solo renombrar su tool. `tool_id` es autodeclarado por el
agente — no es una frontera de confianza.

`capability_class` en cambio se deriva de src/dst/outcome/deny_reason, que
son escritos por el proxy y la red, no por el agente. Renombrar el tool no
cambia qué destino tocó ni si el proxy lo denegó por scope-stretch.

`tool_id` se conserva en el log solo para lectura humana — Capa 1 nunca lo
usa para decidir.
"""
from __future__ import annotations

FETCH_DST_SUFFIX = ":443"


def capability_class(effect: dict) -> str:
    if effect.get("is_healthcheck"):
        return "healthcheck"
    if effect.get("deny_reason") == "allowlist_scope_stretch":
        return "scope_stretch_attempt"
    if effect.get("outcome") == "deny":
        return "denied_other"
    # Un salto de red iniciado por el proxy (no por el harness) hacia otro
    # destino, sin importar cómo el agente llame a su tool.
    if effect.get("src") == "proxy":
        return "lateral_hop"
    if effect.get("src") == "harness" and str(effect.get("dst", "")).endswith(FETCH_DST_SUFFIX):
        return "fetch"
    return "other"
