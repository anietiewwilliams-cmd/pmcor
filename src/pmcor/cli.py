"""Command-line interface.

  pmcor compute record.json [--boundary reaction,workup] [--json]
  pmcor compare a.json b.json [--boundary reaction,workup]
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from .metrics import compare, compute
from .record import load
from .report import summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="pmcor", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compute"); c.add_argument("records", nargs="+")
    c.add_argument("--boundary"); c.add_argument("--json", action="store_true")
    k = sub.add_parser("compare"); k.add_argument("a"); k.add_argument("b"); k.add_argument("--boundary")
    args = ap.parse_args(argv)
    bnd = args.boundary.split(",") if getattr(args, "boundary", None) else None

    if args.cmd == "compute":
        for path in args.records:
            proc = load(path)
            res = compute(proc, bnd)
            print(json.dumps(asdict(res), indent=2) if args.json else summary(res, proc))
            print()
    else:
        cmp = compare(load(args.a), load(args.b), bnd)
        print(summary(cmp.a)); print(); print(summary(cmp.b)); print()
        for w in cmp.warnings:
            print("WARNING:", w)
        for m, r in cmp.ratios.items():
            print(f"{m}: A/B = {'n/a' if r is None else f'{r:.2f}'}  ->  {cmp.verdict(m)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
