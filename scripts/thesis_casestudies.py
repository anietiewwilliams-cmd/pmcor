"""
NOTE: the artemisinin case (Fig. 7) is a literature record; see scripts/triemer_sweep.py.
Reproduce every number and figure in the Perspective's worked examples.

Run:  python scripts/thesis_casestudies.py   (writes results/ and figures/)

All calculations are retrospective: they use experimental records archived in
A. W. Williams' PhD thesis (UConn, 2026), not live instrument streams.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pmcor
from pmcor import compare, completeness, card, compute, load
from pmcor.metrics import CARD_ITEMS

ROOT = Path(__file__).resolve().parents[1]
EX, OUT, FIG = ROOT / "examples", ROOT / "results", ROOT / "figures"
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)

# ---------------------------------------------------------------- records
batch = load(EX / "ch3_srn1_batch.json")
flow = load(EX / "ch3_srn1_flow.json")
ch4 = load(EX / "ch4_hydroamination.json")
lit = {p.stem: load(p) for p in sorted(EX.glob("lit_*.json"))}

# Workup scenarios from thesis Section 3.9, applied identically to both modes.
EXTRACTION = [{"name": "hexanes (extraction)", "volume_mL": 40, "solvent_key": "hexanes",
               "stage": "workup", "role": "extraction"}]
COLUMN = [{"name": "silica gel", "mass_g": 10.0, "stage": "purification", "role": "stationary_phase"},
          {"name": "hexanes/EtOAc eluent", "mass_g": 61.6, "stage": "purification", "role": "eluent",
           "chem21": "Hazardous", "note": "80 mL, hexanes-rich"}]

scen = {}
scen["A. Reaction step"] = (batch, flow)
scen["B. Asymmetric\n(batch + column, flow + none)"] = (
    batch.with_extra("batch + column", COLUMN, ["reaction", "purification"]), flow)
scen["C. Both + extraction"] = (
    batch.with_extra("batch + extraction", EXTRACTION, ["reaction", "workup"]),
    flow.with_extra("flow + extraction", EXTRACTION, ["reaction", "workup"]))
scen["D. Both + column"] = (
    batch.with_extra("batch + column", COLUMN, ["reaction", "purification"]),
    flow.with_extra("flow + column", COLUMN, ["reaction", "purification"]))

ch3_rows = []
for label, (a, b) in scen.items():
    c = compare(a, b)
    ch3_rows.append({"scenario": label.replace("\n", " "), "batch_PMI": c.a.pmi, "flow_PMI": c.b.pmi,
                     "flow/batch": c.b.pmi / c.a.pmi, "symmetric": c.symmetric,
                     "warnings": " | ".join(c.warnings)})

# THF recovery sensitivity (90 % recovered in both modes, reaction step)
def with_recovery(p, frac):
    import copy
    q = copy.deepcopy(p)
    for m in q.materials:
        if m.role == "solvent":
            m.recovered_fraction = frac
    return q
rec90 = (compute(with_recovery(batch, 0.9)).pmi_recycle_credit, compute(with_recovery(flow, 0.9)).pmi_recycle_credit)

# Energy: residence time vs operating time (illustrative, same 80 W device)
def flow_energy(minutes):
    import copy
    q = copy.deepcopy(flow)
    q.energy = [pmcor.record.EnergyInput("80 W device", 80, minutes / 60, "reaction", "nameplate")]
    return compute(q)
e_tau, e_run = flow_energy(33.3), flow_energy(flow.run_time_min)

# PMI floor for batch (100 % yield at current THF loading)
P100 = 1.0 * pmcor.molar_mass("C16H17N") / 1000
floor_pmi = compute(batch).input_g / P100
floor_si = sum(m.mass_g for m in batch.materials if m.role == "solvent") / P100

# ---------------------------------------------------------------- outputs
allres = {"Ch3 batch (opt.)": (batch, compute(batch)), "Ch3 flow (entry 5)": (flow, compute(flow)),
          "Ch4 hydroamination": (ch4, compute(ch4))}
for k, p in lit.items():
    allres[p.name] = (p, compute(p))

with open(OUT / "summary.md", "w") as fh:
    fh.write("# pmcor results (retrospective)\n\n")
    fh.write(pmcor.markdown_table([r for _, r in allres.values()]) + "\n\n")
    for name, (p, r) in allres.items():
        fh.write("```\n" + pmcor.summary(r, p) + "\n```\n\n")
    fh.write("## Ch3 boundary scenarios\n\n| scenario | batch PMI | flow PMI | flow/batch | symmetric |\n|---|---|---|---|---|\n")
    for r in ch3_rows:
        fh.write(f"| {r['scenario']} | {r['batch_PMI']:.1f} | {r['flow_PMI']:.1f} | {r['flow/batch']:.2f} | {r['symmetric']} |\n")
    fh.write(f"\nTHF 90% recovery credit (reaction step): batch {rec90[0]:.1f}, flow {rec90[1]:.1f}\n")
    fh.write(f"Flow energy, 80 W over residence time 33.3 min: {e_tau.energy_intensity:,.0f} kWh/kg; "
             f"over operating time {flow.run_time_min:.1f} min: {e_run.energy_intensity:,.0f} kWh/kg\n")
    fh.write(f"Flags (residence-time case): {e_tau.flags}\n")
    fh.write(f"Batch PMI floor at 100% yield: {floor_pmi:.1f}; solvent-only floor {floor_si:.1f}\n\n")

with open(OUT / "ch3_boundaries.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(ch3_rows[0])); w.writeheader(); w.writerows(ch3_rows)
# ---------------------------------------------------------------- figures
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BATCH, FLOW, INK, MUTED, GRID = "#D95F32", "#1B9E77", "#1f1f1f", "#6b6b66", "#e4e4e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 600})

# ---- Fig. 5: Ch3 boundary
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.1, 3.1), gridspec_kw={"width_ratios": [3.2, 1]})
labels = list(scen)
x = range(len(labels)); w = 0.36
bv = [r["batch_PMI"] for r in ch3_rows]; fv = [r["flow_PMI"] for r in ch3_rows]
ax.bar([i - w / 2 - 0.01 for i in x], bv, w, color=BATCH, label="Batch (80%, 0.10 M)")
ax.bar([i + w / 2 + 0.01 for i in x], fv, w, color=FLOW, label="Flow (44%, 0.02 M combined)")
for i, (b_, f_) in enumerate(zip(bv, fv)):
    ax.text(i - w / 2, b_ + 15, f"{b_:.0f}", ha="center", color=INK, fontsize=7.5)
    ax.text(i + w / 2, f_ + 15, f"{f_:.0f}", ha="center", color=INK, fontsize=7.5)
    ratio = f_ / b_
    ax.text(i, max(b_, f_) + 95, f"flow/batch {ratio:.1f}×", ha="center", color=MUTED, fontsize=7)
ax.text(1 + w / 2 + 0.01, fv[1] / 2, "no\nworkup\ncounted", ha="center", va="center", color="white", fontsize=6)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=7.2)
ax.set_ylabel("PMI (g input per g product)"); ax.set_ylim(0, max(fv + bv) * 1.2)
ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", fontsize=7.5)
ax.set_title("(b) Same chemistry, four boundaries", loc="left", fontsize=9, color=INK)
thf_b = sum(m.mass_g for m in batch.materials if m.role == "solvent") / 0.889
thf_f = sum(m.mass_g for m in flow.materials if m.role == "solvent") / 0.889
ax2.bar([0], [thf_b], 0.55, color=BATCH); ax2.bar([1], [thf_f], 0.55, color=FLOW)
for i, v in enumerate([thf_b, thf_f]):
    ax2.text(i, v + 1, f"{v:.0f} mL", ha="center", fontsize=7.5, color=INK)
ax2.set_xticks([0, 1]); ax2.set_xticklabels(["Batch", "Flow"])
ax2.set_ylabel("THF per mmol substrate (mL)"); ax2.set_ylim(0, thf_f * 1.25)
ax2.yaxis.grid(True, color=GRID, lw=0.6); ax2.set_axisbelow(True)
ax2.set_title("(c) The hidden cost", loc="left", fontsize=9, color=INK)
fig.tight_layout(); fig.savefig(FIG / "fig5_ch3_boundary.png"); plt.close(fig)

# ---- Fig. 6: audit card heatmap + PMI composition
order = ["Ch3 batch (opt.)", "Ch3 flow (entry 5)", "Ch4 hydroamination"]  # own records only; literature is not scored (see text)
short = {"Ch3 batch (opt.)": "SRN1 amination, batch", "Ch3 flow (entry 5)": "SRN1 amination, flow",
         "Ch4 hydroamination": "Hydroamination"}
fig = plt.figure(figsize=(7.1, 2.6))
gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 1], wspace=1.0)
axh = fig.add_subplot(gs[0]); axp = fig.add_subplot(gs[1])
keys = [k for k, _ in CARD_ITEMS]
colhead = ["Boundary declared", "Isolated mass", "PMI by stage", "E-factor by class", "SI + CHEM21 class",
           "Energy intensity", "Recovery stated", "No assumed inputs"]
for i, name in enumerate(order):
    p, r = allres[name]
    c = card(p, r)
    for j, k in enumerate(keys):
        ok = c[k]
        axh.add_patch(plt.Rectangle((j + 0.06, i + 0.06), 0.88, 0.88, color=FLOW if ok else "#f1e3dc", lw=0))
        axh.text(j + 0.5, i + 0.52, "✓" if ok else "✗", ha="center", va="center",
                 color="white" if ok else BATCH, fontsize=8)
    axh.text(len(keys) + 0.25, i + 0.52, f"{100 * completeness(p, r):.0f}%", va="center", fontsize=7.5, color=INK)
axh.set_xlim(0, len(keys) + 1.2); axh.set_ylim(len(order), 0)
axh.set_yticks([i + 0.5 for i in range(len(order))])
axh.set_yticklabels([short.get(n, n.replace(" (", "\n(")) for n in order], fontsize=7)
axh.set_xticks([j + 0.5 for j in range(len(keys))]); axh.set_xticklabels(colhead, fontsize=6.5, rotation=60, ha="left", rotation_mode="anchor")
axh.xaxis.tick_top(); axh.tick_params(length=0)
for s in axh.spines.values(): s.set_visible(False)
axh.text(-3.2, -2.45, "(a) Minimum reporting card", fontsize=9, color=INK)

thesis = order[:3]
solv = [allres[n][1].solvent_intensity for n in thesis]
other = [allres[n][1].pmi - allres[n][1].solvent_intensity for n in thesis]
y = range(len(thesis))
axp.barh(list(y), solv, color=FLOW, height=0.55, label="Solvent")
axp.barh(list(y), other, left=solv, color="#9fd3c1", height=0.55, label="Reagents & substrates")
for i, n in enumerate(thesis):
    r = allres[n][1]
    axp.text(r.pmi * 1.15, i, f"{r.pmi:.1f}  ({100 * r.solvent_share:.0f}% solvent)", va="center", fontsize=7, color=INK)
axp.set_xscale("log"); axp.set_xlim(5, 8000)
axp.set_yticks(list(y)); axp.set_yticklabels([short[n] for n in thesis], fontsize=7)
axp.invert_yaxis(); axp.set_xlabel("Reaction-step PMI (log scale)")
axp.xaxis.grid(True, color=GRID, lw=0.6, which="both"); axp.set_axisbelow(True)
axp.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
axp.set_title("(b) Where the mass goes", loc="left", fontsize=9, color=INK)
fig.savefig(FIG / "fig6_audit.png", bbox_inches="tight"); plt.close(fig)

# ---- Fig. 4: workflow schematic
fig, ax = plt.subplots(figsize=(7.1, 2.5)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 32)
boxes = [
    (1, "PLAN", "Declare the\nboundary: reaction,\nworkup, purification,\ncleaning"),
    (21, "MEASURE", "Inputs by stage:\npump rate × run\ntime, reservoir\nmasses, power"),
    (41, "COMPUTE", "PMI, E-factor,\nsolvent + energy\nintensity, AE, RME;\naudit flags"),
    (61, "OPTIMIZE", "Metrics for every\ncondition; Pareto\nset beside yield\nand productivity"),
    (81, "REPORT", "Symmetric batch/\nflow comparison;\nreporting card;\nJSON record in SI"),
]
for x0, head, body in boxes:
    ax.add_patch(FancyBboxPatch((x0, 3), 17.5, 25, boxstyle="round,pad=0.4,rounding_size=1.5",
                                fc="#eef7f3", ec=FLOW, lw=1))
    ax.text(x0 + 8.75, 24.3, head, ha="center", fontsize=8.5, weight="bold", color=FLOW)
    ax.text(x0 + 8.75, 13.8, body, ha="center", va="center", fontsize=6.6, color=INK, linespacing=1.4)
for x0 in (18.9, 38.9, 58.9, 78.9):
    ax.annotate("", xy=(x0 + 2.0, 15.5), xytext=(x0 + 0.1, 15.5), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1))
ax.text(50, 0.3, "pmcor  —  record.json  →  compute()  →  compare()  →  sweep()/pareto()  →  card()",
        ha="center", fontsize=7, family="DejaVu Sans Mono", color=MUTED)
fig.savefig(FIG / "fig4_workflow.png", bbox_inches="tight"); plt.close(fig)

print((OUT / "summary.md").read_text())
