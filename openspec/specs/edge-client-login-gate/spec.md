# edge-client-login-gate Specification

## Purpose
TBD - created by archiving change edge-client-customer-auth. Update Purpose after archive.
## Requirements
### Requirement: Startup login gate blocks cloud connect until authenticated

edge 客户端启动时 MUST 先恢复并校验客户会话。仍有效的客户令牌 SHALL 按既有续签与客户范围校验继续启动；令牌本地过期或被服务端明确拒绝时，客户端 MUST 读取当前 `userData` 下由 `safeStorage` 加密保存的最近成功 `name + key`，并在主进程内自动登录至多一次。只有现有令牌或该次自动登录建立有效会话后，客户端才 SHALL 继续正常启动。无可用加密凭据或自动登录失败时，客户端 MUST 显示登录门，且 MUST NOT 建立已认证主界面、MUST NOT 启动任何环境子进程、MUST NOT 循环自动重试。

#### Scenario: 有效令牌正常恢复

- **WHEN** 客户端启动且持有仍有效、通过既有续签与范围校验的客户令牌
- **THEN** 客户端继续正常启动，不额外提交保存的 `name + key`

#### Scenario: 无效令牌以保存凭据自动恢复

- **WHEN** 客户端启动时客户令牌已本地过期或被服务端明确拒绝，且当前实例存在可解密的最近成功 `name + key`
- **THEN** 客户端在主进程内自动调用 `/login` 至多一次
- **AND** 登录成功后保存新令牌、刷新该客户权威环境范围并进入主界面

#### Scenario: 无凭据时登录门保持 fail-closed

- **WHEN** 客户端启动时无有效客户令牌，且没有可用的加密登录凭据
- **THEN** 显示登录门，且不建立已认证主界面、不启动任何环境

#### Scenario: 自动登录失败不循环

- **WHEN** 启动自动登录因凭据拒绝、限流或网络错误失败
- **THEN** 客户端停止本次自动恢复并显示登录门
- **AND** 本次应用启动不得再次自动提交保存凭据

#### Scenario: 登录成功后正常启动

- **WHEN** 客户在登录门以正确 name+key 手动登录成功
- **THEN** 客户端保存令牌并进入主界面，按可见环境清单启动环境

### Requirement: Login view is the only new/redesigned surface

登录门 SHALL 是本次唯一新增/重做的界面,视觉为蓝灰简约风、与客户端现有浅色界面连续。其余现有界面(环境栏、主界面各功能区)MUST NOT 被重绘或改变结构。登录门 MUST 提供 name 与 key 两个输入(key 支持显隐切换)、明确的错误态文案(凭据错误 / 账户停用 / 网络错误)、以及无障碍与 `prefers-reduced-motion` 降级。

#### Scenario: 只改登录页

- **WHEN** 本变更落地后打开客户端各现有界面
- **THEN** 除新增的登录门外,其余界面的样式与结构保持与变更前一致

#### Scenario: 错误态给出可辨文案

- **WHEN** 登录因凭据错误 / 账户停用 / 网络故障而失败
- **THEN** 登录门显示对应的、面向客户的中文错误提示,而非静默或含糊报错

### Requirement: Token persistence and session lifecycle

登录成功的客户令牌 MUST 持久化于客户端 userData 目录(随 `AIDCP_USER_DATA_DIR` 多实例隔离)。客户端 SHALL 在令牌临近过期时静默续签；恢复已有会话启动时，若令牌将在首次定时维护前进入续签窗口，客户端 MUST 在主界面和环境启动流程继续前先尝试续签。登出或令牌失效时，客户端 MUST 停止所有环境并回到登录门，MUST NOT 因本地过期而静默跳过失效处理并保留已认证主界面。

#### Scenario: 恢复的会话临近过期

- **WHEN** 客户端启动时恢复到仍有效、但已进入续签窗口的客户令牌
- **THEN** 客户端在主界面和环境启动流程继续前请求静默续签
- **AND** 续签成功后持久化新令牌并继续正常启动

#### Scenario: 定时维护发现本地令牌已过期

- **WHEN** 客户鉴权已启用且定时维护发现本地客户令牌已经过期
- **THEN** 客户端执行既有会话失效流程、停止所有环境并回到登录门
- **AND** 客户端不得静默返回并保留已认证主界面

#### Scenario: 受保护请求发现本地令牌已过期

- **WHEN** 客户在两次定时维护之间发起受保护的客户内容请求且本地令牌已经过期
- **THEN** 客户端立即执行既有会话失效流程并回到登录门
- **AND** 请求如实返回会话已过期，不得只显示可重试的数据读取失败并保留陈旧主界面

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

### Requirement: Login credential prefill is local and clearable

登录成功后，客户端 SHALL 在当前实例的 `userData` 范围内保存账户名与访问密钥的加密副本，并在后续登录门打开时回填两个输入框或按启动恢复契约自动登录一次。访问密钥 MUST NOT 以明文写入本地存储、session 文件、日志、renderer、协议或云端；加密能力不可用时 MUST 不写明文回退且不阻断正常登录。客户令牌失效 SHALL 只清除 session 并保留加密凭据；客户显式退出或启动自动登录收到明确凭据拒绝时 MUST 清除 session 与加密凭据。

#### Scenario: 成功登录后下次自动恢复

- **WHEN** 客户使用有效账户名和访问密钥登录成功，随后在客户令牌无效时重新启动客户端
- **THEN** 主进程从当前实例的加密记忆读取凭据并按启动恢复契约自动登录一次
- **AND** 凭据明文不发送给 renderer、不写入日志

#### Scenario: 网络或限流失败保留回填

- **WHEN** 启动自动登录因网络错误或 429 限流失败
- **THEN** 客户端保留加密凭据并在登录门回填，供客户稍后手动重试

#### Scenario: 明确凭据拒绝清除记忆

- **WHEN** 启动自动登录收到 `/login` 的统一凭据拒绝
- **THEN** 客户端清除旧 session 与本地加密凭据，后续启动不得继续自动提交该旧 key

#### Scenario: 用户手动清空后不再回填

- **WHEN** 客户在登录页把账户名或访问密钥输入框清空
- **THEN** 客户端立即删除本地记忆，后续打开登录门不得回填旧凭据

#### Scenario: 退出登录清除凭据记忆

- **WHEN** 客户显式退出登录
- **THEN** 客户端清除本地令牌与凭据记忆，重新打开或再次启动时保持未登录

#### Scenario: 令牌失效保留加密凭据

- **WHEN** 短期客户令牌在运行期本地过期、续签被拒或受保护请求返回 401
- **THEN** 客户端停止环境并回到登录门，同时保留 `safeStorage` 加密凭据供手动登录或下次启动的一次自动恢复

