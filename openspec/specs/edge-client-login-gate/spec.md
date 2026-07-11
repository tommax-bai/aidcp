# edge-client-login-gate Specification

## Purpose
TBD - created by archiving change edge-client-customer-auth. Update Purpose after archive.
## Requirements
### Requirement: Startup login gate blocks cloud connect until authenticated

edge 客户端启动时 MUST 先检查是否持有效客户令牌。未持有效令牌时,客户端 MUST 显示登录门,且 MUST NOT 连接云端、MUST NOT 启动任何环境子进程。仅在登录成功后,客户端才 SHALL 继续正常启动(连云 + 按可见清单启动环境)。

#### Scenario: 未登录不连云不起环境

- **WHEN** 客户端启动且无有效令牌
- **THEN** 显示登录门,且不建立云端连接、不启动任何环境

#### Scenario: 登录成功后正常启动

- **WHEN** 客户在登录门以正确 name+key 登录成功
- **THEN** 客户端保存令牌并进入主界面,按可见环境清单启动环境

### Requirement: Login view is the only new/redesigned surface

登录门 SHALL 是本次唯一新增/重做的界面,视觉为蓝灰简约风、与客户端现有浅色界面连续。其余现有界面(环境栏、主界面各功能区)MUST NOT 被重绘或改变结构。登录门 MUST 提供 name 与 key 两个输入(key 支持显隐切换)、明确的错误态文案(凭据错误 / 账户停用 / 网络错误)、以及无障碍与 `prefers-reduced-motion` 降级。

#### Scenario: 只改登录页

- **WHEN** 本变更落地后打开客户端各现有界面
- **THEN** 除新增的登录门外,其余界面的样式与结构保持与变更前一致

#### Scenario: 错误态给出可辨文案

- **WHEN** 登录因凭据错误 / 账户停用 / 网络故障而失败
- **THEN** 登录门显示对应的、面向客户的中文错误提示,而非静默或含糊报错

### Requirement: Token persistence and session lifecycle

登录成功的客户令牌 MUST 持久化于客户端 userData 目录(随 `AIDCP_USER_DATA_DIR` 多实例隔离)。客户端 SHALL 在令牌临近过期时静默续签;登出或令牌失效时,客户端 MUST 停止所有环境并回到登录门。

#### Scenario: 登出回到登录门

- **WHEN** 客户在主界面点击登出
- **THEN** 客户端清除本地令牌、停止所有环境、回到登录门

#### Scenario: 令牌失效回到登录门

- **WHEN** 客户端携带的令牌被服务端判为失效(过期/撤销/客户被停用)
- **THEN** 客户端停止环境并回到登录门,提示需重新登录

### Requirement: Environment rail renders only the customer's environments

登录后,客户端 MUST 用客户令牌向云端取该客户的可见环境清单,并以"云端清单 ∩ 本地花名册"为准渲染环境栏与启动环境。不属于当前客户的环境 MUST NOT 显示、MUST NOT 启动。环境栏 MUST 保持既有视觉与结构,仅其数据范围按登录客户收窄。

#### Scenario: 只显示并启动本客户环境

- **WHEN** 客户 A 登录后客户端渲染环境栏
- **THEN** 仅显示归属 A 的环境;同机其他客户的环境不显示、不启动

#### Scenario: 环境栏零视觉改动

- **WHEN** 对比变更前后的环境栏
- **THEN** 其布局、样式、交互结构一致,仅显示的环境集合按客户不同而不同

### Requirement: Client-side environment creation attributes to the logged-in customer

在登录态下,客户端新建/添加环境时 MUST 以当前客户令牌向云端登记该环境的客户归属,使其立即进入该客户可见清单。客户端 MUST NOT 在未登录态下创建可见环境。

#### Scenario: 新建环境即时归属并可见

- **WHEN** 客户 A 在登录态下新建一个环境
- **THEN** 客户端向云端登记归属 A,该环境随即出现在 A 的环境栏

