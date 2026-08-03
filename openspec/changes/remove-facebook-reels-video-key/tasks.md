## 1. Edge Native Reels identity and navigation

- [x] 1.1 Remove `videoKey` from Facebook router probe/action shapes, Rust decoding, and session transition state in `aidcp-edge`
- [x] 1.2 Replace the Reels navigation ladder with one fresh axis-specific trusted key and one bounded canonical `noteId` post-observation
- [x] 1.3 Make Reel like and follow commit/verification freshly note-scoped without saved media or DOM identity
- [x] 1.4 Add focused router and Rust regressions for media/DOM churn, independent later scroll commands, and canonical-only interactions

<!-- Evidence: aidcp-edge commit e6cd4bc. Production-source audit found no videoKey/video_key or saved Reel DOM marker. -->

## 2. Cloud accounting and continuity

- [x] 2.1 Require a canonical Reel `noteId` before risk view accounting and feed that same presentation to cadence
- [x] 2.2 Continue confirmed Reels after Reels-specific terminal scroll receipts through normal admitted/paced scrolling
- [x] 2.3 Add focused handler and dispatcher regressions for anonymous presentations, shared view/cadence identity, and immediate continuation

<!-- Evidence: aidcp-cloud commit 622a1af. Anonymous/non-canonical Reel cards do not consume view risk or cadence opportunities. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Edge tests plus Native acceptance/full tests and typecheck required by the owning repository
- [x] 3.2 Run focused Cloud tests plus risk/protocol acceptance, full tests, and typecheck required by the owning repository
- [x] 3.3 Record repository commits and validation evidence, then run `openspec validate remove-facebook-reels-video-key --strict`
- [x] 3.4 Integrate and push clean default branches; deploy Cloud to DEV with documented preflight and runtime verification, without packaging Edge

<!-- Validation: Edge focused 134/134; npm test 3065 passed, 1 gated skip; npm run typecheck; npm run gate:native (fmt, clippy, full Rust tests). Cloud focused 34/34; npm test 4146 passed, 11 gated skips; npm run typecheck. OpenSpec strict validation passed. -->
<!-- Delivery: aidcp-edge master e6cd4bc, aidcp-cloud master 622a1af, and aidcp main 8878383a were fast-forward pushed. Cloud DEV deployed from clean master 622a1af after backup /opt/aidcp/cloud.bak.20260803-164701.tar.gz plus target-local .env backup. No package/lock or migration changed. Post-deploy evidence: source hashes matched, .deploy-sha=622a1af, service active with NRestarts=0, 8787/8090/5432 listening, panel health ok, all three owner databases answered SELECT 1, schema enforce passed for content/automation/api, automation writer lock held target=dev, and Feishu WSClient reached onReady. Edge was not packaged; OL was untouched; no real-account action was performed. -->
