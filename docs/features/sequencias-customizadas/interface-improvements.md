# Interface Improvements

## Task 1 — Adjust the positioning of sequence tags

On the screen for searching songs by chord sequence, there are sequences identified by the tags "original" and "new".

Currently, these tags appear next to the chords and, depending on their positioning, end up interfering with the visual organization of the hexagonal icons.

### Problem

- The tags may occupy the space intended for the chords.
- This can cause breaks in the alignment of the sequence icons.
- The visual presentation of the sequences becomes inconsistent.

### Expected Behavior

- Position the "original" or "new" tag before the first chord of the sequence.
- The tag should be visually separated from the icons.
- The chords should remain organized in sequence, without the tag interfering with their alignment.
- Preserve the format, colors, and visual style of the hexagonal icons.

## Task 2 — Improve the contrast of sequence names

On the same screen, each sequence has a name, such as "Test," displayed next to its respective tag.

### Problem

- The current text color has little contrast with the pink background.
- This makes it difficult to read the sequence names.

### Expected behavior

- Change the text color to a color that has greater contrast with the background.
- Ensure that the names are easily legible.
- Preserve the current visual identity of the application.
- Maintain a good visual hierarchy between the tag, the sequence name, and the chords.

## Task 3 — Redesign the sequence registration interface

At the bottom of the sequence search screen, there is a section called "Register sequence."

Currently, registration uses text fields to manually enter chords.

I want to replace this experience with a visual chord selection interface, inspired by the application's first screen, where known chords are presented as hexagonal buttons.

### Expected Behavior

- Present available chords as clickable buttons, using the existing hexagonal format in the application.
- Use smaller buttons than those presented on the first screen, so that the interface better adapts to the registration section.
- Allow the user to select chords by clicking on their respective buttons.
- Each click should add the chord to the sequence being built.
- The order of the chords should exactly match the order in which the user clicked.
- Visually display the sequence created by the user.
- Allow the removal of already selected chords, preferably individually, by also clicking above a selected chord.
- Allow the user to enter the sequence name.
- Maintain the functionality to register/save the sequence.

### Visual Reference

Use the screenshot docs/features/sequencias-customizadas/evidence/print-referencia.png as inspiration, which shows the chords in hexagonal buttons organized by category.

It is not necessary to reproduce that interface exactly. I want to reuse its visual language and adapt the size, spacing, and organization of the buttons for the registration section.

### Important Functional Requirement

The selection needs to be ordered. It is not enough to use a conventional multiple selection that stores the chords without guaranteeing the order of the clicks. The final sequence must preserve the order chosen by the user.

# Acceptance Criteria

I will consider the activity completed when:

- The "original" and "new" tags are positioned before the chords.
- The hexagonal icons do not suffer alignment breaks caused by the tags.
- The sequence names have adequate contrast with the background.
- The registration allows selecting chords using hexagonal buttons.
- The sequence respects the order of clicks.
- The user can remove selected chords.
- The user can enter a name and register the sequence.
- The previous search and registration functionalities continue to work.