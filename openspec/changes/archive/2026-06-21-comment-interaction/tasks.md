# Tasks — comment-interaction

> 进度按 sub-repo 分节回写本仓。实装后用 HTML 注释标 `[x]` 并记 `<!-- <repo> <commit-sha> 备注 -->`。
> 排期：cloud 部分排在 `follow-already-followed-truthful-report` 与 `interaction-appraiser-like-rebalance` 归档之后再动（同改调度区域）。
>
> **✅ 已上线（2026-06-21 deployed）**：ECS `aidcp-cloud` 现役代码已含全功能（master 09e39c1，另会话已部署），
> 本次仅置 `AIDCP_COMMENT_APPROVAL=true` + `systemctl restart aidcp-cloud`，healthcheck 全过
> （active / 8787 listening / 飞书长连接已建立 / 0 fatal）；isales 四服务未碰。备份：`/opt/aidcp/cloud/.env.bak.20260621-102946` +
> `/opt/aidcp/cloud.bak.20260621-102946.tar.gz`。回滚 = 恢复 .env 备份 + 重启。
> **现役行为**：高热度高价值笔记被点赞/收藏后 → 精品评估 → 撰写 → 去AI味 → **飞书审批卡**（人点同意才发，90s 超时）→ 执行端发评论+后置校验 → 进主页评估。
> 每账号每日上限 = 风控档位（3/8/15）。关掉 = `.env` 删该行 / 置 false + 重启。

## 0. 先决调研（执行端探针）

- [x] 真机 CDP 探针坐实评论框 / 提交控件 / 发布后校验信号 <!-- aidcp-edge d377691 scripts/comment-probe.ts，只读默认+受闸真发，已在真笔记验证 ownRow+cleared 信号 -->

## 1. aidcp-cloud — 评论支线接线与角色

> **stage-2 已落地** <!-- aidcp-cloud fc9e1f5：四角色 + 事件族 + 调度接线 + AuthorEvaluator 改挂 + 风控计数；cloud 293 全绿（含 11 条 lane 单测）、typecheck 净、零回归。lane 默认 dormant-safe：审批未接线时一律诚实跳过、绝不裸发。 -->

- [x] 1.1 新增 `comment.*` 事件族（`src/event-bus/types.ts`）：`comment.appraised` / `comment.composed` / `comment.cleared` / `comment.approved` / `comment.done` / `comment.skipped` <!-- aidcp-cloud fc9e1f5（held 并入 skipped 语义，未单列） -->
- [x] 1.2 `CommentAppraiser`：消费 `interaction.completed`；精品门槛 + 会话评论预算 + 可选每日上限闸（评估阶段就拦，过不了不付撰写成本） <!-- aidcp-cloud fc9e1f5 -->
- [x] 1.3 `CommentComposer`：消费 `comment.appraised`，LLM 产文本；空/超长拦截 + 剥裸 `@`；emit `comment.composed` / `comment.skipped` <!-- aidcp-cloud fc9e1f5（跨笔记去重待 stage-3 接持久层） -->
- [x] 1.4 `CommentDeAiFlavor`：消费 `comment.composed`，复用 `PostProcessor.process`（确定性、脱 LLM 可跑、不抛）；emit `comment.cleared` / `comment.skipped` <!-- aidcp-cloud fc9e1f5 -->
- [x] 1.5 `CommentApprovalGate`：消费 `comment.cleared`；循环内人审端口（发卡 + 轮询 /tmp 授权 + 短超时）；授权 emit `comment.approved`，超时/拒绝/**未接线** emit `comment.skipped`（绝不裸发，AC-PUB） <!-- aidcp-cloud fc9e1f5；审批端口经 RoleDispatcherOptions.commentApproval 注入，server 接线属 stage-3 -->
- [x] 1.6 `RoleDispatcher`：注册四角色；`comment.approved → comment` 命令翻译（`canInteract('comment')` 闸 → `sendCommand` → 真回执 `consumeBudget`） <!-- aidcp-cloud fc9e1f5 -->
- [x] 1.7 `RoleDispatcher`：`freshBudget()` 加 `comments:2`、`consumeBudget` 加 `comment`、`canInteract` 并集加 `comment` <!-- aidcp-cloud fc9e1f5 -->
- [x] 1.8 `RoleDispatcher`：**`AuthorEvaluator` 改挂** `comment.done` / `comment.skipped`，每篇只触发一次"是否进主页评估" <!-- aidcp-cloud fc9e1f5；含 pendingComment 桥 action.completed{comment}→comment.done -->
- [x] 1.9 ~~「等评论审批」按-edge 暂停~~ → **设计上免做**：审批超时 90s < idle 看门狗 `idleNudgeMs`(130s)，等待期不会触发 idle nudge；AuthorEvaluator 等 `comment.done`/`comment.skipped` 时浏览闭环自然挂起，故 v1 无需显式暂停态 <!-- aidcp-cloud 1b5610b：timeoutMs:90_000 -->

- [x] 1.10 `src/comm/handler.ts`：`interaction.occurred` 过滤与事件类型加 `comment`（真回执 `ok:true` 才计数 → `RiskController.record('comment')`） <!-- aidcp-cloud fc9e1f5 -->

## 2. aidcp-cloud — 每账号每日上限配置 + 面板 API + 审批接线（stage-3）

> **设计收口**：每账号每日评论上限**复用既有风控配额**（`DAILY_QUOTAS` comment：保守 3 / 正常 8 / 激进 15），
> 运营经既有 `setQuotaLevel` 面板写路由（task 8.x）按账号配档位即可——**无需另起配置表/端点**。
> 故 §2.1/§2.2 由既有基础设施满足，本 change 仅补「评估阶段预闸」与「审批接线」。

- [x] 2.1 ~~另起每账号每日上限配置存储~~ → **复用既有按账号风控配额 + `setQuotaLevel`**（保守/正常/激进 = 3/8/15 条/天） <!-- 设计收口：不另起表/UI，运营经既有面板风控档位路由按账号配 -->
- [x] 2.2 评估阶段预闸：`RiskController.dailyRemaining('comment')` + server 接 `getCommentDailyRemaining`，`CommentAppraiser` 据此在最便宜阶段拦超额（dispatch 前 `canDo('comment')` 仍为权威闸） <!-- aidcp-cloud 09e39c1（dailyRemaining + getCommentDailyRemaining + 单测，被并发会话 git add -A 卷入该提交，已在 origin/master）；cloud 295 全绿 -->
- [x] ~~§5 console 后台界面~~ → **复用既有风控档位配置**：评论量 = 账号风控档位，console 面板 V1 已有按账号风控写入；无需新评论专属界面 <!-- 设计收口 -->
- [x] 2.3 server 把 `commentApproval` 接到飞书发卡 + `isPublishApproved`（评论专属 requestId `comment-<noteId>-<ts>`，路径契约不漂移） <!-- aidcp-cloud 1b5610b：comment-approval-card.ts 同形复用 AC-PUB 接收端（零改共享代码）；env 闸 AIDCP_COMMENT_APPROVAL=true 才注入、默认 dormant；card↔receiver 复用单测 -->

## 3. 协议（edge + cloud 三处同步）

- [x] 3.1 两份 `src/comm/protocol.ts` 逐字一致新增 `interaction.comment` + `CommentPayload{noteId,text,thinkMs?}` <!-- aidcp-edge / aidcp-cloud：MessageType + InteractionCommentPayload + PayloadMap 三处同步 -->
- [x] 3.2 `aidcp-cloud/src/comm/command-bridge.ts` 加 `comment → interaction.comment` 映射；`EdgeCommand.action` 并集加 `comment` <!-- aidcp-cloud -->
- [x] 3.3 两份 `test/acceptance/protocol-contract.test.ts` 的 `ALL_MESSAGE_TYPES` + 计数断言 54→55 <!-- AC-PROTO 全过（edge 5/5、cloud 5/5） -->
- [x] 3.4 `docs/protocol.md` 头部计数 + §2 表同步 <!-- 计数 55 + 表行 + payload 示例 + command-bridge 映射 -->

## 4. aidcp-edge — 执行端发评论动作

- [x] 4.1 `src/browse/browse-session.ts` 新增 `interaction.comment` 命令分支 + `executeComment()`：激活折叠入口 → 点编辑器本体落 caret → `dispatchKeystrokes` 拟人输入 → `captchaPresentFresh` 自检 → 点 `button.btn.submit` <!-- aidcp-edge -->
- [x] 4.2 后置校验（探针坐实）：编辑器清空 且 自己的评论作为顶部新 `[id^="comment-"]` 行出现 → `reportActionCompleted{ok:true}`；否则 `no_target` / `state_unchanged` / `blocked_by_captcha`，绝不假成功 <!-- aidcp-edge -->
- [x] 4.3 复用 `dispatchKeystrokes` / `captchaPresentFresh` / `reportActionCompleted` / `dispatchClick`，不破坏接口 <!-- 偏离说明：浏览侧互动（like/collect/follow）本就用直接 inline-JS 定位+后置校验、不走 LocatingEngine 三道闸；executeComment 对齐 executeLikeOrCollect 的同一形态，而非 publish 的 LocatingEngine 路径 -->
- [x] 4.4 executeComment 单测：ok / no_target / state_unchanged 三例（不静默假成功） <!-- aidcp-edge test/browse/browse-session.test.ts；全量 edge 280→283 全绿 -->

> **本阶段（协议 + 执行端）已落地、edge+cloud 全量测试与 typecheck 全绿、零回归。**
> <!-- aidcp-edge 3722e45（协议+executeComment+单测，edge 283 全绿）；aidcp-cloud 10bbc70（协议镜像+command-bridge+EdgeCommand 并集，cloud 281 全绿） -->
> 下面 §1/§2/§5（云端四角色 + 每日上限配置 + console UI）为行为层，排在 `follow-already-followed-truthful-report` 与 `interaction-appraiser-like-rebalance` 归档后再动（同改调度回执记账区域）。

## 5. aidcp-console — 后台配置 UI

- [x] 5.1 ~~评论专属每日上限读写 UI~~ → **复用既有风控档位 UI**：评论量按账号 = 风控档位（3/8/15 条/天），console 面板 V1 已有按账号风控档位写入；v1 无需新评论界面 <!-- 设计收口；若日后要评论独立于 like/collect 的细粒度数值，再起独立 change -->

## 6. 验收与回归

> ⚠️ **2026-06-21 显式归档时本块整块未跑**（用户决定先归档、验证后补）。含安全红线 `AC-PUB-*`/`AC-RISK-*`/`AC-PROTO-*`，**视为未经安全验证**，上真机/扩量前务必补齐。债务台账见 `docs/deferred-verification-2026-06-21.md`。

- [ ] 6.1 cloud 单测：四角色脱 LLM / 脱风控可单测；评论支线终结都汇到"是否进主页评估"且只一次；失败/超时/拒绝不死锁 <!-- DEFERRED 2026-06-21 归档时未跑 -->
- [ ] 6.2 协议红线：`AC-PROTO-*`（计数 55、两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权/超时不发评论）、`AC-RISK-*`（被拒诚实跳过、计数挂真回执、终态单写） <!-- DEFERRED 2026-06-21 归档时未跑 -->
- [ ] 6.3 边缘：`executeComment` 后置校验如实回报（jsdom 桩 + 真机 smoke）；绝不静默假成功 <!-- DEFERRED 2026-06-21 归档时未跑 -->
- [ ] 6.4 已关注作者验收：主页被 `skip-profile-visit-if-followed` 跳过时评论仍正常、仍走"是否进主页评估"出口 <!-- DEFERRED 2026-06-21 归档时未跑 -->
- [ ] 6.5 `npm run test:acceptance` → `npm test` → `npm run typecheck`（edge + cloud 各自）；`openspec validate comment-interaction --strict` <!-- DEFERRED 2026-06-21 归档时未跑 -->
