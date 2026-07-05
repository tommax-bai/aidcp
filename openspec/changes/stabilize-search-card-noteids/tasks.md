## 1. Contract

- [x] 1.1 Specify that targeted search result reporting should not classify a visually present card as missing before a short `noteId` hydration window.

## 2. Implementation

- [x] 2.1 Edge: wait briefly for search-result cards to expose `noteId` before reporting `page.cards` after `search.execute`. <!-- aidcp-edge 5bcdd12 -->
- [x] 2.2 Edge: when folding near-duplicate cards, prefer the duplicate carrying `noteId`.
- [x] 2.3 Edge: extract `noteId` from an ancestor note link wrapping the card element.

## 3. Validation

- [x] 3.1 Run focused edge tests. <!-- npx tsx --test test/browse/browse-session.test.ts; npx tsx --test test/browse/feed-scroller.test.ts; npm run typecheck; npm run test:acceptance; npm test; npm run build:dist -->
- [x] 3.2 Run `openspec validate stabilize-search-card-noteids --strict`. <!-- valid -->
