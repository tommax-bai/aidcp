## ADDED Requirements

### Requirement: Facebook 单建与批量建环境兼容六字段竖线账号记录

桌面外壳 SHALL 在 Facebook“单个新建”和“批量新建”共用的主进程账号解析入口中，同时接受既有 `email----password----2FA----cookie` 与 `uid|password|cookie|access_token|email|timestamp` 行格式；每个非空行 SHALL 独立识别格式，因此同批次 MAY 混用两种格式。六字段格式 SHALL 使用 email 作为 AdsPower `username`、使用 password 与 cookie，并 MUST NOT 把 access token 当作 `fakey`。UID、access token 与 timestamp MUST NOT 进入解析后的创建计划、AdsPower 请求、设置、日志或 UI 回执。输入框 SHALL 明示两种受支持格式。

六字段格式的 Cookie 区段 MAY 自身包含 `|`；解析器 SHALL 从记录两端定位固定字段并完整保留中间 Cookie，MUST NOT 以简单固定六段切分导致 Cookie 截断。当 Cookie 中的 `c_user` 可读取时，解析器 SHALL 在任何 `user/create` 前校验其与首字段 UID 一致；不一致、缺少必需的 UID/email/password/cookie、或字段边界非法时 SHALL 仅以安全行号和字段原因拒绝。批量输入任一行失败时 SHALL 保持既有整批预校验语义，不创建任何环境，不回显原始凭据。

#### Scenario: 单个新建接受六字段导出记录且丢弃无关敏感字段
- **WHEN** 运维在 Facebook“单个新建”粘贴一条合法 `uid|password|cookie|access_token|email|timestamp` 记录，且 Cookie `c_user` 与 UID 一致
- **THEN** 主进程生成只含 email 登录名、password、规范化 Cookie 与既有 Facebook 配置的账号导入对象，创建请求不含 UID、access token、timestamp 或由 access token 映射的 `fakey`

#### Scenario: 批量新建兼容两种格式且仍整批预校验
- **WHEN** 运维在 Facebook“批量新建”中同时粘贴合法旧格式行与合法六字段竖线行
- **THEN** 主进程在第一条 `user/create` 前完成全部行解析，按原顺序形成创建计划，两种行后续沿用相同模板、代理、串行创建和回执规则

#### Scenario: Cookie 内嵌竖线不破坏六字段边界
- **WHEN** 六字段记录的 Cookie 某个值包含一个或多个 `|`
- **THEN** 解析器完整保留 Cookie 内容，并仍从右侧正确识别 access token、email 与 timestamp

#### Scenario: UID 与 Cookie 身份错配时安全拒绝整批
- **WHEN** 单条或批量任一六字段记录的首字段 UID 与可读取的 Cookie `c_user` 不一致
- **THEN** 主进程在任何 `user/create` 前按安全行号拒绝，错误、日志与 UI 不包含 UID、密码、Cookie、access token 或邮箱原文
