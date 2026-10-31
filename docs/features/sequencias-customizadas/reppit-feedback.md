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
...
## implement.md
...
## Missing commands
- test/write-tests (phase 5 has no command)
- adr (phase 2)

> If you write a truly new command (e.g., write-tests.md), place the proposed .md file in reppit-proposals/ next to the feedback and link it in the document. If you want, also open an issue/PR in the RePPIT repo and cite the link — but the minimum is the document in your fork.

> At most, leave a link in the templates: Tool feedback: see reppit-feedback.md. The content of the suggestions is all in the dedicated file.