# Tasks — persona-driven-content-pipeline

> 排序铁律：第 1–3 组「先行批」不碰 `split-topic-roles` 占用的文件，可先做先部署；
> 第 4–5 组「发布侧」改 `prompts.ts` / `content-creator.ts` / `role-catalog.ts`，**必须排在 `split-topic-roles` 落地之后**，避免同文件互吞。

## 0. 前置与排序（务必先读）

- [ ] 0.1 发布侧（第 4/5 组）动手前先 `cd ../aidcp-cloud && git status`，确认 `split-topic-roles` 已提交/归档、`prompts.ts` / `content-creator.ts` / `role-catalog.ts` 工作区干净；未干净则停手，仅做先行批（第 1–3 组）。
- [ ] 0.2 清点当前所有账号 `personaBound` 状态，产出「未绑人设账号」清单（供第 3 组迁移核对）。

## 1. 浏览侧概念抽取通用化（aidcp-cloud，先行、不碰 WIP）

- [ ] 1.1 `concept-extractor-role.ts:107-118` 抽取 prompt 去技术化：改为「抽任何可作搜索词的领域/话题概念」，删「仅技术概念/工具方法名词」限定与「非技术返回 []」及技术范文（RAG/LangGraph/KV Cache）；保留「抽不到即空、不编造」红线。
- [ ] 1.2 `concept-extractor-role.ts:2/4/74` 注释与日志「技术概念」→「领域/话题概念」。
- [ ] 1.3 回归（对应 `concept-pool-search` 新场景）：非技术笔记（美食/旅行/穿搭示例）能抽到概念并写库；纯情绪/无信息内容仍返回空、不写库、不编造。

## 2. 人设解析去兜底 + 无人设诚实拒绝（aidcp-cloud，先行）

- [ ] 2.1 `persona-store.ts:192` `createPersonaResolver`：去掉对 `fallbackSoul` 的静默回落（`:196/:202`），无人设/解析失败时暴露明确「无人设」信号（不返回默认 soul）。
- [ ] 2.2 `server.ts:595/613` 装配：不再注入技术默认 `fallbackSoul`；`getSoul` 调用方（浏览启动、发布入口）在「无人设」时以 `no_persona` 诚实拒绝、不以替代人设运行。
- [ ] 2.3 `soul.yaml`：解除其「全局默认人设兜底」角色，确保不再被当兜底。
- [ ] 2.4 核实 `SearchEvaluator` 的 `seed_keywords` 来源（`concept-pool-search` 现役需求）：确认取自账号人设而非全局 `soul.yaml`；若仍依赖全局默认，评估改为人设兴趣词或暂由概念池驱动（见 design Open Questions）。
- [ ] 2.5 AC-PERSONA-1：无人设账号启动浏览 → `no_persona` 拒绝、不以默认人设开始；无人设账号发布 → `no_persona` 拒绝、不生成内容。

## 3. 人设必填校验 + default 特判清理（aidcp-cloud + aidcp-console，先行）

- [ ] 3.1 cloud 账号绑定/编辑写入校验：未填人设拒绝落库（前端被绕过也不落库）。
- [ ] 3.2 console 账号绑定/编辑：人设必填校验，未填不允许保存 + 明确提示。
- [ ] 3.3 `panel-store.ts:179`：去掉 `accountId !== 'default'` 特判，`needsPersonaSetup` 仅依据 `personaBound`。
- [ ] 3.4 存量迁移：按 0.2 清单补齐所有账号人设，确认无「未绑人设账号」遗留，再正式启用第 2 组「移除兜底 + 无人设拒绝」（如需分步灰度，先上校验、后上拒绝，避免打断在跑账号）。

## 4. ⚠️ 发布侧去技术化（aidcp-cloud，排在 split-topic-roles 落地之后）

- [ ] 4.1 `buildCreatorPrompt`（`prompts.ts:164`，硬编码在 `:211-212`）：删「小林/技术帖」硬编码，改用 `trigger.generateInput.soul.identity`（对齐 `title-creator.ts:62`）；措辞「技术帖」→「笔记」。
- [ ] 4.2 `content-creator.ts:55` system：「你是一个小红书技术博主」→ 人设驱动/领域中立。
- [ ] 4.3 `prompts.ts` 脚手架去技术化：选题侦察 `:126` / 标题 `:272` / 话题 `:310,:333` / 质量评分 `:438`「技术帖」→「笔记」；few-shot 范文去单一技术领域。
- [ ] 4.4 `title-creator.ts:64` / `topic-generator.ts:56` 兜底「小红书技术博主」：改为人设驱动；无人设走 `no_persona` 拒绝（不套默认）。
- [ ] 4.5 若 `split-topic-roles` 新增的话题生成/筛选 prompt 仍含「技术帖/vLLM、RAG」，一并去技术化。
- [ ] 4.6 AC-PUB-DETECH：给定非技术人设账号，生成正文/标题体现该领域、无「技术帖/技术博主」写死；无人设账号发布 `no_persona` 拒绝、不代偿。

## 5. 后台角色标签改名（aidcp-cloud `role-catalog.ts`，随第 4 组同批）

- [ ] 5.1 `role-catalog.ts` displayName：技术帖文案创作→笔记正文创作、技术帖标题创作→笔记标题创作、技术概念关键词抽取→笔记关键词抽取。

## 6. 测试与部署

- [ ] 6.1 cloud：`npm run test:acceptance`（AC-PUB-*/AC-RISK-* 全过）→ `npm test` → `npm run typecheck`。
- [ ] 6.2 console：`npm run typecheck` + `npm run build`。
- [ ] 6.3 部署走安全序列（备份 → scoped rsync → 重启 → healthcheck：active/8787/飞书 onReady/PG `select 1` → 失败回滚），绝不碰同机 isales。先行批（1–3）可先部署；发布侧（4–5）待 `split-topic-roles` 后另批部署。
