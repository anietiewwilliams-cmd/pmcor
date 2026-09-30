"""Optimize step on published data: flow-rate study of Triemer et al. (2018), ESI Table S4.
Writes results/triemer_sweep.csv and figures/fig7_triemer_pareto.png."""
import csv, json
from pathlib import Path
import pmcor
ROOT = Path(__file__).resolve().parents[1]
tmpl = json.loads((ROOT / "examples/lit_triemer_photooxidation.json").read_text())
S4 = [(0.75, 52.1), (0.5, 80.8), (0.33, 83.1), (0.2, 84.1)]  # liquid flow (mL/min), yield of PO1 (%)

def apply(rec, row):
    rec["flow_streams"][0]["flow_rate_mL_min"] = row["Q_L"]
    rec["product"]["yield_pct"] = row["yield"]
    return rec

sweep = pmcor.sweep(tmpl, [{"Q_L": q, "yield": y} for q, y in S4], apply)
ref = next(r for r in sweep if r["Q_L"] == 0.2)
for r in sweep:
    r["rel_pmi"] = r["pmi"] / ref["pmi"]
    r["rel_energy"] = r["energy_intensity"] / ref["energy_intensity"]
    r["throughput_rel"] = (r["Q_L"] * r["yield"]) / (ref["Q_L"] * ref["yield"])
front = pmcor.pareto(sweep, ["pmi", "energy_intensity"])
out = ROOT / "results"; out.mkdir(exist_ok=True)
keys = ["Q_L", "yield", "pmi", "energy_intensity", "rel_pmi", "rel_energy", "throughput_rel"]
with open(out / "triemer_sweep.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(keys + ["pareto"])
    for r in sweep: w.writerow([round(r[k], 3) if isinstance(r[k], float) else r[k] for k in keys] + [r in front])
for r in sweep: print({k: (round(r[k], 3) if isinstance(r[k], float) else r[k]) for k in keys}, "pareto" if r in front else "")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
FLOW, INK, MUTED, GRID = "#1B9E77", "#16211D", "#6b6b6b", "#e5e5e5"
fig, ax = plt.subplots(figsize=(4.4, 2.9))
onf = {id(r) for r in front}
for r in sweep:
    ax.scatter(r["rel_energy"], r["rel_pmi"], s=34, color=FLOW if id(r) in onf else "#b9c7c2", edgecolor="white", lw=0.8, zorder=3)
    ax.annotate(f"{r['Q_L']} mL min$^{{-1}}$\n({r['yield']:.0f}%)", (r["rel_energy"], r["rel_pmi"]), textcoords="offset points",
                xytext=(7, 2), fontsize=6.5, color=INK)
fs = sorted(front, key=lambda r: r["rel_energy"])
ax.plot([r["rel_energy"] for r in fs], [r["rel_pmi"] for r in fs], color=INK, lw=1, zorder=2)
ax.set_xlabel("Lamp energy per kg (relative to 0.2 mL min$^{-1}$)"); ax.set_ylabel("Reaction-step PMI (relative)")
ax.set_xlim(0.3, 1.15); ax.set_ylim(0.95, 1.7)
ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.text(-0.16, 1.02, "(b)", transform=ax.transAxes, fontsize=10, fontweight="bold", color=INK)
fig.tight_layout(); (ROOT / "figures").mkdir(exist_ok=True); fig.savefig(ROOT / "figures/fig7_triemer_pareto.png", dpi=600); plt.close(fig)
