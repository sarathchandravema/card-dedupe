"""Build a static site for Netlify: python build_static.py  ->  public/index.html

Netlify cannot run a Flask server, so the matching work that needs Python (field
normalisation and Jaro-Winkler name similarity) is done here at build time. Every
record pair that shares at least one field is embedded in the page as JSON. The
page then applies the thresholds (min matching fields / min weighted score) and
the transitive grouping in the browser, which mirrors ``find_duplicates``.
"""
from __future__ import annotations

import json
import shutil
from itertools import combinations
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dedupe.generate_data import DATA_DIR, main as generate_main
from dedupe.io import load_records
from dedupe.matcher import MatchConfig, compare

ROOT = Path(__file__).resolve().parent
CSV_PATH = DATA_DIR / "customers.csv"
OUT_DIR = ROOT / "public"


def build_payload() -> dict:
    if not CSV_PATH.exists():
        generate_main()
    records = load_records(CSV_PATH)
    # Loosest possible thresholds: keep every pair with at least one matching field.
    loosest = MatchConfig(min_matches=1, min_score=0.0)
    pairs = []
    for i, j in combinations(range(len(records)), 2):
        result = compare(records[i], records[j], loosest)
        if result.matched:
            pairs.append(
                {"a": i, "b": j, "matched": list(result.matched), "score": result.score}
            )
    defaults = MatchConfig()
    return {
        "records": [r.to_row() for r in records],
        "pairs": pairs,
        "defaults": {"min_matches": defaults.min_matches, "min_score": defaults.min_score},
    }


def main() -> None:
    payload = build_payload()
    # Escape "<" so the JSON can never close the surrounding <script> tag.
    data_json = json.dumps(payload).replace("<", "\\u003c")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape()
    )
    html = env.get_template("static_index.html").render(data_json=data_json)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    (OUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(
        f"Wrote {OUT_DIR / 'index.html'} "
        f"({len(payload['records'])} records, {len(payload['pairs'])} candidate pairs)"
    )


if __name__ == "__main__":
    main()
