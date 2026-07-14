## 0. Blocker

- [ ] 0.1 Confirm `humanize-interaction-prompts` is archived before authoring any MODIFIED delta against `comment-interaction` / `interaction-appraisal`; author threshold MODIFIED against post-humanize spec text (do not revert humanize).

## 1. aidcp-cloud — Vocabulary platform-ization (ADDED capability)

- [ ] 1.1 Extend `CommentPlatformProfile` (`src/platform/registry.ts`) with the site/content/metric nouns the browse-loop prompts need; keep it the single lexicon (already injected into `comment-search-term-generator.ts` / `comment-target-picker.ts`).
- [ ] 1.2 Remove hardcoded 「小红书 / 笔记 / 收藏」 from the 8 role prompts (`content-evaluator`, `content-curator-role`, `comment-reviewer`, `comment-appraiser`, `comment-like-appraiser`, `concept-extractor-role`, `follow-agent`, `comment-composer`), reading from the profile; MUST NOT open a second lexicon table.
- [ ] 1.3 Parameterize `hot-lead/heat-velocity.ts` published-time parsing per platform.
- [ ] 1.4 Make `deep-reader.ts` image-vs-text heuristic platform-aware so a Facebook image post with empty content is not misjudged as a long-text post.

## 2. aidcp-cloud — Comments into compose + merge FB composers

- [ ] 2.1 Add a comments field to `event-bus/types.ts` `NoteDetailData`; feed captured post comments into the browse-loop compose step.
- [ ] 2.2 Merge the two Facebook compose paths (browse-loop `comment-composer.ts` vs targeted `server.ts` `facebookCompose`) into a shared draft helper with platform-specific callers (preserve xhs `withApproval` / Facebook `withValidators` wrapping).

## 3. aidcp-cloud / aidcp-edge — Remove bare platform branches

- [ ] 3.1 Fold the 6 dispatcher `platform==='facebook'` bare branches and edge `main.ts:1069/1077/661-664` into the driver/registry interface.

## 4. Thresholds (post-humanize, MODIFIED)

- [ ] 4.1 Parameterize the quality-comment threshold per platform: collect-less platforms relax only the collect conjunct, the main like threshold is preserved, and it MUST NOT degrade to no threshold. Register the spec↔code drift (spec 1000/300 vs code 300/100/10000). Author the MODIFIED delta against post-humanize `comment-interaction` text.

## 5. contentTruncated + N6 (conditional, C2 P1)

- [ ] 5.1 If C2 probe P1 shows the See-more path needs an explicit truncation flag, land `note.detail.contentTruncated` together with its consumer guards (ContentCurator MUST NOT judge thin_content on short text; CuratedNoteEvaluator MUST NOT admit truncated text) under the same flag — field MUST NOT ship before its consumers.

## 6. Verification

- [ ] 6.1 Cloud unit tests: FB threshold no longer requires ten-thousand likes (a normal-heat post can enter comment appraisal) while a low-heat post is still blocked (no zero-threshold); prompts carry no 「小红书/收藏」; DeepReader image post not misjudged as long text; compose consumes comments[].
- [ ] 6.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`; AC-RISK green.
- [ ] 6.3 Rebase, integrate, push cloud to `master`, deploy dev; register cluster 69.

## 7. Change Record

- [ ] 7.1 Update this task record with commits and validation; `openspec validate platform-vocabulary-and-thresholds --strict`.
