# Tasks — comment-search-command（飞书 /comment：搜索驱动的按需评论任务）

> **依赖序**：协议增量(1) → 命令接入(2) → 评论任务编排(3) → 搜索词角色(4) → 边端原生筛选+收藏数(5) → 候选去重+甄选角色(6) → 撰写读现场评论(7) → 角色注册/目录(8) → 验收/红线(9) → 全量回归+validate(10) → 部署 cloud 先/edge 后(11) → 真机标定(12) → console 标签+归档(13)。
> **回写格式**：完成用 `[ ]`→`[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
> **前置**：复用既有 `comment-interaction`（撰写/去AI味/人审/发布动作/风控配额）、`concept-pool-search`（搜索下发/限频）、`curated_content`（精选集）、`risk_interactions`（每笔记去重）、发布任务接管/恢复范式。纯增量、无新表。

## 1. 协议增量（v2 四处同步——搜索排序/时间参数 + 结果卡片收藏数）

- [x] 1.1 cloud+edge 两份 `src/comm/protocol.ts` 逐字一致：`SearchExecutePayload` 加可选 `sort`（如 `most_collected`）与 `timeWindow`（如 `one_day`）；搜索结果卡片 payload 加 `collectCount`。验证：两份 `protocol-contract.test.ts` 的 `Record<MessageType,true>` 穷举与计数断言更新且 `npm run typecheck` 绿。 <!-- cloud aaa5500 / edge 28db43a：SearchExecutePayload +sort/timeWindow（两份逐字一致）。**collectCount 早已在 PageCardsPayload.cards 上**（非协议缺口，仅 edge reportVisibleCards 硬编码 0→改在 task 5.2）。只加可选字段、无新 MessageType→AC-PROTO 计数无需改；cloud+edge typecheck 净、AC-PROTO 两侧 5/5 -->
- [ ] 1.2 `aidcp-cloud/src/comm/command-bridge.ts` 搜索动作映射透传新参数；如新增 cloud→edge 主动命令则补 `aidcp-edge/src/client/edge-client.ts` 主动命令路由白名单（否则静默丢弃）。验证：`npm run test:acceptance` 的 `AC-PROTO-*` 全过。
- [ ] 1.3 `docs/protocol.md` 头部消息计数与 §2 表同步。验证：人工核对计数与新字段在表内。

## 2. aidcp-cloud — 飞书 /comment 命令接入

- [x] 2.1 `src/feishu/commands.ts`：`CommandAction` 加 `comment`；`parseCommand` 加 `/comment <昵称>` 分支；`CommandRouter.runComment` + `CommandActions.comment(nickname?)`；HELP 文案加一行。验证：单测——`/comment 测评酱` 解析为 `{action:'comment',nickname}`；未带昵称/无匹配走 honest 分支。 <!-- cloud 82c3155 /comment 与 /publish 同构；CommandActions.comment **可选**（server 接线 task 2.2 落、未接线时 runComment honest-fail「未接线」、不破 server typecheck）；两段式回执；+5 单测，feishu-commands 29/29 绿 -->
- [ ] 2.2 `src/server.ts`：接 `actions.comment`（仿 `actions.publish`）——`resolveAccountByNickname` 定位账号（0/多义 honest-fail 列昵称）→ `CommentScheduler.triggerManual(acct)`。两段式回执：同步回「已触发/失败原因」。验证：单测——无匹配回失败列昵称；边端离线回「边端离线」。

## 3. aidcp-cloud — 评论任务编排（独占边端、一次性、按账号串行）

- [ ] 3.1 新建 `src/comment-agent/comment-scheduler.ts`：`triggerManual(accountId)`（仿 `PublishScheduler.triggerManual`），载入 `getSoul` + `curatedStore.selectForCreation`。验证：单测——触发产出任务输入（人设+精选样本）。
- [ ] 3.2 新建有方向步骤时序器（仿 `command-sequencer`/`publish-dispatcher`）：角色①出**有序多词** →〔**逐词循环**：搜索(原生筛选) → 采列表 → 去重 → 甄选；**强相关命中即跳出**，否则**换下一个词**重试〕→ 开笔记 → 翻评论 → 撰写 → 人审 → 发布 → 记账去重 →（可选落精选）。换词有**尝试上限 K(可配)** + 受 `SearchFrequencyLimiter`/搜索预算约束 + 首中即止；词用尽/达上限仍无强相关 → 诚实结束不评。每步压边端约 30s 单步超时内；任一步失败 honest-fail。验证：单测——首中即止 / 换词重试 / 用尽诚实结束 / 上限+限频生效 / 失败短路。 <!-- WIP cloud 099cba4：**控制流核心已落 + 全测**（src/comment-agent/comment-task-runner.ts，纯逻辑、边端/LLM/风控经 CommentTaskSteps 注入；10 单测：无词/首中即止/去重在择优前/换词/用尽诚实结束/上限K/读·撰·发失败终态不偷换/坏pickIndex）。**仍缺=边端触达的步骤适配实现**（searchAndHarvest 发 search.execute 带 sort/timeWindow + 等 page.cards；readNote 开笔记+翻评论等 note.detail/action.completed；composeAndApprove 接评论链；post 发 interaction.comment 等回执）+ 单步 30s 超时 + 搜索限频/预算把关，与 3.1/3.3/5/6/7 一并接线 -->
- [ ] 3.3 边端独占：`src/server.ts` 新增 `onCommentTakeoverStart/End`（reason `comment_takeover`，仿 `onPublishTakeoverStart/End`）——开跑结束自动浏览会话标记不可恢复、`finally` 恢复浏览；按账号 accountTail 串行；`resolveEdgeIdForAccount` 离线 honest-fail。验证：单测——接管→恢复成对；同账号串行；离线诚实失败。

## 4. aidcp-cloud — 新角色①搜索词生成

- [x] 4.1 新建 `src/agents/comment-search-term-generator.ts`（判定类，读 `getSoul` + `curatedStore.selectForCreation('note'|'comment',N)`）→ 严格 JSON `{terms[], source}`，`terms` **有序**（供逐个换词重试）；精选稀疏退回 `seed_keywords`；解析失败/空诚实回退、不编造。验证：单测——有精选出贴领域有序词；精选空退种子词；坏输出回退不崩。 <!-- cloud aaa5500 CommentSearchTermGenerator（独立类，非 BaseRole，命令式调用 generate(samples)；调用方按账号传精选样本=账号隔离）；角色键 browse:comment_search_term_generator；7 单测（精选出词/解析空+降级退种子词/种子也空诚实返空/有序去重上限/source 标注）。**惰性建块、无调用方**（编排在 task 3） -->

## 5. aidcp-edge — 搜索结果原生筛选 + 收藏数采集（最大不确定性、需真机标定）

- [ ] 5.1 `src/browse/search-handler.ts`：搜索后驱动原生「最多收藏」排序标签 +「一天内」时间筛选控件（双布局选择器）；后置校验确实切到目标排序/时间，未生效 honest 报降级、不冒充。验证：jsdom 桩单测点击路径；真机标定见 task 12。
- [ ] 5.2 `src/browse/feed-scroller.ts` 卡片扫描 + `src/browse/browse-session.ts` `reportVisibleCards`：采每卡真实收藏数填 `collectCount`（替换硬编码 0）；采不到则置空、不编造。验证：单测/夹具——卡片含收藏数文本→解析正确；缺失→空不崩。
- [ ] 5.3 edge 侧消费搜索新参数 `sort`/`timeWindow`（来自 task 1）。验证：`npm run typecheck` + `AC-PROTO-*` 绿。

## 6. aidcp-cloud — 候选去重 + 新角色②搜索笔记甄选

- [ ] 6.1 去重接线：采到候选卡片后，对每卡 `InteractionDedup.hasInteracted(noteId,'comment')`（按账号）滤掉已评过的，**在甄选之前**。验证：单测——已评过的笔记不进甄选候选。
- [x] 6.2 新建 `src/agents/comment-target-picker.ts`（判定类，读去重后候选卡片[标题/作者/收藏数] + 人设）→ 严格 JSON `{pickIndex|null, stronglyRelevantIndexes[], reason}`；判**人设强相关**(沾边/泛泛相关不算)，只在强相关候选里挑收藏最高者；无强相关 `pickIndex=null`（编排据此换下一个词）。验证：单测——挑强相关高收藏；仅弱相关→null；全不相关→null；坏输出→null 不默认挑。 <!-- cloud aaa5500 CommentTargetPicker（独立类，命令式 pick(candidates)）；**确定性兜底**：在 LLM 判定的 stronglyRelevantIndexes 里按收藏数取最高（不完全信 LLM pickIndex）；越界 index 过滤；无强相关/降级/解析失败→null；9 单测。**惰性建块、无调用方**（去重接线+编排在 task 6.1/3） -->
- [ ] 6.3 发布成功（真回执 ok:true）后 `InteractionDedup.recordInteraction(noteId,'comment')`（按账号）。验证：单测——ok:true 记账、ok:false 不记。

## 7. aidcp-cloud — 撰写小改读现场评论

- [ ] 7.1 `src/agents/comment-composer.ts` `buildPrompt` 增加可选「现场评论」输入（命令路径在开笔记后先翻一屏评论采集 `CommentCandidate[]` 传入）；正文+现场评论+人设+精选参考一起入 prompt。撰写失败/空/超长诚实跳过、不回退占位。验证：单测——带现场评论的 prompt 含之；空输入退化为原行为；失败 skip。

## 8. aidcp-cloud — 角色注册 + 目录 + 文档

- [x] 8.1 `src/event-bus/types.ts` `RoleName` 加两角色（如需新事件载荷则加 `RoleEventMap`）。验证：typecheck 穷举一致。 <!-- cloud aaa5500 RoleName += comment_search_term_generator/comment_target_picker；无新事件（角色命令式调用、不走 EventBus）；typecheck 净 -->
- [x] 8.2 `src/config/role-catalog.ts` 两角色登记进 `ROLE_CATALOG`（判定类 `browse_judge`，`roleId='browse:<roleName>'` 去前缀逐字等于 `roleName`），否则运行时回落全局默认模型（`curated-admission-eval-roles` 6.1 教训）。验证：后台「角色管理」GET /api/roles 含二者、可配；单测/手测目录解析非 undefined。 <!-- cloud aaa5500 ROLE_CATALOG +browse:comment_search_term_generator（评论·搜索词生成）/browse:comment_target_picker（评论·搜索笔记甄选），均 browse_judge；roleId 后缀逐字=roleName=decide 角色键，故 categoryOf 命中判定类、不回落默认。后台「角色管理」数据驱动→部署后自动出现可配；live /api/roles 验证待部署 -->
- [ ] 8.3 `src/orchestrator/role-dispatcher.ts` 注册两角色（仅相关 store 可用时注册，仿 `concept_extractor`/curated 评估角色），注入账号绑定 LLM + `getSoul` + `curatedStore`。验证：单测——store 缺则不注册不报错。
- [ ] 8.4 中控 `CLAUDE.md` §2 角色数人工计数 +2（以 `RoleName` 穷举为准）。验证：核对计数。

## 9. 验收与红线

- [ ] 9.1 命令路径独占边端：不接管不下发命令；接管→恢复成对。验证：AC 断言。
- [ ] 9.2 去重在择优之前；甄选要**强相关**(弱相关不评)；当前词无强相关 → 换下一个词重试、首中即止；词用尽/达上限仍无 → 诚实结束不评。验证：AC 多路(去重 / 强相关 / 换词 / 用尽 / 上限+限频)。
- [ ] 9.3 命令路径跳过自动硬阈值但**保留人审 + canDo('comment') + 按天配额**；未授权/超时/被风控拒一律不发。验证：`AC-PUB-*`/`AC-RISK-*` 全过 + 单测。
- [ ] 9.4 诚实红线：搜索/筛选未生效、撰写失败、边端离线、LLM 降级一律 honest-fail，不静默假成功。验证：AC。
- [ ] 9.5 账号隔离：人设/精选/去重/落评论/落精选不跨账号。验证：单测——跨账号读被隔离。

## 10. 全量回归 + validate

- [ ] 10.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（安全红线 `AC-PROTO/AC-PUB/AC-RISK` 必过）。
- [ ] 10.2 edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。
- [ ] 10.3 中控：`openspec validate comment-search-command --strict` 通过。

## 11. 部署（ECS 安全序列；cloud 先 / edge 后；协议同版前 edge 对新筛选 honest 降级）

- [ ] 11.1 cloud 部署：§0 前置（私钥/子仓）→ 先备份 → `git archive <sha> src` 推 committed-only → `systemctl restart aidcp-cloud` → healthcheck（active+8787+飞书+PG）→ 失败回滚。绝不碰 isales。
- [ ] 11.2 edge：用户本地 `git pull` + 重启本地 edge（边端本地跑、连生产 8787）；如已打 Electron 包则需重打分发。

## 12. 真机标定（最大未知=原生筛选控件）

- [ ] 12.1 真账号 `/comment <昵称>`：核「最多收藏 + 一天内」是否真切到、收藏数是否真采、去重是否避开已评、甄选是否挑相关高收藏、撰写是否吃到现场评论、人审卡片→发出闭环。据真机回调甄选相关性严格度与筛选选择器（参 [[xhs-responsive-nav-layout]] 双布局、[[curated-inspiration-corpus-impl]] 集成时序 bug 只真机暴露）。

## 13. console 标签（可选）+ openspec 归档

- [ ] 13.1（可选）`aidcp-console/src/types/usageLabels.ts` 给两新角色补中文用量标签（仅用量页显示）。验证：用量页显示中文名。
- [ ] 13.2 全部 task 勾选 + `openspec validate --strict` → archive（delta 并入 `openspec/specs/comment-search-command`）。
