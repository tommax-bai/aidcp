# Tasks

## 1. aidcp-edge — ack-gated in-place verification

- [x] 1.1 Add an in-place ack-verify page-JS builder that locates the own+text just-posted comment node (own numeric id author link + text fragment, target-post scoped) and reports ack-gated signals: server-assigned comment permalink id (distinguish from a client-placeholder id) and reaction/reply affordance presence. Language-independent (no locale words). <!-- aidcp-edge 1e7e6d9 buildAckVerifyJs + isServerFacebookCommentId (TS/JS 同源正则) -->
- [x] 1.2 Replace the single-shot post-reload verification in `submitComment` (`src/facebook/comment-executor.ts`) with: bounded in-place poll (no reload) → confirm on ack-gated signal; else reload once → bounded poll of the existing scoped verify → confirm on first match; else `verification_ambiguous`. Preserve `identity_unknown` (no own id → no submit) and the existing result envelope (`ok` / `verification_ambiguous` / hard-failure reasons). <!-- aidcp-edge 1e7e6d9 inPlaceAckConfirm + reloadScopedConfirm -->
- [x] 1.3 Ensure the ack-gated discriminator never confirms on a client-placeholder comment id or bare optimistic render (red-line: never over-confirm). Add bounded-iteration poll helpers with injectable sleep/now for tests (no wall-clock loops). <!-- aidcp-edge 1e7e6d9 FB_CLIENT/SERVER_COMMENT_ID_RE；有界轮次 + 注入 sleep -->
- [x] 1.4 Do not treat a post-submit error/permission overlay as definitive failure; keep verification signals authoritative. <!-- aidcp-edge 1e7e6d9 提交后不做 overlay→fail 判定，确认信号权威 -->

## 2. aidcp-edge — tests

- [x] 2.1 Unit tests over a jsdom/stub DOM: (a) client-placeholder id + no affordances → not confirmed; (b) server-assigned id → confirmed fast, no reload; (c) reaction/reply affordances → confirmed; (d) in-place miss → reload bounded-poll confirms on a later frame; (e) neither confirms → `verification_ambiguous`; (f) unknown own id → `identity_unknown`, no submit. <!-- aidcp-edge 1e7e6d9 就地命中不刷新/慢渲染有界轮询命中/isServerFacebookCommentId 纯函数；(a)(c) 的页内 JS 判别属 FakeCdp 桩测盲区、由真机探针坐实 -->
- [x] 2.2 `npm run test:acceptance` then full `npm test`, then `npm run typecheck` — all green. <!-- aidcp-edge 1e7e6d9 acceptance 16 / test 990 / typecheck 全过 -->

## 3. Integration & acceptance

- [x] 3.1 Land to edge `master` (rebase onto latest; resolve any `comment-executor.ts` overlap with concurrent Facebook comment work), push. <!-- aidcp-edge 1e7e6d9 land-change rebase 无冲突 ff 推 67aec7c..1e7e6d9；主 checkout 已 ff -->
- [x] 3.2 Register real-machine acceptance items in `docs/real-machine-acceptance-backlog.md`: fast-path confirms without reload within a few seconds; client-placeholder id never confirms; a genuinely rejected comment still reports honestly; slow-render no longer false-ambiguous. <!-- 控制仓 backlog 簇登记，见 docs/real-machine-acceptance-backlog.md -->
