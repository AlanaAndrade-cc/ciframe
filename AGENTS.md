# AGENTS.md

deciframe is a song-discovery tool for musicians: search by title/artist,
genre, chords you already know, or a famous chord sequence, and it finds
similar songs. Full description: [README.md](README.md).

## Stack

- Backend: Python 3.9, Flask 3.1, gunicorn. Single file (`main.py`) that
  loads `data/top/dataset_final.csv` into memory once at startup — there is
  no database.
- Frontend: AngularJS 1.4.9 + jQuery, loaded from CDN in `static/index.html`,
  no build step. Legacy, and there's no plan to modernize the stack itself —
  but touching it is no longer off-limits when a task needs it; see
  [docs/adr/0003-lift-frontend-freeze.md](docs/adr/0003-lift-frontend-freeze.md).
- Deploy: local-only via Docker for now. No cloud target has been chosen.

## Run locally

Docker (matches how the app actually ships):

```
docker build -t ciframe .
docker run -p 8080:8080 ciframe
```

Or a plain virtualenv:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py        # serves on :5000 instead of :8080
```

Run from the repo root: `main.py` opens `data/top/dataset_final.csv` relative
to the current directory.

## Verify it's up

```
curl http://localhost:8080/generos    # :5000 for plain `python main.py`
```

Done when this returns a JSON array of genre names (e.g. `["Rock", "Samba", ...]`), not an error page. If it hangs on startup, it's still parsing the CSV — give it a few seconds.

There is no test suite, linter, typechecker, CI, or task runner. Verify changes
by curling endpoints; don't invent `pytest`/`npm test` commands. If you add
tests, document the exact command here.

## Gotchas

- Editing `data/top/*.csv` requires a restart: it's read once at import time, not per-request.
- The CSV parser is deliberately naive: `main.py` skips the first line with
  `f.readline()` even though it is data, then does `replace('"', '')`,
  `replace('NA', '')` and `split(',')`. The first row is never loaded. Keep the
  column layout intact; commas, quotes, or `NA` in new data need parser changes.
- Every endpoint returns `json.dumps(...)` as a plain string, not `jsonify` — responses come back `Content-Type: text/html`. This is intentional legacy behavior; changing it is a real API change, not a cleanup.
- `/similares?sequencia=...` only recognizes the 6 hardcoded keys in
  `main.py:40-45`. Matching uses the precomputed `SEQ_FAMOSA`/`seqs_famosas`
  CSV tag; there is no live scan of `cifra`.
- The frontend is served by Flask: use the Flask origin, don't open
  `static/index.html` via `file://`. Controllers use relative API URLs; the
  `RESTAPI` constant in `static/assets/js/app.js` is unused. CDN scripts mean
  the page needs network access.
- `scripts/` is legacy Python 2 / R data-pipeline code (print statements,
  BeautifulSoup not in `requirements.txt`) for regenerating CSVs. It is not
  runtime code and won't run under Python 3.
- Check `docs/adr/` before changing the deploy setup. `docs/adr/0002-...md` is
  still an unfilled template, not a decided ADR.

## Coursework feature docs

`docs/features/sequencias-customizadas/` describes the current full-stack
assignment and its required 5-phase workflow (research -> proposal + ADR ->
plan -> implementation -> tests). Read `00-enunciado.md` before implementing.
Hard constraints: songs/genres stay in the in-memory CSV; only the sequence
catalog gets a database; stay on the single local Docker container; keep
`json.dumps` responses; the 6 original sequences must return identical results.
`#/porsequencia` currently hardcodes 4 of the 6 sequences in JS — this mismatch
is pre-existing, not something you introduced.
