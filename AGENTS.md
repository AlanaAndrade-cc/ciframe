# AGENTS.md

deciframe is a song-discovery tool for musicians: search by title/artist,
genre, chords you already know, or a famous chord sequence, and it finds
similar songs. Full description: [README.md](README.md).

## Stack

- Backend: Python 3.9, Flask 3.1, gunicorn. `main.py` loads
  `data/top/dataset_final.csv` into memory once at startup (songs and genres).
  The chord-sequence catalog is the one piece that lives in SQLite
  (`catalogo.py`, default `var/sequences.db`, overridable with
  `SEQUENCES_DB`); the matching rules live in `matching.py`.
- Frontend: AngularJS 1.4.9 + jQuery, loaded from CDN in `static/index.html`,
  no build step. Legacy, and there's no plan to modernize the stack itself —
  but touching it is no longer off-limits when a task needs it; see
  [docs/adr/0003-lift-frontend-freeze.md](docs/adr/0003-lift-frontend-freeze.md).
- Deploy: local-only via Docker for now. No cloud target has been chosen.

## Run locally

Docker (matches how the app actually ships):

```
docker build -t ciframe .
docker run -p 8080:8080 -v deciframe-data:/app/var ciframe
```

The named volume keeps the sequence catalog across `docker restart` and
`docker rm`; without `-v`, `docker rm` resets it to the 6 seeded sequences.

Or a plain virtualenv:

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py        # serves on :5000 instead of :8080
```

Run from the repo root: `main.py` opens `data/top/dataset_final.csv` relative
to the current directory. The catalog is created automatically at
`var/sequences.db` (or `SEQUENCES_DB`) on first import.

## Verify it's up

```
curl http://localhost:8080/generos    # :5000 for plain `python main.py`
```

Done when this returns a JSON array of genre names (e.g. `["Rock", "Samba", ...]`), not an error page. If it hangs on startup, it's still parsing the CSV — give it a few seconds.

Tests use `unittest` (no extra dependency). Run from the repo root:

```
.venv/bin/python -m unittest discover -s tests -v
```

The suite points `SEQUENCES_DB` at a temporary file before importing `main`,
so it never touches `var/`. There is no linter, typechecker, CI, or task
runner; verify changes by curling endpoints too, and don't invent
`pytest`/`npm test` commands.

## Gotchas

- Editing `data/top/*.csv` requires a restart: it's read once at import time, not per-request.
- The CSV parser is deliberately naive: `main.py` skips the first line with
  `f.readline()` even though it is data, then does `replace('"', '')`,
  `replace('NA', '')` and `split(',')`. The first row is never loaded. Keep the
  column layout intact; commas, quotes, or `NA` in new data need parser changes.
- Every endpoint returns `json.dumps(...)` as a plain string, not `jsonify` — responses come back `Content-Type: text/html`. This is intentional legacy behavior; changing it is a real API change, not a cleanup.
- `/similares?sequencia=<legacy_key>` still recognizes only the 6 original
  keys in `main.py:40-45`; it resolves the key through the catalog and uses the
  precomputed `SEQ_FAMOSA`/`seqs_famosas` CSV tag. `sequencia_id=<id>` serves
  the whole catalog: ids 0–5 keep the tag path, new ids use live contiguous
  matching over `Musica.cifra` (see `matching.py`).
- The frontend is served by Flask: use the Flask origin, don't open
  `static/index.html` via `file://`. Controllers use relative API URLs; the
  `RESTAPI` constant in `static/assets/js/app.js` is unused. CDN scripts mean
  the page needs network access. `#/porsequencia` loads the whole catalog from
  `GET /sequencias` and searches with `sequencia_id=`.
- `scripts/` is legacy Python 2 / R data-pipeline code (print statements,
  BeautifulSoup not in `requirements.txt`) for regenerating CSVs. It is not
  runtime code and won't run under Python 3.
- Check `docs/adr/` before changing the deploy setup; ADR 0002
  (`docs/adr/0002-persist-custom-sequences.md`) records the SQLite catalog
  decision.

## Coursework feature docs

`docs/features/sequencias-customizadas/` describes the current full-stack
assignment and its required 5-phase workflow (research -> proposal + ADR ->
plan -> implementation -> tests). Read `00-enunciado.md` before implementing.
Hard constraints: songs/genres stay in the in-memory CSV; only the sequence
catalog gets a database; stay on the single local Docker container; keep
`json.dumps` responses; the 6 original sequences must return identical results.
`#/porsequencia` now loads the catalog from `GET /sequencias` instead of
hardcoding sequences in JS.
