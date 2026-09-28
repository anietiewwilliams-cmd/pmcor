"""
Download step only (standard library, no compiled packages).
Same Unpaywall lookup and PDF-validation logic as Faith's text-mining script:
best_oa_location + all oa_locations, accept a file only if it is a real PDF.
Text extraction and classification are done afterwards with the original script.

Run:  py download_pdfs.py
Output: pdfs folder (one PDF per DOI) and download_log.csv
v3: Unpaywall first, then OpenAlex and Europe PMC as fallbacks; uses the certifi certificate bundle and keeps cookies across redirects within each download (as requests.Session does in the original script).
"""
import os, csv, json, re, ssl, time, urllib.parse, urllib.request, urllib.error, http.cookiejar
try:
    import certifi  # pure-Python certificate bundle, the same one the original script used via requests
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    SSL_CTX = ssl.create_default_context()
from pathlib import Path

INPUT_PATH = "random_sample_300.csv"
UNPAYWALL_EMAIL = os.environ.get("UNPAYWALL_EMAIL", "youremail@xyz.edu")  # REQUIRED by Unpaywall
PDF_DIR = Path("pdfs"); PDF_DIR.mkdir(exist_ok=True)
SLEEP = 0.35; TIMEOUT = 60
UA = f"Mozilla/5.0 (compatible; OA-text-mining/3.0; +mailto:{UNPAYWALL_EMAIL})"


def norm_doi(x):
    x = str(x).strip().lower()
    for p in ("https://doi.org/", "http://doi.org/", "doi:"):
        x = x.replace(p, "")
    return x.strip()


def safe_name(doi):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", doi.strip())


def session():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), urllib.request.HTTPSHandler(context=SSL_CTX))


def get(url, headers, opener=None):
    opener = opener or session()
    req = urllib.request.Request(url, headers=headers)
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", "") if e.headers else "", b""


def unpaywall(doi):
    url = "https://api.unpaywall.org/v2/" + urllib.parse.quote(doi) + "?email=" + urllib.parse.quote(UNPAYWALL_EMAIL)
    _, _, body = get(url, {"User-Agent": UA})
    j = json.loads(body)
    best = j.get("best_oa_location") or {}
    urls = []
    if best.get("url_for_pdf"):
        urls.append(best["url_for_pdf"])
    for loc in j.get("oa_locations") or []:
        if loc and loc.get("url_for_pdf"):
            urls.append(loc["url_for_pdf"])
    seen = set(); urls = [u for u in urls if not (u in seen or seen.add(u))]
    return urls, (best.get("url") or j.get("doi_url"))


def openalex_urls(doi):
    url = "https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) + "?mailto=" + urllib.parse.quote(UNPAYWALL_EMAIL)
    status, _, body = get(url, {"User-Agent": UA})
    if status != 200 or not body:
        return []
    j = json.loads(body)
    locs = [j.get("best_oa_location") or {}] + (j.get("locations") or [])
    return [l["pdf_url"] for l in locs if l and l.get("pdf_url")]


def europepmc_urls(doi):
    q = urllib.parse.quote(f'DOI:"{doi}"')
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&resultType=core"
    status, _, body = get(url, {"User-Agent": UA})
    if status != 200 or not body:
        return []
    out = []
    for r in (json.loads(body).get("resultList", {}).get("result") or []):
        for f in ((r.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
            if f.get("documentStyle") == "pdf" and f.get("availabilityCode") in ("OA", "F") and f.get("url"):
                out.append(f["url"])
        if r.get("pmcid"):
            out.append(f"https://europepmc.org/articles/{r['pmcid']}?pdf=render")
    return out


def download(urls, out, referer):
    h = {"User-Agent": UA, "Accept": "application/pdf,application/xhtml+xml,text/html;q=0.9,*/*;q=0.8",
         "Accept-Language": "en-US,en;q=0.9"}
    if referer:
        h["Referer"] = referer
    last = None
    sess = session()  # one cookie-keeping session per DOI, like requests.Session()
    for u in urls:
        try:
            status, ctype, content = get(u, h, sess)
            if status != 200:
                last = f"HTTP {status}"; continue
            if not ("pdf" in ctype.lower() or content[:4] == b"%PDF"):
                last = f"Not a PDF (Content-Type={ctype})"; continue
            out.write_bytes(content)
            return True, "ok", u
        except Exception as e:
            last = str(e)
        time.sleep(SLEEP)
    return False, last or "download failed", None


def main():
    if "youremail" in UNPAYWALL_EMAIL:
        print("Please put your e-mail in UNPAYWALL_EMAIL at the top of this file first."); return
    rows = list(csv.DictReader(open(INPUT_PATH, encoding="utf-8-sig")))
    log = []
    for i, row in enumerate(rows, 1):
        doi = norm_doi(row.get("DOI", ""))
        rec = {"DOI": doi, "stage": "", "error": "", "used_pdf_url": "", "source": ""}
        print(f"[{i}/{len(rows)}] {doi}", end="  ", flush=True)
        pdf = PDF_DIR / (safe_name(doi) + ".pdf")
        if pdf.exists() and pdf.stat().st_size > 0:
            rec.update(stage="ok", source="cached"); print("cached"); log.append(rec); continue
        ok, used, source, msg, landing = False, None, "", "", None
        try:
            urls, landing = unpaywall(doi)
        except Exception as e:
            urls, msg = [], "unpaywall: " + str(e)
        time.sleep(SLEEP)
        if urls:
            ok, msg, used = download(urls, pdf, landing); source = "unpaywall"
        elif not msg:
            msg = "Unpaywall returned no direct PDF URL"
        # fallbacks: OpenAlex, then Europe PMC (legal open-access copies only)
        for name, finder in (("openalex", openalex_urls), ("europepmc", europepmc_urls)):
            if ok:
                break
            try:
                extra = [u for u in finder(doi) if u not in urls]
            except Exception as e:
                extra = []; msg += f" | {name}: {e}"
            time.sleep(SLEEP)
            if extra:
                urls += extra
                ok, m2, used = download(extra, pdf, landing)
                source = name if ok else source
                if not ok: msg += f" | {name}: {m2}"
        rec.update(stage="ok" if ok else ("no_pdf_url" if not urls else "download_pdf"), error="" if ok else msg,
                   used_pdf_url=used or "", source=source if ok else "")
        print(f"ok ({source})" if ok else ("no PDF url" if not urls else "failed"))
        log.append(rec); time.sleep(SLEEP)
    with open("download_log.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["DOI", "stage", "error", "used_pdf_url", "source"]); w.writeheader(); w.writerows(log)
    n = sum(r["stage"] == "ok" for r in log)
    print(f"\nDone: {n} of {len(log)} PDFs saved in {PDF_DIR}\\ ; log in download_log.csv")


if __name__ == "__main__":
    main()
