# Tasks — facebook-nickname-capture-timing

## 1. aidcp-cloud — 放开采集准入闸到 Facebook

- [x] 1.1 `src/orchestrator/role-dispatcher.ts`：`NicknameEnricher` 的 `isCaptureEligible` 从「仅 `xiaohongshu`」放宽到「`xiaohongshu` + `facebook`」（未知平台仍放行的 fail-open 语义保持）。<!-- cloud 1cd809d -->
- [x] 1.2 cloud 测试：`NicknameEnricher` 增 Facebook 用例——FB 连接在首批 `page.cards{startupId}` 武装采集、emit `self.profile.capture`；收到本人 `profile.detail{authorId===accountId, nickname}` 后差异写库、同代号只采一次、采空进有界重试。<!-- cloud 1cd809d test/integration/role-dispatcher.test.ts -->
- [x] 1.3 `npm run test:acceptance`(54) → `npm test`(2208 pass/3 skip) → `npm run typecheck` 全绿（land-change 内 rebase 后复跑）。<!-- cloud 1cd809d -->

## 2. aidcp-edge — FB 本人采集改就地读（不导航）

- [x] 2.1 `src/facebook/facebook-session.ts`：`openDirectProfile`（`profile.open{direct}` 自采）改为 `readFacebookIdentity(cdp)` **就地读**，按就地读结果上报 `profile.detail`（ok+昵称 / ok+空 / 失败三态如 design 所述），**移除 `Page.navigate` 到 `profile.php`**；删死代码 `waitAndReadProfile`/`readProfileSnapshot`/`FacebookProfileSnapshot`。<!-- edge 9430479 -->
- [x] 2.2 edge 测试：`profile.open{direct}` 就地读用例——断言**不发起任何 `Page.navigate`**、按就地读的 id+昵称上报 `profile.detail`；就地读空时上报空昵称（不写垃圾、不导航）；旧「导航读主页」断言改就地契约。<!-- edge 9430479 test/facebook/facebook-session-inline.test.ts + facebook-session.test.ts -->
- [x] 2.3 `npm run test:acceptance`(20) → `npm test`(1366 pass) → `npm run typecheck` 全绿（含既有 FB / identity 回归；land-change 内复跑）。<!-- edge 9430479 -->

## 3. aidcp（控制仓）— spec / 校验 / 部署 / 归档

- [x] 3.1 spec deltas：`account-identity-resolution`（MODIFIED 时机放宽 XHS+FB）、`facebook-identity`（ADDED FB 就地自采）。<!-- aidcp <sha> -->
- [x] 3.2 `openspec validate facebook-nickname-capture-timing --strict` 通过。<!-- aidcp <sha> -->
- [x] 3.3 部署 cloud 到 dev（安全序列：备份 `cloud.bak.20260715-1935.tar.gz` → rsync src/（clean git-archive 快照、no --delete）→ restart → healthcheck：active + 8787 + 飞书长连接已建立 + PG select 1）；edge canonical checkout 有用户在改的未提交内容、land-change 已跳过同步，edge-only 由用户 ff+rebuild 后生效。<!-- 2026-07-15 deployed dev (cloud only; edge edge-only) -->
- [x] 3.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 42（FB 导入号 / 换语言号 / 走过等登录门的号，启动后昵称随首批 feed 自动写库；就地读不导航）。<!-- aidcp <sha> -->
- [ ] 3.5 全部完成 → archive。<!-- aidcp <sha> -->
