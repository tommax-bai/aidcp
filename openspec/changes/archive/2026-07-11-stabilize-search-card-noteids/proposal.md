# Proposal: stabilize search result noteId capture

## Why

Targeted curated-note comments search by title and then require an exact target `noteId` match before opening/commenting. In live runs, the target card can be visually present immediately after the first search, while the reported `page.cards` snapshot still lacks the target `noteId` because the search result DOM has not fully hydrated links or because near-duplicate folding keeps an earlier duplicate without `noteId`.

That makes cloud treat the first search as a miss and trigger the existing bounded fallback search, even though the target was already visible.

## What Changes

- Edge search result card reporting waits briefly for card `noteId` hydration before reporting search results.
- Edge near-duplicate folding prefers a duplicate carrying `noteId` over an earlier duplicate without `noteId`.
- Edge card extraction also recognizes note links that wrap the card element, not only links inside the card element.
- The targeted comment bounded retry policy remains unchanged: at most two searches and exact `noteId` matching only.

## Impact

- Reduces unnecessary second searches in targeted comments when the first result page already contains the target card.
- Keeps honest fallback when the target `noteId` still cannot be observed.
- Edge-only runtime change; no protocol or cloud behavior change.
