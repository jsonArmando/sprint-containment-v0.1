import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.actuator import Actuator, AssetNotIsolable, DEFAULT_TTL_SECONDS


def test_isolate_only_allowlisted_asset():
    act = Actuator(isolation_allowlist=["proxy"])
    with pytest.raises(AssetNotIsolable):
        act.isolate("collector", rule="test")


def test_isolate_records_rollback_ref_and_ttl():
    act = Actuator(isolation_allowlist=["proxy"])
    action = act.isolate("proxy", rule="scope_stretch", ttl_seconds=300)
    assert action.rollback_ref.startswith("snap-proxy-")
    assert action.ttl_seconds == 300
    assert action.rolled_back is False


def test_ttl_cannot_exceed_ten_minutes():
    act = Actuator(isolation_allowlist=["proxy"])
    with pytest.raises(ValueError):
        act.isolate("proxy", rule="x", ttl_seconds=DEFAULT_TTL_SECONDS + 1)


def test_expire_stale_rolls_back_automatically():
    act = Actuator(isolation_allowlist=["proxy"])
    action = act.isolate("proxy", rule="x", ttl_seconds=1)
    expired = act.expire_stale(now=action.created_at + 10)
    assert action in expired
    assert action.rolled_back is True


def test_fail_closed_egress_cut_is_bounded_action():
    act = Actuator(isolation_allowlist=["proxy", "collector"])
    action = act.fail_closed_egress_cut("proxy")
    assert action.rule == "CONTAIN_FAILCLOSED"
    assert action.ttl_seconds == DEFAULT_TTL_SECONDS
