from pathlib import Path

import pytest

import pmcor
from pmcor import compare, compute, load, molar_mass

EX = Path(__file__).resolve().parents[1] / "examples"


def test_molar_mass():
    assert molar_mass("C16H17N") == pytest.approx(223.32, abs=0.02)
    assert molar_mass("Ca(OH)2") == pytest.approx(74.09, abs=0.02)
    with pytest.raises(KeyError):
        molar_mass("Xx2")


def test_ch3_batch_reproduces_hand_calculation():
    # Thesis Section 3.5 values computed by hand
    r = compute(load(EX / "ch3_srn1_batch.json"))
    assert r.pmi == pytest.approx(52.2, abs=0.1)
    assert r.e_factor == pytest.approx(51.2, abs=0.1)
    assert r.solvent_intensity == pytest.approx(49.8, abs=0.1)
    assert r.atom_economy == pytest.approx(91.8, abs=0.1)
    assert r.energy_intensity == pytest.approx(1791, rel=0.002)
    assert 100 * r.solvent_share == pytest.approx(95.3, abs=0.1)


def test_flow_stream_mass_from_rate_and_time():
    p = load(EX / "ch3_srn1_flow.json")
    assert p.run_time_min == pytest.approx(166.67, abs=0.01)
    thf = sum(m.mass_g for m in p.materials if m.role == "solvent")
    assert thf == pytest.approx(50.0 * 0.889, rel=1e-6)  # 20 + 30 mL


def test_boundary_changes_ratio_and_asymmetry_warns():
    b, f = load(EX / "ch3_srn1_batch.json"), load(EX / "ch3_srn1_flow.json")
    col = [{"name": "silica", "mass_g": 10, "stage": "purification", "role": "stationary_phase"},
           {"name": "hexanes/EtOAc eluent", "mass_g": 61.6, "stage": "purification", "role": "eluent", "chem21": "Hazardous"}]
    b_col = b.with_extra("batch+column", col, ["reaction", "purification"])
    cmp = compare(b_col, f)  # declared boundaries differ
    assert not cmp.symmetric
    f_col = f.with_extra("flow+column", col, ["reaction", "purification"])
    cmp2 = compare(b_col, f_col)
    assert cmp2.symmetric
    assert cmp2.ratios["pmi"] < 1  # batch lower under symmetric boundary


def test_residence_time_flag():
    d = {"name": "x", "mode": "flow", "run_time_min": 100,
         "flow_streams": [{"name": "s", "flow_rate_mL_min": 1, "solvent": "THF",
                           "solutes": [{"name": "A", "mw": 100, "conc_M": 0.1, "role": "reactant"}]}],
         "product": {"mass_g": 0.5, "mw": 100},
         "energy": [{"device": "lamp", "power_W": 50, "duration_min": 20}]}
    r = compute(pmcor.Process.from_dict(d))
    assert any("residence time is not run time" in f for f in r.flags)


def test_recycle_credit_reported_separately():
    d = {"name": "x", "materials": [{"name": "toluene", "volume_mL": 10, "recovered_fraction": 0.9},
                                     {"name": "A", "mass_g": 1, "role": "reactant"}],
         "product": {"mass_g": 0.5}}
    r = compute(pmcor.Process.from_dict(d))
    assert r.pmi == pytest.approx((8.67 + 1) / 0.5, rel=1e-3)
    assert r.pmi_recycle_credit == pytest.approx((0.867 + 1) / 0.5, rel=1e-3)


def test_pareto():
    pts = [{"a": 1, "b": 3}, {"a": 2, "b": 2}, {"a": 3, "b": 3}]
    assert pmcor.pareto(pts, ["a", "b"]) == pts[:2]


def test_reported_record():
    r = compute(load(EX / "lit_zielke_hu331_batch.json"))
    assert r.pmi == 787 and r.reported


def test_independent_literature_validation():
    # Prieschl et al. 2020 report reaction PMI 6, AE 78%, RME 75% (Table 3)
    r = compute(load(EX / "lit_prieschl_flow.json"))
    assert 5.5 <= r.pmi <= 6.6
    assert r.atom_economy == pytest.approx(78, abs=1)
    assert r.rme == pytest.approx(75, abs=1)


def test_pieber_gram_scale_from_esi():
    # Pieber et al. 2018 ESI section 7.5: 16 mmol, 1.637 g isolated
    r = compute(load(EX / "lit_pieber_smbr.json"))
    assert r.pmi == pytest.approx(74.6, abs=0.1)
    assert r.pmi_recycle_credit == pytest.approx(56.8, abs=0.1)


@pytest.mark.parametrize("rec,reported,tol", [
    ("lit_prieschl_flow_esi", (6, 8, 14), 0.06),
    ("lit_prieschl_LAH_esi", (10, 41, 52), 0.06),
    ("lit_prieschl_NaBH4_esi", (23, 110, 133), 0.06),
])
def test_prieschl_full_process_from_esi(rec, reported, tol):
    # Prieschl et al. 2020, Table 3 vs ESI Tables S5-S7 (reaction, work-up, total)
    r = compute(load(EX / f"{rec}.json"), ["reaction", "workup"])
    got = (r.pmi_by_stage["reaction"], r.pmi_by_stage["workup"], r.pmi)
    for g, rep in zip(got, reported):
        assert abs(g - rep) / rep <= tol + 0.5 / rep  # within 6% or reported rounding


def test_zielke_hu331_flow_from_esi():
    # Zielke et al. 2025, Table 5 entry 3: 10.1 / 27.9 / 37.9
    r = compute(load(EX / "lit_zielke_hu331_flow_esi.json"), ["reaction", "workup"])
    assert r.pmi_by_stage["reaction"] == pytest.approx(10.1, rel=0.05)
    assert r.pmi == pytest.approx(37.9, rel=0.10)
