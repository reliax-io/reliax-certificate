"""reliax verify record.json: the auditor's command."""
import argparse
import json
import sys

from . import __version__
from .verify import verify_file


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="reliax", description="Reliax certificate tools (Apache-2.0).")
    parser.add_argument("--version", action="version", version=f"reliax-certificate {__version__}")
    sub = parser.add_subparsers(dest="command")
    v = sub.add_parser("verify", help="verify a record or a chain of records from its JSON file")
    v.add_argument("path", help="record.json: one record, a list of records, or {\"records\": [...]}")
    v.add_argument("--recompute", action="store_true", help="also re-run the route with reliax-core and compare")
    v.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = parser.parse_args(argv)
    if args.command != "verify":
        parser.print_help()
        return 2
    try:
        report = verify_file(args.path, recompute=args.recompute)
    except (OSError, ValueError) as e:
        print(f"reliax verify: cannot read {args.path}: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        c = report["chain"]
        print(f"{report['records']} record(s) · chain {'intact' if c['ok'] else 'BROKEN at record ' + str(c['first_bad_index'])}"
              f" · head {c['head'][:12]}…")
        for r in report["per_record"]:
            mark = "ok " if r["ok"] else "FAIL"
            print(f"  [{mark}] record {r['index']} {r.get('audit_id', '')}")
            for issue in r["issues"]:
                print(f"         {issue}")
        for e in c["errors"]:
            print(f"  chain: {e}")
        print("VERIFIED" if report["ok"] else "NOT VERIFIED")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
