# Tasks — persona-driven-content-pipeline

> 排序铁律：第 1–3 组「先行批」不碰 `split-topic-roles` 占用的文件，可先做先部署；
> 第 4–5 组「发布侧」改 `prompts.ts` / `content-creator.ts` / `role-catalog.ts`，**必须排在 `split-topic-roles` 落地之后**，避免同文件互吞。
>
> 进度（2026-07-01）：
> - **内容去技术化（1/4/5）已实装 + 部署 + 线上生效**（cloud `aecc1ce`；ECS prompts.ts「技术帖」=0、标签已改）。
> - **人设必填 / 无人设拒绝**：浏览侧早由 `retire-default-account` 实现（`canStartSession` + `isPersonaBound` fail-closed + 飞书告警 + `startOnPersonaBound`）；评论侧人设空即 honest-fail（无搜索词→不评）；本 change 补**发布侧人设闸**（`PublishScheduler.isPersonaBound`，未绑人设 `blocked/needs_persona_setup`、绝不用兜底 soul）+ 清 `panel-store` 失效 `default` 特判（cloud `9876eaa` 已提交推送，full suite 1029/1029）。
> - resolver 保留「回落 + 永不抛」（既有 spec，`persona-store.test` task 5.3）——去默认人设由各**闸**在入口 enforce，非改 resolver；ECS 实测 0 个未绑人设账号、`default` 已删。
> - ✅ **`9876eaa` 已部署**：首次 scoped 部署因 ECS 落后于 HEAD（split-topic-roles 已 commit 未 deploy、`server.ts` 依赖其 `roles/index.js` 的 `TopicEvaluatorRole` 导出）触发启动 `SyntaxError`、已即时回滚（restore 3 文件、服务恢复、de-tech 完好）；经用户确认后把 ECS **整体升到 HEAD**——`git archive HEAD` 干净快照 → 全量 `src/` rsync `--delete`（一并部署 split-topic-roles + 发布闸、删去 topic-strategist）→ 重启 healthcheck 全过（active / 8787 / 8090 / PG select 1 / 飞书 onReady、无 SyntaxError、de-tech 完好、isales 未碰）。**ECS 现与 HEAD 一致。**
> - ✅ **`/comment` 触发前人设闸已补 + 部署**（cloud `c1b70b3`）：`CommentScheduler.triggerManual` 未绑人设直接 `ok:false/warning` 拒绝、**不接管边端、不启动评论任务**（此前是接管后到「生成搜索词」才 honest-fail 的空跑）。至此**浏览 / 发布 / 评论三类任务均在入口拒绝未绑人设账号**，全部已部署、healthcheck 过。
> - 备注：`server.ts` 现有三处同款 `isPersonaBound`（浏览闸 retire-default-account + 发布闸 + 评论闸），口径一致。登录采昵称（nickname-capture-on-login）按设计仍对未绑人设账号跑一次——那是登录引导步骤、非浏览/发布/评论任务，不在默认人设上空跑。

## 0. 前置与排序（务必先读）

- [x] 0.1 发布侧动手前确认 `split-topic-roles` 已落地、工作区干净。<!-- aidcp-cloud：split-topic-roles Phase A/C=abf6769、review fixes=af35378 已提交，tree clean 后进行 -->
- [x] 0.2 清点当前所有账号 `personaBound` 状态，产出「未绑人设账号」清单（供第 3 组迁移核对）。<!-- 2026-07-03 以先前 session 实测为准：ECS 0 个未绑人设账号、default 已删（见上方进度注记）；且面板人设页 source=none 行即活清单，改后随时可核 -->

## 1. 浏览侧概念抽取通用化（aidcp-cloud，先行、不碰 WIP）

- [x] 1.1 `concept-extractor-role.ts` 抽取 prompt 去技术化：改为「抽任何可作搜索词的领域/话题概念」，删技术限定与技术范文；保留「抽不到即空、不编造」红线。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 1.2 `concept-extractor-role.ts` 注释与日志「技术概念」→「领域/话题概念」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [ ] 1.3 回归：非技术笔记（美食/旅行/穿搭）能抽到概念并写库；纯情绪/无信息仍返回空。<!-- aidcp-cloud 6097b89 prompt 面已锁：新增 AC-CONCEPT-NEUTRAL（人设驱动、不限技术领域、保留不编造红线）；「真模型抽到美食概念并写库」= 运行时行为 → docs/real-machine-acceptance-backlog.md 簇8 -->

## 2. 人设解析去兜底 + 无人设诚实拒绝（aidcp-cloud，破坏性——待迁移后做）

- [x] 2.1 `persona-store.ts:192` `createPersonaResolver`：去掉对 `fallbackSoul` 的静默回落，无人设/解析失败时暴露明确「无人设」信号（不返回默认 soul）。<!-- aidcp-cloud 6097b89 resolver 删 fallbackSoul、无行/空/解析失败→null，永不抛 -->
- [x] 2.2 `server.ts:595/613` 装配：不再注入技术默认 `fallbackSoul`；`getSoul` 调用方（浏览启动、发布入口）在「无人设」时以 `no_persona` 诚实拒绝。<!-- aidcp-cloud 6097b89 严格 getSoul 遇 null 抛 no_persona（三入口闸后的防御纵深）；人设存储 init 失败改 fail-closed（全体按未绑拒，不再带默认人设跑）。入口拒绝口径沿用既有 needs_persona_setup（persona-gated spec 规定、面板/飞书已消费），resolver 信号=null，未做全局改名 -->
- [x] 2.3 `soul.yaml`：解除其「全局默认人设兜底」角色。<!-- aidcp-cloud 6097b89 文件保留、降级为两个只读用途（面板编辑起点模板 + prompt 预览示例，均明示不进运行时），文件头/loader 加声明；proposal 措辞为「移除依赖」非删文件 -->
- [x] 2.4 核实 `SearchEvaluator` 的 `seed_keywords` 来源。<!-- 已确认：seed_keywords 存在于账号人设 soul.interests.seed_keywords（buildScoutPrompt 已用），非全局写死；无需额外改造 -->
- [x] 2.5 AC-PERSONA-1：无人设账号启动浏览 → `no_persona` 拒绝；无人设账号发布 → `no_persona` 拒绝、不生成内容。<!-- aidcp-cloud 6097b89 test/acceptance/persona-mandatory.test.ts 5 条：resolver null / 浏览拒启动且零指令 / 发布手动+自动拒且不进编排 / 评论拒且不接管边端 / 面板空人设 persona_required 不落库；acceptance 36/36 -->

## 3. 人设必填校验 + default 特判清理（aidcp-cloud + aidcp-console，待与 2 同批）

- [x] 3.1 cloud `PUT /api/persona/:id` 写入校验：空人设拒绝（不再允许清空回落），前端被绕过也不落库。<!-- aidcp-cloud 6097b89 facade 空人设→{ok:false,reason:persona_required}（400），删「清空=回落」语义 -->
- [x] 3.2 console `PersonaPage` 账号绑定/编辑：人设必填校验，未填不允许保存 + 提示。<!-- aidcp-console 7eaf9cc 留空拦截+诚实提示、persona_required 错误映射、「回落系统默认」文案全改「未绑定即拒绝运行」；PersonaSource fallback→none（cloud/console 必须同批部署，旧 console 遇 none 崩） -->
- [x] 3.3 `panel-store.ts:179/187`：去掉 `accountId !== 'default'` 特判（default 账号已删），`needsPersonaSetup` 仅依据 `personaBound`。<!-- 主体已被并发 session 做掉（cloud 9876eaa，已核实在 origin/master）；本批 6097b89 额外清掉 spec 要求的另两处残留 default 特判（cloud role-prompt-preview 预览回落标注、console RolesPage 预览账号下拉） -->
- [x] 3.4 存量迁移：按 0.2 清单补齐所有账号人设，确认无遗留后再启用第 2 组。<!-- 依 0.2：ECS 实测 0 个未绑人设账号（先前 session），无存量需迁移；第 2 组据此启用。部署后若仍有漏网账号会被入口闸拒+面板红标暴露，不会静默 -->

## 4. ⚠️ 发布侧去技术化（aidcp-cloud，split-topic-roles 落地后）——已完成

- [x] 4.1 `buildCreatorPrompt`：删「小林/技术帖」硬编码，改用 `generateInput.soul`（identity + interests）；「技术帖」→「笔记」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.2 `content-creator.ts` system：「小红书技术博主」→ 中立「小红书笔记创作者」，带「正文创作」路由标识（publish-orchestrator.test 路由同步更新）。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.3 `prompts.ts` 脚手架去技术化：选题侦察/标题/话题/质量评分「技术帖」→「笔记」；few-shot 改标注为"只学语气、勿照搬领域"。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed；ECS 抽样 grep 技术帖=0 -->
- [x] 4.4 `title-creator.ts` / `topic-generator.ts` 兜底「小红书技术博主」→「小红书博主」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.5 split-topic-roles 新增话题 prompt 一并去技术化。<!-- aidcp-cloud aecc1ce；prompts.ts 已无「技术帖」 -->
- [ ] 4.6 AC-PUB-DETECH：非技术人设账号生成正文/标题体现该领域、无「技术帖」写死。<!-- aidcp-cloud 6097b89 prompt 面已锁：新增 test/acceptance/content-detech.test.ts（正文/标题/话题 prompt 及 creator system 以非技术人设渲染体现该领域、无「技术帖/小林/技术博主」写死）；「真模型产出正文体现领域」= 运行时行为 → docs/real-machine-acceptance-backlog.md 簇8 -->

## 5. 后台角色标签改名（aidcp-cloud `role-catalog.ts`）——已完成

- [x] 5.1 displayName：技术帖文案创作→笔记正文创作、技术帖标题创作→笔记标题创作、技术概念关键词抽取→笔记关键词抽取。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->

## 6. 测试与部署

- [x] 6.1 cloud：typecheck 干净 + `test:acceptance` 27/27 + `npm test` 1026/1026。<!-- aecc1ce -->
- [x] 6.2 console：`typecheck` + `build`。<!-- aidcp-console 7eaf9cc typecheck 干净 + vite build 过 + vitest 5 pass/1 skip（skip 为既有 gated 用例） -->
- [x] 6.3 部署（内容去技术化批）：备份 `cloud.bak.20260701-225020.tar.gz` → scoped rsync 8 src 文件 → restart → healthcheck（active/8787/8090/飞书 onReady/PG select 1、无报错）→ isales 未碰。<!-- 2026-07-01 deployed；人设必填/去兜底（2/3）另批 -->

- [x] 6.4 人设必填/去兜底批（组 2/3 + console）集成：fleet agent 于隔离 worktree 实装，`scripts/land-change --yes` 串行落地——cloud `6097b89`（rebase 过 dashboard 同文件改动、acceptance 36/36 + 全量绿后 ff 推送）、console `7eaf9cc`。附带：comment-scheduler 任务启动 promise 补 .catch（闸后解绑 TOCTOU 防 unhandled rejection）；补 account-persona-config + persona-gated-session-start 两份 MODIFIED spec delta（旧「回落默认/default 豁免」条款与本批矛盾，归档时随 delta 修正）。<!-- 2026-07-03 -->
- [x] 6.5 部署：cloud + console **必须同批**上线（PersonaSource fallback→none 双向不兼容，先 cloud 后 console 连发、窗口仅影响人设页渲染数秒）；⚠️ 运维语义变化周知：PG 故障时人设镜像为空 → 全账号 fail-closed 拒绝运行（此前静默套默认人设照跑）。<!-- 2026-07-03 deployed — 备份 cloud.bak.20260703-120144 → git archive HEAD(6097b89) 快照 rsync src --delete → restart → console dist 秒级跟上(no --delete) → healthcheck 全绿(active/8787/8090/8088/PG/飞书 onReady/0 error/isales 未碰)；部署前探明 ECS=master 纯祖先(并发方 content-schedule 1h 前部署内容已含于 HEAD)、无未落库私货 -->
