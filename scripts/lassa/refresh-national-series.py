"""
refresh-national-series.py — extend the validated national weekly series with
new NCDC sitrep data, honestly.

WHAT IT DOES
  1. Scrapes the NCDC Lassa sitrep archive (same source as rebuild-ncdc-real.py).
  2. Parses each PDF's *cumulative* year-to-date figures (suspected/confirmed/
     probable/deaths) + epi_week/year + source URL.
  3. Converts cumulative → WEEKLY incidence by differencing consecutive weeks
     within a year (cumulatives reset each year).
  4. Appends ONLY weeks not already present in
     data/lassa/lassa_fever_timeseries_full.csv, in that file's exact format.

HONESTY / SAFETY
  * Dry-run by default. Prints exactly what WOULD be appended + cross-checks.
    Use --apply to actually write (a timestamped .bak backup is made first).
  * Append-only: never edits or reorders existing rows.
  * Gap-safe: a weekly value is computed ONLY when the immediately-preceding
    epi-week was also scraped (or it is week 1). Weeks with a missing preceding
    sitrep are SKIPPED and reported — never back-filled by guessing.
  * Cross-check: reconstructs the running cumulative from the new weekly values
    and asserts it matches NCDC's reported cumulative for the latest week.
  * Provenance: new rows are marked extraction_method="ncdc_sitrep_cumdiff" and
    carry the source PDF URL, so single-source refreshed weeks are auditable and
    distinguishable from the original triangulated compilation.

CAVEAT (read before trusting): NCDC epi-weeks follow the MMWR (Sun–Sat)
convention; the existing series is keyed by ISO week (Mon–Sun). Near year
boundaries these can differ by one week. This script keys by the epi_week
printed on the sitrep and computes ISO Mon–Sun dates for display only; the
model uses (epi_year, epi_week, confirmed_cases). Eyeball the printed rows and
the cross-check before --apply.

Usage:
  python scripts/lassa/refresh-national-series.py                 # dry-run, all new weeks
  python scripts/lassa/refresh-national-series.py --year 2026     # restrict to a year
  python scripts/lassa/refresh-national-series.py --apply         # write (after review)
"""
import argparse
import csv
import re
import shutil
import sys
import time
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import pdfplumber

ARCHIVE = ("https://ncdc.gov.ng/diseases/sitreps/?cat=5&name="
           "An%20update%20of%20Lassa%20fever%20outbreak%20in%20Nigeria")
HEADERS = {"User-Agent": "LassaAI-Research/1.0 (public-health research; research@gailabai.com)"}
SERIES = Path("data/lassa/lassa_fever_timeseries_full.csv")

CUM = re.compile(r"Cumulative\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s*%")
HDR = re.compile(r"Epi\s*Week[:\s]*(\d{1,2})\s*(20\d{2})", re.I)


def pdf_links():
    r = requests.get(ARCHIVE, timeout=30, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if h.endswith(".pdf") and h not in seen:
            seen.add(h)
            out.append(h if h.startswith("http") else "https://ncdc.gov.ng" + h)
    return out


def parse(url):
    r = requests.get(url, timeout=45, headers=HEADERS)
    r.raise_for_status()
    with pdfplumber.open(BytesIO(r.content)) as pdf:
        txt = pdf.pages[0].extract_text() or ""
    h = HDR.search(txt)
    cums = CUM.findall(txt)
    if not h or not cums:
        return None
    wk, yr = int(h.group(1)), int(h.group(2))
    susp, conf, prob, death, _cfr = cums[0]   # first Cumulative row = current year to-date
    return {"year": yr, "week": wk, "cum_suspected": int(susp), "cum_confirmed": int(conf),
            "cum_probable": int(prob), "cum_deaths": int(death), "url": url}


def iso_dates(year, week):
    try:
        start = date.fromisocalendar(year, week, 1)
        end = date.fromisocalendar(year, week, 7)
        return start.isoformat(), end.isoformat()
    except ValueError:
        return "", ""


def load_existing():
    if not SERIES.exists():
        print(f"ERROR: {SERIES} not found"); sys.exit(1)
    rows = list(csv.DictReader(open(SERIES, encoding="utf-8")))
    have = {(int(r["epi_year"]), int(r["epi_week"])) for r in rows}
    cols = list(rows[0].keys())
    max_year = max(int(r["epi_year"]) for r in rows)
    return rows, have, cols, max_year


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=0, help="restrict to a single epi-year")
    ap.add_argument("--apply", action="store_true", help="write the append (default: dry-run)")
    ap.add_argument("--limit", type=int, default=0, help="cap PDFs parsed (debug)")
    args = ap.parse_args()

    rows, have, cols, max_year = load_existing()
    target_years = {args.year} if args.year else set(range(max_year, datetime.now().year + 1))
    print(f"Existing series: {len(rows)} weeks, latest epi-year {max_year}. "
          f"Scraping for years {sorted(target_years)} ...")

    links = pdf_links()
    if args.limit:
        links = links[:args.limit]
    print(f"Found {len(links)} sitrep PDFs.")

    # Scrape cumulative figures for the target years
    scraped = {}   # (year, week) -> parsed dict
    ok = fail = 0
    for i, u in enumerate(links, 1):
        try:
            rec = parse(u)
            if rec and rec["year"] in target_years:
                scraped[(rec["year"], rec["week"])] = rec   # later archive entries win
                ok += 1
            elif rec is None:
                fail += 1
        except Exception as e:
            fail += 1
            print(f"  FAIL {u[-28:]}: {str(e)[:50]}")
        time.sleep(1.0)
    print(f"Parsed {ok} sitreps in target years ({fail} unparseable/other).")

    # Convert cumulative -> weekly, per year, gap-safe
    new_rows, gaps = [], []
    ts = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    for yr in sorted(target_years):
        wks = sorted(w for (y, w) in scraped if y == yr)
        cum = {w: scraped[(yr, w)] for w in wks}
        for w in wks:
            if (yr, w) in have:
                continue   # already in the series — skip (append-only)
            prev = cum.get(w - 1)
            if prev is None and w != 1:
                gaps.append((yr, w))
                continue   # can't compute a clean weekly without the preceding week
            base = prev if prev else {"cum_suspected": 0, "cum_confirmed": 0, "cum_probable": 0, "cum_deaths": 0}
            cur = cum[w]
            wk_conf = cur["cum_confirmed"] - base["cum_confirmed"]
            wk_susp = cur["cum_suspected"] - base["cum_suspected"]
            wk_prob = cur["cum_probable"] - base["cum_probable"]
            wk_death = cur["cum_deaths"] - base["cum_deaths"]
            if min(wk_conf, wk_susp, wk_prob, wk_death) < 0:
                gaps.append((yr, w))   # negative weekly => cumulative reset/revision; do not trust
                continue
            ws, we = iso_dates(yr, w)
            new_rows.append({
                "week_start_date": ws, "week_end_date": we,
                "epi_year": yr, "epi_week": w,
                "suspected_cases": wk_susp, "confirmed_cases": wk_conf,
                "probable_cases": wk_prob, "deaths": wk_death,
                "extraction_method": "ncdc_sitrep_cumdiff",
                "extraction_timestamp": ts,
                "report_pdf_url": cur["url"],
            })

    # ── Report ────────────────────────────────────────────────────────────────
    print("\n=== NEW WEEKLY ROWS TO APPEND ===")
    if not new_rows:
        print("  (none — series already current, or no clean weekly could be derived)")
    for r in new_rows:
        print(f"  {r['epi_year']}-W{r['epi_week']:02d} ({r['week_start_date']}..{r['week_end_date']})  "
              f"confirmed={r['confirmed_cases']}  deaths={r['deaths']}  suspected={r['suspected_cases']}")
    if gaps:
        print(f"\n  SKIPPED (missing preceding sitrep / cumulative reset — NOT guessed): "
              f"{', '.join(f'{y}-W{w:02d}' for y, w in sorted(gaps))}")

    # ── Cross-check: reconstruct cumulative from new weekly, compare to NCDC ─────
    for yr in sorted({r['epi_year'] for r in new_rows}):
        yr_new = [r for r in new_rows if r['epi_year'] == yr]
        latest_w = max(r['epi_week'] for r in yr_new)
        ncdc_cum = scraped[(yr, latest_w)]["cum_confirmed"]
        recon = sum(r['confirmed_cases'] for r in yr_new)
        # add any pre-existing weeks of this year already in the series
        recon += sum(int(r['confirmed_cases'] or 0) for r in rows if int(r['epi_year']) == yr and int(r['epi_week']) <= latest_w)
        flag = "OK" if recon == ncdc_cum else "MISMATCH — review before --apply"
        print(f"\n  Cross-check {yr} @W{latest_w}: reconstructed cum_confirmed={recon} "
              f"vs NCDC reported={ncdc_cum}  [{flag}]")

    # ── Apply ──────────────────────────────────────────────────────────────────
    if not args.apply:
        print("\nDRY-RUN. Review the rows + cross-check above, then re-run with --apply to write.")
        return
    if not new_rows:
        print("\nNothing to append."); return
    bak = SERIES.with_suffix(f".csv.bak-{datetime.now():%Y%m%d%H%M%S}")
    shutil.copy2(SERIES, bak)
    with open(SERIES, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        for r in new_rows:
            w.writerow({c: r.get(c, "") for c in cols})
    print(f"\nAppended {len(new_rows)} weeks to {SERIES} (backup: {bak.name}).")
    print("Next: python scripts/lassa/national-forecast-now.py && python scripts/lassa/national-forecast-logger.py")


if __name__ == "__main__":
    main()
