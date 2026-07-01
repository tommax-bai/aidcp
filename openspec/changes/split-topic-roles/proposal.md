## Why

当前小红书笔记的「话题」既没有独立生成/评判角色、边缘也从未真正把话题贴上：话题（=标签）由写正文的 `ContentCreator` 一次 JSON 顺带产出（`content-creator.ts:77`），名为 `TopicStrategist` 的「话题角色」只做去重+截断、不调 LLM（`topic-strategist.ts:28-32`）；边缘 `add_with_candidate{topic}` 只往「话题」按钮 set value、从不打 `#`/等下拉/点建议，后置校验又只查全局子串（`publish-post.ts:232-240`）→ 要么被发布页遮罩绊成 `guard_persist`、要么「静默假成功」贴了个假话题。本变更把话题的**生成 / 评判 / 填写**拆成三个专职角色，与正文彻底解耦，并让边缘做真实的加话题交互——这与 `publish-pipeline` 已确立的「标题拆独立角色、不再是单次 JSON 子字段」同一条治理路线。

## What Changes

- **新增 `TopicGenerator`（cloud, LLM）**：以定稿正文为输入，独立生成话题候选；与 `TitleCreator` 并行（避免串行 LLM 尾撞总闸）。产出新黑板键 `topicCandidates`。
- **新增 `TopicEvaluator`（cloud, LLM 评判）**：纯 LLM 按相关性/质量/合规评判候选，**只筛不加**（kept ⊆ candidates）、去重截断 ≤30、失败保守空；接管现有 `topicSelection` 键（下游 `MetadataAggregator` / `publishMetadata` 零改）。
- **删除 `TopicStrategist`**（其去重/截断折进 Evaluator 的确定性后处理）。
- **BREAKING（内部管线）**：`ContentCreator` 停产 tags（prompt 去掉 tags、`parseOutput` 返回 `[]`）；`ContentAssembler.finalTags` 不再 ← `createdContent.tags`、恒 `[]`。话题的唯一真源变为 `publishMetadata.topics`。
- **审批==下发**：审批卡 / 落库的 tags 改读 `publishMetadata.topics`（`PublishExecutor` 的 `waitAll` 加入 `publishMetadata`），杜绝「审批显示空、下发发真话题」的错位。
- **新增边缘 `runAddTopic`（edge, CDP 直驱）**：聚焦正文富文本 → 打 `#关键词` → 等建议下拉 → 点匹配建议（或 Enter 兜底）→ 断言真话题 token/pill 出现（非全局子串）→ fail-closed。**由显式开关 `AIDCP_PUBLISH_TOPIC_CDP`（默认 OFF）门控**，实机 DOM 校准前保留原路径为兜底、绝不在生产静默丢话题。
- **协议零改动**：`add_with_candidate` payload 不变，`candidates` 参数退化保留（向后兼容 + 无 cdp 兜底路径仍用）。
- **后台可配**：两个新 LLM 角色登记 `role-catalog` 供后台独立配模型，并纳入「模型调用 ≥180s 超时下限」不变量。

## Capabilities

### New Capabilities
- `topic-authoring`: 小红书笔记话题的生成/评判/填写三职分离——独立话题生成角色（依定稿正文）、独立话题评判角色（纯 LLM 相关性质量、只筛不加、失败保守）、边缘真实加话题交互（真 token 校验、fail-closed、开关门控、未校准不上线），以及话题角色的后台模型可配置性。

### Modified Capabilities
- `publish-pipeline`: `ContentCreator` 不再产出标签、正文角色单产正文；`ContentAssembler.finalTags` 语义改为恒空、话题落地改由 `publishMetadata.topics` 单一真源；黑板新增 `topicCandidates` 唯一生产者且 `topicSelection` 生产者换角色仍不死锁；审批卡/落库的 tags 与实际下发一致（读 `publishMetadata.topics`、`PublishExecutor` 增 `publishMetadata` 依赖）。

## Impact

- **aidcp-cloud**：`src/publish-agent/roles/`（新增 `topic-generator.ts` / `topic-evaluator.ts`，删除 `topic-strategist.ts`，改 `content-creator.ts` / `publish-executor.ts`，`index.ts` 换 export）、`src/publish-agent/types.ts`（新增 `TopicCandidates` + `topicCandidates` 键）、`src/publish-agent/prompts.ts`（去 creator tags、加话题生成/评判 prompt）、`src/server.ts`（导入+注册）、`src/config/role-catalog.ts`（两 roleId）；`MetadataAggregator` / `publish-dispatcher.ts` 无需改。
- **aidcp-edge**：`src/flows/publish-command-handlers.ts`（新增 `runAddTopic` + 路由 + 开关）、`src/flows/publish-post.ts`（收紧话题后置校验为真 token），复用 `cdp-util.ts` / `action-executor.ts`。
- **协议**：无（`docs/protocol.md` 与两份 `protocol.ts` 不动）。
- **测试**：删 `topic-strategist.test.ts`；加 `topic-generator` / `topic-evaluator` / edge `runAddTopic` 单测；更新 `publish-orchestrator.test.ts`（角色数 23→24 + fakeLlm 路由）、`model-call-timeout-invariants.test.ts`、`publish-executor.test.ts`。安全红线 `AC-PROTO-*` / `AC-PUB-*` 须绿。
- **实机 gated**：边缘话题下拉容器 / 真 token 选择器 / Enter-vs-click 提交行为需一次真机 CDP 校准后方可打开 `AIDCP_PUBLISH_TOPIC_CDP`。
