import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.planes import ControlPlane, ControlPlaneDenied, IntentStore, ObservedStore


def test_agent_cannot_write_control_plane():
    cp = ControlPlane()
    with pytest.raises(ControlPlaneDenied):
        cp.set_policy(actor_role="agent", actor_id="agent-under-test", payload={"resume": True})
    denied = [e for e in cp.audit_log if e["event"] == "control_plane_denied"]
    assert len(denied) == 1
    assert denied[0]["actor_role"] == "agent"  # C8: nunca se re-etiqueta como "user"


def test_operator_can_write_control_plane():
    cp = ControlPlane()
    result = cp.set_policy(actor_role="operator", actor_id="human-1", payload={"resume": True})
    assert result == {"resume": True}


def test_observer_cannot_read_intent_store():
    intent = IntentStore()
    intent.write("agent", {"plan": ["x"]})
    # IntentStore no expone ningún método de lectura genérico para el
    # observador -- solo un snapshot de contraste explícito, distinto de
    # cualquier canal que el observador de adecuación consuma.
    assert not hasattr(intent, "read")


def test_observed_store_rejects_intent_keys_on_write():
    store = ObservedStore()
    with pytest.raises(AssertionError, match="AUDIT_FAIL"):
        store.write("proxy", {"dst": "x", "plan": ["leak"]})


def test_observed_store_only_observer_reads():
    store = ObservedStore()
    store.write("proxy", {"ts": 1, "dst": "x", "outcome": "allow"})
    with pytest.raises(PermissionError):
        store.read("agent")
    assert store.read("observer") == [{"ts": 1, "dst": "x", "outcome": "allow"}]
