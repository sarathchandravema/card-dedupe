# Card customer de-duplication

Finds the same customer across different 16-digit card ids issued by different banks.

## Setup (Windows)
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run
```
.venv\Scripts\python -m dedupe.generate_data     # writes data/customers.csv + data/ground_truth.csv (52 records)
.venv\Scripts\python -m dedupe.cli               # prints duplicate groups + accuracy vs ground truth
.venv\Scripts\python app.py                      # web UI at http://127.0.0.1:5000
.venv\Scripts\python -m pytest -q                # tests
```

## Deploy to Netlify
Netlify cannot run the Flask server, so `build_static.py` pre-computes the field matches with the
Python matcher and writes a static `public/index.html`. The thresholds form still works: the page
re-applies them and regroups in the browser. `netlify.toml` already sets the build command,
publish directory and Python version.
```
.venv\Scripts\python build_static.py             # optional local build -> public/index.html
```
Then push the repo to GitHub/GitLab and import it in Netlify (no settings to change), or run
`netlify deploy --build --prod` with the Netlify CLI. `app.py` (Flask) is still for local use.

## Matching rule
Fields compared: name (fuzzy, Jaro-Winkler >= 0.90, word-order independent), mobile (last 10 digits),
email (lower-cased, `+tag` dropped, Gmail dots ignored), ATM used, IP address.

Weights: mobile 2.0, email 2.0, name 1.5, ATM 1.0, IP 1.0.
Two records are the same customer when **at least 3 fields match AND weighted score >= 4.5**.
So three weak matches alone (name + shared IP + shared ATM = 3.5) are NOT enough, since IPs and
popular ATMs are shared by strangers. Pairs are merged transitively (union-find) into groups.
Tune with `--min-matches` / `--min-score` (CLI) or the form in the web UI.

## Scaling note
`find_duplicates` compares all pairs (O(n^2)), fine for thousands of rows. For millions, add blocking
(index by mobile / email / phonetic name) so only candidate pairs are compared.
