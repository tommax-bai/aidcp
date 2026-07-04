# Tasks — fix-interaction-and-comment-capture

限流/节奏闸（冷却、软暂停、点赞比例闸）为设计，**不动**。
子仓改动在隔离 worktree 开发（`../aidcp-{edge,cloud}.wt/fix-interaction-and-comment-capture`），控制仓 change 目录留主 checkout（§7）。

## 1. aidcp-edge — 点赞/收藏定位加固（毛病 A）

- [x] 1.1 `executeLikeOrCollect` 定位互动栏前 `await this.waitForEngageBar()`（复用现有有界等待，超时不抛、仍走诚实 `no-bar`）。 <!-- edge 46a204e -->
- [x] 1.2 定位 JS 与后置校验 JS 的互动栏选择器加 `.engage-bar` 兜底：用 `querySelector('.interactions.engage-bar') || querySelector('.engage-bar')`（对齐 `executeComment` / `note-extractor`，保留「先严格类后裸类」偏好，采纳审查 #9）。 <!-- edge 46a204e -->
- [~] 1.3 edge 单测：字符串桩 CDP 无法真验 DOM 选择器匹配变体 → 转真机 backlog 7.1；不为此塞无效用例（呼应「测试别加太多」）。

## 2. aidcp-edge — 现场评论采集保真（毛病 B）

- [x] 2.1 `scrollNoteComments` 滚动循环中逐屏 `harvestCommentCandidates`、按 `anchorId` 去重累计（HARVEST_CAP=40，不再只取终态一屏）。 <!-- edge 46a204e -->
- [x] 2.2 末屏渲染门：仅当真滚动过（moved>0）才 settle 再抓一次；no_target/no_scroll 不白等一拍（采纳审查 #7）。 <!-- edge 46a204e -->
- [x] 2.3 `no_target` / `no_scroll` 分支返回前带回累计候选；ok/reason 保持诚实。 <!-- edge 46a204e -->
- [x] 2.4 edge 单测：no_scroll / no_target 仍带回可见候选；成功路径经 harvest 回流候选（browse-session.test.ts 新增 3 例）。 <!-- edge 46a204e -->

## 3. aidcp-cloud — 点赞/收藏失败可重试（毛病 A）

- [x] 3.1 `action.completed`：like/collect 可重试失败（`state_unchanged`/`btn_no-bar`/`btn_no-btn`）从 `interactionRetry` 回捞 noteId 原地重发一次（每 note+action 上限 1）。 <!-- cloud 82941b9 -->
- [x] 3.2 `blocked_by_captcha`/`already_*`/`no_like_btn` 不重试（诚实终止）。 <!-- cloud 82941b9 -->
- [x] 3.3 like/collect 加入 `noRecoverScroll`（失败不再兜底滚动把详情页滚走）；重发被软暂停/去重丢弃则不烧重试名额（采纳审查 #3）；会话结束/重启清 `interactionRetry`+`pendingInteractionKeys`（采纳审查 #5）。 <!-- cloud 82941b9 -->
- [x] 3.4 cloud 单测：可重试失败触发一次重发且不超上限；不可重试不重发；均不发兜底滚动（interaction-retry-and-budget.test.ts）。 <!-- cloud 82941b9 -->

## 4. aidcp-cloud — 预算按真成功扣（毛病 A 红线）

- [x] 4.1 移除下发处乐观 `consumeBudget`；改在 `action.completed{ok:true}` 的 like/collect 分支扣（对齐 follow/comment）。 <!-- cloud 82941b9 -->
- [x] 4.2 cloud 单测：下发不扣、ok:true 扣一次、ok:false 不扣、重试成功只扣一次。 <!-- cloud 82941b9 -->

## 5. aidcp-cloud — 采评论失败与真无评论分开（毛病 B）

- [x] 5.1 `edge-steps.readNote`：`note.scroll_comments` count 1→2；仅 `no_target`（找不到评论容器）时 warn，`no_scroll`（短评论区多为真少/无）不误告警（采纳审查 #10）。 <!-- cloud 82941b9 -->
- [x] 5.2 cloud 单测：ok:false 但带回候选 → comments 仍填充（edge-steps.test.ts 新增 1 例）。 <!-- cloud 82941b9 -->

## 6. 回归与红线

- [x] 6.1 edge：`typecheck` + `test:acceptance`（11）+ `test`（60）全过。 <!-- edge 46a204e -->
- [x] 6.2 cloud：`typecheck` + `test:acceptance`（36）+ `test`（1176）全过（AC-RISK-* / budget 不漂移）。 <!-- cloud 82941b9 -->
- [x] 6.3 对抗性 diff 审查：12 条全 low/nit，无 blocker/high；采纳 #3/#5/#7/#9/#10，其余记录为既有模式/今日不可达/可接受。

## 7. 真机验收 backlog（登记，不在本地阻塞）

- [x] 7.1 登记：`.engage-bar`-only 布局变体核验 → `docs/real-machine-acceptance-backlog.md` 簇 4。
- [x] 7.2 登记：评论行 `[id^="comment-"]` 与可滚容器种子选择器真机校准 → 同上。
- [x] 7.3 登记：线上抓 `skip reason=cooldown` / `recover_after_*_failed` / `no_target` vs candidates 分布 / `btn_no-bar` vs `state_unchanged` → 同上。

## 8. 收口

- [x] 8.1 `openspec validate fix-interaction-and-comment-capture --strict`（valid）。
- [x] 8.2 land（worktree→ff）+ push：edge `46a204e` / cloud `82941b9` 均在 origin master、本仓 `c0f698d` 在 origin main。cloud 部署：并发方 console-cloud-panel-hardening 部署整仓 master（`565d8d4`，含本 change）于 2026-07-04 09:06 上线；已核我六处改动逐字在线 + 服务 active + 飞书长连 + 8787 + PG`select 1` + isales 未碰。 <!-- cloud 82941b9 2026-07-04 deployed (随 565d8d4 整仓 master 部署) -->
- [x] 8.3 archive。
