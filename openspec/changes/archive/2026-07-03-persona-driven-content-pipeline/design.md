## Context

系统内容生成把领域写死为「技术」，而非跟随账号人设：

- 正文创作 `buildCreatorPrompt`（`aidcp-cloud/src/publish-agent/prompts.ts:164`）**已收到** `trigger.generateInput.soul`（账号人设），但函数体硬编码「你是小林…技术帖」（`:211-212`）、无视人设；`content-creator.ts:55` 的 system 又写死「小红书技术博主」。相较之下标题角色 `title-creator.ts:62` 已经正确使用 `trigger.generateInput.soul.identity`。
- 脚手架「技术帖」散落于选题侦察 `:126`、标题 `:272`、话题 `:310/:333`、质量评分 `:438`；`title-creator.ts:64`、`topic-generator.ts:56` 兜底「小红书技术博主」。
- 浏览概念抽取 `concept-extractor-role.ts:107-118` 只挖技术概念、非技术返回 `[]`。
- 人设解析 `createPersonaResolver`（`persona-store.ts:192`）在账号无人设或解析失败时静默回落 `fallbackSoul`（`soul.yaml` 小林，`:196/:202`）；`server.ts:613` 装配。人设经 `getSoul(accountId)` 供浏览与发布共用。
- 「default 账号」已被运营删除，`panel-store.ts:179` 的 `accountId !== 'default'` 特判已失效。

约束：不改协议 / DB 结构；守「不静默假成功」红线；发布侧核心文件（`prompts.ts` / `content-creator.ts` / `role-catalog.ts`）当前被在飞 change `split-topic-roles`（0/22）占用。

## Goals / Non-Goals

**Goals:**
- 内容生成（正文 + 各脚手架）与浏览概念抽取由「技术」写死改为**人设驱动、话题中立**。
- 人设成为账号运行的硬前提：绑定必填、无人设诚实拒绝（`no_persona`）、系统不存在默认/兜底人设。
- 后台角色标签同步去技术化（纯展示）。

**Non-Goals:**
- 概念抽取的「人设感知」（只抽账号所在领域的概念）——本期做话题中立、领域无关即可，人设感知留后续（YAGNI）。
- 可编辑 prompt / prompt 模板库（与本 change 无关）。
- 不改 `build*Prompt` 的结构性契约（输入/输出形状、黑板键），仅去除领域硬编码 + 接人设。
- 不新增协议消息、不改 DB schema。

## Decisions

**D1：正文创作直接使用已传入的人设，而非新增线路。**
`trigger.generateInput.soul` 已在参数里，改法是让 `buildCreatorPrompt` 与 `content-creator` system 像标题角色那样取 `soul.identity`（role / background / tone），并把「技术帖」措辞换成中立「笔记」。
- 备选：新增 persona 形参贯穿管线——否，人设已在手边，多此一举。

**D2：无默认人设——解析器暴露「无人设」信号，调用方诚实拒绝。**
移除 `fallbackSoul` 的静默回落语义：`resolvePersona` 对无人设账号返回明确的「无人设」信号（而非某个默认 soul）；浏览启动与发布入口据此以 `no_persona` 拒绝。`soul.yaml` 技术默认人设不再作为兜底。
- 备选：保留一个「中立通用」默认人设——否，用户已定「不要默认人设、人设必填」，且静默套用任何人设都违背红线。

**D3：人设必填在绑定入口强制，双端校验。**
console 未填人设不允许保存；cloud 写入校验同样拒绝无人设绑定（前端被绕过也不落库）。清理 `panel-store.ts:179` 的 `'default'` 特判——是否需补人设仅看 `personaBound`。
- 备选：只在发布处校验——否，浏览也吃人设，前置到绑定最省事、语义最一致。

**D4：概念抽取做话题中立、领域无关。**
抽取 prompt 改为「抽任何可作搜索词的领域/话题概念」，删除「仅技术概念/非技术返回空」的限定与技术范文；保留「抽不到即空、不编造」红线。
- 备选：人设感知抽取（只抽账号领域词）——留后续，避免过度设计。

**D5：本 change 独立立项，发布侧任务排在 `split-topic-roles` 之后。**
发布侧改的 `prompts.ts` / `content-creator.ts` / `role-catalog.ts` 与 `split-topic-roles` 同文件，同时改会互吞。故：浏览侧（`concept-extractor-role.ts`）、人设解析（`persona-store.ts`）、console 校验先行；发布侧 prompt 与 role-catalog 标签**待 `split-topic-roles` 落地后**再动（届时其新增的话题 prompt 也一并去技术化）。tasks.md 显式标注此排序。
- 备选：并入 `split-topic-roles`——若那路 owner 同意可合并，但跨 owner 协调成本高，先独立、以排序约束解耦。

## Risks / Trade-offs

- **[存量账号无人设 → 突然拒绝运行]** → 上线前先补齐所有存量账号人设（或提供「未绑人设账号」核对清单）；分步：先上「必填校验 + 概念抽取通用化」，确认存量补齐后再上「移除兜底人设 + 无人设拒绝」，避免一刀切打断在跑账号。
- **[`SearchEvaluator` 依赖 `soul.yaml` 的 `seed_keywords`（`concept-pool-search` 现役需求）]** → 移除默认 soul 后，`seed_keywords` 须来自账号人设；确认账号人设结构含 `seed_keywords`，否则搜索候选仅剩概念池（见 Open Questions）。
- **[与 `split-topic-roles` 同文件冲突]** → D5 排序约束；发布侧动手前先 `git status` 确认那路已提交/归档。
- **[标签改名与行为未同时上线 → 名不副实]** → 标签改名与发布侧去技术化同批上（都在 `role-catalog.ts` / 发布 prompt，天然同处 split-topic-roles 之后）。

## Migration Plan

1. 先行批（不碰 WIP 文件）：概念抽取通用化（`concept-extractor-role.ts`）、人设解析去兜底 + 暴露无人设信号（`persona-store.ts`）、console + cloud 人设必填校验、清理 `panel-store.ts` `default` 特判。
2. 运营侧补齐存量账号人设；用「未绑人设账号」清单核对，确认无遗漏。
3. 待 `split-topic-roles` 落地后：发布侧 prompt 去技术化 + 正文接人设（`prompts.ts` / `content-creator.ts` / `title-creator.ts` / `topic-generator.ts`）+ role-catalog 标签改名。
4. 部署走既定安全序列（备份→scoped rsync→重启→healthcheck→失败回滚），绝不碰同机 isales。
- **回滚**：各步 scoped，单文件级可回退；发布侧改动集中于 prompt 文件，回滚即恢复上一版 prompt + 重启。

## Open Questions

- 账号人设结构是否已包含 `seed_keywords`（供 `SearchEvaluator` 取代 `soul.yaml` 全局种子词）？若无，是否本期补，还是搜索暂由概念池 + 人设兴趣词驱动？
- 存量「未绑人设账号」的补录由谁执行、是否需要后台提供一键清单/导出？
- `split-topic-roles` 的 owner 是否愿意把「话题 prompt 去技术化」并入其改动（避免二次改同文件）？
