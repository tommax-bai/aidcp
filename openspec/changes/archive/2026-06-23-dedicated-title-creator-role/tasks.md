# Tasks — dedicated-title-creator-role

回归铁律：发布链改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`；红线 `AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 必须全过，新增 `AC-TITLE-*`。
提交纪律：并发会话在改两仓 `protocol.ts`；**精确 `git add` 仅本 change 文件、不 `-A`**；改前 `git pull --rebase`，按符号定位（`publish-executor.ts`/`prompts.ts` 行号可能漂移）。
红线：MUST NOT 静默假成功；标题失败=发布失败、不造假标题；记录==下发==审批卡==真实发布；edge 不做标题策略。

## 0. 前置坐实（BLOCKING，决定 abort 失败语义）

- [x] 0.1 坐实 `abort`+`waitAll` 上游永不写键时流水线的现状收敛：读 `base-role.ts` 失败处理（`fallback:'abort'` 分支是否写键/是否抛）、`pipeline-context.ts` 的 `waitAll` 触发条件、`PublishOrchestrator` 如何结束一次 run（settle 在 `publishResult` 还是有 abort 传播）。判定标题 `abort` 后是「即时 `failed`」还是「干等 `pipelineTimeoutMs`(18min)」。**验证**：写清现状结论（带 `文件:行`）于本 task HTML 注释
<!-- 现状=HANG_UNTIL_TIMEOUT。base-role.ts:97-100 的 abort 分支只 log、不写键/不抛/不发事件；pipeline-context.ts:37-54 waitAll 仅在 ready.size===keys.length 才触发，缺键永不激活下游；publish-orchestrator.ts:91-123 awaitCompletion 仅 settle 于 publishResult 写入 / scoutDecision.shouldPublish=false / setTimeout(pipelineTimeoutMs)；server.ts:279 注入 pipelineTimeoutMs=1_080_000(18min)。故 TitleCreator abort 后 PublishExecutor 的 waitAll 永缺 titleSelection → 干等 18 分钟才 failed。结论：必须做 0.2 即时收敛。 -->

- [x] 0.2 若现状是「干等超时」：在本 change 内让标题 `abort` **即时**冒泡为流水线 `failed`（最小改动，复用现有 abort 传播或在 orchestrator 侧加即时收敛），不引入 18 分钟挂死。若现状已即时失败：记录无需改、引用证据。**验证**：单测「`TitleCreator` 抛错 → 流水线秒级 `failed`、无 `titleSelection`、未发布」
<!-- cloud ee8ef6f Option A：types.ts 加 PipelineAbort 键；base-role.ts:97-100 abort 分支 context.write('pipelineAbort',{role,reason,abortedAt})；publish-orchestrator.ts awaitCompletion 加第三个 watch('pipelineAbort')→reject→既有 trigger.catch 收敛为 failed。单测 publish-orchestrator.test.ts「TitleCreator 抛错→即时 failed、未落库未发布」(elapsed<4000ms < pipelineTimeoutMs 5000) + title-creator.test.ts「连续失败→abort、写 pipelineAbort、不写 titleSelection」。 -->

## 1. aidcp-cloud — 类型、黑板字段、字形安全截断工具

- [x] 1.1 `src/publish-agent/types.ts`：加 `export interface TitleSelection { title: string; source: 'llm' | 'derived'; decidedAt: number }`（不加 candidates/score）；`PipelineFields` 加 `titleSelection: TitleSelection`。**验证**：`npm run typecheck`
<!-- cloud ee8ef6f 另加 PipelineAbort 接口 + PipelineFields.pipelineAbort（task 0.2 用）。typecheck 绿。 -->
- [x] 1.2 `src/publish-agent/title-clamp.ts`（新）：`clampTitle(s: string, max = 18): string`——`Intl.Segmenter` 按 grapheme 计数；≤max 原样；超 max 在 [max-window, max] 窗口回退到最近词/标点边界，窗口内无边界则硬切到 max；**绝不返空**（空输入返回空串本身，由调用方按空标题策略处理）。附 `firstSentence(s)` 供 deriveTitle 兜底复用。**验证**：单测见 5.1
<!-- cloud ee8ef6f 另导出 graphemeCount(s)。window=4。空串/max<=0 返空串。AC-TITLE-CLAMP 全过。 -->

## 2. aidcp-cloud — TitleCreator 角色 + 提示词

- [x] 2.1 `src/publish-agent/prompts.ts`：加 `buildTitlePrompt(body, persona, styleType, seedTitle?)`——短提示（不复述长正文规则）：输入定稿正文+人设+风格，产出一个 ≤18 可见字符钩子标题、至多 1 emoji、无省略号、无标题党、结尾不带标点、复用 `BANNED_PHRASES`、给好/坏范例、只输出 `{"title":"…"}`。**验证**：`npm run typecheck`；prompt 不夹长正文规则块
<!-- cloud ee8ef6f 短提示、复用 BANNED_PHRASES、好/坏范例、只输出 {"title":"…"}。 -->
- [x] 2.2 `src/publish-agent/roles/title-creator.ts`（新）：`watchKeys=['assembledContent']`、`outputKey='titleSelection'`、`fallback:'abort'`、`timeoutMs=120000`；`extractInput` 读 `assembledContent.finalContent`（可读 `createdContent.title` 作 seed）；`execute` 调 `llmClient.chat`（传 `{ timeoutMs: 120000 }`，因 QwenClient 默认 30s 会先 abort）→ 解析 JSON → `Intl.Segmenter` 量长度，>18 或含禁用词或含「…/...」则语义重试 ≤2 次 → `clampTitle(.,18)` 收口 → 写 `{title, source:'llm', decidedAt}`。LLM/解析/重试用尽失败则**抛错**（走 `abort`，不写键、不派生）。**验证**：单测见 5.2
<!-- cloud ee8ef6f system='…标题创作专家…'（与 ContentCreator 区分，便于桩按 system 路由）；persona 取 soul.identity；空正文短路写空标题 source=derived 不调 LLM。AC-TITLE-ROLE 全过。 -->
- [x] 2.3 `src/publish-agent/roles/index.ts`：导出 `TitleCreatorRole`。**验证**：`npm run typecheck`
<!-- cloud ee8ef6f -->

## 3. aidcp-cloud — PublishExecutor 接线（发布门 + 标题出口收口）

- [x] 3.1 `src/publish-agent/roles/publish-executor.ts`：`watchKeys=['gateDecision','titleSelection']` + `waitAll:true`；`extractInput` 加 `titleSelection`。**验证**：`npm run typecheck`；单测「`titleSelection` 未写 → executor 不激活」
<!-- cloud ee8ef6f AC-TITLE-GATE「titleSelection 未写→不激活、不落库」。 -->
- [x] 3.2 同文件全部标题出口改读 `input.titleSelection.title`：DB 写入、序列下发（流向 edge `fill_field(title)`）、飞书审批卡、`handleManualReview`、`handleAbort`。`deriveTitle` 仅保留为 `titleSelection` 意外缺失时的最后兜底（内部改用 `clampTitle`，不再盲切 30）。**验证**：单测「DB/序列/卡片三处标题为同一 clamp 后字符串」
<!-- cloud ee8ef6f execute 一次 resolveTitle 后 title 串穿全部 handler；deriveTitle=clampTitle(firstSentence(...),18)。AC-TITLE-FIDELITY「DB==序列==审批卡 同一字符串」。 -->

## 4. aidcp-cloud — 模型按角色可配 + 注册

- [x] 4.1 `src/config/role-catalog.ts`：加目录行 `{ roleId: 'publish:TitleCreator', displayName: '技术帖标题创作', group: 'publish', llmKind: 'text', tunableTemperature: true }`。**验证**：后台「角色配置页」可见该角色（或 catalog 单测）
<!-- cloud ee8ef6f 插在 publish:ContentCreator 后。 -->
- [x] 4.2 `src/server.ts`：`publishOrchestrator.registerRole(new TitleCreatorRole({ llmClient: roleLlm('publish:TitleCreator') }))`，注册在装配器之后（注册顺序与正确性无关，data-driven）。**验证**：启动日志「PublishOrchestrator 已就绪，角色: … TitleCreator …」
<!-- cloud ee8ef6f 导入 + 注册在 ContentAssembler 之后。getRoles 数 21→22（orchestrator 单测已更新断言）。 -->

## 5. aidcp-cloud — 测试与回归

- [x] 5.1 `title-clamp` 单测（AC-TITLE-CLAMP）：18 字不变、19 字截断、25 连续汉字返回恰 18 非空、emoji 不拆代理对、含空格在边界回退、空串入空串出。**验证**：`npm test`
<!-- cloud ee8ef6f test/publish-agent/title-clamp.test.ts 8 例全过。 -->
- [x] 5.2 `TitleCreator` 单测（AC-TITLE-ROLE）：有效 LLM 标题 >18 → 重试/clamp 后 ≤18 且 `source='llm'`；LLM 连续失败 → 抛错走 abort、**不写 `titleSelection`**（红线：不派生假标题）；取 `finalContent` 非 `createdContent.content`。**验证**：`npm test`
<!-- cloud ee8ef6f test/publish-agent/title-creator.test.ts 5 例全过。 -->
- [x] 5.3 集成单测（AC-TITLE-GATE / AC-TITLE-FIDELITY）：标题就绪前 executor 不发布；标题 abort → 流水线即时 `failed`、未发布（接 0.2）；成功路径下 DB 写入标题==序列下发标题==审批卡标题（同一字符串、≤18）。**验证**：`npm test`
<!-- cloud ee8ef6f AC-TITLE-GATE/FIDELITY 在 publish-executor.test.ts；即时 failed 在 publish-orchestrator.test.ts。 -->
- [x] 5.4 全量回归：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿；`AC-PUB-*`/`AC-PROTO-*`/`AC-RISK-*` 不破。**验证**：三命令退出码 0
<!-- cloud ee8ef6f test:acceptance 26/26、test 324/324、typecheck 0 err。红线全过。 -->

## 6. aidcp-edge — 移除标题截断（不做策略）

- [x] 6.1 `src/flows/publish-command-handlers.ts`：移除 `XHS_TITLE_MAX` 常量与 `runFillField` 标题分支的 `slice`，标题原样填入（撤回本会话 commit `472cda1`）；正文分支不动。**验证**：`grep -n XHS_TITLE_MAX` 无残留
<!-- edge 8cb8d01 const value = rawValue（标题/正文均原样填入）；grep XHS_TITLE_MAX 无残留。 -->
- [x] 6.2 edge 回归：`npm test`（含 publish 处理器单测，若有断言标题截断的用例同步更新为「原样填入」）+ `npm run test:acceptance` + `npm run typecheck` 全绿。**验证**：三命令退出码 0
<!-- edge 8cb8d01 现有 publish-handler 单测用短标题、无截断断言，无需改。test 283/283、test:acceptance 11/11、typecheck 0 err。 -->

## 7. 部署与真机验证

- [x] 7.1 云端部署（与 edge 同批）：§0 私钥/子仓前置检查 → ECS 备份 `.bak.<ts>.tar.gz` → rsync **仅本 change 文件**（dry-run surface scope，不带并发会话的 protocol.ts） → `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连接 + PG + isales 未触碰）→ 失败回滚。**验证**：healthcheck 全过 + 启动日志含 TitleCreator
<!-- cloud ee8ef6f 2026-06-22 deployed。备份 /opt/aidcp/cloud.bak.20260622-171437.tar.gz(13.4MB)+.env.bak.20260622。dry-run surface scope=恰本 change 14 文件（comment-like 已先期在 ECS、未额外 co-ship）。healthcheck：active + 8787 监听 + 启动日志「PublishOrchestrator 已就绪，角色: … ContentAssembler, TitleCreator, TopicStrategist …」+ 飞书长连接已建立 + PG select 1=1 + isales 4 服务(api/engine/scheduler/worker) 全 active 未触碰。 -->
- [x] 7.2 edge 本地重启连 `ws://121.89.85.150:8787`（新代码：无标题截断）。**验证**：`已连接云端 … 等待命令`
<!-- edge 8cb8d01 2026-06-22 后台启动（AIDCP_AUTO_BROWSE=false）：Chrome 就绪 CDP 9222、复用 ~/.aidcp-chrome-profile 小红书登录态、握手 sess-1、日志「已连接云端 ws://121.89.85.150:8787，等待命令」。 -->
- [x] 7.3 真机端到端：飞书 `/publish` → 审批卡**标题栏为真实 ≤18 字标题** → 通过 → 发布成功（URL `/publish/success`）→ 核对 `publish_log.title` == 平台显示标题（≤18、未切碎、records==published）。**验证**：三方一致
<!-- 2026-06-22 真机跑（publish-12）：本 change 的标题目标【已验证】——TitleCreator 线上产出真实标题、DB publish_log id=12 title="TP 设置踩坑实录"(9 可见字)、records==下发(序列)==审批卡 三方同一字符串、≤18 未切碎。【偏离】「发布成功(records==published)」这一腿未达成：发布卡在 seq11 submit_publish→post_validate_failed。多 agent 评审(对抗性证伪)结论：这是【与标题无关的独立、早存在的提交 bug】——runSubmit/发布按钮锚点自 3590f3c(06-21)逐字未变、id 11 用同套代码发成功；6 个元数据 guard_persist 经证伪为 jsdom 可见性误判(噪声非真遮挡)。真实候选：发布时风控/拦截 toast 不匹配 15s 成功正则 / 按钮禁用 no-op / >15s 假阴性超时(账号侧或已真发)。已解耦：标题保真为本 change 范围且已达成；提交失败另开 change「先诊断后修」跟踪。 -->
- [ ] 7.3b（移交新 change）发布提交失败诊断：先在 runSubmit 加只观测日志(按钮 disabled 态 / elementFromPoint / 超时时 location.href+正文头)+ 账号侧确认 id 12 是否真发，再诚实修(硬必选 guard_persist 判致命收口云端，边缘不加兜底启发式)。**验证**：新 change 接手

## 8. 收尾（中控）

- [x] 8.1 各 task 用 HTML 注释标 `[x]` + `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。**验证**：本文件各 task 带注释
<!-- aidcp 本提交：tasks 0-6 + 8.1/8.2 已标注；7.x 部署/真机验证待执行；8.3 archive 待部署验证后。 -->
- [x] 8.2 三仓提交推送：本仓 tasks/docs 推 `main`，cloud/edge 代码各推 `master`（精确 `git add`，Co-Authored-By 行）。**验证**：三仓 `git status` 干净、已 push
<!-- cloud ee8ef6f / edge 8cb8d01 / aidcp 本提交。精确 git add（未碰并发 protocol.ts / chrome-launcher WIP / comment-like tasks.md）。 -->
- [x] 8.3 `openspec validate dedicated-title-creator-role --strict` 通过 → `openspec archive dedicated-title-creator-role`（delta 并入 `openspec/specs/publish-pipeline/`）。**验证**：archive 后 `openspec list` 该 change 不再活跃
<!-- 2026-06-22 archive。标题保真目标完成并线上验证（见 7.3）；end-to-end 发布成功被独立提交 bug 阻断，已解耦移交新 change 跟踪（见 7.3b），不阻塞本 change 归档。validate --strict 通过。 -->
- [x] 8.4 评审存档：post_validate_failed 根因评审（多 agent + 对抗性证伪）结论写入 docs/handoff + 记忆 [[publish-pipeline-deployed]]；提交失败移交新 change。
