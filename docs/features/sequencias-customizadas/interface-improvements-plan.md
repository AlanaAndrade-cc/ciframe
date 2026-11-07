# Plan — Interface improvements for `#/porsequencia`

## Context

- The target screen is served by `static/templates/sequencia.html` and
  `static/assets/js/controllers/sequencia.js`; the route is
  `#/porsequencia` (`static/assets/js/routes.js`).
- The catalog row currently puts the tag, the sequence name and the chord
  hexes in the same `.acordes-container`
  (`static/templates/sequencia.html:17-23`). The hexes use a floating wrapper
  (`static/assets/css/app.css:161-190`), so the inline tag/name share the line
  with the first hexes and can push them out of alignment.
- The sequence name uses Bootstrap's `small.text-muted`
  (`static/templates/sequencia.html:21`). On the pink panel
  (`#BA007C`, `static/assets/css/app.css:79`) that is `#777777`, a contrast
  ratio of **1.39:1**, below WCAG AA (4.5:1).
- Registration currently uses free-text inputs
  (`static/templates/sequencia.html:27-43`), with `adicionarAcorde` /
  `removerAcorde` operating on an array of strings
  (`static/assets/js/controllers/sequencia.js:126-136`). The initial state is
  `{ nome: '', acordes: [''] }` (`static/assets/js/controllers/sequencia.js:33`).
- The first screen already has the chord catalog as seven groups of
  `{acorde, cor}` objects in `static/assets/js/controllers/acordes.js:2-44`.
  The `df-hex` directive already supports a smaller 30px variant
  (`small="true"`) and a checked/selected state
  (`static/assets/js/directives/df-hex.js`,
  `static/templates/directives/df-hex.html`).
- Visual reference:
  `docs/features/sequencias-customizadas/evidence/print-referencia.png`.
- `templates/design_doc_template.md` does not exist in this repository (there is
  no `templates/` directory). This plan follows the existing
  `docs/features/sequencias-customizadas/03-plan.md` structure plus the
  sections requested in the prompt.
- There is no calendar deadline; use ordered checkpoints.

## Requirements

### Task 1 — Tag positioning

- Put the `original` / `nova` tag before the first chord, in its own block
  above the chord row, visually separated from the hexes.
- Keep the chord row aligned across sequences; the tag must not consume the
  space of the first hex or cause wrapping differences.
- Preserve the current hex format, colors and `df-hex` behavior.

### Task 2 — Name contrast

- Replace the low-contrast `text-muted` name with a high-contrast style on the
  pink panel. Use white (`#FFFFFF`), which is **6.22:1** against `#BA007C`.
- Keep the tag, name and chords in a clear hierarchy: small tag, stronger name,
  then the chord row.
- Preserve the application's existing visual identity and tag colors.

### Task 3 — Visual sequence registration

- Replace the free-text chord inputs with a palette of clickable hexagonal
  buttons based on the first screen's chord catalog.
- Use the existing `df-hex` directive with `small="true"`; do not create a
  second hex implementation.
- Every palette click appends the chord to the sequence. The stored order must
  be exactly the click order, including repeated chords.
- Display the sequence being built, in order, using small hexes.
- Allow individual removal by clicking a selected chord in the built sequence.
- Keep the name field and the save action; keep the existing `POST /sequencias`
  contract and its 400/409 handling.
- Enforce the existing 1–32 chord limit in the UI; the backend remains the
  source of truth.

### Constraints

- AngularJS 1.4.9, no build step, no new JavaScript dependencies.
- No backend, API, database, Docker or `requirements.txt` changes.
- Keep `json.dumps(...)` responses and the existing endpoints untouched.
- Preserve catalog search, pagination, genre filter, catalog click behavior and
  the 400/409 registration messages.
- Keep `GENEROS` fixed in `static/assets/js/app.js`.
- Only change what the three tasks require.

## Design decisions

1. **Tag/name header above the chord row.** Render a
   `.sequencia-meta` block before the `.acordes-container`, with the tag first
   and the name second. Give the header the same 300px centered width as the
   chord row so the tag starts at the first chord's left edge without sitting
   in the float flow. This is the smallest change that removes the interference
   and keeps every sequence row aligned.
2. **White, semibold name.** Replace `class="text-muted"` with
   `class="sequencia-nome"` and style it `color: #fff; font-weight: 600;`.
   Keep the existing `label-primary` / `label-success` tag classes and colors.
3. **Local palette copy, no first-screen refactor.** Copy the seven chord
   groups from `static/assets/js/controllers/acordes.js:2-44` into
   `SequenciaController` as `ACORDES_PALETA`, preserving the exact chord names,
   colors and group order. Do not modify `acordes.js`, `app.js` or the first
   screen. This keeps the change contained to `#/porsequencia`; extracting a
   shared constant is a separate refactor and is out of scope.
4. **Ordered selection is an array of strings.** Keep
   `vm.novaSequencia.acordes` as the API-ready array of chord names. A palette
   click pushes the name; removal splices by index. Do not sort, deduplicate or
   use an unordered selection structure. Use `track by $index` so repeated
   chords are preserved.
5. **Palette clicks always add; selected chips remove.** The requirement says
   each click adds a chord, so a palette button is not a toggle. The built
   sequence is the removal surface: clicking a selected chord removes that
   occurrence. Add helper text explaining both actions. This also removes the
   ambiguity when the same chord appears more than once.
6. **Reuse `df-hex`.** Palette buttons use `small="true"` and
   `acorde-checked` to show chords already present. Selected chips use their
   normal color and are clickable to remove. Do not modify the directive or its
   template.
7. **Client-side save guard only.** Disable the submit button while saving,
   when the trimmed name is empty, or when no chord is selected. Keep the
   existing server validation and 400/409 messages as the final authority.
8. **No free-text chords in the new UI.** The palette covers the 36 chords
   already offered on `#/poracordes`; arbitrary chord strings are no longer
   entered by hand. This is the requested replacement, not a backend change.

## Implementation plan

### Step 1 — Baseline the current screen

- [ ] Start the app from the repository root:
  `.venv/bin/python main.py` (serves on `:5000`).
- [ ] Open `http://localhost:5000/#/porsequencia` and confirm the current
  catalog loads, a catalog card starts a search, and the text-input form can
  register a sequence.
- [ ] Record the current layout issue and the current name contrast in the
  task notes/evidence before editing.
- **Checkpoint 1:** the app is serving, the catalog is populated, and the
  existing search/registration flow works before any change.

### Step 2 — Add the local chord palette

- [ ] In `static/assets/js/controllers/sequencia.js`, add `ACORDES_PALETA`
  with the seven groups copied verbatim from
  `static/assets/js/controllers/acordes.js:2-44`. Preserve group order, chord
  names, colors and the 36-chord total.
- [ ] Expose it as `vm.acordesPaleta = ACORDES_PALETA;`.
- [ ] Do not modify `acordes.js`, `app.js` or `#/poracordes`.
- **Checkpoint 2:** the palette data matches the first screen's 36 chords and
  colors; `#/poracordes` is untouched; `#/porsequencia` still loads the
  catalog.

### Step 3 — Fix the catalog row layout and name contrast

- [ ] In `static/templates/sequencia.html`, replace the catalog repeat body
  (`:17-23`) with:
  - a `.sequencia-item` wrapper carrying the existing
    `ng-click="Sequencia.pesquisarPorSequencia(sequencia)"`;
  - a `.sequencia-meta` header containing the existing tag `<span>` and a
    `span.sequencia-nome` (remove `text-muted`);
  - a separate `.acordes-container` holding the existing `df-hex` repeat.
- [ ] In `static/assets/css/app.css`, add:
  - `.sequencia-item { margin-bottom: 14px; cursor: pointer; }`
  - `.sequencia-item::after { content: ""; display: table; clear: both; }`
  - `.sequencia-meta { width: 300px; max-width: 100%; margin: 0 auto 4px; }`
  - `.sequencia-meta .label { margin-right: 6px; }`
  - `.sequencia-nome { color: #fff; font-weight: 600; }`
- [ ] Keep `.acordes-container` and the `df-hex` markup unchanged so the hex
  size, colors and float behavior stay the same.
- **Checkpoint 3:** every catalog tag sits above the first chord and is
  visually separated; all chord rows share the same left edge; names are white
  and readable; clicking a row still starts the search; tag colors and hex
  appearance are unchanged.

### Step 4 — Implement ordered selection state

- [ ] In `static/assets/js/controllers/sequencia.js`, change the initial form
  state to `vm.novaSequencia = { nome: '', acordes: [] }`
  (`:33`) and update the reset in `cadastrar` (`:147`) to the same shape.
- [ ] Add:
  - `vm.corDoAcorde = corDoAcorde;` so the template can color selected chips;
  - `vm.temAcordeSelecionado(acorde)` → `indexOf(acorde) > -1`;
  - `vm.adicionarAcorde(acorde)` → push when
    `vm.novaSequencia.acordes.length < 32`;
  - `vm.removerAcorde(indice)` → `splice(indice, 1)` with no minimum-length
    guard;
  - `vm.podeSalvar()` → non-empty trimmed name, at least one chord, and not
    `vm.salvando`.
- [ ] Keep `vm.cadastrar` posting `{ nome, acordes }` exactly as today; on
  success reload the catalog and reset the form.
- [ ] Do not change `vm.temAcorde` used by the catalog search highlighting; it
  operates on the selected catalog sequence objects.
- **Checkpoint 4:** clicking C, G, Am, F displays `C, G, Am, F` in that order;
  adding a repeated chord preserves the repetition; removing a middle chord
  leaves the remaining order intact; the 33rd chord is rejected; the submit
  button is disabled until a name and at least one chord exist.

### Step 5 — Build the visual registration interface

- [ ] In `static/templates/sequencia.html`, keep the name input
  (`:29-31`) and replace the text-input repeat and `+ acorde` button
  (`:32-40`) with:
  - a `.acordes-selecionados` block that repeats
    `Sequencia.novaSequencia.acordes` with `track by $index` when the array is
    non-empty; each item is a small `df-hex` with `acorde="{{acorde}}"`,
    `acorde-color="{{Sequencia.corDoAcorde(acorde)}}"`, `small="true"`,
    `acorde-checked="false"`, `title="Clique para remover"`, and
    `ng-click="Sequencia.removerAcorde($index)"`;
  - a muted placeholder such as “Nenhum acorde selecionado.” when the array is
    empty;
  - helper text: “Clique nos acordes para adicionar. Clique em um acorde da
    sequência para remover.”;
  - a `.acordes-container.acordes-paleta` repeat over
    `Sequencia.acordesPaleta`, each group rendering `df-hex` with
    `acorde="{{acordeon.acorde}}"`, `acorde-color="{{acordeon.cor}}"`,
    `small="true"`, `acorde-checked="Sequencia.temAcordeSelecionado(acordeon.acorde)"`,
    `title="Adicionar {{acordeon.acorde}}"`, and
    `ng-click="Sequencia.adicionarAcorde(acordeon.acorde)"`;
  - a `{{Sequencia.novaSequencia.acordes.length}}/32` counter.
- [ ] Update the submit button to
  `ng-disabled="Sequencia.salvando || !Sequencia.podeSalvar()"`.
- [ ] Keep the existing `erroCadastro` paragraph and the form `ng-submit`.
- [ ] In `static/assets/css/app.css`, add spacing for the palette and selected
  row using the existing float/clearfix pattern:
  - `.acordes-selecionados { width: 300px; max-width: 100%; min-height: 36px; margin: 0 auto 8px; clear: both; }`
  - `.acordes-paleta { margin-bottom: 2px; }`
  - `.acordes-paleta .acorde-wrapper { margin-right: 2px; }`
- [ ] Keep the palette grouped by root exactly like `#/poracordes`; use
  `small="true"` so the buttons are 30px instead of 50px.
- [ ] Close each floated block with `<br style="clear: both;">`, matching the
  existing catalog/palette pattern, so the next section does not overlap.
- **Checkpoint 5:** the registration section shows the hex palette, the
  selected sequence in order, individual removal, the name field, the counter
  and the save button; the old text inputs and `+ acorde` button are gone.

### Step 6 — Final verification

- [ ] Run the backend suite from the repository root:
  `.venv/bin/python -m unittest discover -s tests -v` → expect 45 tests, `OK`.
- [ ] Run `git diff --check` and confirm only the intended static files
  changed.
- [ ] Run the manual matrix below against
  `http://localhost:5000/#/porsequencia` and `http://localhost:5000/#/poracordes`.
- **Checkpoint 6:** all acceptance criteria pass and no existing search,
  pagination, genre-filter or registration behavior regressed.

## Files affected

| File | Change |
|---|---|
| `static/assets/js/controllers/sequencia.js` | Add local `ACORDES_PALETA`, ordered add/remove state, 32-chord guard, save guard, form reset. |
| `static/templates/sequencia.html` | Catalog header above chords; name class; visual registration palette and selected sequence; remove text inputs. |
| `static/assets/css/app.css` | `.sequencia-item`, `.sequencia-meta`, `.sequencia-nome`, `.acordes-selecionados`, `.acordes-paleta` spacing. |
| `static/assets/js/controllers/acordes.js` | No change; the palette is copied into `sequencia.js`. |
| `static/assets/js/app.js` | No change. |
| `main.py`, `catalogo.py`, `matching.py` | No change. |
| `tests/` | No change; existing suite is the regression gate. |
| `Dockerfile`, `README.md`, `requirements.txt` | No change. |
| `data/top/*.csv`, `GENEROS` | No change. |

## Testing and verification

### Automated

```sh
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```

The suite must still report 45 tests and `OK`. There is no frontend test
harness in this repository, so the UI is verified in the browser served by
Flask; do not add `npm`/`pytest` commands.

### Manual matrix

| Check | How |
|---|---|
| Tag before chords | Open `#/porsequencia`; every tag is above its chord row and does not overlap or shift the hexes. |
| Row alignment | All sequence rows start at the same left edge; resize the window and re-check. |
| Name contrast | Names are white on `#BA007C`; computed ratio 6.22:1; visually readable. |
| Ordered selection | Click C, G, Am, F; the built sequence shows exactly that order. |
| Repeated chords | Add C twice; both appear and remain in click order. |
| Individual removal | Click the first C in the built sequence; only that occurrence disappears and the rest keep their order. |
| Limit | Add 32 chords; further palette clicks do nothing; counter shows `32/32`. |
| Save | Enter a name, save; the new card appears with the `nova` tag and can be searched. |
| 400/409 | Register a duplicate to see 409; send an invalid payload with `curl`/devtools to see the 400 message. |
| Existing features | Catalog click search, genre filter, previous/next pagination and the six original sequences still work. |
| First screen | `#/poracordes` still shows the same 36 chords, colors and grouping. |

## Risks and mitigation

| Risk | Detection | Mitigation |
|---|---|---|
| Palette copy drifts from the first screen | A chord/color differs between `#/poracordes` and the registration palette | Copy the seven groups verbatim from `acordes.js:2-44`; checkpoint 2 compares both screens. |
| Float/negative-margin layout causes overlap | Selected row or palette overlaps the next section | Reuse the existing `.acordes-container` + `small` pattern; add clearfix blocks; verify at 100% and narrow widths. |
| Duplicate chords are collapsed by Angular | Repeated C disappears from the built sequence | `track by $index` and removal by index; test the repeated-chord case. |
| Palette click removes instead of adds | Order changes unexpectedly | Palette handler only appends; removal is only on selected chips; helper text states both actions. |
| Save posts invalid data | 400 response or disabled button confusion | `podeSalvar()` mirrors the server rules (trimmed name, 1–32 chords); keep server validation and messages. |
| Tag still interferes with the first hex | First hex shifts or row wraps differently | Put tag/name in a block above the `.acordes-container`; use the same 300px centered width; do not put the tag inside the float flow. |
| Name contrast regresses | Name looks muted again | Remove `text-muted`; use `.sequencia-nome { color: #fff; }`; verify the computed ratio. |

## Definition of done

- [ ] `original` / `nova` tags render before the chord rows and are visually
  separated from the hexes.
- [ ] No tag causes a hex alignment break; all catalog rows align.
- [ ] Sequence names are high-contrast and readable on the pink panel.
- [ ] Registration uses small hexagonal chord buttons from the first screen's
  catalog.
- [ ] Selected chords are stored and displayed in exact click order, including
  repetitions.
- [ ] Selected chords can be removed individually.
- [ ] The name field and save action still work; 400/409 messages still appear.
- [ ] Existing catalog search, genre filter, pagination and the six original
  sequences still work.
- [ ] `#/poracordes` is visually unchanged.
- [ ] Backend suite is green (`45 tests`, `OK`) and `git diff --check` is clean.

## Out of scope

- Backend/API, SQLite catalog, matching rules and test fixtures.
- Docker/deploy changes, new dependencies or a build step.
- Drag-and-drop reordering, editing/deleting saved sequences, or free-text
  chord entry.
- Refactoring the first screen or extracting a shared chord constant.
- Observability, rollout and security: this is a local-only static UI change
  with no new runtime surface, so no new sections are needed.
