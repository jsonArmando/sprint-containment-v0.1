import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.egress import audit_allowlist, policy_digest


def test_allowed_destination_is_no_violation():
    effects = [{"outcome": "allow", "dst": "proxy.eval.lab:443"}]
    assert audit_allowlist(effects, ["proxy.eval.lab:443"]) == []


def test_out_of_allowlist_allow_is_a_violation_regardless_of_prompt():
    effects = [{"outcome": "allow", "dst": "attacker.example:443"}]
    violations = audit_allowlist(effects, ["proxy.eval.lab:443"])
    assert len(violations) == 1


def test_denied_out_of_scope_destination_is_not_a_violation():
    effects = [{"outcome": "deny", "dst": "attacker.example:443"}]
    assert audit_allowlist(effects, ["proxy.eval.lab:443"]) == []


def test_policy_digest_is_stable_regardless_of_input_order():
    assert policy_digest(["b:443", "a:443"]) == policy_digest(["a:443", "b:443"])
