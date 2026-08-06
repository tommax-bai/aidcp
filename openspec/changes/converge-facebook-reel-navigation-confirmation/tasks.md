## 1. aidcp-edge — 收敛确认判据

- [ ] 1.1 在 `native/page-engine/src/facebook/reels.rs` 的 `canonical_facebook_reel_card_matches` 中，删除 `list_state == Ready`、`cards.len() == 1`、`current.ok`、`card.is_video == Some(true)`、`note_id_kind` 允许表这五项判断，保留「输出是卡片批次」与「list_kind == Reels」
- [ ] 1.2 把 `&cards.cards[0]` 换成 checked 取值（`first()`），取不到即返回 false（不确认），确认删除 1.1 的计数判断后不会越界 panic
- [ ] 1.3 删除 `current_id != card_id` 相等判断；保留「卡片侧与探针侧身份各自都能解析成 canonical reel id」这一前提，movement 比对继续用探针侧身份
- [ ] 1.4 就地补一条注释，写明两侧身份同源（`feedCards()` 在 Reels 面上调 `safeActiveReel()` 取单节点，见 `facebook-router/20-feed.js:122-124`），因此相等判断不构成交叉验证——防止后来者按「多一道校验更安全」原样加回

## 2. aidcp-edge — 超时路径带回已观测身份

- [ ] 2.1 给 `facebook/shared.rs` 的 `facebook_scroll_failure` / `facebook_scroll_failure_on_surface` 增加可选的 canonical 身份入参，填入 `ActionReceipt.note_id`；不新增协议字段、不改消息类型
- [ ] 2.2 在 `execute_facebook_reel_navigation` 超时分支复用已经算出的 `canonical_reel_id(current.note_id)`：解析得到即回 `reels_navigation_unconfirmed` 并携带该身份，解析不到即回 `reels_identity_unresolved` 且不带身份
- [ ] 2.3 核对该 helper 的其余调用点（`reels_target_unavailable` / `reels_entry_unconfirmed` / `reels_navigation_cancelled` 等）行为不变——无身份可带者显式传空，不得因新增入参而误填
- [ ] 2.4 确认携带身份不产生卡片、不触发 view 记账（spec 的 no-card 规则不变）

## 3. aidcp-edge — 测试

- [ ] 3.1 单测：探针身份相对前态发生变化时，即使 list_state 非 ready、卡片计数非 1、probe ok 为假、is_video 为假、note_id_kind 非 Permalink，仍判确认
- [ ] 3.2 单测：卡片侧与探针侧身份解析为不同 canonical Reel（模拟一次 CDP 往返间的推进）且探针身份 ≠ 前态时，判确认，不因两者不等而拒绝
- [ ] 3.3 单测：卡片批次为空时判不确认且不 panic
- [ ] 3.4 单测：卡片侧身份无法解析成 canonical reel id 时仍判不确认（保住下游点赞可定位）
- [ ] 3.5 单测：超时且身份可解析 → `reels_navigation_unconfirmed` 且回执带该身份；超时且身份不可解析 → `reels_identity_unresolved` 且回执不带身份
- [ ] 3.6 更新 `native/page-engine/tests/fake_cdp.rs` 中既有的 `reels_navigation_unconfirmed` 断言（1366 / 1419 附近），使其同时断言回执携带的身份

## 4. 验证与集成

- [ ] 4.1 `cd ../aidcp-edge && cargo test`（native page-engine）全绿；cargo 路径见 memory `native-engine-cargo-path`（不在 PATH，需指 rustup toolchain bin）
- [ ] 4.2 `npm run typecheck` 与 `npm test` 全绿；协议/风控/发布相关红线用例（`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`）必须通过
- [ ] 4.3 变异验证：把 1.3 删掉的相等判断临时加回，确认 3.2 转红——证明该用例抓的是这条判据本身，而非顺带通过
- [ ] 4.4 提交并推送到 `aidcp-edge` master（worktree 开发、`scripts/land-change` 集成），tasks.md 回写 commit sha
- [ ] 4.5 登记真机验收项到 `docs/real-machine-acceptance-backlog.md`：本改动的确认率变化只能在真实 Facebook Reels 面上观测（本机今日基线 688 confirmed / 501 ambiguous）
- [ ] 4.6 记录后续层次未做：云端收到 unconfirmed 后的无上限重发与会话动作数到顶自动续场造成的空转，本 change 明确不动
