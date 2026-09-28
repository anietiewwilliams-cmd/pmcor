"""pmcor — Plan, Measure, Compute, Optimize & Report green metrics for flow chemistry.

Turns a machine-readable process record (materials by stage, flow streams,
product, energy) into PMI, E-factor, solvent intensity, energy intensity,
atom economy and RME, with boundary-aware batch/flow comparison and audit
flags for the most common accounting errors.
"""
from .chem import molar_mass, solvent
from .metrics import Comparison, Result, card, compare, completeness, compute
from .record import FlowStream, Material, Process, load, load_many
from .optimize import pareto, sweep
from .report import markdown_table, summary

__version__ = "0.1.0"
__all__ = [
    "molar_mass", "solvent", "compute", "compare", "card", "completeness", "Result",
    "Comparison", "Process", "Material", "FlowStream", "load", "load_many",
    "markdown_table", "summary", "sweep", "pareto",
]
