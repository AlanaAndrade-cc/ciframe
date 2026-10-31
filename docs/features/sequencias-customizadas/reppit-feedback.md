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
...
## make-plan.md
...
## implement.md
...
## Missing commands
- test/write-tests (phase 5 has no command)
- adr (phase 2)

> If you write a truly new command (e.g., write-tests.md), place the proposed .md file in reppit-proposals/ next to the feedback and link it in the document. If you want, also open an issue/PR in the RePPIT repo and cite the link — but the minimum is the document in your fork.

> At most, leave a link in the templates: Tool feedback: see reppit-feedback.md. The content of the suggestions is all in the dedicated file.