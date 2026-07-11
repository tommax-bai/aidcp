## Why

Facebook comment publish-success is currently judged by a single check after a fixed reload wait: reload the page, wait ~5s, then run one scoped verify (own-identity + text fragment in the target post's comment area). On slow renders the comment is already live server-side but has not re-rendered in that one window, so the edge honestly reports `verification_ambiguous` (the "posted but shows unconfirmed" symptom). A real-machine probe (edge `scripts/fb-comment-verify-probe.ts`) captured the post-submit signal timeline and established the load-bearing facts:

- The just-posted comment renders **optimistically** ~68ms after Enter, carrying a **client-placeholder** comment id (`client:…`) and the author link, but **zero reaction/reply affordances**.
- The server write response arrives ~3.5s later; only then does the comment id **upgrade to a server-assigned id** and reaction/reply affordances appear.
- Therefore "a comment id is present" is NOT proof of server acceptance (it would over-confirm ~3.4s before the server even responds), but "a **server-assigned** comment id" or "reaction/reply affordances present" IS server-ack-gated.
- The same run showed a **misleading error overlay** ("no permission to add this comment / post may be deleted") while the comment actually succeeded, and the single-shot reload verify returning a **false negative** — a live reproduction of the unconfirmed-but-succeeded symptom.

## What Changes

- Replace the single-shot post-reload verification with a **server-ack-gated in-place confirmation** as the fast primary path, and a **bounded-poll reload** scoped verify as the authoritative fallback. No protocol, cloud, or console change; edge-only. The edge result contract (`ok` / `verification_ambiguous` / hard-failure reasons) and cloud dedup semantics are unchanged.
- Confirm success only on ack-gated signals on the own-identity + text-fragment comment node: a **server-assigned comment id** (not a client placeholder) OR **reaction/reply affordances present**. Never confirm on bare optimistic render, whole-page text match, or a client-placeholder comment id.
- Keep the existing identity guard: unknown own stable numeric id → do not submit (`identity_unknown`).
- Do not treat a post-submit error/permission overlay as definitive failure; verification signals remain authoritative (the observed overlay is misleading and can accompany a successful post).
- When neither the in-place watch nor the bounded reload can confirm, return `verification_ambiguous` as today (dedup still marks it, so no duplicate re-post).

## Capabilities

### New Capabilities

- `facebook-comment-verification`: Defines how Facebook comment publish-success is judged from ack-gated post-submit signals, the in-place-primary / bounded-reload-fallback structure, the never-over-confirm invariant, and honest ambiguous reporting.

## Impact

- Affected repos: `aidcp-edge` only.
- Edge areas: `src/facebook/comment-executor.ts` post-submit verification (`submitComment` and its scoped-verify helpers).
- Contract stability: no change to the edge→cloud result envelope, protocol messages, or cloud dedup/quota logic; a comment that today lands in `verification_ambiguous` on slow render will now more often confirm `ok`, and genuine failures still surface honestly.
- Rollout: edge-only, no ECS deploy; operator machines pick it up on the next edge build/pull. No new env flag required (behavioral hardening of existing verification).
- Real-machine acceptance: confirm on a controlled test post that (a) fast-path confirms within a few seconds without reload, (b) the client-placeholder id never confirms, (c) a genuinely rejected comment still reports honestly.
