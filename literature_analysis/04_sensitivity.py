import re, math, json
from pathlib import Path
import pandas as pd
src=open(Path(__file__).resolve().parent / "rules" / "text_mining_rules.py").read()
s=src.index("sust_patterns = ["); e=src.index("# =========================\n# HELPERS")
ns={"re":re}; exec(src[s:e],ns)
W=lambda k,n,z=1.96: (lambda p:(lambda d,c,h:(round(100*(c-h),1),round(100*(c+h),1)))(1+z*z/n,(p+z*z/(2*n))/(1+z*z/n),z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)))(k/n)
m=pd.read_csv("random_sample_fulltext_results.csv"); N=len(m)
fn=lambda d: re.sub(r"[^A-Za-z0-9._-]+","_",d)
# 1 paired headline
print("abs proxy flag among 134:", int(m.proxy_improvement_abstract.sum()), round(100*m.proxy_improvement_abstract.mean(),1), W(int(m.proxy_improvement_abstract.sum()),N))
gen=["10.1016/j.cesx.2019.100024","10.1016/j.chemosphere.2024.143392","10.3390/molecules25122945"]
print("genuine value & abs proxy:", m[m.DOI_norm.isin(gen)].proxy_improvement_abstract.tolist())
# 2 reference-list exclusion
REF=re.compile(r"\n\s*(references and notes|notes and references|references|bibliography|literature cited)\s*\n",re.I)
def strip_refs(t):
    ms=list(REF.finditer(t))
    if not ms: return t, False
    last=ms[-1]
    return (t[:last.start()], True) if last.start()>0.4*len(t) else (t, False)
rows=[]
BROAD=re.compile(r"\batom[-\s]?economy\b|\breaction mass efficiency\b|\brme\b|\bspace[-\s]?time[-\s]?yield\b|\bsty\b|\beco[-\s]?scale\b|\bproductivity\b", re.I)
BROAD_Q=re.compile(r"\b(?:atom[-\s]?economy|reaction mass efficiency|space[-\s]?time[-\s]?yield|eco[-\s]?scale)\b.{0,60}(?:\d+(?:\.\d+)?)", re.I)
for _,r in m.iterrows():
    t=Path(f"txt/{fn(r.DOI_norm)}.txt").read_text(errors="ignore")
    body,found=strip_refs(t); b=body.lower(); tl=t.lower()
    rows.append({"DOI":r.DOI_norm,"refs_found":found,
      "sust_body":bool(ns["sust_re"].search(b)),"metric_body":bool(ns["metric_terms_re"].search(b)),
      "value_body":any(rx.search(b) for rx in ns["quant_patterns"].values()),"proxy_body":bool(ns["proxy_re"].search(b)),
      "broad_mention":bool(BROAD.search(b)) or bool(ns["metric_terms_re"].search(b)),
      "broad_value":bool(BROAD_Q.search(b)) or any(rx.search(b) for rx in ns["quant_patterns"].values()),
      "greenchem_journal_only": bool(re.search(r"green chem",tl)) and not bool(ns["sust_re"].search(re.sub(r"green chem\.?","",tl)))})
x=pd.DataFrame(rows)
print("refs section detected:", int(x.refs_found.sum()))
for c in ["sust_body","metric_body","value_body","proxy_body","broad_mention","broad_value","greenchem_journal_only"]:
    k=int(x[c].sum()); print(c,k,round(100*k/N,1),W(k,N))
x.to_csv("sensitivity_fulltext.csv",index=False)
# 3 selection bias: retrieved vs not among the 300 (metadata flags)
f=pd.read_csv("keyword_sample_flags.csv"); samp=pd.read_csv("random_sample_300.csv")
f["DOI_norm"]=f.DOI.astype(str).str.lower().str.strip(); samp["DOI_norm"]=samp.DOI.str.lower().str.strip()
s3=f[f.DOI_norm.isin(samp.DOI_norm)].copy(); s3["retrieved"]=s3.DOI_norm.isin(m.DOI_norm)
print(len(s3), s3.retrieved.sum())
for c in ["sust","metric","proxy"]:
    a=s3[s3.retrieved][c]; b_=s3[~s3.retrieved][c]
    print(c, "retrieved", round(100*a.mean(),1), "not", round(100*b_.mean(),1))
from scipy.stats import fisher_exact
for c in ["sust","metric","proxy"]:
    t=[[int(s3[s3.retrieved][c].sum()), int((~s3[s3.retrieved][c]).sum())],[int(s3[~s3.retrieved][c].sum()), int((~s3[~s3.retrieved][c]).sum())]]
    print(c, "fisher p=%.2f"%fisher_exact(t)[1])
pub=lambda d: d.split("/")[0]
PUB={"10.1039":"RSC","10.1021":"ACS","10.1016":"Elsevier","10.1002":"Wiley","10.3390":"MDPI","10.1038":"Nature Portfolio","10.1007":"Springer","10.3389":"Frontiers","10.3762":"Beilstein"}
s3["publisher"]=s3.DOI_norm.map(lambda d: PUB.get(pub(d),"Other"))
tab=pd.crosstab(s3.publisher,s3.retrieved); tab["total"]=tab.sum(1); tab["rate %"]=(100*tab[True]/tab.total).round(0)
print(tab.sort_values("total",ascending=False))
tab.to_csv("publisher_mix.csv")
json.dump({"yearcmp":[round(s3[s3.retrieved].Year.mean(),1), round(s3[~s3.retrieved].Year.mean(),1)]},open("year_comparison.json","w")); print("mean year", round(s3[s3.retrieved].Year.mean(),1), round(s3[~s3.retrieved].Year.mean(),1))
