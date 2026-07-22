## Context

回复规则已经有冻结字段 `actions.polish` 和 `actions.allowAutoSend`，账号/渠道也已有 `auto_safe`、`sendReplies` 和 `allowAutoSend`。但 Console 在启用 AI 时强制把规则字段写回 false；Cloud 的预览判定和发送编排又只允许“未运行 AI、最终文本等于模板、没有任何风险标签”的候选，因此 AI 规则没有真实自动发送路径。

真实发送仍经过 Cloud 的 queued job、运行控制、账号 allowlist、平台身份与 capability、登录冷却、RiskController、专用限速、幂等和结果核验。本变更只开放一条受约束的 AI 候选准入，不新增发送旁路，也不改变 Edge 协议。

## Goals / Non-Goals

**Goals:**

- 让规则级 `allowAutoSend` 对 AI 润色规则真实生效，并在 Console 中以“人工审核 / 自动回复”直接表达。
- 允许安全的风格润色，以及有知识文档依据的普通问答，在完整门禁通过后直接进入现有发送队列。
- 在生成准入与实际派发两个阶段都保留确定性复核；任何未知或失败降级人工。
- 保留过程标签和审计证据，不把“风险显示为 low”等同于无条件发送。

**Non-Goals:**

- 不自动修改或发布现有规则，不为任何账号开启账号级自动模式、渠道自动范围、runtime controls 或运维 allowlist。
- 不允许订单、退款、价格、促销、库存、时效、售后、投诉争议、个人数据、医疗、法律、安全、辱骂或未成年人安全内容自动发送。
- 不新增模型、数据库字段、API DTO、WS v2 命令或 Edge 行为；不开放 v1 私信 AI。
- 不用真实平台发送作为开发或部署验收。

## Decisions

### 1. 复用规则 `allowAutoSend`，不扩展数据模型

规则编辑器把发送方式改为互斥选择：`allowAutoSend=false` 表示人工审核，true 表示自动回复。`polish` 只控制是否运行 AI，不再改写发送方式。账号必须选择 `auto_safe`，渠道必须加入自动范围，规则的 true 才可能生效；因此它仍是单调授权的一部分，而不是绕过上层开关。

备选方案是增加 `reviewMode` 枚举。它会扩大冻结 schema、历史 JSONB 和 Cloud/Console 兼容范围，而现有布尔字段已经能无歧义表达当前两种选择，因此不采用。

### 2. 把实质风险、流程标签和规则强制标签分开

订单、退款、价格等实质风险与 `unknown` 永远阻断自动发送。`meaning_changed`、`introduced_claim` 继续记录在 job 和预览中，但不再无条件等价于实质高风险：

- 纯风格润色只有在 `meaningChanged=false` 且没有新增事实时可自动发送；
- 普通知识问答可以发生语义变化并记录新增事实，但必须有当前渠道知识文档、普通问答 intent、成功的全部 AI 调用、至少一项 `introducedClaims`、候选通过确定性检查且汇总标签仅为流程标签；
- 改义但没有可审计知识事实、没有知识文档却新增事实，或任一条件不完整时降级人工。

`forceHumanTags` 按交集判断：只有最终实际标签命中管理员选定项才强制人工。实质硬风险仍由独立硬门禁处理，不依赖管理员是否选择标签。

备选方案是删除流程标签。这样会丢失审计证据，也无法让运营解释 AI 做了什么，因此不采用。

### 3. 用一套确定性资格判定支撑生成准入和派发复核

Cloud 把自动内容资格收敛为共享的纯函数/等价判定，输入只包括已发布配置、命中规则、渠道 profile 和候选的结构化字段。生成阶段额外要求 classifier、polisher、reviewer 均无 fallback、候选未被拒、reviewer 返回 low 且建议允许自动发送。满足后，system actor 才把 job 从 classifying 直接转 queued。

派发阶段从 job 固定的 `configVersion/configScopeId` 读取同一版本规则和 profile，重新检查规则授权、风险等级、流程标签组合、知识文档条件、最终文本和确定性 claim gate。运行控制、平台能力、登录冷却、allowlist、RiskController、限速、CAS、幂等和核验继续按原顺序执行。任一复核失败不得创建 send attempt。

不在 job 新增 AI fallback 字段：只有生成阶段完整成功的 job 才能进入无人审批 queued；派发阶段以 queued 状态加固定版本配置和持久化风险证据复核，避免数据库迁移。

### 4. reviewer 给内容建议，Cloud 决定最终发送

reviewer prompt 明确：普通低风险内容应返回 `riskLevel=low` 且 `allowAutoSend=true`；实质风险或未知返回 false。Cloud 不解析自然语言 reasons，也不单独信任模型布尔值：模型建议只是资格条件之一，最终仍需全部确定性条件。

### 5. 预览只模拟内容资格，不冒充真实平台发送

预览在满足内容与已发布策略条件时显示“可自动回复/直接发送”，否则显示“需要人工审核”并保留风险、fallback 和候选拒绝信息。预览不会检查每个瞬时派发条件，也不会真实入队或发送；实际发送仍以派发时真态为准。

## Risks / Trade-offs

- [知识文档事实无法用字符串比较证明语义完全一致] → 只开放普通问答、要求文档非空和 introducedClaims 审计、全 AI 成功、reviewer low、确定性 claim gate 为空；实质类别和未知继续强制人工。
- [生成准入与派发条件漂移] → 抽取共享资格判定，并用测试同时覆盖 preview/job 两种输入；派发继续 fail closed。
- [旧规则启用 AI 但 allowAutoSend=false] → 不迁移、不改发布版本，仍保持人工；只有管理员主动选择并发布才扩权。
- [客户端显示自动但运维 allowlist 或运行门禁关闭] → UI 说明该选择只是规则授权，预览与发送记录如实展示最终降级，不能宣称已发送。
- [模型低风险误判] → reviewer 不是唯一事实源；确定性 intent/claim/text/profile/硬标签检查和两阶段门禁继续独立生效。

## Migration Plan

1. 先部署 Cloud，使新旧 Console payload 都兼容；默认和现有规则不变。
2. 再部署 Console，提供规则发送方式选择并更新发布摘要。
3. 用本地测试和 dev 无副作用 preview 验证低风险 AI 路径与强制降级路径；核对 send attempt 计数不增加。
4. 回滚时先恢复 Console 静态产物，再恢复 Cloud；没有 schema 或数据迁移需要回退。

## Open Questions

无。运维 allowlist 的账号纳入仍按现有上线流程处理，不由本次 UI 自动开启。
