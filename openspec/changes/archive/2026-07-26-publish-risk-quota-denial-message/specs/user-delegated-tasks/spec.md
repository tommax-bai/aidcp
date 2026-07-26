## MODIFIED Requirements

### Requirement: 批量和异步委托必须遵守自动化风险额度并保留人审

**操作员主动单次指令** SHALL 以操作员全权执行——越过发布／评论前的风控 status、`canDo` 与配额闸，但**发布前／评论前的人审 MUST 仍强制**（越权只越风控／配额，绝不越人审）。操作员主动单次指令仅包含以下服务端可信形状：

1. 精确 slash 命令：`source=legacy_command` 且 `targetConstraints.manualSingle=true`（含 `/publish` 与 `/comment`）；
2. Console 或 Edge 精选内容页中，用户在单条已校验精选图文上明确点击“洗稿”后，由专用服务端入口创建的 `source=operator_action` 单篇 `publish_post` 任务。

第二类来源 MUST 只能由专用精选洗稿服务端入口写入，通用 Edge／Console／API 建任务请求 MUST NOT 自报或伪造 `operator_action`。executor 对第二类还 MUST 校验单篇目标与已冻结的精选参照快照，形状不符时 MUST NOT 置 `operatorOverride`。

人工洗稿的“不受配额限制”只改变发布前放行：若平台最终确认发布成功，系统 MUST 与其它真实发布一样记录该账号的 `publish` 配额计数；未真实发布、仅排队、生成候选或等待人审 MUST NOT 提前计数。该事实计数 MUST NOT 反向触发风控威胁态升级。

`targetSuccessCount>1`、跨账号、自然语言（`source=feishu`）、通用结构化（`source ∈ {edge,console,api}`）委托、自动排期与后台自动创作 MUST 使用自动化额度与风险闸（`governed`），MUST NOT 置 `operatorOverride`／为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控配置明确允许其他模式。

#### Scenario: 批量评论不能循环绕额度

- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险／配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

#### Scenario: 精确 /publish 在风控受限账号仍以操作员全权执行

- **WHEN** 管理群对一个风控非 normal 或当天已达发布配额的账号发送 `/publish <昵称>`（`source=legacy_command`、`manualSingle`）
- **THEN** 系统越过风控 status／canDo 与配额生成草稿并发出发布人审卡（`operatorOverride=true`）
- **AND** MUST NOT 因风控／配额把该精确命令 blocked→deferred→静默判失败
- **AND** 发布前人审 MUST 仍强制，越权 MUST NOT 越过人审

#### Scenario: 人工精选洗稿越过配额但保留人审和真实计数

- **WHEN** 操作员在 Console 或 Edge 精选内容页对一条已校验图文明确点击“洗稿”，该账号发布配额已满或上限为 0
- **THEN** 专用服务端入口创建 `source=operator_action` 的单篇必审任务，executor 以 `operatorOverride=true` 进入候选生成与发布人审
- **AND** 仅排队、生成候选或等待人审时 MUST NOT 记录 publish 计数
- **AND** 平台确认真实发布成功后 MUST 记录一次 publish 计数，即使该动作发布前已处于配额外

#### Scenario: 通用结构化请求不能伪造人工洗稿权限

- **WHEN** 通用 Edge／Console／API 建任务请求提交 `operator_action`、人工标记或仿造精选字段
- **THEN** 服务端 MUST 将其收口为既有普通来源或拒绝，executor MUST 走 governed 路径
- **AND** MUST NOT 因客户端自报字段置 `operatorOverride`

#### Scenario: 自然语言与普通结构化发帖不得越风控

- **WHEN** 委托发帖来自自然语言（`source=feishu`）或非专用人工洗稿的结构化入口（edge／console／api）
- **THEN** 系统走 `governed` 路径，风控非 normal／canDo 拒时诚实 blocked
- **AND** MUST NOT 置 `operatorOverride`

## ADDED Requirements

### Requirement: 委托发帖的风控拒绝必须分别展示状态、档位和真实原因

governed 委托发帖在平台动作开始前被风控或配额闸拒绝时，系统 MUST 在已持久化 attempt reason 与用户可见终态回执中分别给出：风控状态 `status`、生效配额档位 `quotaLevel` 与实际拒绝原因。状态和档位 MUST 同时展示稳定英文值及可读中文含义，MUST NOT 再以“风控拒绝（状态 normal）”代替配额原因。

配额拒绝还 MUST 给出命中的 `minute`／`hour`／`day` 窗口、该窗口已用量与生效上限，且这些值 MUST 与同一次 `RiskController.explain()` 判定同源。非 normal 威胁态拒绝 MUST 明确是状态闸，不得伪装成额度已满。未知或历史旧原因 MUST 兼容读取并诚实透传，MUST NOT 猜测补全。

#### Scenario: normal 状态因保守档发布上限为 0 被拒绝

- **WHEN** governed 发帖账号的风控状态为 `normal`、配额档位为 `conservative`，分钟发布已用量为 0 且生效上限为 0
- **THEN** attempt reason SHALL 结构化携带 `status=normal`、`tier=conservative`、`cause=quota:minute`、`used=0`、`limit=0`
- **AND** 用户提示 SHALL 明确表达“风控状态 normal（正常）”“配额档位 conservative（保守）”以及“分钟发布配额 0/0，已达到上限”
- **AND** MUST NOT 只显示“状态 normal”或暗示账号处于平台威胁态

#### Scenario: 非 normal 状态明确显示状态闸与档位

- **WHEN** governed 发帖因 `warned`／`restricted`／`frozen` 状态在配额检查前被拒绝
- **THEN** 用户提示 SHALL 同时显示该风控状态及中文含义、当前配额档位及中文含义
- **AND** SHALL 明确说明本次由风控状态闸暂停发帖，MUST NOT 编造成某个配额窗口已满

#### Scenario: 历史旧原因仍可读

- **WHEN** 终态组装读取到部署前持久化的 `risk_status(<status>)` 或 `risk_denied(status=<status>)`
- **THEN** 系统 SHALL 沿用兼容人话化或原样透传
- **AND** MUST NOT 因缺少档位／窗口字段而抛错、丢失终态卡或虚构字段
