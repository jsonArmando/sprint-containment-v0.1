import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.layer2 import correlate, graduate_response


def test_single_signal_never_causes_hard_isolate():
    """El punto exacto que se señaló: baja confianza no debe pagar el costo
    de disponibilidad de un isolate perimetral."""
    l2 = correlate(["replay_outside_retry"], {"n_effects": 2})
    assert l2["confidence"] == "low"
    assert graduate_response("contain", l2) == "contain_soft"


def test_two_corroborating_signals_cause_hard_contain():
    l2 = correlate(["allowlist_scope_stretch", "replay_outside_retry"], {"n_effects": 3})
    assert l2["confidence"] == "high"
    assert graduate_response("contain", l2) == "contain"


def test_layer1_abstain_is_never_escalated_by_layer2():
    l2 = correlate([], {"n_effects": 0})
    assert graduate_response("abstain", l2) == "abstain"


def test_zero_candidates_layer2_abstains():
    l2 = correlate([], {"n_effects": 5})
    assert l2["decision"] == "abstain"
    assert l2["confidence"] == "n/a"
