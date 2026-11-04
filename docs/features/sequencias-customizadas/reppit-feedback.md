# Feedback on RePPIT commands

## Context
Which commands I used in each phase, with which prompts.

- Phase 1 / research: `research-codebase`, prompt: “Research and document the
  existing codebase exactly as it is today; no suggestions or evaluations…
  Read `docs/features/sequencias-customizadas/01-research.md` and build on the
  ‘Registro das descobertas’ session. This pass deliberately overrides the
  ‘no evaluations’ contract; note this deviation… add candidate matching
  hypotheses and trade-offs, still without choosing a final solution.”
- Run 1 was the initial current-state pass. Run 2 is this deliberate
  hypothesis/trade-off pass.
- Phase 2 / proposal: `make-proposals`, prompt: “Read `00-enunciado.md` and the
  full `01-research.md`… Generate 3 distinct proposals, ordered from most to
  least aligned… For each of the 12 open questions, either answer it or
  explicitly mark it out of scope. Do NOT choose a winner… Save to
  `evidence/02-proposals-draft.md`.” A follow-up prompt chose the hybrid and
  asked for `02-proposal.md`, which the command has no mode for.
- Phase 3 / plan: `make-plan`, prompt: “Read `00-enunciado.md`,
  `02-proposal.md`, `01-research.md` §1/§2.3/§3/§4, ADRs 0001–0003, `main.py`,
  `musica.py`, `Dockerfile`, `requirements.txt`, `sequencia.js`,
  `sequencia.html`, `AGENTS.md` and `README.md`… Write only `03-plan.md`; ignore
  `templates/design_doc_template.md` because it does not exist here; use the
  existing `03-plan.md` and keep its four sections… remove the blockquote, no
  timelines (ordered checkpoints), baseline fixture before any code change, do
  not re-open the decided matching/DB/API/scope.”
- Phase 4 / implementation: `implement`, prompt: “Read
  `docs/features/sequencias-customizadas/03-plan.md` first. Implement steps
  3–16 in order, stopping at each checkpoint to report the exact commands and
  output. Do not regenerate `tests/fixtures/sequencias_golden.json`; it is the
  source of truth for ‘before’. If a prompt instruction contradicts the plan,
  follow the prompt and record the correction in `03-plan.md` before
  continuing. Do not commit; leave the changes uncommitted for review.” Run 1
  was baseline-only (steps 1–2). Run 2 implemented steps 3–16.

## research-codebase.md
- Expected: the command’s behavior contract says “Only document what exists
  today; do not suggest improvements, RCA, or future work” and “Place the
  research document in the top level `research/` directory.” The phase-1
  template, however, asks for “Hipóteses candidatas” and “Trade-offs
  identificados” in `docs/features/sequencias-customizadas/01-research.md`.
- Observed: the two instructions conflict. Run 1 followed the no-evaluations
  contract and filled only the current-state evidence in the template. Run 2
  deliberately deviated: it kept all existing evidence, added candidate
  matching rules, applied them to the real CSV, and filled trade-offs/open
  questions, but did not choose or recommend a final solution. It wrote to
  `01-research.md`, not `research/`, and did not create `research/`.
- Evidence: run 1 is commit `93366c4` (`docs/features/sequencias-customizadas/
  01-research.md`). Run 2 edits the same file on top of that commit; the
  quantitative checks are in
  `docs/features/sequencias-customizadas/evidence/hypotheses_metrics.py` and
  `docs/features/sequencias-customizadas/evidence/extra_metrics.py` (outputs
  `.out` in the same directory). The key result is that the legacy tag rule is
  “contiguous sequence **and** every song chord belongs to the sequence
  vocabulary”, not merely “contiguous sequence”; this reproduces all six tag
  sets exactly.

- Suggested change: make the research command’s contract match the phase-1
  template, and make the output location conditional.

```diff
- Only document what exists today; do not suggest improvements, RCA, or future work
+ Document what exists today. When the research question explicitly asks for
+ them, add candidate hypotheses and trade-offs, but do not choose or recommend
+ a final solution.

- Place the research document in the top level `research/` directory.
+ If the feature template already defines a research file (for example
+ `docs/features/<feature>/01-research.md`), write there and preserve existing
+ evidence. Otherwise, place the document in the top level `research/`
+ directory.
```

- Impact: removes the direct contradiction between “no evaluations” and the
  template’s hypotheses/trade-offs, avoids a second parallel research file, and
  keeps run 1’s evidence intact. It also makes the “no final decision” boundary
  explicit, so the research phase can feed the proposal without pre-deciding
  it.

## make-proposals.md
- Expected: the command produces two or three distinct approaches ordered by
  alignment with the constraints, with trade-offs, validation and open
  questions, and deliberately does not pick a winner. Its output template is
  “Solution Proposals” (Context + Proposal N with Overview/Key Changes/
  Trade-offs/Validation/Open Questions). It does not write the phase-2 decision
  document, and it does not produce the ADR.
- Observed: the run produced three proposals in
  `docs/features/sequencias-customizadas/evidence/02-proposals-draft.md`, with
  the hybrid placed between H1 and H2/H3 by constraint adherence and an
  explicit “não há vencedor” — exactly what the command promises. But phase 2
  needs the opposite: `02-proposal.md` asks for one “Abordagem escolhida”, the
  discarded alternatives with concrete reasons, and an explicit scope. None of
  that is in the command's output template, so the decision had to be
  synthesized in a follow-up prompt, and the ADR
  (`docs/adr/0002-persist-custom-sequences.md`) was written outside the command
  entirely. The 12 open questions were answered only because the prompt
  demanded them item by item; the command's Notes merely say to “call out the
  gaps”, so a run without that explicit instruction can leave the decision
  document with unanswered questions. The requested numbering (1 = H1,
  2 = H2/H3, 3 = hybrid) also conflicted with “ordered from most to least
  aligned”: the draft had to put the hybrid second and add a note mapping the
  two orders.
- Evidence: proposals in commit `d219414`
  (`docs/features/sequencias-customizadas/evidence/02-proposals-draft.md`); the
  decision in commit `8b79e48`
  (`docs/features/sequencias-customizadas/02-proposal.md`); the ADR written in
  a separate step (`docs/adr/0002-persist-custom-sequences.md`). The draft's
  12-row tables exist only because the prompt required “For each of the 12 open
  questions, either answer it or explicitly mark it out of scope”.
- Suggested change: add a `decide` mode that consumes the research and the
  options and emits the phase-2 template; make per-question resolution
  mandatory in that mode; and have it draft the ADR, or hand off to the `adr`
  command listed under “Missing commands”.

```diff
- Produce two distinct solution approaches, each tied back to the research
- findings.
+ Produce two or three distinct approaches in `options` mode, each tied back to
+ the research findings and ordered by alignment with the stated constraints.
+ Do not pick a winner in `options` mode.
+
+ Add a `decide` mode: given the research document and the proposals, produce
+ the phase-2 decision document — one chosen approach, the discarded
+ alternatives with concrete reasons, explicit in/out-of-scope, and every open
+ question resolved or marked out of scope. `decide` should also draft the ADR,
+ or hand off to the `adr` command.

- ## Solution Proposals
+ ## Solution Proposals   (options mode)
+ ## Decision Proposal    (decide mode)
```

```diff
- When the research does not directly address the request, call out the gaps
- and suggest additional research before proposing solutions.
+ When the research does not directly address the request, call out the gaps
+ and suggest additional research before proposing solutions.
+
+ If the research ends with a numbered list of open questions, `decide` must
+ address every item — a decision or an explicit out-of-scope with reason. Do
+ not silently skip items; the number of answers must match the research.
```

- Impact: closes the gap between “generate options” and the phase-2 template's
  required choice, removes the manual synthesis step, makes ADR production an
  explicit part of the phase instead of an afterthought, and prevents decision
  documents that inherit unanswered open questions. `options` keeps its
  no-winner boundary, so the two modes stay separable.

## make-plan.md
- Expected: the command's numbered steps are to clarify scope, constraints and
  timelines; open `templates/design_doc_template.md`, mirror its structure and
  write the plan at `desired_location`; populate “current context,
  requirements, design decisions, and implementation plan” with concise,
  actionable bullets; note testing, observability, rollout and security only if
  they influence the change, leaving sections blank when they do not; not
  implement anything; and only make requested changes. It has no step that
  reads the project, and `desired_location` is never defined.
- Observed: the command assumes a template that may not exist and a document
  shape that may not match the repo. `templates/design_doc_template.md` does
  not exist here — there is no `templates/` directory at all — so “mirror its
  structure” was impossible as written. The phase-3 template that does exist,
  `docs/features/sequencias-customizadas/03-plan.md`, has four sections
  (`Passos`, `Arquivos afetados`, `Riscos e mitigação`, `Definição de pronto`),
  not the command's “current context / requirements / design decisions /
  implementation plan / testing / observability / rollout / security”. Following
  the command literally would have produced a document that contradicts the
  feature template. Two smaller mismatches follow from the same assumption:
  the command asks for “timelines”, which this project does not have (ordered
  checkpoints were used instead), and it would keep blank testing, observability,
  rollout and security sections for a local-only single-container change where
  they do not influence anything. The bigger gap is that the command never says to
  read anything: it does not know what `02-proposal.md`, `main.py` or
  `musica.py` are unless they are passed in. Phase 3 exists to decompose the
  decided proposal, yet no step opens it. Here the prompt had to enumerate the
  files (`00-enunciado.md`, `02-proposal.md`, `01-research.md` §1/§2.3/§3/§4,
  ADRs 0001–0003, `main.py`, `musica.py`, `Dockerfile`, `requirements.txt`,
  `sequencia.js`, `sequencia.html`, `AGENTS.md`, `README.md`), restate the four
  sections, forbid timelines, require a baseline fixture before any code change,
  require a startable checkpoint after each group, and forbid re-opening the
  matching, DB, API and scope decisions. Without that, the run would have
  produced a generic design document with an invented structure and no
  `file:line` grounding. `desired_location` is also undefined, so the output
  path had to be supplied explicitly.
- Evidence: the plan is commit `2cc7a49`
  (`docs/features/sequencias-customizadas/03-plan.md`, 253 insertions). Every
  citation in it (`main.py:187-189`, `main.py:203-223`, `musica.py:16`,
  `Dockerfile:3,8,12`, `sequencia.js:2-37`, `sequencia.html:42`) exists because
  the prompt supplied the file list; no command step opens the repository. The
  four sections and step 1's baseline capture come from the prompt, not from the
  command. `find . -name design_doc_template.md` returns nothing and there is no
  `templates/` directory.
- Suggested change: make template resolution conditional and define the output
  path; add a required reading step before writing; use ordered checkpoints
  when there are no deadlines; and omit sections that do not apply instead of
  leaving them blank.

```diff
- Clarify the code change scope, constraints, and timelines before writing anything down.
+ Clarify the code change scope and constraints before writing anything down.
+ If the project has no calendar deadlines, plan ordered checkpoints instead of
+ timelines.
```

```diff
- Open `templates/design_doc_template.md`, mirror its structure, and draft the plan as a `.md` file in `desired_location`.
+ If the project has `templates/design_doc_template.md`, mirror its structure.
+ Otherwise use the phase-3 template that already exists in the repo (for
+ example `docs/features/<feature>/03-plan.md`) and preserve its sections rather
+ than inventing a new structure. Write to the path given in the prompt; do not
+ guess `desired_location`.
```

```diff
- Populate current context, requirements, design decisions, and implementation plan with concise, actionable bullets.
+ Before writing, read the phase-2 decision document, the research it cites, the
+ ADRs it depends on, and the files the plan will touch. Populate the plan with
+ concise, actionable bullets that cite `file:line`, and decompose the decided
+ approach instead of re-opening it.
```

```diff
- Note testing, observability, rollout, and security sections only if they influence this change; leave sections blank when they do not apply.
+ Note testing, observability, rollout, and security only if they influence this
+ change. When they do not, omit the section entirely instead of leaving it
+ blank, and keep the project template's sections when the two disagree.
```

- Impact: removes a dead reference to a template that may not exist, defines
  where the plan is written, and forces the command to ground the plan in the
  actual decision, research and source files instead of producing a generic
  design document. It also stops timelines and boilerplate sections from leaking
  into projects whose phase-3 template has a different shape, while keeping the
  command's useful boundaries (no implementation, only requested changes).

## implement.md
- Expected: `implement.md` is one line — “Implement the plan described in
  `/path/to/plan_md`.” — so the plan should be the source of truth: execute its
  steps, stop where it says to stop, and run the verification it names. Here
  the plan deliberately puts the baseline capture before any code change
  (steps 1–2) and defines seven ordered checkpoints, so the command should
  respect that order, leave the captured “before” artifact untouched, and be
  usable across more than one sitting.
- Observed: the command has no notion of a baseline, a checkpoint, a resume
  point, or a verification gate, so it could not be run as written. Its natural
  reading is “start implementing”, which would have edited `main.py` before the
  baseline fixture existed and destroyed the only reliable record of the
  pre-change behavior. The run had to be split into two calls:
  - Call 1 executed only steps 1–2: capture the six legacy result sets into
    `tests/fixtures/sequencias_golden.json`, validate the counts, and stop
    before touching runtime code. The baseline is commit `fe48087`.
  - Call 2 implemented steps 3–16 in order, stopping at checkpoints 1–7,
    without regenerating the fixture, recording prompt-driven corrections in
    the plan, and leaving the tree uncommitted for review. Those changes were
    committed afterwards as `dbbe072`…`20e0c93`.

  Without that split the baseline would have been captured after the first edit
  (useless as “before”) or skipped entirely. The command also does not say to
  stop at checkpoints, so the prompt had to restate it; it does not require the
  plan to be updated when implementation diverges, so the seven recorded
  corrections would have been silent; and it does not define a commit boundary,
  so “leave uncommitted” was also a prompt instruction, and the eight-commit
  split had to be decided by the operator outside the command.
- Evidence: `~/.config/opencode/commands/implement.md` is exactly one line
  (`Implement the plan described in /path/to/plan_md.`). The baseline commit
  `fe48087` contains only `tests/fixtures/sequencias_golden.json`,
  `tests/fixtures/capture_baseline.py` and the plan’s step-1/2 checkboxes — no
  runtime code. The implementation commits are `dbbe072` (catalog), `8443bcd`
  (matching), `f19215c` (API), `5c8cd72` (frontend), `9be7e20` (Docker),
  `70471c1` (tests), `bf567d2` (AGENTS) and `20e0c93` (plan corrections). The
  plan records the deviations the command never asked for: stdlib-only capture
  (`03-plan.md:21-23`), `path=None` on the catalog functions
  (`03-plan.md:35-38`), Python 3.9 syntax (`03-plan.md:44-46`), the local
  `python3` being 3.14 without Flask (`03-plan.md:82`), id `0` being valid
  (`03-plan.md:122`), per-origin ports (`03-plan.md:165`) and `atexit` instead
  of `tearDownModule` (`03-plan.md:190-191`). The final suite ran 45 tests,
  `OK`, and the six legacy sets stayed at 199/296/4/5/7/3.
- Suggested change: turn the one-liner into an ordered contract with a
  baseline gate, checkpoint stops, a deviation log, a final verification step,
  and a resume/selection mode.

```diff
- Implement the plan described in /path/to/plan_md.
+ Implement the plan described in `/path/to/plan_md`, in its own order.
+
+ 1. Read the plan and the decision/research documents it cites. List its steps
+    and checkpoints before changing anything.
+ 2. Baseline gate: if the plan captures a "before" artifact (fixture, snapshot,
+    measurements), execute that step first and stop for confirmation. Do not
+    modify runtime code until it exists. Never regenerate an existing baseline
+    artifact unless the prompt explicitly asks for it.
+ 3. Implement the remaining steps in order. Stop at every checkpoint and run
+    the exact command it names; report the command and its output. Do not
+    continue past a failing checkpoint.
+ 4. If reality contradicts the plan (API, version, path, test isolation),
+    record the correction in the plan before continuing. Do not silently
+    change scope or invent a different design.
+ 5. Run the project's full verification command at the end and report the
+    result. Leave changes uncommitted unless the prompt asks for a commit, and
+    do not rewrite or drop existing work.
+
+ Support `--from <step>` and `--only <steps>` so a long plan can be resumed or
+ split across calls without re-describing the whole plan in the prompt.
```

- Impact: protects the “before” artifact from being overwritten by the first
  edit, makes a long plan resumable without a bespoke prompt, enforces the
  checkpoints the plan already defines, forces deviations to be documented
  instead of silently absorbed, and makes the final test run and commit state
  explicit. It keeps the command's original scope — implement the plan, not
  redesign it.

## Missing commands
- test/write-tests (phase 5 has no command)
- adr (phase 2)

> If you write a truly new command (e.g., write-tests.md), place the proposed .md file in reppit-proposals/ next to the feedback and link it in the document. If you want, also open an issue/PR in the RePPIT repo and cite the link — but the minimum is the document in your fork.

> At most, leave a link in the templates: Tool feedback: see reppit-feedback.md. The content of the suggestions is all in the dedicated file.