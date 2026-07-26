## MODIFIED Requirements

### Requirement: Facebook 单建与批量建环境兼容六字段竖线账号记录

桌面外壳 SHALL 在 Facebook“单个新建”和“批量新建”共用的主进程账号解析入口中，通过可扩展的确定性规则同时接受既有 `email----password----2FA----cookie`、既有 `uid|password|cookie|access_token|email|timestamp` 与 `uid|password|2FA|email|cookie|access_token` 行格式；每个非空行 SHALL 独立运行适用规则，因此同批次 MUST 能混用受支持格式。解析器 MUST 仅在恰好一个规则完成必需字段与语义校验时接受该行；零个或多个规则通过时 MUST 按安全行号拒绝，不得按规则顺序猜测。

两种 UID 竖线格式 SHALL 使用 email 作为 AdsPower `username`、使用 password 与 Cookie；含 2FA 的格式 SHALL 仅把经 Base32 特征校验的 2FA 映射为 `fakey`，MUST NOT 把 Access Token 当作 `fakey`。UID、Access Token、timestamp 与其他无关字段 MUST NOT 进入解析后的创建计划、AdsPower 请求、设置、日志或 UI 回执。输入框 SHALL 明示自动识别的受支持格式以及 Token 不会导入或保存，不得宣称兼容任意未知格式。

两种竖线格式的 Cookie 区段 MAY 自身包含 `|`；各规则 SHALL 从记录两端定位其固定字段并完整保留中间 Cookie，MUST NOT 以简单固定段数切分导致 Cookie 截断。Cookie 中的 `c_user` 可读取时，解析器 SHALL 在任何 `user/create` 前校验其与 UID 一致；不一致、缺少必需字段、字段特征非法、边界非法、未知格式或歧义格式时 SHALL 仅以安全行号和字段原因拒绝。批量输入任一行失败时 SHALL 保持整批预校验语义，不创建任何环境，不回显原始凭据。

#### Scenario: 单个新建接受既有六字段导出记录且丢弃无关敏感字段
- **WHEN** 运维在 Facebook“单个新建”粘贴一条合法 `uid|password|cookie|access_token|email|timestamp` 记录，且 Cookie `c_user` 与 UID 一致
- **THEN** 主进程生成只含 email 登录名、password、规范化 Cookie 与既有 Facebook 配置的账号导入对象，创建请求不含 UID、Access Token、timestamp 或由 Access Token 映射的 `fakey`

#### Scenario: 自动识别 UID 密码 2FA 邮箱 Cookie Token 格式
- **WHEN** 运维粘贴一条合法 `uid|password|2FA|email|cookie|access_token` 记录，2FA 符合 Base32 特征且 Cookie `c_user` 与 UID 一致
- **THEN** 主进程将 email、password、2FA 与完整 Cookie 分别映射为 `username`、`password`、`fakey` 与规范化 Cookie，并丢弃 UID 与 Access Token

#### Scenario: 批量新建混用三种受支持格式
- **WHEN** Facebook 批量输入同时包含合法四字段行、既有六字段竖线行与含 2FA 的六字段竖线行
- **THEN** 主进程在第一条 `user/create` 前完成全部行的唯一规则识别，按原顺序形成创建计划，并沿用相同模板、代理、串行创建和回执规则

#### Scenario: Cookie 内嵌竖线不破坏任一竖线规则边界
- **WHEN** 任一受支持竖线记录的 Cookie 值包含一个或多个 `|`
- **THEN** 对应规则从两端定位固定字段并完整保留 Cookie，且不会把 Cookie 片段、Access Token、时间戳或 2FA 互相错配

#### Scenario: UID 与 Cookie 身份错配时安全拒绝整批
- **WHEN** 单条或批量任一 UID 记录的 UID 与可读取 Cookie `c_user` 不一致
- **THEN** 主进程在任何 `user/create` 前按安全行号拒绝，错误、日志与 UI 不包含 UID、密码、2FA、Cookie、Access Token 或邮箱原文

#### Scenario: 未知或歧义格式失败关闭
- **WHEN** 一行账号资料没有任何规则通过，或有多个规则同时通过
- **THEN** 主进程按安全行号拒绝整批且不创建环境，不猜测密码或其他敏感字段的角色
