INTENT_KEYS = frozenset(
    {"plan", "hypothesis_id", "next_ttp", "cot", "chain_planned"}
)


def assert_frontier(observed: dict) -> None:
    leaked = INTENT_KEYS.intersection(_keys(observed))
    if leaked:
        raise AssertionError(f"AUDIT_FAIL Intent leaked into Observed: {sorted(leaked)}")


def _keys(obj, acc=None):
    acc = acc or set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(str(k))
            _keys(v, acc)
    elif isinstance(obj, list):
        for x in obj:
            _keys(x, acc)
    return acc
