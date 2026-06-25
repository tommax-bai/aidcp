> **协调与红线（动手前必读）**
> - **仅 aidcp-cloud**：edge / console / 协议 / 迁移一律不动。不新增 `MessageType`、不碰两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / edge `edge-client.ts` 白名单。无新迁移（冷却内存态）。
> - **风控终态单写不破**：冷却为附加只读节奏闸——MUST NOT 写 `risk_state`、MUST NOT 调 `setQuotaLevel` / `applySignal`、MUST NOT 改 `quotaLevel`。账号风控终态仍仅由 `RiskController` 单写。
> - **诚实硬失败**：被冷却 / 未达阈值一律诚实跳过（不下发、不扣预算、不计数、不假成功），记中性可观测原因。
> - **并发会话**：共享文件（`role-dispatcher.ts` / `server.ts`）只 **APPEND** 自己的接线、不重排他流既有块；`git add` 只暂存本 change 列出的具体文件、**绝不 `-A`**（见 memory `precise-git-add-concurrent-sessions`）。
> - **关注防回归（硬约束）**：收紧关注 MUST 不重新引入「作品数」依赖、MUST NOT 以「作品数未知」skip；`follow-decision` 既有场景（130 粉 / 6707 赞相关创作者仍被关注）必须仍通过。

## 1. aidcp-cloud — 冷却闸模块 + 单测

- [x] 1.1 新增 `src/risk/action-cooldown.ts`：`ActionCooldownGate`，内部 `Map<accountId, Map<action, lastTsMs>>`；写死常量 `COOLDOWN_MS = { like:120000, collect:300000, follow:600000, comment:1800000 }`；`canAct(accountId, action, nowMs): boolean`（`nowMs - (last ?? -Infinity) >= COOLDOWN_MS[action]`，未配置动作放行）；`markActed(accountId, action, nowMs): void`；`nowMs` 由调用方注入（默认 `Date.now`）便于单测；从 `src/risk/index.ts` 导出 <!-- cloud 755baa9 -->
- [x] 1.2 单测 `test/risk/action-cooldown.test.ts`：按账号按动作隔离、注入假时钟下「未到点抑制 / 恰好到点放行 / 过点放行」、不同账号互不影响、未配置动作恒放行、`markActed` 后即进入冷却 <!-- cloud 755baa9 -->

## 2. aidcp-cloud — 接入下发统一闸（like / collect / follow）

- [x] 2.1 `src/orchestrator/role-dispatcher.ts`：`RoleDispatcherOptions` 加可选 `cooldownGate?: ActionCooldownGate`，构造时持有；`src/server.ts` 装配处 `new ActionCooldownGate()` + 注入（**APPEND**，不动他流既有块） <!-- cloud 755baa9 -->
- [x] 2.2 `role-dispatcher.ts` 命令翻译统一闸（现有 `canInteract` + `canDo` 同处）：下发 `interaction.like` / `interaction.collect` / `interaction.follow` 前加 `cooldownGate?.canAct(currentAccountId, action, Date.now())`；未到点诚实跳过——不下发、不扣预算、记可观测 `reason='cooldown'`；`page.scroll` / `navigation.back` / `note.open` / `profile.open` 等推进 / 导航指令 MUST NOT 查冷却 <!-- cloud 755baa9 -->
- [x] 2.3 真实成功落时间戳：在 `action.completed{ok:true}` 驱动 `RiskController.record(action)` 的同一路径调 `cooldownGate?.markActed(accountId, action, Date.now())`；`follow` 排除 `already_followed`（`reason!=='already_followed'` 才落，与配额扣减口径一致）；`ok:false` MUST NOT 落 <!-- cloud 755baa9 -->
- [x] 2.4 红线核对：grep 确认冷却路径未写 `risk_state` / 未调 `setQuotaLevel` / `applySignal`；`canDo` 单写路径不变；推进指令未被冷却拦（加针对性断言或单测） <!-- cloud 755baa9 -->

## 3. aidcp-cloud — 评论硬阈值 + 评论冷却早判

- [x] 3.1 `src/agents/comment-appraiser.ts` `onInteractionCompleted`：取 `noteData` 之后、调 LLM 之前加硬阈值 `if (!(note.likeCount > 1000 && note.collectCount > 300)) skip('below_comment_threshold')`（严格大于）；阈值写死常量（就近集中点） <!-- cloud 755baa9 -->
- [x] 3.2 `comment-appraiser.ts`：早判评论冷却——`cooldownGate?.canAct(accountId, 'comment', Date.now())`，未到点 `skip('cooldown')` 直接进「是否进主页评估」，MUST NOT 进入撰写 / 去 AI 味 / 人审；`CommentAppraiser` 经 options 注入 `cooldownGate` 访问；comment 真成功（`ok:true`）落 `markActed`（复用 §2.3 路径，`comment` 计数同处） <!-- cloud 755baa9 -->
- [x] 3.3 单测 `test/agents/comment-appraiser.*`：阈值边界（1001/301 过；1000/301、1001/300、1000/300 均不过）；评论冷却中在评估阶段即 `skip('cooldown')`、不调 LLM <!-- cloud 755baa9 -->

## 4. aidcp-cloud — 四道判定 prompt 收紧 + 人设同步

- [x] 4.1 `src/agents/content-curator-role.ts` `buildPrompt`：「宽松 / 默认继续看 / 拿不准就过」→「话题强相关且真有信息 / 观点 / 经验才 pass；蹭热点 / 泛泛 / 擦边 / 纯情绪 → close_note；拿不准倾向 close」（保留「正文短≠低质」一句，避免误杀图文 / 视频笔记） <!-- cloud 755baa9 -->
- [x] 4.2 `src/agents/interaction-appraiser-role.ts` `buildPrompt` 决策逻辑：like「多数值得互动的笔记都该至少点赞」→「只在真有共鸣 / 学到具体东西 / 观点眼前一亮时才点；普通、泛泛认同、刷过即忘不点」；collect 仍更稀有、不比 like 易命中；「倾向 both」保留 <!-- cloud 755baa9 -->
- [x] 4.3 `src/soul/soul.yaml` `like_principle`：「有共鸣 / 认同 / 觉得有用就点赞，轻量高频」→ 选择性点赞措辞（与 4.2 prompt 框定一致、去掉「轻量高频」）；`collection_principle` 保持选择性 <!-- cloud 755baa9 -->
- [x] 4.4 `src/agents/author-evaluator.ts` `buildPrompt`：进主页门槛抬高——仅当作者明显有专业深度 + 方向高度吻合 + 确有长期关注价值才 visit，普通作者倾向 skip <!-- cloud 755baa9 -->
- [x] 4.5 `src/agents/follow-agent.ts` `buildPrompt`：抬至「主题强相关 + 至少一个真实质量信号（粉丝 / 获赞与收藏）」才 follow；**防回归**——prompt 仍不出现「作品数」项、不以「作品数未知」skip（`follow-decision` 不破） <!-- cloud 755baa9 -->
- [x] 4.6 一致性：`previewPrompt` / `personaSegments`（若措辞内联）随同步；`npm run typecheck` 绿 <!-- cloud 755baa9 -->

## 5. 回归与验收（§4 纪律）

- [x] 5.1 cloud `npm run test:acceptance`——`AC-RISK-*` / `AC-PROTO-*` / `AC-PUB-*` 全过（冷却为附加闸不破单写；协议未动计数不变；发布未动） <!-- cloud test:acceptance 26/26 绿（AC-RISK/PUB/PROTO/SEARCH） -->
- [x] 5.2 cloud 全量 `npm test`（含新增冷却闸 + 评论阈值单测） <!-- cloud npm test 693/693 绿（修了 路径F 集成测试 fixture + comment-lane fixture 因新评论阈值需高热度笔记） -->
- [x] 5.3 cloud `npm run typecheck` <!-- 我碰的文件 typecheck 0 报错；全仓残留报错仅并发 publish-multi-image WIP(publish-agent/*)，非本 change，按精确暂存不动 -->
- [x] 5.4 自查：`git status` 只含本 change 列出的 cloud 文件；`grep` 确认未碰 `protocol.ts` / `command-bridge` / edge / 迁移 <!-- git status 仅本 change 文件 + publish WIP(不暂存)；未碰 protocol/command-bridge/edge/迁移 -->

## 6. 部署与真机验证（显式动作，按 §5 安全序列；gated）

- [ ] 6.1 部署 `aidcp-cloud` 到 ECS（备份 → rsync → restart → healthcheck）；部署后 `grep` 关键文件确认新码生效（见 memory `deploy-verify-content-after-rsync`）
- [ ] 6.2 真机一轮观察：互动密度明显下降（冷却生效——赞 ~2min 一次、关注 ~10min、评论 ~30min）；评论仅出现在高热度笔记（>1000 赞 & >300 收藏）；粗筛 / 点赞 / 进主页 / 关注更挑剔；全程无 `no_target` / 假成功
