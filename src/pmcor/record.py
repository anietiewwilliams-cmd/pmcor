"""Data model for a process record: materials, flow streams, product, energy.

A *record* is the machine-readable description of one experiment or process
condition: what went in (by stage), what came out, how much energy was used,
and which system boundary the author declares. Records can be written by hand
as JSON or generated from pump logs / ELN exports.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .chem import molar_mass, solvent

STAGES = ("reaction", "workup", "purification", "cleaning")
SOLVENT_ROLES = {"solvent", "extraction", "eluent", "wash", "quench_solvent"}


def _mw(d: dict) -> Optional[float]:
    if d.get("mw") is not None:
        return float(d["mw"])
    if d.get("formula"):
        return molar_mass(d["formula"])
    return None


@dataclass
class Material:
    name: str
    mass_g: float
    stage: str = "reaction"
    role: str = "reagent"
    is_water: bool = False
    recovered_fraction: float = 0.0
    waste_class: str = "organic"  # organic | aqueous | solid | gas
    chem21: Optional[str] = None
    assumed: bool = False
    note: str = ""

    @property
    def is_solvent(self) -> bool:
        return self.role in SOLVENT_ROLES

    @classmethod
    def from_dict(cls, d: dict) -> "Material":
        name = d["name"]
        sdata = solvent(d.get("solvent_key", name))
        if d.get("mass_g") is not None:
            mass = float(d["mass_g"])
        elif d.get("mass_mg") is not None:
            mass = float(d["mass_mg"]) / 1000.0
        elif d.get("volume_mL") is not None:
            rho = d.get("density") or (sdata.density if sdata else None)
            if rho is None:
                raise ValueError(f"{name}: volume given but no density known")
            mass = float(d["volume_mL"]) * float(rho)
        elif d.get("mmol") is not None:
            mw = _mw(d)
            if mw is None:
                raise ValueError(f"{name}: mmol given but no mw/formula")
            mass = float(d["mmol"]) * mw / 1000.0
        else:
            raise ValueError(f"{name}: need mass_g, mass_mg, volume_mL or mmol")
        role = d.get("role", "solvent" if sdata else "reagent")
        chem21 = d.get("chem21") or (sdata.chem21 if sdata and role in SOLVENT_ROLES else None)
        is_water = d.get("is_water", name.strip().lower() == "water")
        return cls(
            name=name, mass_g=mass, stage=d.get("stage", "reaction"), role=role,
            is_water=is_water, recovered_fraction=float(d.get("recovered_fraction", 0.0)),
            waste_class=d.get("waste_class", "aqueous" if is_water else ("solid" if role == "stationary_phase" else "organic")),
            chem21=chem21, assumed=bool(d.get("assumed", False)), note=d.get("note", ""),
        )


@dataclass
class Solute:
    name: str
    conc_M: float
    mw: float
    role: str = "reagent"


@dataclass
class FlowStream:
    """A pumped feed. Mass delivered = flow rate x operating time."""
    name: str
    flow_rate_mL_min: float
    solvent_name: str
    solutes: List[Solute] = field(default_factory=list)
    stage: str = "reaction"
    solvent_density: Optional[float] = None
    assumed: bool = False

    def to_materials(self, duration_min: float) -> List[Material]:
        vol = self.flow_rate_mL_min * duration_min  # mL
        sdata = solvent(self.solvent_name)
        rho = self.solvent_density or (sdata.density if sdata else None)
        if rho is None:
            raise ValueError(f"stream {self.name}: unknown solvent density")
        mats = [Material(
            name=f"{self.solvent_name} ({self.name})", mass_g=vol * rho, stage=self.stage,
            role="solvent", chem21=sdata.chem21 if sdata else None, assumed=self.assumed,
            note=f"{vol:.2f} mL at {self.flow_rate_mL_min} mL/min x {duration_min:.1f} min",
        )]
        for s in self.solutes:
            mmol = s.conc_M * vol  # M x mL = mmol
            mats.append(Material(name=s.name, mass_g=mmol * s.mw / 1000.0, stage=self.stage,
                                 role=s.role, assumed=self.assumed,
                                 note=f"{mmol:.3f} mmol from {self.name}"))
        return mats

    def mmol_of(self, solute_name: str, duration_min: float) -> float:
        for s in self.solutes:
            if s.name == solute_name:
                return s.conc_M * self.flow_rate_mL_min * duration_min
        raise KeyError(solute_name)

    @classmethod
    def from_dict(cls, d: dict) -> "FlowStream":
        solutes = [Solute(name=s["name"], conc_M=float(s["conc_M"]), mw=_mw(s), role=s.get("role", "reagent"))
                   for s in d.get("solutes", [])]
        return cls(name=d["name"], flow_rate_mL_min=float(d["flow_rate_mL_min"]),
                   solvent_name=d["solvent"], solutes=solutes, stage=d.get("stage", "reaction"),
                   solvent_density=d.get("solvent_density"), assumed=bool(d.get("assumed", False)))


@dataclass
class EnergyInput:
    device: str
    power_W: float
    duration_h: float
    stage: str = "reaction"
    source: str = "nameplate"  # metered | nameplate | assumed

    @property
    def kWh(self) -> float:
        return self.power_W * self.duration_h / 1000.0

    @classmethod
    def from_dict(cls, d: dict) -> "EnergyInput":
        if "duration_h" in d:
            h = float(d["duration_h"])
        else:
            h = float(d["duration_min"]) / 60.0
        return cls(device=d["device"], power_W=float(d["power_W"]), duration_h=h,
                   stage=d.get("stage", "reaction"), source=d.get("source", "nameplate"))


@dataclass
class Product:
    name: str
    mass_g: float
    mw: Optional[float]
    yield_type: str = "isolated"  # isolated | assay (NMR/HPLC)
    mmol: Optional[float] = None


@dataclass
class Process:
    name: str
    mode: str  # batch | flow
    product: Product
    materials: List[Material]
    energy: List[EnergyInput] = field(default_factory=list)
    declared_boundary: List[str] = field(default_factory=lambda: ["reaction"])
    ae_reactants: List[dict] = field(default_factory=list)
    run_time_min: Optional[float] = None
    source: str = ""
    basis: str = ""
    notes: List[str] = field(default_factory=list)
    reported: Optional[dict] = None  # literature values entered as reported

    @classmethod
    def from_dict(cls, d: dict) -> "Process":
        streams = [FlowStream.from_dict(s) for s in d.get("flow_streams", [])]
        run_time = d.get("run_time_min")
        rb = d.get("run_basis")
        if rb and streams:
            # operating time needed to deliver `mmol` of a named solute
            for s in streams:
                if any(x.name == rb["solute"] for x in s.solutes):
                    conc = next(x.conc_M for x in s.solutes if x.name == rb["solute"])
                    run_time = float(rb["mmol"]) / (conc * s.flow_rate_mL_min)
                    break
            else:
                raise KeyError(f"run_basis solute {rb['solute']} not in any stream")
        materials = [Material.from_dict(m) for m in d.get("materials", [])]
        if streams:
            if run_time is None:
                raise ValueError(f"{d['name']}: flow streams need run_time_min or run_basis")
            for s in streams:
                materials = s.to_materials(run_time) + materials

        p = d.get("product", {})
        mw = _mw(p)
        if p.get("mass_g") is not None:
            mass, mmol = float(p["mass_g"]), (float(p["mass_g"]) * 1000 / mw if mw else None)
        elif p.get("mass_mg") is not None:
            mass, mmol = float(p["mass_mg"]) / 1000, (float(p["mass_mg"]) / mw if mw else None)
        elif p.get("mmol") is not None:
            mmol = float(p["mmol"]); mass = mmol * mw / 1000
        elif p.get("yield_pct") is not None:
            mmol = float(p["yield_pct"]) / 100 * float(p["limiting_mmol"]); mass = mmol * mw / 1000
        elif d.get("reported"):
            mass, mmol = 1.0, None
        else:
            raise ValueError(f"{d['name']}: product amount missing")
        product = Product(name=p.get("name", "product"), mass_g=mass, mw=mw,
                          yield_type=p.get("yield_type", "isolated"), mmol=mmol)

        energy = []
        for e in d.get("energy", []):
            if e.get("duration") == "run_time":
                e = {**e, "duration_min": run_time}
            energy.append(EnergyInput.from_dict(e))

        return cls(name=d["name"], mode=d.get("mode", "batch"), product=product, materials=materials,
                   energy=energy, declared_boundary=d.get("declared_boundary", ["reaction"]),
                   ae_reactants=d.get("ae_reactants", []), run_time_min=run_time,
                   source=d.get("source", ""), basis=d.get("basis", ""), notes=d.get("notes", []),
                   reported=d.get("reported"))

    def with_extra(self, name: str, extra: List[dict], stages: Optional[List[str]] = None) -> "Process":
        """Return a copy with additional materials (e.g., a workup scenario)."""
        import copy
        p = copy.deepcopy(self)
        p.name = name
        p.materials += [Material.from_dict(m) for m in extra]
        if stages:
            p.declared_boundary = stages
        return p


def load(path) -> Process:
    return Process.from_dict(json.loads(Path(path).read_text()))


def load_many(paths) -> Dict[str, Process]:
    out = {}
    for pth in paths:
        pr = load(pth)
        out[pr.name] = pr
    return out
