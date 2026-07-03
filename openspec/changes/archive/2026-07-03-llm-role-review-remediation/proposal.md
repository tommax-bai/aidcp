# llm-role-review-remediation

## Why

2026-07-03 对全部 LLM 角色做了一轮选型 + prompt 复审（8-agent workflow，行情/评测/代码三线核验），结论是现役选型为局部最优、不需大改，但揪出一批**违背「绝不静默假成功」红线的解析缺口**与两处下架潮防御项：

- 列表页卡片择选：LLM 回的序号越界或非法时**静默落到第一张卡**（`content-evaluator.ts` 使用处 `candidates[result.index] ?? candidates[0]`、解析层非数字默认 `0`）——会打开一篇从未被评估过的笔记；换轻量模型后越界概率升高，是降档改动的前置。
- 搜索关键词决策：LLM 返回的词**不校验是否属于给定候选集**，编造词会被真实搜索且占用搜索预算。
- 标题创作解析：未接控制字符修复（正文创作已接 `escapeControlCharsInJsonStrings`，同用 doubao 系、有裸换行前科）；解析炸 = fallback abort = 整篇枪毙（含已产配图）。
- 去 AI 味重写 prompt：无「只输出正文」约束——模型若带前言（如“好的，以下是重写后的内容：”），前言会**逐字进入最终发布正文**，后续无任何环节能查出。发布链最高危 prompt 缺陷。
- 质量评分对象错位：`QualityScorer` 嵌入 prompt 的正文是**重写前草稿**（`buildAssemblerPrompt(input.created, …)`），清洗稿只传了元数据——发生重写时质量闸评的不是将发布的文本。
- 代码兜底默认模型是 `qwen-turbo`，而百炼 2026-07-13 将其下架——DB 配置行存在时不触发，但该兜底自 7-13 起是坏的。

同轮复审的**配置优化**（零代码，随本 change 部署一并落地）：高频阻塞判定角色降档 `deepseek-v4-flash`（延迟+成本双降，同组合已在精选评估角色实测 685ms）；`qwen-flash` 两角色防御迁移（该别名已从官方文档消失，同批 `qwen-turbo` 已定 7-13 下架；2026-07-03 实测仍 200 但无文档背书）；生成类两角色温度微调；发布审批 thinking 关闭（阈值表判定无需推理）。

## What Changes

- **浏览侧解析防线**：卡片择选序号做整数 + 域界校验，非法/越界按 skip 如实处理（绝不静默换卡）；搜索词做候选集成员校验，编造词走既有安全回退、绝不真实搜索。
- **发布侧输出契约**：标题解析接入 JSON 控制字符修复；去 AI 味重写 prompt 增加「只输出重写后正文」约束（顺修「口吾」→「口吻」笔误——该 prompt 原为逐字冻结，本 change 即是修订它的 change）；质量评分改为评清洗稿（发生重写时评将发布文本）。
- **配置兜底**：代码级全局默认模型 `qwen-turbo` → `qwen3.7-plus`（防 7-13 下架后兜底失效）。
- **线上配置（非代码，随部署执行）**：批次 A——`publish:TopicGenerator` 温度 0.5、`publish:ApprovalGatekeeper` thinking on→off（`publish:ImagePromptComposer` 温度 0.6 已被先行改好，核验即可）；批次 B——`browse:content_evaluator` / `browse:concept_extractor` / `browse:comment_like_appraiser` → `deepseek-v4-flash`，`browse:comment_reviewer` / `browse:search_evaluator` 由 `qwen-flash` 迁 `deepseek-v4-flash`；ECS `.env` 增 `AIDCP_PUBLISH_CATEGORY_TIMEOUT_MS=180000`（对齐 180s 天花板，防将来换慢模型静默超时落 general）。
- **不做**：GLM 引入（百炼无轻量档、无 JSON 不可靠实测痛点）；Kimi K2.6 创作 A/B（B 阶段可选）；重判定角色（interaction_appraiser / follow_agent / comment_appraiser）降档；延迟入表观测（另立 change）；面板探活 8s 修复（本次走 psql 直写绕过，另行考虑）。

## Capabilities

### New Capabilities
- `llm-output-honesty`: LLM 输出解析与评审对象的诚实防线——判定类输出的域内校验（卡片序号、搜索词候选集）、生成类输出的解析修复与 prompt 输出约束（标题控制字符、重写只输出正文）、质量评审对象必须是将发布文本、代码兜底模型必须现役。

### Modified Capabilities
<!-- 无:不触碰既有 7+ spec 的 requirement;卡片择选/发布管线此前无 spec 覆盖,本 change 以新 capability 立防线。 -->

## Impact

- **aidcp-cloud**：`src/agents/content-evaluator.ts`（序号校验）、`src/agents/search-evaluator.ts`（候选集校验）、`src/publish-agent/roles/title-creator.ts`（json-repair）、`src/publish-agent/prompts.ts`（重写 prompt 约束）、`src/publish-agent/roles/quality-scorer.ts`（评清洗稿）、`src/config/model-config-store.ts`（兜底默认）；对应单测。
- **ECS 线上配置**：`role_config` 表 6 行写入/更新（psql 直写绕探活 8s 假 model_invalid，同 2026-07-01 playbook）+ `.env` 一行 + 重启热载。
- **不碰**：协议两份 `protocol.ts`、`command-bridge.ts`、角色注册（`RoleName`/`role-catalog`）、风控状态机——全部热点文件零触碰，可与并行 change 共存。
- **回滚**：配置项面板/psql 一键改回；代码项 git revert;部署前有 ECS 全量备份。
