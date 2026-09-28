"""Independent keyword-defined sample: metadata-level analysis with Faith's exact pattern sets."""
import re, math, json
import pandas as pd
from pathlib import Path
HERE = Path(__file__).resolve().parent
RULES = HERE / "rules" / "text_mining_rules.py"


# --- Faith's pattern sets, taken verbatim from Listing S2 (module-level definitions only)
src = open(RULES).read()
start = src.index("sust_patterns = ["); end = src.index("# =========================\n# HELPERS")
ns = {"re": re}; exec(src[start:end], ns)
sust_re, metric_terms_re, proxy_re = ns["sust_re"], ns["metric_terms_re"], ns["proxy_re"]

# --- pre-declared exclusion rule (fixed before any outcome was computed)
EXCL_TEXT = re.compile(r"\bcombustion\b|\bflames?\b|\bignition\b|jet[- ]stirred|shock[- ]tubes?\b|\bsoot\b|tropospher|atmospheric chemistry|laminar burning", re.I)
EXCL_SRC = re.compile(r"combust|flame|\bfuels?\b|atmospher", re.I)

d = pd.read_csv("scopus_oa_4608.csv")  # Scopus export (see README); not redistributed
n0 = len(d)
d = d[d["Language of Original Document"].fillna("").str.strip().eq("English")].copy(); n_en = len(d)
txt_kw = (d["Title"].fillna("") + " " + d["Author Keywords"].fillna("") + " " + d["Index Keywords"].fillna(""))
d["excluded_gas_phase"] = txt_kw.str.contains(EXCL_TEXT) | d["Source title"].fillna("").str.contains(EXCL_SRC)
meta = (d["Title"].fillna("") + " " + d["Abstract"].fillna("") + " " + d["Author Keywords"].fillna("") + " " + d["Index Keywords"].fillna("")).str.lower()
d["sust"] = meta.apply(lambda s: bool(sust_re.search(s)))
d["metric"] = meta.apply(lambda s: bool(metric_terms_re.search(s)))
d["proxy"] = meta.apply(lambda s: bool(proxy_re.search(s)))
d["cat"] = "none"; d.loc[d.proxy, "cat"] = "proxy"; d.loc[d.metric, "cat"] = "metric"

def wilson(k, n, z=1.96):
    p = k / n; den = 1 + z*z/n; c = (p + z*z/(2*n)) / den; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return 100*(c-h), 100*(c+h)

def summ(x, label):
    n = len(x); out = {"set": label, "N": n}
    for k, col in (("sust", x.sust), ("metric", x.cat.eq("metric")), ("proxy", x.cat.eq("proxy")), ("none", x.cat.eq("none"))):
        c = int(col.sum()); lo, hi = wilson(c, n); out[k] = (c, round(100*c/n, 1), round(lo, 1), round(hi, 1))
    return out

res = [summ(d, "keyword sample, all English OA"), summ(d[~d.excluded_gas_phase], "keyword sample, excl. gas-phase combustion/atmospheric")]
flow = {"exported_OA": n0, "english": n_en, "excluded_gas_phase": int(d.excluded_gas_phase.sum()), "retained": int((~d.excluded_gas_phase).sum())}
d.to_csv("keyword_sample_flags.csv", index=False)
json.dump({"flow": flow, "results": res}, open("results.json", "w"), indent=1)
print(flow)
for r in res: print(r)
print(d[d.excluded_gas_phase]["Source title"].value_counts().head(15))

# random sample for full-text analysis (reproduces data/random_sample_300_ids.csv)
d[~d.excluded_gas_phase].sample(300, random_state=20260926).to_csv("random_sample_300.csv", index=False)
