"""Full-text step with Faith's functions (extract_pdf_text_to_file, analyze_fulltext, build_abstract_flags, three-way classes)."""
import re, math, json, csv, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
import pandas as pd
src = open(HERE / "rules" / "text_mining_rules.py").read()
s = src.index("sust_patterns = ["); e = src.index("def plot_three_figures_abs_vs_full")
ns = {}; exec("import re\nfrom pathlib import Path\nfrom typing import Dict, Any, Tuple, List, Optional\nimport pandas as pd\nfrom pdfminer.high_level import extract_text\n" + src[s:e], ns)
PDF = Path("pdfs")
TXT = Path("txt"); TXT.mkdir(exist_ok=True)
samp = pd.read_csv("random_sample_300.csv"); samp["DOI_norm"] = samp["DOI"].map(ns["norm_doi"])
name2doi = {ns["safe_filename_from_doi"](d): d for d in samp.DOI_norm}
rows, fails = [], []
for pdf in sorted(PDF.glob("*.pdf")):
    doi = name2doi.get(pdf.stem)
    ok, msg, txt = ns["extract_pdf_text_to_file"](pdf, TXT)
    if not ok or txt is None:
        fails.append({"DOI": doi, "stage": "extract_text", "error": msg}); continue
    t = txt.read_text(encoding="utf-8", errors="ignore")
    if len(t.strip()) < 500:
        fails.append({"DOI": doi, "stage": "extract_text", "error": f"too little text ({len(t.strip())} chars)"}); continue
    r = {"DOI_norm": doi, "chars": len(t)}; r.update(ns["analyze_fulltext"](t)); rows.append(r)
res = pd.DataFrame(rows)
absf = ns["build_abstract_flags"](samp[samp.DOI_norm.isin(res.DOI_norm)].copy())
m = res.merge(absf[["DOI_norm", "mentions_sustainability_abstract", "mentions_metrics_terms_abstract", "proxy_improvement_abstract"]], on="DOI_norm")
def wilson(k, n, z=1.96):
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return round(100*(c-h),1), round(100*(c+h),1)
N = len(m)
full_cat = pd.Series("none", index=m.index); full_cat[m.proxy_improvement_fulltext & ~m.quantifies_any_metric_fulltext] = "proxy"; full_cat[m.quantifies_any_metric_fulltext] = "metric"
abs_cat = pd.Series("none", index=m.index); abs_cat[m.proxy_improvement_abstract & ~m.mentions_metrics_terms_abstract] = "proxy"; abs_cat[m.mentions_metrics_terms_abstract] = "metric"
out = {"N": N, "extract_failures": fails}
for k, col in [("sust_abstract", m.mentions_sustainability_abstract), ("sust_full", m.mentions_sustainability_fulltext),
               ("metric_terms_abstract", m.mentions_metrics_terms_abstract), ("metric_terms_full", m.mentions_metrics_terms_fulltext),
               ("metric_value_full", m.quantifies_any_metric_fulltext), ("proxy_full", m.proxy_improvement_fulltext),
               ("cat_full_proxy", full_cat.eq("proxy")), ("cat_full_none", full_cat.eq("none")),
               ("cat_abs_proxy", abs_cat.eq("proxy")), ("cat_abs_none", abs_cat.eq("none"))]:
    c = int(col.sum()); out[k] = [c, round(100*c/N, 1), *wilson(c, N)]
m["cat_full"] = full_cat; m.to_csv("random_sample_fulltext_results.csv", index=False)
log = list(csv.DictReader(open("download_log.csv")))
out["download_stage"] = dict(collections.Counter(r["stage"] for r in log)); out["source"] = dict(collections.Counter(r["source"] for r in log if r["stage"] == "ok"))
json.dump(out, open("fulltext_summary.json", "w"), indent=1)
for k, v in out.items(): print(k, v)
print(m.loc[m.quantifies_any_metric_fulltext, ["DOI_norm"] + [c for c in m.columns if c.endswith("_value")]].to_string())
