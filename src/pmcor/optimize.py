"""Module D helpers: evaluate metrics across a condition sweep and find the Pareto set.

``sweep`` takes a record template (dict) and a list of condition rows, applies
each row with a user function, and returns metrics per row, so green metrics
can be ranked beside yield and productivity — or fed to an optimizer as
objectives.
"""
from __future__ import annotations

import copy
from typing import Callable, Dict, Iterable, List, Sequence

from .metrics import compute
from .record import Process


def sweep(template: dict, rows: Iterable[dict], apply: Callable[[dict, dict], dict]) -> List[Dict]:
    out = []
    for row in rows:
        rec = apply(copy.deepcopy(template), row)
        res = compute(Process.from_dict(rec))
        out.append({**row, "pmi": res.pmi, "solvent_intensity": res.solvent_intensity,
                    "energy_intensity": res.energy_intensity, "product_g": res.product_g,
                    "run_time_min": rec.get("run_time_min")})
    return out


def pareto(points: Sequence[Dict], minimize: Sequence[str]) -> List[Dict]:
    """Non-dominated subset of ``points`` for objectives to be minimized."""
    front = []
    for p in points:
        dominated = False
        for q in points:
            if q is p:
                continue
            if all(q[k] <= p[k] for k in minimize) and any(q[k] < p[k] for k in minimize):
                dominated = True
                break
        if not dominated:
            front.append(p)
    return front
