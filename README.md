# pmcor

**Plan → Measure → Compute → Optimize & Report.** Boundary-aware green metrics for flow (and batch) chemistry records.

`pmcor` turns a plain JSON record of a process (inputs by stage, pumped streams, product, energy) into PMI, E-factor (by waste class), solvent intensity with CHEM21 class, energy intensity, atom economy and RME. It also flags the accounting errors that most often decide a batch-versus-flow verdict by accident:

- **Asymmetric boundaries.** One route includes workup and the other does not.
- **Stages declared but empty.** "No workup required" is asserted, not shown.
- **Assay yields used as isolated mass.** This gives a lower-bound PMI.
- **Energy from residence time instead of operating time.** Common in flow.
- **Assumed quantities and nameplate power.** These are surfaced, not hidden.

It has no runtime dependencies. Plotting needs `matplotlib`.

## Install

```bash
pip install -e .            # from a clone
pip install -e ".[plot,test]"
```

## Use

```bash
pmcor compute examples/ch3_srn1_batch.json
pmcor compare examples/ch3_srn1_batch.json examples/ch3_srn1_flow.json --boundary reaction
```

```python
import pmcor
batch = pmcor.load("examples/ch3_srn1_batch.json")
res = pmcor.compute(batch)             # declared boundary
print(pmcor.summary(res, batch))
cmp = pmcor.compare(batch, pmcor.load("examples/ch3_srn1_flow.json"))
print(cmp.ratios, cmp.warnings)
```

## Record format

```json
{
  "name": "...", "mode": "batch | flow",
  "declared_boundary": ["reaction", "workup", "purification", "cleaning"],
  "materials": [
    {"name": "THF", "volume_mL": 10, "stage": "reaction", "role": "solvent"},
    {"name": "substrate", "formula": "C12H9F", "mmol": 1.0, "role": "reactant"},
    {"name": "silica gel", "mass_g": 10, "stage": "purification", "role": "stationary_phase"}
  ],
  "flow_streams": [
    {"name": "feed A", "flow_rate_mL_min": 0.12, "solvent": "THF",
     "solutes": [{"name": "substrate", "formula": "C12H9F", "conc_M": 0.05, "role": "reactant"}]}
  ],
  "run_basis": {"solute": "substrate", "mmol": 1.0},
  "product": {"formula": "C16H17N", "yield_pct": 80, "limiting_mmol": 1.0, "yield_type": "isolated | assay"},
  "ae_reactants": [{"formula": "C12H9F"}, {"formula": "C4H9N"}],
  "energy": [{"device": "sonicator", "power_W": 80, "duration_h": 4, "source": "metered | nameplate | assumed"}]
}
```

- **Amounts.** Each material can be given as `mass_g`, `mass_mg`, `volume_mL` (the density is looked up for common solvents), or `mmol` with `formula`/`mw`.
- **Flow streams.** These are converted to masses as flow rate × operating time. The operating time comes from `run_time_min`, or from `run_basis`, which is the time needed to deliver *n* mmol of a named solute.
- **Literature values.** Values that cannot be recomputed can be entered under `"reported"` and are flagged as such.

## Reproducing the Perspective

This repository accompanies A. W. Williams, F. M. Wariri and K. M. Gilmore, "Is green chemistry dead in flow? Closing the metrics gap with open, boundary-aware accounting", *Green Chem.* (submitted).

```bash
python scripts/thesis_casestudies.py   # writes results/summary.md, CSVs and figures/
python scripts/triemer_sweep.py        # Fig. 7
pytest -q
```

The artemisinin case (Fig. 7) uses the published inventory of Triemer et al., *Angew. Chem. Int. Ed.*, 2018, **57**, 5525: `examples/lit_triemer_artemisinin.json`, `examples/lit_triemer_photooxidation.json` and `scripts/triemer_sweep.py`.

The literature analysis (the metrics-gap survey) is in [`literature_analysis/`](literature_analysis/README.md).

All thesis calculations are **retrospective**. They use experimental records archived in A. W. Williams, PhD thesis, University of Connecticut (2026), not live instrument streams. Every assumed quantity is marked `"assumed": true` in `examples/`.

## Scope and limits

- Mass-based metrics are gate-to-gate within the declared stages. `pmcor` is not an LCA tool. Its records are meant to serve as the inventory for one.
- Energy intensity at laboratory scale reflects the equipment, not the chemistry. Compare within one platform, and report the source (metered or nameplate).
- CHEM21 rankings are the final categories from Prat et al., *Green Chem.*, 2016, **18**, 288. Override `chem21` for anything not listed.

## Licence and citation

Code: MIT licence (see `LICENSE`). Data files in `literature_analysis/data/`: CC BY 4.0.
If you use pmcor, please cite the Perspective above and the archived software (see `CITATION.cff`).
