# Persist the custom sequence catalog in a local SQLite file

The sequence catalog used to be a hardcoded dict in `main.py` (`main.py:40-45`),
mapping six chord strings to ids 0–5. It could only change by editing code, and
there was nowhere for a visitor-created sequence to live: anything created at
runtime would be lost on restart. The customizable-sequences feature (see
`docs/features/sequencias-customizadas/00-enunciado.md`) needs the opposite — an
anonymous, append-only catalog that any visitor can add to and that survives
restarts. Songs and genres are a separate concern and stay where they are,
loaded from `data/top/dataset_final.csv` into memory at import time
(`main.py:49-98`).

We're persisting only the sequence catalog in a SQLite database file at
`/app/var/sequences.db`, using the `sqlite3` module that ships with Python 3.9,
in a single `sequences` table. The six originals are seeded idempotently with
their existing ids 0–5 and legacy keys (`BmGDA`, `CGAmF`, `EmG`, `CA7DmG7`,
`GmF`, `CC7FFm`), so existing lookups and the legacy `sequencia=` parameter keep
working. The database is created and seeded at import time, in the same flow
that already loads the CSV (`main.py:49-98`), since gunicorn imports `main:app`
(`Dockerfile:12`). The image gets a writable `/app/var` directory, and the run
command documented in the README mounts a named volume over it:
`docker run -p 8080:8080 -v deciframe-data:/app/var ciframe`.

SQLite is the smallest thing that satisfies the constraints. It stays inside
the single local container from `docs/adr/0001-local-only-docker-deploy.md`,
needs no external service and no new dependency (`requirements.txt:4-5`), and
the catalog is small — six rows today, not a workload that justifies anything
heavier. It also gives transactions and a unique constraint, which the catalog
needs to reject duplicate sequences without hand-rolled locking. The volume is
what makes persistence real: the writable layer survives `docker restart`, but
not `docker rm` plus recreation, and the requirement is that the catalog not
disappear. The volume is mounted at `/app/var`, not `/app/data`, because
`/app/data` holds the CSV copied into the image (`Dockerfile:8`) and a mount
there could hide it. Responses stay `json.dumps(...)` strings with
`Content-Type: text/html` (`main.py:197,201`); this decision changes where the
catalog lives, not how the API serializes it.

Two costs come with that. First, schema and migrations become part of the
system: the table is versioned with `PRAGMA user_version`, and any future column
change needs a migration step; there is deliberately no ORM or migration
framework, because the catalog is small and the dependency budget is tight.
Second, persistence now depends on how the container is run — without the named
volume, `docker rm` loses the catalog, and that has to be documented rather
than silently assumed. Concurrency is a smaller concern today, since gunicorn
runs a single worker (`Dockerfile:12`), but WAL mode and a busy timeout are set
so that adding `--workers` later doesn't corrupt writes; SQLite still serializes
writers. If the catalog ever grows to the point where a full scan per search
hurts, that is a separate decision, not a reason to change the database now.

The hardcoded `sequencias` dict stops being the source of truth; the database
is. That leaves a second potential source of truth for the six originals
specifically: their rows in the database and the precomputed tags they still
match against in the CSV. The rows own identity and display — id, name, chord
list — while the tags own matching for the originals in this iteration. Startup
verifies that ids and legacy keys agree, so a mismatch fails loudly instead of
producing subtly different results. The matching rule itself, including that
split and how each row records it, is not decided here; it is documented in
`docs/features/sequencias-customizadas/02-proposal.md`. This ADR only settles
where the catalog lives and how it survives.
