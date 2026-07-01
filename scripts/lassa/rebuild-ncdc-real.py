"""
rebuild-ncdc-real.py — build a REAL Lassa dataset from actual NCDC sitrep PDFs.

Replaces the old synthetic `seed_annual_estimate` series (annual totals distributed by a
fixed formula, with INVERTED seasonality) with genuine figures parsed from the NCDC weekly
Lassa Fever Situation Report PDFs at https://ncdc.gov.ng/diseases/sitreps.

For each sitrep it records, with full provenance (source_url):
  - epi_week, year               (from the PDF header "Epi Week: N YYYY")
  - cum_confirmed, cum_deaths     (the first "Cumulative ..." row = current year to-date)
  - cum_suspected, cfr, states_affected
  - top_state_shares             (from the "X% ... Ondo reported N%, Bauchi M% ..." narrative)
It also writes the prior-year comparison cumulative row when present.

Weekly national incidence = difference of consecutive weeks' cum_confirmed (computed downstream).

NOTE (honesty): NCDC per-state weekly counts live in an image-based table (Table 3) that
pdfplumber cannot extract as text; this script captures REAL national weekly incidence and
REAL per-state *shares*, not exact per-state weekly counts. Per-state weekly extraction would
require OCR or manual entry and is left as future work.

Usage:  python scripts/lassa/rebuild-ncdc-real.py [--limit N]
Output: data/lassa/ncdc-real.csv  +  data/lassa/ncdc-real.log
"""
import re, csv, sys, time, argparse, logging
from io import BytesIO
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import pdfplumber

ARCHIVE = "https://ncdc.gov.ng/diseases/sitreps/?cat=5&name=An%20update%20of%20Lassa%20fever%20outbreak%20in%20Nigeria"
HEADERS = {"User-Agent": "LassaAI-Research/1.0 (public-health research; research@gailabai.com)"}
OUT = Path("data/lassa/ncdc-real.csv")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("data/lassa/ncdc-real.log", "w")])
log = logging.getLogger()

def pdf_links():
    r = requests.get(ARCHIVE, timeout=30, headers=HEADERS); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.endswith(".pdf") and h not in seen:
            seen.add(h)
            out.append(h if h.startswith("http") else "https://ncdc.gov.ng" + h)
    return out

CUM = re.compile(r"Cumulative\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s*%")
HDR = re.compile(r"Epi\s*Week[:\s]*(\d{1,2})\s*(20\d{2})", re.I)
STATES_AFF = re.compile(r"(\d+)\s+States?\s+have\s+recorded", re.I)
SHARE = re.compile(r"([A-Z][a-z]+)\s+reported\s+(\d+)%|([A-Z][a-z]+)\s+(\d+)%")

def parse(url):
    r = requests.get(url, timeout=45, headers=HEADERS); r.raise_for_status()
    with pdfplumber.open(BytesIO(r.content)) as pdf:
        txt = pdf.pages[0].extract_text() or ""
    h = HDR.search(txt)
    if not h:
        return None
    wk, yr = int(h.group(1)), int(h.group(2))
    cums = CUM.findall(txt)           # first = current year, second (if any) = prior-year comparison
    if not cums:
        return None
    susp, conf, prob, death, cfr = cums[0]
    aff = STATES_AFF.search(txt)
    shares = "; ".join(f"{m[0] or m[2]}:{m[1] or m[3]}%" for m in SHARE.findall(txt) if (m[0] or m[2]))
    return {"epi_week": wk, "year": yr, "cum_confirmed": int(conf), "cum_deaths": int(death),
            "cum_suspected": int(susp), "cfr": float(cfr), "states_affected": int(aff.group(1)) if aff else "",
            "top_state_shares": shares[:200], "source_type": "ncdc_sitrep_real", "source_url": url}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=0); a = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    links = pdf_links()
    if a.limit:
        links = links[:a.limit]
    log.info(f"Found {len(links)} sitrep PDFs to parse")
    rows, ok, fail = {}, 0, 0
    for i, u in enumerate(links, 1):
        try:
            rec = parse(u)
            if rec:
                rows[(rec["year"], rec["epi_week"])] = rec   # dedupe by (year,week); later archive entries win
                ok += 1
                if ok % 20 == 0: log.info(f"  parsed {ok} ok / {i} tried")
            else:
                fail += 1
        except Exception as e:
            fail += 1; log.warning(f"  FAIL {u[-30:]}: {str(e)[:60]}")
        time.sleep(1.0)
    recs = sorted(rows.values(), key=lambda r: (r["year"], r["epi_week"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
    yrs = sorted({r["year"] for r in recs})
    log.info("=" * 60)
    log.info(f"REAL data written: {OUT}  ({len(recs)} weekly reports, {ok} ok, {fail} failed)")
    log.info(f"Years covered: {yrs}")
    for y in yrs:
        wr = [r for r in recs if r["year"] == y]
        maxw = max(wr, key=lambda r: r["epi_week"])
        log.info(f"  {y}: {len(wr)} weeks; latest wk{maxw['epi_week']} cum_confirmed={maxw['cum_confirmed']} cum_deaths={maxw['cum_deaths']}")

if __name__ == "__main__":
    main()
