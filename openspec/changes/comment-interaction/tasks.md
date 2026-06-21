# Tasks — comment-interaction

> 进度按 sub-repo 分节回写本仓。实装后用 HTML 注释标 `[x]` 并记 `<!-- <repo> <commit-sha> 备注 -->`。
> 排期：cloud 部分排在 `follow-already-followed-truthful-report` 与 `interaction-appraiser-like-rebalance` 归档之后再动（同改调度区域）。

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
- [ ] 1.9 「等评论审批」按-edge 暂停的进入/退出（复用 captcha pause 通道）；看门狗按"有意暂停"处理、`session.end` 仍可达 <!-- 延后 stage-3：当前 gate 有短超时兜底；ws-server pause 集成（防审批等待期 idle nudge）待接 -->
- [x] 1.10 `src/comm/handler.ts`：`interaction.occurred` 过滤与事件类型加 `comment`（真回执 `ok:true` 才计数 → `RiskController.record('comment')`） <!-- aidcp-cloud fc9e1f5 -->

## 2. aidcp-cloud — 每账号每日上限配置 + 面板 API + 审批接线（stage-3）

> CommentAppraiser 已留 `getDailyRemaining?` 注入缝、ApprovalGate 已留 `commentApproval?` 注入缝；本节为 server 侧接线。

- [ ] 2.1 每账号每日评论上限配置存储（PG 按 accountId，幂等 DDL）；读写访问
- [ ] 2.2 面板 `/api` 读写端点（console 用）；server 把 `getCommentDailyRemaining` 接到「配置上限 − 今日已评（风控计数）」喂 `CommentAppraiser`
- [ ] 2.3 server 把 `commentApproval` 接到飞书发卡 + `isPublishApproved`（评论专属 requestId 命名空间，路径契约不漂移）

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

- [ ] 5.1 每账号每日评论上限读写 UI（一个写操作 + 只读回显，经面板 `/api`）

## 6. 验收与回归

- [ ] 6.1 cloud 单测：四角色脱 LLM / 脱风控可单测；评论支线终结都汇到"是否进主页评估"且只一次；失败/超时/拒绝不死锁
- [ ] 6.2 协议红线：`AC-PROTO-*`（计数 55、两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权/超时不发评论）、`AC-RISK-*`（被拒诚实跳过、计数挂真回执、终态单写）
- [ ] 6.3 边缘：`executeComment` 后置校验如实回报（jsdom 桩 + 真机 smoke）；绝不静默假成功
- [ ] 6.4 已关注作者验收：主页被 `skip-profile-visit-if-followed` 跳过时评论仍正常、仍走"是否进主页评估"出口
- [ ] 6.5 `npm run test:acceptance` → `npm test` → `npm run typecheck`（edge + cloud 各自）；`openspec validate comment-interaction --strict`
