from pathlib import Path
"""Metadata-level comparison of open-access vs subscription records (all 10,758), same rules as analyse.py."""
import re, math, json
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact
src=open(Path(__file__).resolve().parent / "rules" / "text_mining_rules.py").read(); ns={"re":re}
exec(src[src.index("sust_patterns = ["):src.index("# =========================\n# HELPERS")],ns)
sust_re,metric_re,proxy_re=ns["sust_re"],ns["metric_terms_re"],ns["proxy_re"]
EXCL_TEXT=re.compile(r"\bcombustion\b|\bflames?\b|\bignition\b|jet[- ]stirred|shock[- ]tubes?\b|\bsoot\b|tropospher|atmospheric chemistry|laminar burning",re.I)
EXCL_SRC=re.compile(r"combust|flame|\bfuels?\b|atmospher",re.I)
d=pd.read_csv("scopus_all_10758.csv"); flow={"exported":len(d)}
d=d[d["Language of Original Document"].fillna("").str.strip().eq("English")].copy(); flow["english"]=len(d)
kw=d["Title"].fillna("")+" "+d["Author Keywords"].fillna("")+" "+d["Index Keywords"].fillna("")
d["excl"]=kw.str.contains(EXCL_TEXT)|d["Source title"].fillna("").str.contains(EXCL_SRC)
flow["excluded"]=int(d.excl.sum()); d=d[~d.excl].copy(); flow["retained"]=len(d)
meta=(d["Title"].fillna("")+" "+d["Abstract"].fillna("")+" "+d["Author Keywords"].fillna("")+" "+d["Index Keywords"].fillna("")).str.lower()
d["sust"]=meta.apply(lambda s:bool(sust_re.search(s))); d["metric"]=meta.apply(lambda s:bool(metric_re.search(s))); d["prox"]=meta.apply(lambda s:bool(proxy_re.search(s)))
d["cat"]="none"; d.loc[d.prox,"cat"]="proxy"; d.loc[d.metric,"cat"]="metric"
d["OA"]=d["Open Access"].fillna("").str.contains("All Open Access")
def wil(k,n,z=1.96):
    p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return round(100*(c-h),1),round(100*(c+h),1)
rows=[]
for lab,col in [("Sustainability language",d.sust),("Mentions a green metric",d.cat.eq("metric")),("Describes a proxy improvement",d.cat.eq("proxy")),("No explicit improvement",d.cat.eq("none"))]:
    r={"label":lab}
    for g,m in [("all",slice(None)),("OA",d.OA),("sub",~d.OA)]:
        x=col[m]; k=int(x.sum()); n=len(x); r[g]=(k,n,round(100*k/n,1),wil(k,n))
    t=[[r["OA"][0],r["OA"][1]-r["OA"][0]],[r["sub"][0],r["sub"][1]-r["sub"][0]]]
    r["p"]=chi2_contingency(t)[1]; r["OR"]=round(fisher_exact(t)[0],2); rows.append(r)
flow["OA"]=int(d.OA.sum()); flow["sub"]=int((~d.OA).sum())
print(flow)
for r in rows: print(r)
# by source type: process journals
for j in ["Organic Process Research and Development","Reaction Chemistry and Engineering","Green Chemistry","ACS Sustainable Chemistry and Engineering"]:
    x=d[d["Source title"].fillna("").str.lower()==j.lower()]
    if len(x): print(j,len(x),"OA",int(x.OA.sum()),"metric%",round(100*x.cat.eq("metric").mean(),1),"sub metric%",round(100*x[~x.OA].cat.eq("metric").mean(),1) if (~x.OA).sum() else None)
json.dump({"flow":flow,"rows":rows},open("all_records_results.json","w"),indent=1,default=str)
d.drop(columns=["excl"]).to_csv("all_records_flags.csv",index=False)
