"""Small chemical property helpers: molar masses from formulae and a solvent table.

The solvent table carries density (g/mL, ~20-25 degC) and the CHEM21 ranking
(Prat et al., Green Chem., 2016, 18, 288). Rankings are the final
"after discussion" category. Users should verify rankings against Table 7 of
that paper for any solvent not listed here and may override via ``Solvent``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

ATOMIC_MASS = {
    "H": 1.008, "Li": 6.94, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999,
    "F": 18.998, "Na": 22.990, "Mg": 24.305, "Si": 28.085, "P": 30.974,
    "S": 32.06, "Cl": 35.45, "K": 39.098, "Ca": 40.078, "Fe": 55.845,
    "Ni": 58.693, "Cu": 63.546, "Zn": 65.38, "Se": 78.971, "Br": 79.904,
    "Ru": 101.07, "Rh": 102.91, "Pd": 106.42, "Ag": 107.87, "Te": 127.60,
    "I": 126.90, "Ir": 192.22, "Pt": 195.08,
}

_TOKEN = re.compile(r"([A-Z][a-z]?|\(|\)|\d+)")


def molar_mass(formula: str) -> float:
    """Return molar mass (g/mol) for a formula such as 'C16H17N' or 'Ca(OH)2'."""
    tokens = _TOKEN.findall(formula.replace(" ", ""))
    if "".join(tokens) != formula.replace(" ", ""):
        raise ValueError(f"Cannot parse formula {formula!r}")
    stack = [0.0]
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "(":
            stack.append(0.0)
        elif t == ")":
            group = stack.pop()
            mult = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                mult = int(tokens[i + 1])
                i += 1
            stack[-1] += group * mult
        elif t.isdigit():
            raise ValueError(f"Unexpected count in {formula!r}")
        else:
            if t not in ATOMIC_MASS:
                raise KeyError(f"Element {t} not in table")
            mult = 1
            if i + 1 < len(tokens) and tokens[i + 1].isdigit():
                mult = int(tokens[i + 1])
                i += 1
            stack[-1] += ATOMIC_MASS[t] * mult
        i += 1
    if len(stack) != 1:
        raise ValueError(f"Unbalanced parentheses in {formula!r}")
    return stack[0]


@dataclass(frozen=True)
class SolventData:
    name: str
    density: float  # g/mL
    chem21: str  # Recommended | Problematic | Hazardous | Highly hazardous | Not ranked


# Final CHEM21 rankings (Prat et al. 2016, Table 7). Mixed or non-classical
# media are "Not ranked"; override explicitly if a ranking is known.
SOLVENTS = {
    "water": SolventData("water", 0.997, "Recommended"),
    "ethanol": SolventData("ethanol", 0.789, "Recommended"),
    "methanol": SolventData("methanol", 0.792, "Recommended"),
    "isopropanol": SolventData("isopropanol", 0.786, "Recommended"),
    "ethyl acetate": SolventData("ethyl acetate", 0.902, "Recommended"),
    "acetone": SolventData("acetone", 0.784, "Recommended"),
    "anisole": SolventData("anisole", 0.995, "Recommended"),
    "tert-butanol": SolventData("tert-butanol", 0.775, "Problematic"),
    "thf": SolventData("THF", 0.889, "Problematic"),
    "2-methf": SolventData("2-MeTHF", 0.854, "Problematic"),
    "cpme": SolventData("CPME", 0.860, "Problematic"),
    "toluene": SolventData("toluene", 0.867, "Problematic"),
    "heptane": SolventData("heptane", 0.684, "Problematic"),
    "acetonitrile": SolventData("acetonitrile", 0.786, "Problematic"),
    "dmso": SolventData("DMSO", 1.100, "Problematic"),
    "hexane": SolventData("hexane", 0.659, "Hazardous"),
    "hexanes": SolventData("hexanes", 0.659, "Hazardous"),
    "dichloromethane": SolventData("dichloromethane", 1.33, "Hazardous"),
    "dmf": SolventData("DMF", 0.944, "Hazardous"),
    "1,4-dioxane": SolventData("1,4-dioxane", 1.033, "Hazardous"),
    "mtbe": SolventData("MTBE", 0.740, "Hazardous"),
    "diethyl ether": SolventData("diethyl ether", 0.713, "Highly hazardous"),
}

CHEM21_ORDER = ["Recommended", "Problematic", "Hazardous", "Highly hazardous", "Not ranked"]


def solvent(name: str) -> Optional[SolventData]:
    return SOLVENTS.get(name.strip().lower())
