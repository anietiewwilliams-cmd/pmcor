"""Plain-text reporting helpers."""
from __future__ import annotations

from typing import Iterable

from .metrics import CARD_ITEMS, Result, card


def markdown_table(results: Iterable[Result]) -> str:
    rows = [r.row() for r in results]
    if not rows:
        return ""
    cols = list(rows[0])
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join("—" if r[c] is None else str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def summary(res: Result, proc=None) -> str:
    L = [f"== {res.name} ({res.mode}; boundary: {' + '.join(res.boundary)}) =="]
    if res.reported:
        L.append(f"Reported PMI {res.pmi:.1f}" + ("" if res.solvent_intensity != res.solvent_intensity
                                                   else f" | SI {res.solvent_intensity:.1f}"))
    else:
        L.append(f"Product: {res.product_g * 1000:.1f} mg ({res.yield_type})")
        L.append(f"PMI {res.pmi:.1f} | E-factor {res.e_factor:.1f} (dry {res.e_factor_dry:.1f}) | "
                 f"SI {res.solvent_intensity:.1f} ({100 * res.solvent_share:.1f}% of inputs)")
    if res.pmi_by_stage:
        L.append("PMI by stage: " + ", ".join(f"{k} {v:.1f}" for k, v in res.pmi_by_stage.items()))
    if res.pmi_recycle_credit < res.pmi - 1e-9:
        L.append(f"PMI with stated recovery credit: {res.pmi_recycle_credit:.1f}")
    if res.energy_intensity is not None:
        L.append(f"Energy {res.energy_kWh:.3f} kWh -> {res.energy_intensity:,.0f} kWh/kg ({'/'.join(res.energy_sources)})")
    if res.atom_economy is not None:
        L.append(f"AE {res.atom_economy:.1f}%" + (f" | RME {res.rme:.1f}%" if res.rme else ""))
    if res.chem21_mass:
        L.append("Solvent by CHEM21 class (g/g): " + ", ".join(f"{k} {v:.1f}" for k, v in res.chem21_mass.items()))
    for f in res.flags:
        L.append(f"  ! {f}")
    if proc is not None:
        c = card(proc, res)
        L.append("Reporting card: " + ", ".join(f"{'✓' if c[k] else '✗'} {k}" for k, _ in CARD_ITEMS))
    return "\n".join(L)
