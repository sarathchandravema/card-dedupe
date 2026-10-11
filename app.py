"""Flask UI: python app.py  ->  http://127.0.0.1:5000"""
from __future__ import annotations

from flask import Flask, render_template, request

from dedupe.generate_data import DATA_DIR, main as generate_main
from dedupe.io import load_records
from dedupe.matcher import MatchConfig, find_duplicates

app = Flask(__name__)
CSV_PATH = DATA_DIR / "customers.csv"


@app.route("/")
def index():
    if not CSV_PATH.exists():
        generate_main()
    min_matches = request.args.get("min_matches", default=3, type=int)
    min_score = request.args.get("min_score", default=4.5, type=float)
    records = load_records(CSV_PATH)
    clusters = find_duplicates(records, MatchConfig(min_matches=min_matches, min_score=min_score))
    grouped_ids = {r.id for c in clusters for r in c.records}
    return render_template(
        "index.html",
        records=records,
        clusters=clusters,
        unique_count=len(records) - len(grouped_ids),
        min_matches=min_matches,
        min_score=min_score,
    )


if __name__ == "__main__":
    app.run(debug=True)
