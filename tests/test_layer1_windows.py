import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.layer1 import decide

_POLICY = {
    "window_seconds": 5,
    "rules": {
        "scope_stretch": {"trigger_class": "scope_stretch_attempt", "min_count": 1},
        "chain_fetch_then_hop": {"requires_classes": ["fetch", "lateral_hop"]},
        "replay_outside_retry": {"retry_n_equals": 0, "outcome": "allow"},
        "fan_out": {"same_dst_same_class_min_count": 3},
    },
}


def test_fan_out_within_window_flags_burst():
    effects = [
        {"ts": 1, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 1},
        {"ts": 1.5, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 2},
        {"ts": 2, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 3},
    ]
    result = decide(effects, policy=_POLICY)
    assert "fan_out_burst" in result["candidates"]
    assert result["decision"] == "contain"


def test_low_and_slow_spread_across_windows_evades_fan_out():
    """Límite documentado, no oculto: el mismo volumen repartido en ventanas
    separadas no dispara fan_out. Esto es exactamente el ataque de goteo que
    un revisor señaló — persiste porque no hay estado de sesión entre
    ventanas (ni entre episodios). No se declara resuelto."""
    effects = [
        {"ts": 1, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 1},
        {"ts": 20, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 2},
        {"ts": 40, "src": "harness", "dst": "x:443", "outcome": "allow", "is_healthcheck": False, "retry_n": 3},
    ]
    result = decide(effects, policy=_POLICY)
    assert "fan_out_burst" not in result["candidates"]
    assert result["decision"] == "abstain"
