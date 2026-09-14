"""C6 — Isolate con TTL y rollback. C7 — Fail-closed si el observador cae.

La contención es L3/L4 sobre un activo que está en el allowlist de
aislamiento (no "cualquier cosa"). TTL por defecto fin-de-episodio o <=10
min. Cada acción guarda un `rollback_ref` y puede revertirse explícitamente
o expirar sola.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from time import time

DEFAULT_TTL_SECONDS = 600  # <=10 min, C6


class AssetNotIsolable(ValueError):
    pass


@dataclass
class ContainmentAction:
    asset: str
    rule: str
    ttl_seconds: int
    rollback_ref: str
    created_at: float = field(default_factory=time)
    rolled_back: bool = False

    def as_log(self) -> dict:
        return {
            "event": "ContainmentAction",
            "asset": self.asset,
            "rule": self.rule,
            "ttl": self.ttl_seconds,
            "rollback_ref": self.rollback_ref,
            "rolled_back": self.rolled_back,
        }


class Actuator:
    def __init__(self, isolation_allowlist: list[str]):
        self.isolation_allowlist = set(isolation_allowlist)
        self.actions: list[ContainmentAction] = []
        self.soft_signals: list[dict] = []

    def soft_signal(self, asset: str, rule: str) -> dict:
        """Respuesta graduada para confidence=low (C5/layer2): refuerza
        logging / aplica rate-limit, pero NO aísla el activo. No es un
        `ContainmentAction` porque no hay TTL ni rollback que ofrecer —
        no se tocó nada que revertir."""
        entry = {
            "event": "SoftSignal",
            "asset": asset,
            "rule": rule,
            "action": "heightened_logging_rate_limit",
            "isolated": False,
        }
        self.soft_signals.append(entry)
        return entry

    def isolate(self, asset: str, rule: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> ContainmentAction:
        if asset not in self.isolation_allowlist:
            raise AssetNotIsolable(
                f"'{asset}' no está en el allowlist de aislamiento {sorted(self.isolation_allowlist)}"
            )
        if ttl_seconds > DEFAULT_TTL_SECONDS:
            raise ValueError("C6: TTL no puede exceder 10 minutos sin fin-de-episodio explícito")
        action = ContainmentAction(
            asset=asset,
            rule=rule,
            ttl_seconds=ttl_seconds,
            rollback_ref=f"snap-{asset}-{int(time())}",
        )
        self.actions.append(action)
        return action

    def rollback(self, action: ContainmentAction) -> ContainmentAction:
        action.rolled_back = True
        return action

    def expire_stale(self, now: float | None = None) -> list[ContainmentAction]:
        now = now if now is not None else time()
        expired = [
            a for a in self.actions
            if not a.rolled_back and (now - a.created_at) > a.ttl_seconds
        ]
        for a in expired:
            self.rollback(a)
        return expired

    def fail_closed_egress_cut(self, proxy_asset: str = "proxy") -> ContainmentAction:
        """C7 — colector caído no anula el episodio a favor del workload:
        se corta el egress allowlist por defecto."""
        return self.isolate(proxy_asset, rule="CONTAIN_FAILCLOSED", ttl_seconds=DEFAULT_TTL_SECONDS)
