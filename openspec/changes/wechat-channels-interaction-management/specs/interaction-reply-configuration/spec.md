## ADDED Requirements

### Requirement: Runtime controls 与版本化回复配置必须分离

系统 SHALL 把账号 capability/ingestion/write kill switch 存为独立 CAS runtime controls，把 policy/templates/rules/profiles 存为 draft/published 配置。坏 draft、配置缺失或 published 失效 MUST NOT 停止已获授权的入站同步，但 MUST 停止草稿生成和发送。写总开关、账号写、comment write、dm write 与 auto-safe 初始值 MUST 为 false。

#### Scenario: 坏 draft 不停止收取
- **WHEN** 管理员保存了校验失败的 draft 而账号 read capability 已启用
- **THEN** 评论/DM 继续同步，运行时仍使用上一 published 配置或停生成，MUST NOT 使用坏 draft

#### Scenario: Kill switch 立即停写但保留读取
- **WHEN** 管理员关闭账号 write kill switch
- **THEN** 新发送立即被拒，已同步内容仍可读，pending job 保留而非烧成 failed

### Requirement: 配置发布必须原子生成不可变版本

每账号 SHALL 只有一个可编辑 draft；每次写携 aggregate `expectedVersion`。publish MUST 在单事务内验证 policy、templates、rules、profiles、变量 fallback、规则冲突、硬门禁和 role 引用，成功后生成新的 immutable published `configVersion` 并记录 actor/diff/time。历史 job MUST 继续引用创建时的 config/template version。

#### Scenario: 发布校验失败不产生半版本
- **WHEN** draft 同时包含合法模板和冲突规则
- **THEN** publish 返回 `INTERACTION_VALIDATION_FAILED` 的全部相关 issues，published 指针与所有历史版本不变

#### Scenario: 老 job 不受模板更新改写
- **WHEN** 模板发布新版本而旧 job 已引用前一版本
- **THEN** 旧 job 的 rendered/final 审计保持旧版本，新 message 才使用新 published version

### Requirement: 模板变量与规则排序必须确定性

模板只允许 `{{user_name}}`、`{{video_title}}`、`{{account_name}}`、`{{support_channel}}` 的字面替换，MUST NOT 支持表达式、脚本或 HTML。published profile MUST 为每个可能缺失且被使用的变量提供非空安全 fallback；运行时不得输出 null/raw ID。规则顺序固定为 `priority ASC,ruleId ASC`；相同 priority + 规范化条件命中不同模板 MUST 阻止发布。

#### Scenario: 未知变量阻止发布
- **WHEN** 模板含 `{{order_total}}` 或任意非白名单变量
- **THEN** publish 返回 validation issue，MUST NOT 保存为 published 或在运行时执行

#### Scenario: 缺失昵称使用配置 fallback
- **WHEN** 入站消息没有可读 user name 且模板使用 `{{user_name}}`
- **THEN** renderer 使用 published profile 的非空 fallback，MUST NOT 发送 `null`、空 raw ID 或未替换 token

### Requirement: AI role schema 与失败回退必须固定

模型 role ID SHALL 仅为 `reply_intent_classifier`、`reply_polisher`、`reply_risk_reviewer`；`reply_template_renderer` SHALL 是确定性程序而非 LLM。所有 role MUST 通过共享 JSON Schema 校验。classifier 失败 SHALL 产生 unknown/人工；polisher 失败 SHALL 回退原 rendered template；reviewer 失败 SHALL risk=unknown、禁止自动发送但保留人工审核。`meaningChanged=true` 或 `introducedClaims` 非空 MUST 禁止自动发送。

#### Scenario: Polisher 超时不生成空回复
- **WHEN** reply_polisher 超时或输出不符合 schema
- **THEN** job 保留 deterministic rendered text 并进入相应人工状态，MUST NOT 使用空串或编造 fallback

#### Scenario: AI 引入价格承诺禁止自动发送
- **WHEN** polished output 引入模板中不存在的价格/优惠 claim
- **THEN** introducedClaims 非空且 risk reviewer 禁止 auto，job 进入 approval_required

#### Scenario: DM AI 默认关闭
- **WHEN** 业务/合规尚未确认 DM 可发送给模型
- **THEN** DM 使用确定性模板并强制人工，MUST NOT 把 DM 正文发给 AI 供应商

### Requirement: 人工编辑必须重新评审且保留差异审计

客户编辑 final text SHALL 使用 CAS，保存 actor、before/after hash 与可展示差异，并重新运行确定性 gate 与 `reply_risk_reviewer`。编辑后原批准 MUST 失效，job 回到 `approval_required`；完整敏感正文 MUST NOT 写普通日志。

#### Scenario: 已批准文本被修改后不能沿用批准
- **WHEN** job 已 approved，操作者修改 final text
- **THEN** version 增加、批准清除、风险复核重跑并回 approval_required，旧 send 不可继续

### Requirement: 配置预览必须无副作用且逐步可解释

`POST /api/accounts/:accountId/reply-preview` SHALL 返回命中规则/理由、模板版本/渲染、润色前后、风险等级/原因和最终动作；预览 MUST NOT 创建真实 message/job/attempt、发送 WS 命令或调用平台写接口。预览输入/输出普通日志只记录 request/rule/template ID 与结果标签。

#### Scenario: 预览 auto-safe 不真实发送
- **WHEN** 模拟输入命中 low-risk auto-safe 规则
- **THEN** 响应可显示 `would_auto_send`，但数据库无真实 job/attempt 且 Edge 收不到 send 命令

### Requirement: 自动发送必须满足全部硬门禁

自动发送 SHALL 同时要求：有效 published config、runtime/global/account/channel write 开关、账号与 rule 白名单、mode=`auto_safe`、auth active、identity match、effective capability、text message、模板变量完整、job/version 唯一、无 active/ambiguous attempt、账号单飞/限速/登录冷却通过、Cloud RiskController 允许、risk=`low`、AI 未改义/引入 claim。任一条件未知或失败 MUST 降级 `approval_required` 或具名阻断，MUST NOT 自动发送。

#### Scenario: High-risk 标签强制人工
- **WHEN** classifier/reviewer 命中订单、退款、价格、促销、库存、发货、个人信息、投诉、法律、医疗、安全或未成年人风险
- **THEN** auto=false 且 job 进入 approval_required，普通管理员 MUST NOT 关闭平台级硬门禁

#### Scenario: 登录冷却未过不自动发送
- **WHEN** 账号刚重新登录且 published policy 的 new-login cooldown 未结束
- **THEN** 消息 MAY 继续同步/生成草稿，但 MUST NOT 自动排入发送
