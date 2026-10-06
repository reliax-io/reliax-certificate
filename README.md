# reliax-certificate

The Reliax certificate, as an open format: what is written on a decision's
record, how records chain, how the wording is rendered, and how anyone checks
one. Apache-2.0. No dependencies. Terms used here are defined in the
[glossary](https://github.com/reliax-io#terms).

**Pre-1.0.** Schema v18 and wording template 18.0 are published so that they
can be read, tested and challenged. They may still change before 1.0; any
change is a new schema or template version, and every record names the
versions it was written with, so an old record always verifies against its
own version.

```
pip install reliax-certificate
reliax verify record.json
```

`reliax verify` walks a record or a chain of records and reports, per record:
the schema (every field present with its class), the hash chain, the stored
wording against the template, banned wording, and whether the reason codes
belong to the rule that fired. With `--recompute` and
[reliax-core](https://github.com/reliax-io/reliax-core) installed it also
re-runs the routing rule from the record's own fields and compares the route.
It works if Reliax no longer exists.

## What is in it

| Part | What it is | Where |
|---|---|---|
| Envelope schema v18 | The payload of one record: the calibration set (name, size, freeze date, hash), segment, prediction as received, the certified set, the credibility p-value, the bracket, the drift state and the dated outcome recheck, the guarantee state and scope, the route with the rule that fired, the trace, reason codes and certificate reasons, the criticality score, the versions, the stored text. **Every field carries one class**: `guarantee`, `exact`, `signal`, `rule`, `carried` or `record`. | `schema/certificate.v18.json`, `reliax_certificate/schema.py`, `types/certificate.d.ts` |
| Policy schema | What the deployer decides, kept as a signed version: the coverage target, the credibility floors, the actions per rule, the bracket ceiling, the calibration set, the segments, cell and schema rules, the privacy budget, queue capacity. | `schema/policy.v2.json` |
| Hash chain | `record_hash_k = SHA-256(record_hash_{k-1} ‖ canonical_JSON(payload_k))`, `record_hash_0 = 0^64`; canonical JSON is sorted keys, no whitespace. Any edit to a historical payload breaks verification at that record. | `reliax_certificate/chain.py` |
| Wording template 18.0 | The stored text is rendered from the signed fields and only from them; the verifier re-renders and compares. The same template in every domain: only the calibration set, the segment and the policy change. | `reliax_certificate/wording.py` |
| Banned wording | Phrases that turn a statement about the calibration set into a personal probability ("95% reliable", "the probability that this applicant…") or bring in vocabulary the certificate does not use. | `reliax_certificate/wording.py` |
| Fidelity check | For any readable rendering, plain or written by a customer-hosted language model: every number in the text must be a signed value, and no banned wording may appear. A rendering that fails is replaced by the plain template and never replaces the certificate. | `reliax_certificate/fidelity.py`, `schema/rendering-record.v1.json` |
| Verifier | `reliax verify record.json [--recompute] [--json]`; exit code 0 when verified. | `reliax_certificate/verify.py`, `cli.py` |

## What a certificate says

```
Certificate · rxe_7f3a9b · credit PD · evaluated · 2026-09-10T09:14:07Z
Prediction set {repay}, produced by a procedure that on calibration set C (n = 7,500, frozen 2026-06-30, sha256 3f9a…) and segment thin-file (definition hash 8c1d…) contains the true outcome at least 95% of the time.
Exchangeability at this point: no alarm. Credibility 0.61: this input is consistent with calibration set C.
Calibration at this score level: model said 0.03. Calibrated bracket [0.02, 0.05]. The stated probability carries a calibration error of 0.08 on 412 calibration observations in this cell, segment thin-file, error bar ±0.07 at 95%.
Drift: inputs and scores OK. Outcome recheck as of 2026-08-31, n = 1,240: OK.
Routing: ALLOW under policy credit-pd@4 · guarantee scope: stage · criticality 16 (advisory)
Reasons: Route trace: rules 1 to 5 passed; rule 6 allows. Certificate reasons: input within the scope of the guarantee; one label left standing; 412 observations in the cell. The model's own reason codes are recorded as received: R01, R07.
Note: this is not a probability that this applicant turns out well.
```

The certificate names the calibration data behind its guarantee: its size,
freeze date and hash. Coverage belongs to the procedure over that calibration set, not
to any one decision; the banned-wording list below enforces that, and the
reading rules are set out once in
[Note](https://github.com/reliax-io#note). When
outcomes land they are checked against what was claimed and join the next
set, which is a new frozen set under a new hash, so every later
certificate names it.

## Python

```python
from reliax_certificate import seal, verify_records, render_certificate, fidelity_check

record = seal(payload)                       # first record: prev_hash is 64 zeros
record2 = seal(payload2, record["hash"])     # chained
report = verify_records([record, record2], recompute=False)
report["ok"], report["chain"]["head"], report["per_record"]

text = render_certificate(payload)           # the template rendering, deterministic
fidelity_check("Coverage target 95%, credibility 0.61.", payload)["ok"]
```

`examples/chain.json` is a two-record chain built by `examples/make_example.py`;
`reliax verify examples/chain.json --recompute` passes with reliax-core installed.

## Two levels of replay

From the record alone: the chain, the stored wording, the route and its
reasons, the versions. With the customer-held inputs and the calibration
reference, which never leave the customer: the credibility, the segment
membership and the prediction set, recomputed with reliax-core. The claim
"replayable by an auditor" names both levels.

## Development

```
git clone https://github.com/reliax-io/reliax-certificate.git && cd reliax-certificate
python -m venv .venv && .venv/bin/pip install -e ".[test,recompute]"
.venv/bin/python -m pytest
```

A change to the schema, the template or the banned wording is a new version
and goes through an issue first: see
[CONTRIBUTING.md](https://github.com/reliax-io/.github/blob/main/CONTRIBUTING.md).

## Licence

Apache-2.0, with its patent grant. See [LICENSE](LICENSE).

## About this documentation

The documentation in this repository was written with the help of AI and
reviewed by the Reliax team.
