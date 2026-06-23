## ADDED Requirements

### Requirement: 提交失败可观测
发布执行端 SHALL 在 `submit_publish` 未在后置校验窗口内达成成功时，捕获并回报足以**定位根因**的页面状态，区分「按钮被遮挡 / 按钮禁用 / 已跳转但晚于窗口」三类。捕获 MUST 只含页面公开状态、不含任何密钥/令牌等敏感值。

#### Scenario: 点击未达成成功 → 留下可定位线索
- **WHEN** 发布按钮点击后未在后置校验窗口内出现真实成功信号
- **THEN** 执行端 SHALL 记录：解析出的点击中心坐标、命中的「发布」元素 tag/class 及 `disabled`/`aria-disabled`/`pointer-events`、`document.elementFromPoint(中心坐标)` 命中元素及其最近的 `[role=dialog]`/`[aria-modal]`、页面是否存在 `role=dialog`/`aria-modal`

#### Scenario: 超时时记录终态
- **WHEN** 后置校验窗口到期仍未成功
- **THEN** 执行端 SHALL 记录最终 `location.href` 与页面正文开头一段，用于区分「仍在编辑页有弹层」「错误/拦截 toast」「确认子框」或「晚到的真实成功跳转」

### Requirement: 提交失败双向诚实（不掩盖、不假成功）
发布执行端 SHALL 如实回报真实的 `submit_publish` 失败，且 MUST NOT 引入任何可能把**未真正发布**的帖子误报为成功的兜底——包括禁用态启发式、重试、放宽超时窗口、放松成功匹配条件。

#### Scenario: 未达真实成功 → 诚实失败
- **WHEN** 提交未达到真实成功信号
- **THEN** 执行端 SHALL 回报失败（如 `post_validate_failed`），且 MUST NOT 推断或伪造成功

#### Scenario: 不以弱条件冒充成功
- **WHEN** 执行端无法确认真实成功
- **THEN** 仅凭「URL 离开编辑页」这一弱条件 MUST NOT 被当作发布成功的证据

### Requirement: 硬必选元数据缺失判致命
云端发布指令编排 SHALL 把**硬必选**元数据步骤（可见范围）的失败判**致命**于本次发布，而非静默 best-effort 跳过后继续提交；并 SHALL 在提交失败上下文中带出被 best-effort 跳过的步骤数量/项。

#### Scenario: 硬必选步骤失败 → 整体诚实失败
- **WHEN** 一个硬必选元数据步骤（可见范围）失败
- **THEN** 编排 SHALL 诚实判本次发布失败，而非跳过它并继续去点提交按钮

#### Scenario: 提交失败上下文带跳过计数
- **WHEN** `submit_publish` 失败
- **THEN** `failedAt` 上下文 SHALL 包含本次 best-effort 跳过了多少（及哪些）元数据步骤

### Requirement: 成功判定锚定真实成功信号
发布后置校验 SHALL 仅依据**真实平台成功信号**（实测确认的成功 URL / 成功痕迹）判定成功；任何对等待窗口的延长 SHALL 有界且仍以真实成功信号为门，MUST NOT 退化为「默认成功」或无界重试。

#### Scenario: 平台拦截/报错未发布 → 不判成功
- **WHEN** 平台出现拦截/风控/错误提示且帖子未真正发布
- **THEN** 后置校验 MUST NOT 判为成功

#### Scenario: 晚到成功 → 有界等待、仍凭真实信号
- **WHEN** 真实成功晚于固定短窗口才到达
- **THEN** 任何延长等待 SHALL 有界，且仍以真实成功信号为判据（无无界重试、无默认成功）
