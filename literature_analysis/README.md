# Literature analysis: the metrics gap

Scripts and data behind the literature survey in the Perspective (main-text Fig. 2 and 3; ESI section S1).

## What is here

| Path | Content |
|---|---|
| `rules/text_mining_rules.py` | Rule-based text-mining framework (F. M. Wariri): pattern sets, full-text extraction and classification. |
| `01_classify_metadata.py` | Classifies Scopus titles, abstracts and keywords; applies the pre-declared gas-phase exclusion rule; draws the random sample of 300 (seed 20260926). |
| `02_download_pdfs.py` | Retrieves open-access PDFs (Unpaywall, then OpenAlex and Europe PMC). Set `UNPAYWALL_EMAIL` in your environment. |
| `03_fulltext.py` | Extracts text from the PDFs and classifies the full texts. |
| `04_sensitivity.py` | Reference-list exclusion, broader metric definitions, paired comparison, retrieval bias and publisher mix. |
| `05_all_records_access.py` | Open-access versus subscription comparison over all 10,758 records. |
| `06_fig3.py` | Main-text Fig. 3. |
| `07_hand_labels.py` | Precision and recall of the improvement rule, and the hand-labelled paired result. |
| `data/` | Record identifiers (EID, DOI), all rule outputs, retrieval log, reading verdicts and hand labels. |

## Scopus exports are not redistributed

Scopus terms do not permit redistribution of abstracts, so `data/` contains identifiers and labels only. To rerun from scratch, export from Scopus (all fields, CSV) with

```
TITLE-ABS-KEY("continuous flow" OR "continuous-flow" OR "flow chemistry" OR "flow synthesis" OR "flow reactor" OR microreactor)
AND SUBJAREA(CHEM) AND DOCTYPE(ar) AND PUBYEAR > 2016 AND PUBYEAR < 2026
```

Save the open-access subset as `scopus_oa_4608.csv` and all records as `scopus_all_10758.csv` in this folder. Scopus content changes over time, so a new export may differ slightly from the one analysed (26–27 September 2026); the identifiers in `data/` define the analysed sets exactly.

## Run order

```bash
pip install pandas scipy matplotlib pdfminer.six certifi openpyxl
python 01_classify_metadata.py
UNPAYWALL_EMAIL=you@example.org python 02_download_pdfs.py
python 03_fulltext.py
python 04_sensitivity.py
python 05_all_records_access.py
python 07_hand_labels.py     # runs from data/ alone
```

## Hand labels

`data/hand_labels_85.csv` is a random sample of 85 records (60 flagged and 25 not flagged by the improvement rule, which is applied to title, abstract and keyword metadata); their abstracts were labelled blind to the rule output. `data/hand_labels_134.csv` holds labels for the abstracts of all 134 full-text papers. Label Y means the abstract claims an advantage of the flow or continuous process over batch or conventional processing, stated explicitly or clearly implied. `data/metric_verification.csv` records the reading of every full text that mentions a green metric.
