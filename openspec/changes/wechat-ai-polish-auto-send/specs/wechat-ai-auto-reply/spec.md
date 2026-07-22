## ADDED Requirements

### Requirement: AI 规则必须允许运营选择人工审核或自动回复

管理后台 SHALL 为每条回复规则提供互斥的“人工审核”和“自动回复”发送方式，并分别确定性写入 `actions.allowAutoSend=false|true`。启用或取消 AI 润色 MUST NOT 隐式改变该发送方式；已有规则 MUST 保持服务端原值，只有管理员主动保存并发布后才可改变自动化范围。

#### Scenario: AI 润色规则选择自动回复

- **WHEN** 管理员为启用 AI 润色的规则选择“自动回复”并保存
- **THEN** Console 写入 `polish=true` 与 `allowAutoSend=true`，并说明通过安全检查后将直接发送、仍受账号和渠道上限及 Cloud 硬门禁约束

#### Scenario: AI 润色规则选择人工审核

- **WHEN** 管理员为规则选择“人工审核”并保存
- **THEN** Console 写入 `allowAutoSend=false`，无论 `polish` 是否开启，命中后的回复都不得无人审批入队

#### Scenario: 打开旧规则不静默扩权

- **WHEN** 已发布 AI 规则的 `allowAutoSend=false`，管理员只打开编辑器或切换 AI 润色开关但没有主动选择自动回复并发布
- **THEN** 系统 MUST 保持人工审核语义，不得自动改写为 true 或触发发送

### Requirement: 安全 AI 候选必须可以进入既有自动发送队列

当已发布账号策略为 `auto_safe` 且允许生成和发送、当前渠道启用并允许 AI 与自动发送、命中规则选择自动回复时，Cloud SHALL 允许满足全部内容资格的 AI 候选由 system actor 直接进入既有 queued 状态。内容资格 MUST 同时要求 classifier、实际调用的 polisher 和 reviewer 无 fallback，候选未被确定性规则拒绝，最终风险为 low，reviewer 建议允许自动发送，且没有 `unknown`、实质 hard-risk 或命中的规则强制人工标签。

#### Scenario: 纯风格润色直接自动回复

- **WHEN** AI 只把模板润色得更简短亲切，`meaningChanged=false`、没有新增事实、全部 AI 调用成功、reviewer 为 low/允许自动，且所有上层策略和确定性检查通过
- **THEN** 最终文本可以不同于 rendered template，job SHALL 无需人工批准直接进入 queued，并由既有发送编排处理

#### Scenario: 基于知识文档回答普通问题后自动回复

- **WHEN** 用户提出普通信息问题，当前渠道知识文档有明确答案，polisher 基于文档生成答案并记录至少一项 introducedClaims，全部 AI 调用成功，候选只携带 `meaning_changed`/`introduced_claim` 流程标签且其它资格均通过
- **THEN** 这些流程标签 MUST 保留用于审计，但不得仅凭自身强制人工，job SHALL 可以直接进入 queued

#### Scenario: 无依据新增事实降级人工

- **WHEN** AI 候选新增事实但当前渠道没有知识文档、intent 不是普通问答、没有记录 introducedClaims，或改义却没有可审计的知识事实
- **THEN** Cloud MUST 设置 requiresApproval，MUST NOT 让该 job 无人审批入队

#### Scenario: AI 或候选检查失败降级人工

- **WHEN** classifier、polisher 或 reviewer 发生 timeout、upstream、JSON/schema fallback，或候选超长、改写受保护联系方式行、命中禁词/链接/声明检查
- **THEN** Cloud MUST 降级人工审核并保留具名 fallback/拒绝原因，不得把回退模板当成成功 AI 自动回复

#### Scenario: 实质风险继续强制人工

- **WHEN** intent、候选或 reviewer 命中订单、退款、售后、价格、促销、库存、时效、投诉争议、个人数据、医疗、法律、安全、辱骂或未成年人安全风险，或风险仍为 unknown
- **THEN** Cloud MUST 强制人工审核，不得因规则选择自动回复、reviewer 自报 low 或流程标签白名单绕过

### Requirement: 规则强制人工标签必须按实际命中生效

`actions.forceHumanTags` SHALL 表达“最终风险标签命中所选项时强制人工”。Cloud MUST 计算所选标签与最终实际标签的交集；配置列表非空但实际未命中时 MUST NOT 无条件阻断低风险自动回复。独立实质硬门禁不受该列表影响。

#### Scenario: 配置标签但本次未命中

- **WHEN** 规则配置“价格”标签强制人工，但本次普通问答的最终标签不含 pricing
- **THEN** Cloud 不得仅因配置列表包含 pricing 而强制人工，仍按其它自动发送资格判断

#### Scenario: 本次命中所选标签

- **WHEN** 最终风险标签包含规则 `forceHumanTags` 中任一项
- **THEN** Cloud MUST 要求人工审核，即使其它自动发送条件均满足

### Requirement: 无人审批 AI job 必须在派发前再次复核

Cloud SHALL 在生成准入和真实派发前分别复核无人审批 AI job。派发复核 MUST 使用 job 固定的配置版本查找命中规则、渠道 profile 和策略，并重新验证规则授权、风险等级、流程标签组合、知识依据条件、最终文本和确定性 claim gate；原有账号 allowlist、runtime controls、active identity、capability、登录冷却、RiskController、专用限速、CAS、幂等与结果核验 MUST 保持生效。

#### Scenario: 生成后运行门禁关闭

- **WHEN** AI job 已进入 queued，但派发时账号写暂停、渠道发送关闭、身份或 capability 失效、登录冷却未结束、风险状态阻断或限速用尽
- **THEN** Cloud MUST 在创建或派发 send attempt 前拒绝本次自动发送，不得把 queued 状态或先前 preview 当作发送证明

#### Scenario: 固定版本规则不再支持自动资格

- **WHEN** 派发复核无法从 job 固定配置版本找到命中规则/profile，或持久化风险证据与自动资格不一致
- **THEN** Cloud MUST fail closed 并要求人工处理，不得回退使用当前最新配置扩大权限

### Requirement: 预览必须如实区分自动资格与真实发送

无副作用 preview SHALL 使用与生成阶段一致的内容资格判定，并以最终动作显示“可自动回复”或“需要人工审核”。preview MUST 展示 AI fallback、风险标签和候选拒绝信息，但 MUST NOT 入队、创建 send attempt 或宣称平台已发送；真实发送结果只能来自既有派发与核验状态机。

#### Scenario: 自动回复规则预览通过

- **WHEN** 自动回复规则的 AI 候选满足内容资格与已发布策略条件
- **THEN** preview 显示该路径可自动回复/直接发送，并同时注明仅模拟、实际仍受派发时运行门禁约束

#### Scenario: 预览不产生平台副作用

- **WHEN** 管理员运行任意评论或私信回复预览
- **THEN** 系统不得创建 reply job 或 send attempt，不得调用 Edge 发送命令，且不得把模拟结果呈现为已发送
