"""
OA full-text miner + Abstract-vs-Fulltext comparison
What this script does:
1) Loads your Scopus OA candidate table (e.g., 330 OA candidates) from CSV/XLSX.
2) For each DOI:
   - Uses Unpaywall to find OA PDF URLs (best_oa_location + all oa_locations)
   - Downloads a valid PDF (verifies %PDF signature / content-type)
   - Extracts full text (pdfminer.six) -> saves .txt
   - Computes FULL-TEXT flags:
       mentions_sustainability_fulltext
       mentions_metrics_terms_fulltext
       quantifies_any_metric_fulltext (metric term + nearby number)
       proxy_improvement_fulltext
3) Builds ABSTRACT/METADATA flags for the same successfully processed DOIs (N ~ 113):
   - Uses Title + Abstract + Author Keywords + Index Keywords from Scopus file
   - Computes:
       mentions_sustainability_abstract
       mentions_metrics_terms_abstract
       proxy_improvement_abstract
4) Merges abstract + full-text flags and plots 3 figures:
   A) Sustainability: abstract vs full text
   B) Metric terminology: abstract vs full text
   C) 3-category evidence: abstract vs full text (metrics > proxy > none)
5) Saves:
   - oa_fulltext_results.csv
   - oa_fulltext_failures.csv
   - oa_abs_vs_full_merged.csv
   - PDFs + TXT files
   - 3 figures (PNG)
Install:
   pip install pandas requests pdfminer.six tqdm matplotlib numpy
Run:
   python this_script.py
   or run in a notebook cell.
NOTE:
   - Some OA pages block automated downloads; those go to failures.
   - Scanned PDFs may produce poor text extraction.
"""
import re
import time
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
import matplotlib.pyplot as plt
from pdfminer.high_level import extract_text

# =========================
# USER SETTINGS
# =========================
INPUT_PATH = "scopus_export_Jan 26_330.csv"  # <-- change to your file
INPUT_SHEET = None  # Excel sheet name if needed
DOI_COL = "DOI"  # DOI column name in your Scopus file
UNPAYWALL_EMAIL = "youremail@xyz.edu"  # REQUIRED by Unpaywall
OUTDIR = Path("oa_abs_vs_full_mining")
PDF_DIR = OUTDIR / "pdfs"
TXT_DIR = OUTDIR / "txt"
OUTDIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
TXT_DIR.mkdir(exist_ok=True)
MAX_DOWNLOADS = None
SLEEP_BETWEEN_REQUESTS = 0.35
REQUEST_TIMEOUT = 60
USER_AGENT = f"Mozilla/5.0 (compatible; OA-text-mining/3.0; +mailto:{UNPAYWALL_EMAIL})"

# =========================
# PATTERNS
# =========================
sust_patterns = [
    r"\bsustainab",
    r"\bgreen chemistry\b",
    r"\bgreen chem\b",
    r"\benvironmental (impact|performance|footprint)\b",
    r"\beco[-\s]?friendly\b",
    r"\b12 principles\b",
    r"\bprinciples of green chemistry\b",
    r"\blife[-\s]?cycle assessment\b",
    r"\blca\b",
]
metric_term_patterns = [
    r"\bprocess mass intensity\b",
    r"\bpmi\b",
    r"\be[-\s]?factor\b",
    r"\bmass intensity\b",
    r"\bsolvent intensity\b",
    r"\benergy intensity\b",
    r"\bkwh\b",
    r"\bcumulative energy demand\b",
    r"\bced\b",
    r"\blife[-\s]?cycle assessment\b",
    r"\blca\b",
    r"\bglobal warming potential\b",
    r"\bgwp\b",
    r"\bcarbon footprint\b",
    r"\bco2[-\s]?eq\b",
]
proxy_patterns = [
    # --- Direct comparison language (batch/flow) ---
    r"\bcompared to (batch|traditional|conventional)\b",
    r"\bversus (batch|traditional|conventional)\b",
    r"\bvs\.?\s*(batch|traditional|conventional)\b",
    r"\boutperform(s|ed)?\b",
    r"\bsuperior to\b",
    r"\bimprov(e|ed|ement)\s+over\b",
    r"\bbenchmark(ed|ing)?\b",
    r"\bhead[-\s]?to[-\s]?head\b",
    r"\bdirect comparison\b",
    # --- Yield / conversion / selectivity / purity ---
    r"\bhigh(er)? yield(s)?\b",
    r"\bimprov(e|ed|ement)\s+yield(s)?\b",
    r"\bexcellent yield(s)?\b",
    r"\bincreased yield(s)?\b",
    r"\bhigh conversion\b",
    r"\bquantitative conversion\b",
    r"\bnear[-\s]?quantitative\b",
    r"\bcomplete conversion\b",
    r"\bimprov(e|ed|ement)\s+conversion\b",
    r"\bimprov(e|ed|ement)\s+selectivit(y|ies)\b",
    r"\bhigh selectivit(y|ies)\b",
    r"\bchemo[-\s]?selectiv(e|ity)\b",
    r"\bregio[-\s]?selectiv(e|ity)\b",
    r"\bstereo[-\s]?selectiv(e|ity)\b",
    r"\benhanced selectivit(y|ies)\b",
    r"\bimprov(e|ed|ement)\s+purity\b",
    r"\bhigh purity\b",
    r"\bclean(er)? reaction\b",
    r"\bclean(er)? profile\b",
    r"\bfewer by[-\s]?products?\b",
    r"\breduced by[-\s]?products?\b",
    r"\bminimi[sz](e|ed|ing)\s+side[-\s]?products?\b",
    r"\bimprov(e|ed|ement)\s+chemoselectivity\b",
    r"\bimprov(e|ed|ement)\s+regioselectivity\b",
    r"\bimprov(e|ed|ement)\s+stereoselectivity\b",
    # --- Productivity / throughput / STY / scale ---
    r"\b(productivit(y|ies)|space[-\s]?time yield|sty)\b",
    r"\bhigher (productivity|throughput|output)\b",
    r"\bincreased (productivity|throughput|output)\b",
    r"\bimprov(e|ed|ement)\s+(productivity|throughput)\b",
    r"\bhigh throughput\b",
    r"\bkilogram\b|\bkg\b|\bgram[-\s]?scale\b|\bpilot\b|\bscale[-\s]?up\b",
    r"\bcontinuous manufacturing\b",
    r"\bprocess intensification\b",
    r"\bintensif(y|ied|ication)\b",
    r"\bhigh concentration\b",
    r"\bconcentrated\b",
    r"\bhigh loading\b",
    r"\blow catalyst loading\b",
    r"\bcatalyst recycling\b",
    r"\bcatalyst reuse\b",
    r"\bimmobilized catalyst\b",
    r"\bpacked[-\s]?bed\b",
    # --- Time / residence time / kinetics ---
    r"\bshort(er)? (reaction time|residence time)\b",
    r"\breduc(e|ed|tion)\s+(reaction time|residence time)\b",
    r"\bra(p|pi)d\b",
    r"\bfast(er)?\b",
    r"\baccelerat(e|ed|ion)\b",
    r"\bminutes?\b|\bseconds?\b",
    r"\bshort residence time\b",
    r"\bhigh flow rate\b",
    r"\bhighly efficient\b",
    # --- Energy / temperature / pressure conditions ---
    r"\bmild(er)? conditions\b",
    r"\blower temperature\b|\broom temperature\b|\bambient\b",
    r"\blower pressure\b",
    r"\benergy[-\s]?efficient\b",
    r"\breduc(e|ed|tion)\s+energy\b",
    r"\blower energy\b",
    r"\bphotochemical\b|\bphotoredox\b|\belectrochemical\b|\belectrosynth(esis|etic)\b",
    r"\benable(s|d)? (light|electricity|electrons?)\b",
    # --- Solvent / waste / workup minimization ---
    r"\breduc(e|ed|tion)\s+solvent(s)?\b",
    r"\blower solvent\b|\bminimal solvent\b",
    r"\bsolvent[-\s]?free\b",
    r"\bgreener solvent(s)?\b",
    r"\bbenign solvent(s)?\b",
    r"\bwater as (the )?only by[-\s]?product\b",
    r"\bwater[-\s]?only by[-\s]?product\b",
    r"\breduc(e|ed|tion)\s+waste\b",
    r"\bminimi[sz](e|ed|ation)\s+waste\b",
    r"\bless waste\b",
    r"\blow(er)? e[-\s]?factor\b|\be[-\s]?factor\b",
    r"\bpm[i|I]\b|\bprocess mass intensity\b",
    r"\blca\b|\blife[-\s]?cycle assessment\b",
    r"\bsolvent intensity\b",
    r"\bmass intensity\b",
    r"\bcarbon footprint\b|\bco2\b|\bghg\b",
    r"\bno (aqueous )?work[-\s]?up\b",
    r"\beliminat(e|ed|ing)\s+(work[-\s]?up|extraction|chromatography|purification)\b",
    r"\bavoids?\s+(chromatography|extraction|work[-\s]?up)\b",
    r"\binline (workup|purification|extraction|separation)\b",
    r"\bin[-\s]?line (workup|purification|extraction|separation)\b",
    # --- Step economy / telescoping / one-pot / automation ---
    r"\bfewer steps\b|\breduc(e|ed|tion)\s+steps\b",
    r"\bstep[-\s]?econom(y|ic)\b",
    r"\btelescop(e|ed|ing)\b",
    r"\bone[-\s]?pot\b",
    r"\bmultistep\b|\bcascade\b|\bdomino\b",
    r"\bintegrat(e|ed|ion)\b",
    r"\bin[-\s]?line analytics\b|\binline analytics\b|\bPAT\b",
    r"\breal[-\s]?time monitoring\b",
    r"\bautomation\b|\bself[-\s]?optim(iz|is)(e|ed|ation)\b|\bclosed[-\s]?loop\b",
    # --- Safety / hazard reduction / containment ---
    r"\bsafer\b|\binherently safer\b",
    r"\breduc(e|ed|tion)\s+risk\b",
    r"\bimprov(e|ed|ement)\s+safety\b",
    r"\bhazard(s)?\b|\bhazardous\b",
    r"\bcontain(ed|ment)\b",
    r"\bexotherm(s|ic)?\b|\bthermal runaway\b",
    r"\bexplosive\b|\btoxic\b|\bcorrosive\b|\bpyrophoric\b",
    r"\bsafer handling\b",
    r"\bon[-\s]?demand generation\b",
    r"\bin situ generation\b",
    r"\bminimi[sz](e|ed|ing)\s+inventory\b",
    r"\bsmall reactor volumes?\b|\bsmall hold[-\s]?up\b",
    # --- General broad green terms ---
    r"\bgreen\b|\bsustainab(le|ility)\b|\benvironmental\b|\beco[-\s]?friendly\b",
]
sust_re = re.compile("|".join(sust_patterns), flags=re.IGNORECASE)
metric_terms_re = re.compile("|".join(metric_term_patterns), flags=re.IGNORECASE)
proxy_re = re.compile("|".join(proxy_patterns), flags=re.IGNORECASE)

# Quantified metric detectors (keyword + nearby number)
NUM = r"(?:(?:\d{1,3}(?:,\d{3})+)|(?:\d+))(?:\.\d+)?"
WINDOW = 60
quant_patterns = {
    "PMI_value": re.compile(rf"\b(?:pmi|process mass intensity)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
    "E_factor_value": re.compile(rf"\b(?:e[-\s]?factor)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
    "Energy_kWh_value": re.compile(rf"\b(?:kwh|energy intensity|cumulative energy demand|ced)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
    "GWP_CO2eq_value": re.compile(rf"\b(?:gwp|global warming potential|co2[-\s]?eq|carbon footprint)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
    "Solvent_intensity_value": re.compile(rf"\b(?:solvent intensity)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
    "Mass_intensity_value": re.compile(rf"\b(?:mass intensity)\b.{{0,{WINDOW}}}{NUM}", re.IGNORECASE),
}


# =========================
# HELPERS
# =========================
def norm_doi(x: str) -> str:
    x = str(x).strip().lower()
    x = x.replace("https://doi.org/", "").replace("http://doi.org/", "")
    x = x.replace("doi:", "").strip()
    return x


def safe_filename_from_doi(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", doi.strip())


def looks_like_pdf(content: bytes, content_type: str) -> bool:
    if content_type and "pdf" in content_type.lower():
        return True
    return content[:4] == b"%PDF"


def unpaywall_lookup(doi: str) -> Dict[str, Any]:
    url = f"https://api.unpaywall.org/v2/{doi}"
    r = requests.get(
        url,
        params={"email": UNPAYWALL_EMAIL},
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
    )
    r.raise_for_status()
    j = r.json()
    best = j.get("best_oa_location") or {}
    oa_locs = j.get("oa_locations") or []
    pdf_urls: List[str] = []
    if best.get("url_for_pdf"):
        pdf_urls.append(best["url_for_pdf"])
    for loc in oa_locs:
        if not loc:
            continue
        u = loc.get("url_for_pdf")
        if u:
            pdf_urls.append(u)
    # de-dup preserving order
    seen = set()
    pdf_urls = [u for u in pdf_urls if not (u in seen or seen.add(u))]
    landing_url = best.get("url") or j.get("doi_url")
    return {
        "doi": doi,
        "is_oa": j.get("is_oa"),
        "oa_status": j.get("oa_status"),
        "landing_url": landing_url,
        "license": best.get("license"),
        "host_type": best.get("host_type"),
        "candidate_pdf_urls": pdf_urls,
        "oa_locations_n": len(oa_locs),
    }


def download_pdf_with_fallback(pdf_urls: List[str], outpath: Path, referer: Optional[str]) -> Tuple[bool, str, Optional[str]]:
    sess = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    if referer:
        headers["Referer"] = referer
    last_err = None
    for url in pdf_urls:
        try:
            r = sess.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            if r.status_code != 200:
                last_err = f"HTTP {r.status_code}"
                continue
            ctype = r.headers.get("Content-Type", "")
            if not looks_like_pdf(r.content, ctype):
                last_err = f"Not a PDF (Content-Type={ctype})"
                continue
            outpath.write_bytes(r.content)
            return True, "ok", url
        except Exception as e:
            last_err = str(e)
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return False, last_err or "download failed", None


def extract_pdf_text_to_file(pdf_path: Path, txt_dir: Path) -> Tuple[bool, str, Optional[Path]]:
    try:
        txt = extract_text(str(pdf_path))
        txt = re.sub(r"\s+\n", "\n", txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        out_txt = txt_dir / (pdf_path.stem + ".txt")
        out_txt.write_text(txt, encoding="utf-8", errors="ignore")
        return True, "ok", out_txt
    except Exception as e:
        return False, str(e), None


def analyze_fulltext(text: str) -> Dict[str, Any]:
    t = text.lower()
    mentions_sust = bool(sust_re.search(t))
    mentions_metric_terms = bool(metric_terms_re.search(t))
    proxy_improvement = bool(proxy_re.search(t))
    quantified_hits = {k: bool(rx.search(t)) for k, rx in quant_patterns.items()}
    any_quantified = any(quantified_hits.values())
    return {
        "mentions_sustainability_fulltext": mentions_sust,
        "mentions_metrics_terms_fulltext": mentions_metric_terms,
        "proxy_improvement_fulltext": proxy_improvement,
        "quantifies_any_metric_fulltext": any_quantified,
        **quantified_hits,
    }


def build_abstract_flags(df_scopus_subset: pd.DataFrame) -> pd.DataFrame:
    # metadata text: Title + Abstract + keywords
    text_abs = (
        df_scopus_subset.get("Title", "").fillna("").astype(str) + " " +
        df_scopus_subset.get("Abstract", "").fillna("").astype(str) + " " +
        df_scopus_subset.get("Author Keywords", "").fillna("").astype(str) + " " +
        df_scopus_subset.get("Index Keywords", "").fillna("").astype(str)
    ).str.lower()
    out = df_scopus_subset.copy()
    out["mentions_sustainability_abstract"] = text_abs.apply(lambda s: bool(sust_re.search(s)))
    out["mentions_metrics_terms_abstract"] = text_abs.apply(lambda s: bool(metric_terms_re.search(s)))
    out["proxy_improvement_abstract"] = text_abs.apply(lambda s: bool(proxy_re.search(s)))
    return out


def plot_three_figures_abs_vs_full(merged_df: pd.DataFrame, outdir: Path) -> None:
    N = len(merged_df)
    if N == 0:
        print("No rows to plot.")
        return
    for c in [
        "mentions_sustainability_abstract", "mentions_sustainability_fulltext",
        "mentions_metrics_terms_abstract", "mentions_metrics_terms_fulltext",
        "proxy_improvement_abstract", "proxy_improvement_fulltext",
        "quantifies_any_metric_fulltext"
    ]:
        if c in merged_df.columns:
            merged_df[c] = merged_df[c].fillna(False).astype(bool)
    w = 0.35

    # ---------- FIGURE A: Sustainability ----------
    sust_abs = int(merged_df["mentions_sustainability_abstract"].sum())
    sust_full = int(merged_df["mentions_sustainability_fulltext"].sum())
    no_sust_abs = N - sust_abs
    no_sust_full = N - sust_full
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    x = np.arange(2)
    ax.bar(x - w/2, [100*sust_abs/N, 100*no_sust_abs/N], width=w, label="Abstract/metadata")
    ax.bar(x + w/2, [100*sust_full/N, 100*no_sust_full/N], width=w, label="Full text")
    ax.set_xticks(x)
    ax.set_xticklabels(["Mentions sustainability", "Does not mention"])
    ax.set_ylabel("Share of publications (%)", fontsize=14)
    ax.set_ylim(0, 110)
    ax.set_title(f"Sustainability framing: abstract vs full text (N={N})", pad=15)
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99), frameon=False)
    vals_abs = [100*sust_abs/N, 100*no_sust_abs/N]
    vals_full = [100*sust_full/N, 100*no_sust_full/N]
    ns_abs = [sust_abs, no_sust_abs]
    ns_full = [sust_full, no_sust_full]
    for i in range(2):
        ax.text(i - w/2, vals_abs[i] + 1, f"{vals_abs[i]:.1f}%\n(n={ns_abs[i]})", ha="center", va="bottom", fontsize=9)
        ax.text(i + w/2, vals_full[i] + 1, f"{vals_full[i]:.1f}%\n(n={ns_full[i]})", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    fA = outdir / "FigureA_sustainability_abs_vs_full.png"
    plt.savefig(fA, dpi=300, bbox_inches="tight")
    plt.show()

    # ---------- FIGURE B: Metrics (TERM MENTIONS vs TERM MENTIONS) ----------
    met_abs = int(merged_df["mentions_metrics_terms_abstract"].sum())
    met_full = int(merged_df["mentions_metrics_terms_fulltext"].sum())
    no_met_abs = N - met_abs
    no_met_full = N - met_full
    fig, ax = plt.subplots(figsize=(7.5, 3.2))
    x = np.arange(2)
    ax.bar(x - w/2, [100*met_abs/N, 100*no_met_abs/N], width=w, label="Abstract/metadata")
    ax.bar(x + w/2, [100*met_full/N, 100*no_met_full/N], width=w, label="Full text")
    ax.set_xticks(x)
    ax.set_xticklabels(["Mentions green metrics", "Does not mention"])
    ax.set_ylabel("Share of publications (%)", fontsize=14)
    ax.set_ylim(0, 110)
    ax.set_title(f"Green-metric terminology: abstract vs full text (N={N})", pad=15)
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99), frameon=False)
    vals_abs = [100*met_abs/N, 100*no_met_abs/N]
    vals_full = [100*met_full/N, 100*no_met_full/N]
    ns_abs = [met_abs, no_met_abs]
    ns_full = [met_full, no_met_full]
    for i in range(2):
        ax.text(i - w/2, vals_abs[i] + 1, f"{vals_abs[i]:.1f}%\n(n={ns_abs[i]})", ha="center", va="bottom", fontsize=9)
        ax.text(i + w/2, vals_full[i] + 1, f"{vals_full[i]:.1f}%\n(n={ns_full[i]})", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    fB = outdir / "FigureB_metrics_abs_vs_full.png"
    plt.savefig(fB, dpi=300, bbox_inches="tight")
    plt.show()

    # ---------- FIGURE C: 3-category (metrics > proxy > none) ----------
    def classify_three(mets: pd.Series, proxy: pd.Series) -> pd.Series:
        cat = pd.Series(index=mets.index, dtype="object")
        cat.loc[mets] = "Green metric (term in metadata; value in full text)"  # metadata: metric-term mention; full text: reported value
        cat.loc[~mets & ~proxy] = "No explicit improvement"
        cat.loc[~mets & proxy] = "Reports improvement vs batch (proxy)"
        return cat

    cat_abs = classify_three(
        merged_df["mentions_metrics_terms_abstract"],
        merged_df["proxy_improvement_abstract"]
    )
    # For full text, require a reported value (keyword + number within 60 characters)
    cat_full = classify_three(
        merged_df["quantifies_any_metric_fulltext"],
        merged_df["proxy_improvement_fulltext"]
    )
    order = ["Green metric (term in metadata; value in full text)", "No explicit improvement", "Reports improvement vs batch (proxy)"]
    pct_abs = (cat_abs.value_counts(normalize=True) * 100).reindex(order).fillna(0)
    pct_full = (cat_full.value_counts(normalize=True) * 100).reindex(order).fillna(0)
    n_abs = cat_abs.value_counts().reindex(order).fillna(0).astype(int)
    n_full = cat_full.value_counts().reindex(order).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(len(order))
    ax.bar(x - w/2, pct_abs.values, width=w, label="Abstract/metadata")
    ax.bar(x + w/2, pct_full.values, width=w, label="Full text")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=0)
    ax.set_ylabel("Share of publications (%)", fontsize=14)
    ax.set_ylim(0, 110)
    ax.set_title(f"Evidence categories: abstract vs full text (N={N})", pad=15)
    ax.legend(loc="upper left", bbox_to_anchor=(0.01, 0.99), frameon=False)
    for i in range(len(order)):
        ax.text(i - w/2, pct_abs.values[i] + 1, f"{pct_abs.values[i]:.1f}%\n(n={n_abs.values[i]})", ha="center", va="bottom", fontsize=9)
        ax.text(i + w/2, pct_full.values[i] + 1, f"{pct_full.values[i]:.1f}%\n(n={n_full.values[i]})", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    fC = outdir / "FigureC_categories_abs_vs_full.png"
    plt.savefig(fC, dpi=300, bbox_inches="tight")
    plt.show()
    print("Saved:")
    print(f" - {fA}")
    print(f" - {fB}")
    print(f" - {fC}")


# =========================
# MAIN
# =========================
def main():
    # Load Scopus table
    if INPUT_PATH.lower().endswith((".xlsx", ".xls")):
        df_scopus = pd.read_excel(INPUT_PATH, sheet_name=INPUT_SHEET)
    else:
        df_scopus = pd.read_csv(INPUT_PATH)
    if DOI_COL not in df_scopus.columns:
        raise ValueError(f"DOI column '{DOI_COL}' not found. Available: {list(df_scopus.columns)}")
    df_scopus[DOI_COL] = df_scopus[DOI_COL].astype(str).map(norm_doi)
    df_scopus = df_scopus[df_scopus[DOI_COL].notna() & (df_scopus[DOI_COL] != "")].copy()
    dois = df_scopus[DOI_COL].tolist()
    if MAX_DOWNLOADS is not None:
        dois = dois[:MAX_DOWNLOADS]
    results = []
    failures = []
    for doi in tqdm(dois, desc="Processing DOIs"):
        row: Dict[str, Any] = {"DOI": doi}
        # 1) Unpaywall lookup
        try:
            meta = unpaywall_lookup(doi)
            row.update({
                "is_oa": meta.get("is_oa"),
                "oa_status": meta.get("oa_status"),
                "landing_url": meta.get("landing_url"),
                "license": meta.get("license"),
                "host_type": meta.get("host_type"),
                "oa_locations_n": meta.get("oa_locations_n"),
            })
            candidate_pdf_urls = meta.get("candidate_pdf_urls", [])
        except Exception as e:
            row["stage"] = "unpaywall_lookup"
            row["error"] = str(e)
            failures.append(row)
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            continue
        time.sleep(SLEEP_BETWEEN_REQUESTS)
        if not candidate_pdf_urls:
            row["stage"] = "no_pdf_url"
            row["error"] = "Unpaywall returned no direct PDF URL (best + oa_locations)"
            failures.append(row)
            continue
        # 2) Download PDF
        pdf_name = safe_filename_from_doi(doi) + ".pdf"
        pdf_path = PDF_DIR / pdf_name
        if not pdf_path.exists():
            ok, msg, used_url = download_pdf_with_fallback(candidate_pdf_urls, pdf_path, referer=row.get("landing_url"))
            row["download_ok"] = ok
            row["download_msg"] = msg
            row["used_pdf_url"] = used_url
            time.sleep(SLEEP_BETWEEN_REQUESTS)
            if not ok:
                row["stage"] = "download_pdf"
                row["error"] = msg
                failures.append(row)
                continue
        else:
            row["download_ok"] = True
            row["download_msg"] = "already_exists"
            row["used_pdf_url"] = "cached"
        # 3) Extract text
        ok, msg, txt_path = extract_pdf_text_to_file(pdf_path, TXT_DIR)
        row["extract_ok"] = ok
        row["extract_msg"] = msg
        if not ok or txt_path is None:
            row["stage"] = "extract_text"
            row["error"] = msg
            failures.append(row)
            continue
        # 4) Analyze full text
        try:
            text = txt_path.read_text(encoding="utf-8", errors="ignore")
            feats = analyze_fulltext(text)
            row.update(feats)
            results.append(row)
        except Exception as e:
            row["stage"] = "analyze_text"
            row["error"] = str(e)
            failures.append(row)
            continue
    results_df = pd.DataFrame(results)
    failures_df = pd.DataFrame(failures)
    # Save base outputs
    out_results = OUTDIR / "oa_fulltext_results.csv"
    out_failures = OUTDIR / "oa_fulltext_failures.csv"
    results_df.to_csv(out_results, index=False)
    failures_df.to_csv(out_failures, index=False)
    print("\nSaved outputs:")
    print(f" - Results: {out_results}")
    print(f" - Failures: {out_failures}")
    print(f" - PDFs: {PDF_DIR}")
    print(f" - TXT: {TXT_DIR}")
    if len(results_df) == 0:
        print("No successful parses; no abstract-vs-full plots generated.")
        return
    # Build abstract flags for SAME successful DOIs
    results_df["DOI_norm"] = results_df["DOI"].map(norm_doi)
    df_sub = df_scopus[df_scopus[DOI_COL].isin(results_df["DOI_norm"])].copy()
    df_sub = build_abstract_flags(df_sub).rename(columns={DOI_COL: "DOI_norm"})
    merged = results_df.merge(
        df_sub[["DOI_norm", "mentions_sustainability_abstract", "mentions_metrics_terms_abstract", "proxy_improvement_abstract"]],
        on="DOI_norm",
        how="left"
    )
    print("Full-text N:", len(results_df))
    print("Merged N:", len(merged))
    print("Abstract sustain missing:", merged["mentions_sustainability_abstract"].isna().mean())
    print("Abstract metric missing:", merged["mentions_metrics_terms_abstract"].isna().mean())
    merged_out = OUTDIR / "oa_abs_vs_full_merged.csv"
    merged.to_csv(merged_out, index=False)
    print(f" - Merged: {merged_out}")
    # Plot abstract vs full
    plot_three_figures_abs_vs_full(merged, OUTDIR)
    # Quick summary (full text)
    print("\nQuick summary (full text, % of successful parses):")
    for col in [
        "mentions_sustainability_fulltext",
        "mentions_metrics_terms_fulltext",
        "quantifies_any_metric_fulltext",
        "proxy_improvement_fulltext",
    ]:
        if col in results_df.columns:
            print(f" {col}: {100*results_df[col].mean():.1f}%")


if __name__ == "__main__":
    main()
