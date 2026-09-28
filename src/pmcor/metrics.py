"""Green-metric calculations and boundary-aware comparison.

Definitions (all per mass of product, g/g == kg/kg):
  PMI            = sum(input masses within boundary) / product mass
  E-factor       = (sum(inputs) - product) / product          (Sheldon; water incl.)
  E-factor (dry) = as above, excluding water inputs
  Solvent int.   = sum(solvent-role masses) / product
  Energy int.    = sum(kWh) / kg product
  AE             = MW(product) / sum(coeff * MW(reactants)) x 100
  RME            = product mass / sum(stoichiometric reactant masses) x 100
PMI (recycle credit) subtracts the recovered fraction of each input; reported
separately so that recovery claims are visible rather than silently applied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .chem import CHEM21_ORDER, molar_mass
from .record import STAGES, Process


@dataclass
class Result:
    name: str
    mode: str
    boundary: List[str]
    product_g: float
    yield_type: str
    input_g: float
    pmi: float
    pmi_by_stage: Dict[str, float]
    pmi_recycle_credit: float
    e_factor: float
    e_factor_dry: float
    e_factor_by_class: Dict[str, float]
    solvent_intensity: float
    solvent_intensity_by_stage: Dict[str, float]
    solvent_share: float
    energy_kWh: Optional[float]
    energy_intensity: Optional[float]
    energy_sources: List[str]
    atom_economy: Optional[float]
    rme: Optional[float]
    chem21_mass: Dict[str, float]
    worst_solvent_class: Optional[str]
    breakdown: Dict[str, float]
    flags: List[str] = field(default_factory=list)
    reported: bool = False

    def row(self) -> dict:
        r = lambda x, n=1: None if x is None else round(x, n)
        return {
            "process": self.name, "mode": self.mode, "boundary": "+".join(self.boundary),
            "PMI": r(self.pmi), "E-factor": r(self.e_factor),
            "SI": r(self.solvent_intensity), "solvent %": r(100 * self.solvent_share),
            "EI (kWh/kg)": r(self.energy_intensity, 0), "AE %": r(self.atom_economy),
            "RME %": r(self.rme), "worst CHEM21": self.worst_solvent_class,
        }


def _ae(proc: Process) -> Optional[float]:
    if not proc.ae_reactants or not proc.product.mw:
        return None
    denom = 0.0
    for r in proc.ae_reactants:
        mw = r.get("mw") or molar_mass(r["formula"])
        denom += float(r.get("coeff", 1)) * float(mw)
    return 100.0 * proc.product.mw / denom


def compute(proc: Process, boundary: Optional[List[str]] = None) -> Result:
    """Compute metrics for a process within a boundary (list of stages).

    Defaults to the boundary the record declares.
    """
    bnd = list(boundary or proc.declared_boundary)
    flags: List[str] = []

    if proc.reported:
        return _from_reported(proc, bnd)

    unknown = set(bnd) - set(STAGES)
    if unknown:
        raise ValueError(f"unknown stage(s) {unknown}")
    mats = [m for m in proc.materials if m.stage in bnd]
    P = proc.product.mass_g
    if P <= 0:
        raise ValueError("product mass must be positive")

    total = sum(m.mass_g for m in mats)
    by_stage = {s: sum(m.mass_g for m in mats if m.stage == s) / P for s in bnd}
    water = sum(m.mass_g for m in mats if m.is_water)
    credit = sum(m.mass_g * m.recovered_fraction for m in mats)
    by_class: Dict[str, float] = {}
    for m in mats:
        w = m.mass_g * (1 - m.recovered_fraction)
        by_class[m.waste_class] = by_class.get(m.waste_class, 0.0) + w / P
    # product leaves as product, not waste: remove from organic share
    by_class["organic"] = by_class.get("organic", 0.0) - 1.0

    solv = [m for m in mats if m.is_solvent]
    solv_mass = sum(m.mass_g for m in solv)
    si_stage = {s: sum(m.mass_g for m in solv if m.stage == s) / P for s in bnd}
    chem21: Dict[str, float] = {}
    for m in solv:
        k = m.chem21 or "Not ranked"
        chem21[k] = chem21.get(k, 0.0) + m.mass_g / P
    ranked = [c for c in CHEM21_ORDER[:-1] if c in chem21]
    worst = ranked[-1] if ranked else None

    en = [e for e in proc.energy if e.stage in bnd]
    kwh = sum(e.kWh for e in en) if en else None
    ei = kwh / (P / 1000.0) if kwh is not None else None

    react = [m for m in mats if m.role == "reactant"]
    rme = 100.0 * P / sum(m.mass_g for m in react) if react else None

    breakdown = {}
    for m in mats:
        breakdown[m.name] = breakdown.get(m.name, 0.0) + m.mass_g / P

    # ---- audit flags -------------------------------------------------
    if proc.product.yield_type != "isolated":
        flags.append(f"Product mass is an {proc.product.yield_type} yield, not isolated; PMI is a lower bound.")
    if bnd == ["reaction"]:
        flags.append("Boundary is reaction-step only; workup/purification excluded.")
    missing = [s for s in bnd if s != "reaction" and not any(m.stage == s for m in proc.materials)]
    if missing:
        flags.append(f"Declared stage(s) {missing} contain no materials.")
    if kwh is None:
        flags.append("No energy inventory: energy intensity not determinable.")
    else:
        srcs = sorted({e.source for e in en})
        if srcs != ["metered"]:
            flags.append(f"Energy from {'/'.join(srcs)} values, not metered.")
        stages_no_e = [s for s in bnd if not any(e.stage == s for e in en)]
        if stages_no_e and any(by_stage.get(s, 0) > 0 for s in stages_no_e):
            flags.append(f"No energy logged for stage(s) {stages_no_e}.")
        if proc.mode == "flow" and proc.run_time_min:
            short = [e.device for e in en if e.duration_h * 60 < 0.99 * proc.run_time_min]
            if short:
                flags.append(f"Energy duration for {short} is shorter than the operating time "
                             f"({proc.run_time_min:.0f} min); residence time is not run time.")
    if any(m.assumed for m in mats):
        flags.append("Inventory contains assumed quantities: " + ", ".join(sorted({m.name for m in mats if m.assumed})) + ".")
    if "Not ranked" in chem21:
        flags.append("Some solvents lack a CHEM21 ranking.")

    return Result(
        name=proc.name, mode=proc.mode, boundary=bnd, product_g=P,
        yield_type=proc.product.yield_type, input_g=total, pmi=total / P, pmi_by_stage=by_stage,
        pmi_recycle_credit=(total - credit) / P, e_factor=(total - P) / P,
        e_factor_dry=(total - water - P) / P, e_factor_by_class=by_class,
        solvent_intensity=solv_mass / P, solvent_intensity_by_stage=si_stage,
        solvent_share=solv_mass / total if total else 0.0, energy_kWh=kwh, energy_intensity=ei,
        energy_sources=sorted({e.source for e in en}), atom_economy=_ae(proc), rme=rme,
        chem21_mass=chem21, worst_solvent_class=worst, breakdown=breakdown, flags=flags,
    )


def _from_reported(proc: Process, bnd: List[str]) -> Result:
    rep = proc.reported
    by_stage = {s: float(v) for s, v in rep.get("pmi_by_stage", {}).items() if s in bnd}
    pmi = float(rep["pmi"]) if "pmi" in rep and set(bnd) >= set(rep.get("pmi_by_stage", {})) else sum(by_stage.values())
    flags = ["Values entered as reported in the source; inventory not recomputed."]
    return Result(
        name=proc.name, mode=proc.mode, boundary=bnd, product_g=1.0, yield_type="reported",
        input_g=pmi, pmi=pmi, pmi_by_stage=by_stage, pmi_recycle_credit=pmi,
        e_factor=pmi - 1, e_factor_dry=pmi - 1, e_factor_by_class={}, solvent_intensity=float(rep.get("solvent_intensity", float("nan"))),
        solvent_intensity_by_stage={}, solvent_share=float("nan"), energy_kWh=None,
        energy_intensity=rep.get("energy_intensity"), energy_sources=[], atom_economy=rep.get("atom_economy"),
        rme=None, chem21_mass={}, worst_solvent_class=None, breakdown={}, flags=flags, reported=True,
    )


@dataclass
class Comparison:
    a: Result
    b: Result
    ratios: Dict[str, Optional[float]]
    symmetric: bool
    warnings: List[str]

    def verdict(self, metric: str = "pmi") -> str:
        r = self.ratios.get(metric)
        if r is None:
            return "not determinable"
        if abs(r - 1) < 0.05:
            return "equivalent"
        better = self.b.name if r > 1 else self.a.name
        return f"{better} lower by {max(r, 1 / r):.1f}x"


def compare(a: Process, b: Process, boundary: Optional[List[str]] = None) -> Comparison:
    """Compare process A against B (ratio = A/B) on an identical boundary.

    If no boundary is given, each record's declared boundary is used and an
    asymmetry warning is raised when they differ.
    """
    warnings = []
    if boundary is None:
        ra, rb = compute(a), compute(b)
        if set(ra.boundary) != set(rb.boundary):
            warnings.append(f"Asymmetric boundaries: {a.name}={ra.boundary}, {b.name}={rb.boundary}. "
                            "Ratios compare unlike systems.")
    else:
        ra, rb = compute(a, boundary), compute(b, boundary)
    for r, p in ((ra, a), (rb, b)):
        for s in r.boundary:
            if s != "reaction" and not p.reported and not any(m.stage == s for m in p.materials):
                warnings.append(f"{p.name}: stage '{s}' is inside the boundary but empty "
                                "(is no workup really required?).")

    def ratio(x, y):
        return None if x is None or y is None or y == 0 else x / y
    ratios = {
        "pmi": ratio(ra.pmi, rb.pmi), "e_factor": ratio(ra.e_factor, rb.e_factor),
        "solvent_intensity": ratio(ra.solvent_intensity, rb.solvent_intensity),
        "energy_intensity": ratio(ra.energy_intensity, rb.energy_intensity),
    }
    return Comparison(ra, rb, ratios, symmetric=not any("Asymmetric" in w for w in warnings), warnings=warnings)


# ---------------------------------------------------------------------------
# Minimum reporting card
# ---------------------------------------------------------------------------
CARD_ITEMS = [
    ("boundary", "System boundary declared (stages included)"),
    ("isolated", "Product basis is isolated mass"),
    ("pmi_stage", "PMI reported by stage (reaction / workup / purification)"),
    ("efactor_class", "E-factor split by waste class (organic / aqueous / solid)"),
    ("si", "Solvent intensity with CHEM21 class"),
    ("energy", "Energy intensity with source (metered / nameplate)"),
    ("recovery", "Recovery / recycle assumptions stated"),
    ("no_assumed", "No assumed (unmeasured) inventory items"),
]


def card(proc: Process, res: Optional[Result] = None) -> Dict[str, bool]:
    res = res or compute(proc)
    has_post = any(s in res.boundary for s in ("workup", "purification"))
    return {
        "boundary": bool(proc.declared_boundary),
        "isolated": res.yield_type == "isolated",
        "pmi_stage": has_post,
        "efactor_class": len([v for v in res.e_factor_by_class.values() if v > 0]) >= 1 and not res.reported,
        "si": bool(res.chem21_mass) and "Not ranked" not in res.chem21_mass,
        "energy": res.energy_intensity is not None,
        "recovery": any(m.recovered_fraction > 0 for m in proc.materials) or any("recover" in n.lower() for n in proc.notes),
        "no_assumed": not any(m.assumed for m in proc.materials),
    }


def completeness(proc: Process, res: Optional[Result] = None) -> float:
    c = card(proc, res)
    return sum(c.values()) / len(c)
