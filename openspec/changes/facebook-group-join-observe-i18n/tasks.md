# Tasks — facebook-group-join-observe-i18n

## 1. aidcp-edge — multilingual Join-button observation

- [x] 1.1 Replace EN/ZH exact-match `ctaKind` with multilingual contains-match over shared keyword lists (join/joined/pending), joined+pending checked before join. Extract `classifyCtaLabel()` as the single source of truth; the observe IIFE interpolates the same lists. <!-- aidcp-edge 3000db2: src/facebook/join-executor.ts JOIN/MEMBER/PENDING_CTA_LABELS + classifyCtaLabel + anyIncludes in IIFE -->
- [x] 1.2 Harden header/text extraction: broaden heading selectors, fall back to `[role="main"]` text then `document.title`. <!-- aidcp-edge 3000db2 -->
- [x] 1.3 Preserve fail-closed: unrecognized label → no join classification, no fabricated click target; gate decision stays in the cloud. <!-- aidcp-edge 3000db2: classifyCtaLabel returns '' for unknown; joinButton only set for classified join -->

## 2. Tests + verification

- [x] 2.1 Unit tests for `classifyCtaLabel` (multilingual join; joined/pending precedence over join; empty/unknown → ''). <!-- aidcp-edge 3000db2: test/facebook/join-executor.test.ts, 3 new tests -->
- [x] 2.2 `npm test` (877) + `npm run typecheck` green in edge. <!-- aidcp-edge 3000db2 -->

## 3. Rollout

- [ ] 3.1 Land edge branch to `master`; land control change to `main`.
- [ ] 3.2 Edge is a local Electron client (no ECS service): operator pulls/rebuilds the local edge, then re-runs `/comment <昵称> --join` on a non-EN/ZH group and confirms it progresses past observation (join clicked + server-verified, or an honest gated/pending outcome — no longer a silent ambiguous_skip on a real Join button). Real-machine confirmation logged under `docs/real-machine-acceptance-backlog.md` 簇 32.

## 4. Closeout

- [ ] 4.1 `openspec validate facebook-group-join-observe-i18n --strict`.
- [ ] 4.2 Archive after edge rebuild + real-machine confirmation.
