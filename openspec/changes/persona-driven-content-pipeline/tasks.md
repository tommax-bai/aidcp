# Tasks — persona-driven-content-pipeline

> 排序铁律：第 1–3 组「先行批」不碰 `split-topic-roles` 占用的文件，可先做先部署；
> 第 4–5 组「发布侧」改 `prompts.ts` / `content-creator.ts` / `role-catalog.ts`，**必须排在 `split-topic-roles` 落地之后**，避免同文件互吞。
>
> 进度（2026-07-01）：
> - **内容去技术化（1/4/5）已实装 + 部署 + 线上生效**（cloud `aecc1ce`；ECS prompts.ts「技术帖」=0、标签已改）。
> - **人设必填 / 无人设拒绝**：浏览侧早由 `retire-default-account` 实现（`canStartSession` + `isPersonaBound` fail-closed + 飞书告警 + `startOnPersonaBound`）；评论侧人设空即 honest-fail（无搜索词→不评）；本 change 补**发布侧人设闸**（`PublishScheduler.isPersonaBound`，未绑人设 `blocked/needs_persona_setup`、绝不用兜底 soul）+ 清 `panel-store` 失效 `default` 特判（cloud `9876eaa` 已提交推送，full suite 1029/1029）。
> - resolver 保留「回落 + 永不抛」（既有 spec，`persona-store.test` task 5.3）——去默认人设由各**闸**在入口 enforce，非改 resolver；ECS 实测 0 个未绑人设账号、`default` 已删。
> - ⚠️ **`9876eaa` 未部署**：其 `server.ts` 依赖 split-topic-roles 的 `roles/index.js`（`TopicEvaluatorRole` 导出），而 **ECS 落后于 HEAD——split-topic-roles 已 commit 未 deploy**；scoped 部署 `server.ts` 触发启动 `SyntaxError` 崩溃、已即时回滚（restore 3 文件、服务 active、de-tech 完好）。**部署本闸须先把 ECS 升到 HEAD（含 split-topic-roles）。**

## 0. 前置与排序（务必先读）

- [x] 0.1 发布侧动手前确认 `split-topic-roles` 已落地、工作区干净。<!-- aidcp-cloud：split-topic-roles Phase A/C=abf6769、review fixes=af35378 已提交，tree clean 后进行 -->
- [ ] 0.2 清点当前所有账号 `personaBound` 状态，产出「未绑人设账号」清单（供第 3 组迁移核对）。<!-- 破坏性 2/3 的前置，未做 -->

## 1. 浏览侧概念抽取通用化（aidcp-cloud，先行、不碰 WIP）

- [x] 1.1 `concept-extractor-role.ts` 抽取 prompt 去技术化：改为「抽任何可作搜索词的领域/话题概念」，删技术限定与技术范文；保留「抽不到即空、不编造」红线。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 1.2 `concept-extractor-role.ts` 注释与日志「技术概念」→「领域/话题概念」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [ ] 1.3 回归：非技术笔记（美食/旅行/穿搭）能抽到概念并写库；纯情绪/无信息仍返回空。<!-- 概念抽取为 LLM 行为、现有单测桩 LLM 不覆盖领域判断；未加专门断言 -->

## 2. 人设解析去兜底 + 无人设诚实拒绝（aidcp-cloud，破坏性——待迁移后做）

- [ ] 2.1 `persona-store.ts:192` `createPersonaResolver`：去掉对 `fallbackSoul` 的静默回落，无人设/解析失败时暴露明确「无人设」信号（不返回默认 soul）。
- [ ] 2.2 `server.ts:595/613` 装配：不再注入技术默认 `fallbackSoul`；`getSoul` 调用方（浏览启动、发布入口）在「无人设」时以 `no_persona` 诚实拒绝。
- [ ] 2.3 `soul.yaml`：解除其「全局默认人设兜底」角色。
- [x] 2.4 核实 `SearchEvaluator` 的 `seed_keywords` 来源。<!-- 已确认：seed_keywords 存在于账号人设 soul.interests.seed_keywords（buildScoutPrompt 已用），非全局写死；无需额外改造 -->
- [ ] 2.5 AC-PERSONA-1：无人设账号启动浏览 → `no_persona` 拒绝；无人设账号发布 → `no_persona` 拒绝、不生成内容。

## 3. 人设必填校验 + default 特判清理（aidcp-cloud + aidcp-console，待与 2 同批）

- [ ] 3.1 cloud `PUT /api/persona/:id` 写入校验：空人设拒绝（不再允许清空回落），前端被绕过也不落库。
- [ ] 3.2 console `PersonaPage` 账号绑定/编辑：人设必填校验，未填不允许保存 + 提示。
- [ ] 3.3 `panel-store.ts:179/187`：去掉 `accountId !== 'default'` 特判（default 账号已删），`needsPersonaSetup` 仅依据 `personaBound`。
- [ ] 3.4 存量迁移：按 0.2 清单补齐所有账号人设，确认无遗留后再启用第 2 组。

## 4. ⚠️ 发布侧去技术化（aidcp-cloud，split-topic-roles 落地后）——已完成

- [x] 4.1 `buildCreatorPrompt`：删「小林/技术帖」硬编码，改用 `generateInput.soul`（identity + interests）；「技术帖」→「笔记」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.2 `content-creator.ts` system：「小红书技术博主」→ 中立「小红书笔记创作者」，带「正文创作」路由标识（publish-orchestrator.test 路由同步更新）。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.3 `prompts.ts` 脚手架去技术化：选题侦察/标题/话题/质量评分「技术帖」→「笔记」；few-shot 改标注为"只学语气、勿照搬领域"。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed；ECS 抽样 grep 技术帖=0 -->
- [x] 4.4 `title-creator.ts` / `topic-generator.ts` 兜底「小红书技术博主」→「小红书博主」。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->
- [x] 4.5 split-topic-roles 新增话题 prompt 一并去技术化。<!-- aidcp-cloud aecc1ce；prompts.ts 已无「技术帖」 -->
- [ ] 4.6 AC-PUB-DETECH：非技术人设账号生成正文/标题体现该领域、无「技术帖」写死。<!-- LLM 行为断言、现有单测桩不覆盖；未加专门断言 -->

## 5. 后台角色标签改名（aidcp-cloud `role-catalog.ts`）——已完成

- [x] 5.1 displayName：技术帖文案创作→笔记正文创作、技术帖标题创作→笔记标题创作、技术概念关键词抽取→笔记关键词抽取。<!-- aidcp-cloud aecc1ce; 2026-07-01 deployed -->

## 6. 测试与部署

- [x] 6.1 cloud：typecheck 干净 + `test:acceptance` 27/27 + `npm test` 1026/1026。<!-- aecc1ce -->
- [ ] 6.2 console：`typecheck` + `build`。<!-- 仅第 3 组 console 改动时需要，本批未改 console -->
- [x] 6.3 部署（内容去技术化批）：备份 `cloud.bak.20260701-225020.tar.gz` → scoped rsync 8 src 文件 → restart → healthcheck（active/8787/8090/飞书 onReady/PG select 1、无报错）→ isales 未碰。<!-- 2026-07-01 deployed；人设必填/去兜底（2/3）另批 -->
