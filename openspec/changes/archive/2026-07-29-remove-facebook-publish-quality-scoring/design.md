## Context

现有发布管线为所有平台注册同一组角色。`QualityScorer` 读取 `cleanedContent` 后调用 LLM 产出 `qualityScore`，`ContentAssembler` 等待该键，`ApprovalGatekeeper` 再调用另一模型决定 `auto_publish | manual_review | retry | abort`，`PublishExecutor` 等 `gateDecision` 后行动。

这套图最初按小红书建立。当前质量 prompt 仍明确写“评估一篇小红书笔记”，`QualityScorer` 输入也没有平台。Facebook 同时已有独立正文 prompt、素材池、语言校验、发布执行器和强制人工审批；因此继续让两个主观模型决定候审稿能否出现，既平台错配又与人工审批重复。

管线有两个结构约束：

- `ContentAssembler` 的 `waitAll` 不能缺少 `qualityReport`，否则会死锁到整轮超时。
- `PublishExecutor` 现有依赖包含 `gateDecision`；直接让 Facebook 的 Gatekeeper “不产出”同样会死锁。

## Goals / Non-Goals

**Goals:**

- Facebook 一轮发布对 `publish:QualityScorer` 和 `publish:ApprovalGatekeeper` 的 LLM 调用均为零。
- 不用固定高分、零分或 `NaN` 冒充“跳过评分”；以显式 `null + not_applicable` 表示没有评分。
- 保持现有黑板单生产者与 `waitAll` 拓扑，避免再造一套 Facebook 平行管线。
- Facebook 在语言、素材和既有确定性处理通过后，确定性地产生 `manual_review` admission，继续走同一草稿落库与审批链。
- 小红书路径的提示、分数、降级公式、Gatekeeper LLM 和阈值不变。

**Non-Goals:**

- 不取消 Facebook 人工审批，不增加自动发布。
- 不移除 `ContentCleaner`、AI 味审计或合规元数据。
- 不修改协议、edge、数据库 schema、角色配置目录或小红书行为。
- 不在本 change 中批量修复历史 `reserved` 媒体；只避免质量评分再次制造这条退出路径。
- 不实现 100–350 的确定性长度收敛；该项仍由 `fb-publish-fill-deadline` 的 5.3b 承载。

## Decisions

### 1. 用显式“不适用”结果保持单生产者拓扑

`QualityReport` 改为携带：

- `qualityScore: number | null`
- `status: 'scored' | 'not_applicable'`
- `reviewedAt`

`QualityScorer` 继续是 `qualityReport` 的唯一生产者。它从 trigger 读取 platform：

- Facebook：同步返回 `{ qualityScore: null, status: 'not_applicable' }`，记录安全枚举日志，不构建 prompt、不调用 LLM。
- 其他平台：逐字沿用现有 LLM 评分与降级公式，返回 `status:'scored'`。

选择该方案而不是删除角色/动态改 `watchKeys`，是因为后者会打破 `ContentAssembler.waitAll` 或引入第二个同键生产者；选择 `null` 而不是固定分，是为了不制造可被下游误读的假事实。

### 2. ContentAssembler 只透传适用性，不承担平台策略

`AssembledContent.qualityScore` 改为 `number | null`，新增 `qualityStatus`。`ContentAssembler` 仍只做纯字段映射，不读 platform、不自行决定是否评分。

这样平台政策只存在于评分角色入口，组装层不会重新长出策略分支；下游和日志也能区分“真实 0 分”与“未评分”。

### 3. Gatekeeper 保留唯一生产者，但 Facebook 分支为确定性人工审批

`ApprovalGatekeeper` 输入加入 platform：

- Facebook：不构建 Gatekeeper prompt、不调用 LLM，返回
  `recommendedAction:'manual_review'`、`needsApproval:true`、reason=`facebook_quality_scoring_disabled`。
- 非 Facebook：要求 `qualityStatus='scored'` 且分数非 null，然后逐字沿用现有 LLM 与 fallback 规则。

选择保留 `gateDecision` 而不是让 `PublishExecutor` 增加一套无 gate 的动态依赖，是为了维持“标题 + 元数据 + admission 决策”同一发布门，以及复用现有草稿/审批实现。这里的 `gateDecision` 对 Facebook 表示平台 admission，不表示质量评分结论。

### 4. PublishExecutor 不新增旁路

Facebook 的确定性 `manual_review` 继续进入既有 `stageDraftForApproval`。`PublishExecutor` 仍执行发言语言检查、素材必需检查、草稿落库、审批通知；它不根据 `null` 分数做判断，也不产生 `retry`。

草稿写入适配器当前不持久化 qualityScore，故 schema 无需变化。Cloud 内部记录类型接受 nullable，测试锁定 Facebook 候审记录不带虚构分数。

### 5. 验收以“零模型调用 + 候审真态”为准

新增测试必须同时证明：

- Facebook 的 QualityScorer/Gatekeeper fake LLM 计数均为 0。
- `qualityReport.status='not_applicable'`、`qualityScore=null`。
- 最终 `publishResult.status='pending_approval'`，而非 `retry`/`failed`。
- 小红书仍调用两个模型并按既有分数/动作工作。

DEV 部署后只做一轮受控 `/publish` 到候审卡为止；不点击批准、不触发 Facebook 真实提交。运行日志必须看不到该 run 的两个质量模型调用，并能看到待审记录。

## Risks / Trade-offs

- [风险] `qualityScore` 变 nullable 会暴露隐含的 number 假设。→ 用 typecheck 与全量测试逐个收口；禁止 `?? 0` 这类静默回落。
- [风险] “跳过质量评分”被误解为自动发布。→ Facebook Gate 决策固定为 `manual_review`，审批链与授权要求不变。
- [风险] 保留角色名称可能让日志看起来仍在评分。→ Facebook 分支记录明确 reason=`not_applicable`，并以模型调用计数为验收真据。
- [风险] 历史媒体预约泄漏仍占池。→ 本 change 不写数据库；另行审计并修复通用 reservation 生命周期后再安全回收。
- [代价] Facebook 仍运行 ContentCleaner/AI 味审计。→ 这是确定性后处理与合规元数据，不是本次移除的主观质量评分；保留可避免扩大安全边界。

## Migration Plan

1. 先以 nullable 类型和平台分支补齐单元/管线验收，运行 acceptance、全量与 typecheck。
2. 合入 Cloud master 后部署 DEV；无依赖或 migration 变化，不执行 `npm ci`/迁移写入。
3. 重启后确认服务、schema gate、writer lock、Feishu 与 health。
4. 受控触发一次 Facebook 候审生成，不批准；核对该 run 两个质量 LLM 调用均为零且草稿进入 `pending_approval`。
5. 若候审链异常，回滚 Cloud 提交并重启；数据库无 schema 变更。

## Open Questions

- 历史 `reserved` 媒体的安全回收标准与通用 pre-draft 资源结算另开 change，不在本批假设或批量更新。
