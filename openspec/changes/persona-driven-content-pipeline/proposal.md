## Why

内容生成把「技术帖 / 技术博主 / 小林」写死，无视账号已绑的人设——`buildCreatorPrompt`（`aidcp-cloud/src/publish-agent/prompts.ts:164`）明明收到了 `trigger.generateInput.soul`，函数体却直接硬编码「你是小林…技术帖」（`prompts.ts:211-212`），`content-creator.ts:55` 的 system 又写死一遍「小红书技术博主」。结果是系统只会写技术笔记，运营给账号绑了别的人设也没用。同时「default 账号」已删除，`soul.yaml`（小林）这套技术兜底人设与 `panel-store.ts:179` 的 `!== 'default'` 特判都已失效，却仍在悄悄给没绑人设的账号套一个技术人设——违背「不静默假成功」。

## What Changes

- **内容生成改为人设驱动**：`buildCreatorPrompt` 与 `content-creator` 的 system 改用账号真实人设（`generateInput.soul.identity`，标题角色 `title-creator.ts:62` 已是此法），不再硬编码。
- **发布脚手架去技术化**：`prompts.ts` 中散落的「技术帖」全量改为「笔记」（选题侦察 :126 / 标题 :272 / 话题 :310,:333 / 质量评分 :438），领域交给人设决定；few-shot 范文不再全是 RAG/LLM。
- **概念抽取通用化**：`concept-extractor-role.ts:107-118` 从「只挖技术概念、非技术返回 []」放宽为「抽取任何可作搜索词的领域/话题词」，让概念池对任意账号领域都能用。
- **人设改为必填** **BREAKING**：账号绑定必须写人设（console + cloud 双端校验）；人设是账号能运行的前提（浏览与发布都吃 `getSoul`）。
- **移除默认/兜底人设** **BREAKING**：删除 `soul.yaml` 技术兜底 + `createPersonaResolver` 的 `fallbackSoul` 静默回落语义（`persona-store.ts:196,202`）；无人设的账号在浏览/发布处**诚实拒绝 `no_persona`，绝不静默套通用或技术人设**。清理 `panel-store.ts:179` 已失效的 `'default'` 特判。
- **后台角色标签改名**（`role-catalog.ts` displayName，纯展示）：技术帖文案创作→笔记正文创作、技术帖标题创作→笔记标题创作、技术概念关键词抽取→笔记关键词抽取。

## Capabilities

### New Capabilities
- `mandatory-account-persona`：每个账号必须绑定人设方可运行（浏览与发布）；系统不存在默认/兜底人设；账号无人设时浏览与发布均诚实拒绝（`no_persona`），绝不静默套用任何通用或技术人设。绑定入口（console + cloud）强制人设必填。

### Modified Capabilities
- `publish-pipeline`：内容生成（正文 + 各脚手架 prompt）必须**人设驱动且话题中立**——不得硬编码「技术帖 / 技术博主 / 小林」等特定领域；正文创作 prompt 必须使用账号绑定的人设；账号无人设时拒绝发布，绝不用默认人设代偿。
- `concept-pool-search`：浏览概念抽取必须**话题中立**——从笔记正文抽取任意可作搜索词的领域/话题概念（不限技术领域），使概念池 → 主动检索对任意账号领域成立。

## Impact

- **cloud（aidcp-cloud）**：`src/publish-agent/prompts.ts`（`buildCreatorPrompt` 用人设 + 全量「技术帖→笔记」）、`roles/content-creator.ts`（system 去技术化）、`roles/title-creator.ts` 与 `roles/topic-generator.ts`（兜底「小红书技术博主」改为拒绝/人设驱动）、`src/agents/concept-extractor-role.ts`（抽取 prompt 通用化）、`src/config/persona-store.ts`（去 `fallbackSoul` 静默回落、暴露「无人设」信号）、`src/soul/soul.yaml`（移除技术默认人设依赖）、`src/panel/panel-store.ts:179`（清理 `'default'` 特判）、`src/config/role-catalog.ts`（3 处 displayName 改名）、`src/server.ts`（装配调整）。
- **console（aidcp-console）**：账号绑定/编辑处人设必填校验（未填不允许保存）。
- **协议 / DB / 迁移**：不改协议、不改 DB 结构。**存量迁移**：已存在但未绑人设的账号在本 change 后将被拒绝运行，须先补人设——需一次运营侧补录（或提供列出「未绑人设账号」的核对手段）。
- **⚠️ 排期依赖（关键）**：发布侧要改的 `prompts.ts` / `content-creator.ts` / `role-catalog.ts` 目前被在飞的 change `split-topic-roles`（0/22）占着同文件。本 change 的发布侧任务**必须排在 `split-topic-roles` 落地之后**（或与其协调合并），避免同文件互吞；浏览侧 `concept-extractor-role.ts` 与 console 校验不在其 WIP 内、可先行。
- **红线**：无人设绝不静默套人设（不静默假成功）；不改任何 `build*Prompt` 的结构性契约，仅去除领域硬编码 + 接人设。
