import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from reliax_certificate.chain import GENESIS, canonical_json, record_hash, seal, verify_chain  # noqa: E402


def test_canonical_json_is_order_independent():
    assert canonical_json({"b": 1, "a": [1, {"d": 2, "c": 3}]}) == canonical_json({"a": [1, {"c": 3, "d": 2}], "b": 1})
    assert canonical_json({"a": 1}) == '{"a":1}'


def test_seal_and_verify_and_tamper():
    r1 = seal({"x": 1}); r2 = seal({"x": 2}, r1["hash"])
    assert r1["prev_hash"] == GENESIS and r2["prev_hash"] == r1["hash"]
    assert record_hash(r1["prev_hash"], r1["payload"]) == r1["hash"]
    ok = verify_chain([r1, r2]); assert ok["ok"] and ok["first_bad_index"] is None and ok["head"] == r2["hash"]
    r1["payload"]["x"] = 9
    bad = verify_chain([r1, r2]); assert not bad["ok"] and bad["first_bad_index"] == 0
    assert any("altered" in e for e in bad["errors"])


def test_broken_link_is_reported_at_the_right_index():
    r1 = seal({"x": 1}); r2 = seal({"x": 2}, "f" * 64)
    bad = verify_chain([r1, r2]); assert bad["first_bad_index"] == 1 and "link" in bad["errors"][0]
