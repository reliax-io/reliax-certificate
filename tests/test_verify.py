import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from reliax_certificate.verify import verify_file, verify_records  # noqa: E402
from reliax_certificate.cli import main  # noqa: E402

EX = pathlib.Path(__file__).resolve().parent.parent / "examples" / "chain.json"


def test_example_chain_verifies(tmp_path):
    rep = verify_file(str(EX))
    assert rep["ok"] and rep["records"] == 2 and rep["chain"]["ok"]
    assert main(["verify", str(EX)]) == 0


def test_recompute_when_core_is_available():
    try:
        import reliax_core  # noqa: F401
    except ImportError:
        return
    rep = verify_file(str(EX), recompute=True)
    assert rep["ok"], rep


def test_tampered_record_fails(tmp_path):
    data = json.loads(EX.read_text())
    data["records"][0]["payload"]["credibility"] = 0.62          # edit a value: hash breaks
    p = tmp_path / "t.json"; p.write_text(json.dumps(data))
    rep = verify_file(str(p))
    assert not rep["ok"] and rep["chain"]["first_bad_index"] == 0
    assert main(["verify", str(p)]) == 1


def test_wrong_text_fails_without_breaking_the_chain():
    from reliax_certificate.chain import seal
    data = json.loads(EX.read_text())
    payload = data["records"][0]["payload"]
    payload["certificate_text"] = payload["certificate_text"].replace("least 95%", "least 99%")
    rep = verify_records([seal(payload)])
    assert rep["chain"]["ok"] and not rep["ok"]
    assert any("wording" in i for i in rep["per_record"][0]["issues"])
