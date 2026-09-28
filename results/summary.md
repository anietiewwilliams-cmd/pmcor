# pmcor results (retrospective)

| process | mode | boundary | PMI | E-factor | SI | solvent % | EI (kWh/kg) | AE % | RME % | worst CHEM21 |
|---|---|---|---|---|---|---|---|---|---|---|
| Ch3 SRN1 amination — optimized batch | batch | reaction | 52.2 | 51.2 | 49.8 | 95.3 | 1791.0 | 91.8 | 51.0 | Problematic |
| Ch3 SRN1 amination — flow (Table 3.5, entry 5) | flow | reaction | 458.4 | 457.4 | 451.3 | 98.5 | — | 91.8 | 16.4 | Problematic |
| Ch4 anti-Markovnikov hydroamination (2-MeTHF) | batch | reaction | 19.5 | 18.5 | 18.2 | 93.6 | 213.0 | 100.0 | 83.3 | Problematic |
| (Fluoromethoxy)benzene, gram-scale SMBR run (Pieber 2018) | flow | reaction | 74.6 | 73.6 | 62.5 | 83.7 | — | 24.9 | 67.4 | Recommended |
| LiAlH4 reduction, batch (Prieschl 2020, ESI Table S6) | batch | reaction+workup | 49.3 | 48.3 | 45.4 | 92.1 | — | — | 73.3 | Hazardous |
| NaBH4 reduction, batch (Prieschl 2020, ESI Table S7) | batch | reaction+workup | 131.4 | 130.4 | 126.1 | 95.9 | — | — | 64.0 | Recommended |
| Ru-MACHO ester hydrogenation, flow (Prieschl 2020) | flow | reaction | 6.5 | 5.5 | 5.1 | 78.4 | — | 77.4 | 74.9 | Recommended |
| Ru-MACHO ester hydrogenation, flow long run (Prieschl 2020, ESI Table S5) | flow | reaction+workup | 14.7 | 13.7 | 13.3 | 90.5 | — | — | 75.3 | Recommended |
| HU-331 — batch (Zielke 2025) | batch | reaction+workup | 787.0 | 786.0 | nan | nan | — | — | — | — |
| HU-331 — flow (Zielke 2025) | flow | reaction+workup | 37.9 | 36.9 | nan | nan | — | — | — | — |
| CBD to HU-331 aerobic oxidation, flow scale-out (Zielke 2025, ESI 2.1) | flow | reaction+workup | 35.0 | 34.0 | 32.9 | 94.1 | — | — | 93.7 | Recommended |

```
== Ch3 SRN1 amination — optimized batch (batch; boundary: reaction) ==
Product: 178.7 mg (assay)
PMI 52.2 | E-factor 51.2 (dry 51.2) | SI 49.8 (95.3% of inputs)
PMI by stage: reaction 52.2
Energy 0.320 kWh -> 1,791 kWh/kg (nameplate)
AE 91.8% | RME 51.0%
Solvent by CHEM21 class (g/g): Problematic 49.8
  ! Product mass is an assay yield, not isolated; PMI is a lower bound.
  ! Boundary is reaction-step only; workup/purification excluded.
  ! Energy from nameplate values, not metered.
Reporting card: ✓ boundary, ✗ isolated, ✗ pmi_stage, ✓ efactor_class, ✓ si, ✓ energy, ✗ recovery, ✓ no_assumed
```

```
== Ch3 SRN1 amination — flow (Table 3.5, entry 5) (flow; boundary: reaction) ==
Product: 98.5 mg (assay)
PMI 458.4 | E-factor 457.4 (dry 457.4) | SI 451.3 (98.5% of inputs)
PMI by stage: reaction 458.4
AE 91.8% | RME 16.4%
Solvent by CHEM21 class (g/g): Problematic 451.3
  ! Product mass is an assay yield, not isolated; PMI is a lower bound.
  ! Boundary is reaction-step only; workup/purification excluded.
  ! No energy inventory: energy intensity not determinable.
  ! Inventory contains assumed quantities: Li metal.
Reporting card: ✓ boundary, ✗ isolated, ✗ pmi_stage, ✓ efactor_class, ✓ si, ✗ energy, ✗ recovery, ✗ no_assumed
```

```
== Ch4 anti-Markovnikov hydroamination (2-MeTHF) (batch; boundary: reaction) ==
Product: 187.4 mg (isolated)
PMI 19.5 | E-factor 18.5 (dry 18.5) | SI 18.2 (93.6% of inputs)
PMI by stage: reaction 19.5
Energy 0.040 kWh -> 213 kWh/kg (nameplate)
AE 100.0% | RME 83.3%
Solvent by CHEM21 class (g/g): Problematic 18.2
  ! Boundary is reaction-step only; workup/purification excluded.
  ! Energy from nameplate values, not metered.
Reporting card: ✓ boundary, ✓ isolated, ✗ pmi_stage, ✓ efactor_class, ✓ si, ✓ energy, ✗ recovery, ✓ no_assumed
```

```
== (Fluoromethoxy)benzene, gram-scale SMBR run (Pieber 2018) (flow; boundary: reaction) ==
Product: 1637.0 mg (isolated)
PMI 74.6 | E-factor 73.6 (dry 58.5) | SI 62.5 (83.7% of inputs)
PMI by stage: reaction 74.6
PMI with stated recovery credit: 56.8
AE 24.9% | RME 67.4%
Solvent by CHEM21 class (g/g): Recommended 43.8, Not ranked 18.6
  ! Boundary is reaction-step only; workup/purification excluded.
  ! No energy inventory: energy intensity not determinable.
  ! Some solvents lack a CHEM21 ranking.
Reporting card: ✓ boundary, ✓ isolated, ✗ pmi_stage, ✓ efactor_class, ✗ si, ✗ energy, ✓ recovery, ✓ no_assumed
```

```
== LiAlH4 reduction, batch (Prieschl 2020, ESI Table S6) (batch; boundary: reaction + workup) ==
Product: 11000.0 mg (isolated)
PMI 49.3 | E-factor 48.3 (dry 23.7) | SI 45.4 (92.1% of inputs)
PMI by stage: reaction 10.3, workup 39.0
Solvent by CHEM21 class (g/g): Problematic 8.6, Recommended 24.7, Hazardous 12.1
  ! No energy inventory: energy intensity not determinable.
Reporting card: ✓ boundary, ✓ isolated, ✓ pmi_stage, ✓ efactor_class, ✓ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== NaBH4 reduction, batch (Prieschl 2020, ESI Table S7) (batch; boundary: reaction + workup) ==
Product: 934.0 mg (isolated)
PMI 131.4 | E-factor 130.4 (dry 73.9) | SI 126.1 (95.9% of inputs)
PMI by stage: reaction 23.1, workup 108.4
Solvent by CHEM21 class (g/g): Recommended 126.1
  ! No energy inventory: energy intensity not determinable.
Reporting card: ✓ boundary, ✓ isolated, ✓ pmi_stage, ✓ efactor_class, ✓ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== Ru-MACHO ester hydrogenation, flow (Prieschl 2020) (flow; boundary: reaction) ==
Product: 774.9 mg (isolated)
PMI 6.5 | E-factor 5.5 (dry 5.5) | SI 5.1 (78.4% of inputs)
PMI by stage: reaction 6.5
AE 77.4% | RME 74.9%
Solvent by CHEM21 class (g/g): Recommended 5.1
  ! Boundary is reaction-step only; workup/purification excluded.
  ! No energy inventory: energy intensity not determinable.
Reporting card: ✓ boundary, ✓ isolated, ✗ pmi_stage, ✓ efactor_class, ✓ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== Ru-MACHO ester hydrogenation, flow long run (Prieschl 2020, ESI Table S5) (flow; boundary: reaction + workup) ==
Product: 13700.0 mg (isolated)
PMI 14.7 | E-factor 13.7 (dry 10.1) | SI 13.3 (90.5% of inputs)
PMI by stage: reaction 6.5, workup 8.2
Solvent by CHEM21 class (g/g): Recommended 13.3
  ! No energy inventory: energy intensity not determinable.
Reporting card: ✓ boundary, ✓ isolated, ✓ pmi_stage, ✓ efactor_class, ✓ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== HU-331 — batch (Zielke 2025) (batch; boundary: reaction + workup) ==
Reported PMI 787.0
PMI by stage: reaction 224.0, workup 563.0
  ! Values entered as reported in the source; inventory not recomputed.
Reporting card: ✓ boundary, ✗ isolated, ✓ pmi_stage, ✗ efactor_class, ✗ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== HU-331 — flow (Zielke 2025) (flow; boundary: reaction + workup) ==
Reported PMI 37.9
  ! Values entered as reported in the source; inventory not recomputed.
Reporting card: ✓ boundary, ✗ isolated, ✓ pmi_stage, ✗ efactor_class, ✗ si, ✗ energy, ✗ recovery, ✓ no_assumed
```

```
== CBD to HU-331 aerobic oxidation, flow scale-out (Zielke 2025, ESI 2.1) (flow; boundary: reaction + workup) ==
Product: 30990.0 mg (isolated)
PMI 35.0 | E-factor 34.0 (dry 18.3) | SI 32.9 (94.1% of inputs)
PMI by stage: reaction 10.3, workup 24.7
Solvent by CHEM21 class (g/g): Not ranked 24.2, Recommended 8.7
  ! No energy inventory: energy intensity not determinable.
  ! Inventory contains assumed quantities: tBuOH/toluene 6:1 (feed 1), tBuOH/toluene 6:1 (feed 2).
  ! Some solvents lack a CHEM21 ranking.
Reporting card: ✓ boundary, ✓ isolated, ✓ pmi_stage, ✓ efactor_class, ✗ si, ✗ energy, ✗ recovery, ✗ no_assumed
```

## Ch3 boundary scenarios

| scenario | batch PMI | flow PMI | flow/batch | symmetric |
|---|---|---|---|---|
| A. Reaction step | 52.2 | 458.4 | 8.77 | True |
| B. Asymmetric (batch + column, flow + none) | 453.0 | 458.4 | 1.01 | False |
| C. Both + extraction | 199.8 | 726.0 | 3.63 | True |
| D. Both + column | 453.0 | 1185.4 | 2.62 | True |

THF 90% recovery credit (reaction step): batch 7.5, flow 52.2
Flow energy, 80 W over residence time 33.3 min: 451 kWh/kg; over operating time 166.7 min: 2,256 kWh/kg
Flags (residence-time case): ['Product mass is an assay yield, not isolated; PMI is a lower bound.', 'Boundary is reaction-step only; workup/purification excluded.', 'Energy from nameplate values, not metered.', "Energy duration for ['80 W device'] is shorter than the operating time (167 min); residence time is not run time.", 'Inventory contains assumed quantities: Li metal.']
Batch PMI floor at 100% yield: 41.8; solvent-only floor 39.8

