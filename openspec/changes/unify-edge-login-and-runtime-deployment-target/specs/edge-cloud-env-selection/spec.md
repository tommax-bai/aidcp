## MODIFIED Requirements

### Requirement: Cloud environment is selectable in the client login gate

边缘客户端 SHALL 在登录门提供 DEV 与 OL 两个部署目标并持久化唯一的 `deploymentTarget`。DEV/OL SHALL 由 Edge 主进程内同一目标目录同时解析 customer-auth `http(s)` API base 与 automation `ws(s)` URL；普通客户界面 MUST NOT 接受、保存或分别覆盖两个地址。自定义目标 MAY 仅在显式开发者门下以成对地址启用，并 MUST NOT 出现在客户登录选择器中。

#### Scenario: Customer selects an official deployment target

- **WHEN** 客户在登录门选择 DEV 或 OL 并提交登录
- **THEN** 客户端先持久化该目标，再使用同一目标目录中的数据 API 与 automation 地址
- **AND** 写盘失败时拒绝登录并如实提示目标未保存

#### Scenario: Ordinary login cannot split endpoints

- **WHEN** 普通客户打开登录门或主界面设置
- **THEN** 界面只提交 `dev | ol` 枚举，MUST NOT 提供独立 HTTP/WS URL 输入

### Requirement: Deployment target resolves every official Cloud endpoint

Electron 客户端 SHALL 以已持久化并通过登录验证的 `deploymentTarget` 解析 customer-auth 登录、续签、客户数据、环境归属以及 automation WebSocket。派生或重连自动化引擎时 SHALL 显式注入该目标目录中的 `AIDCP_CLOUD_URL`。构建元数据、持久化设置或启动环境中的独立绝对 URL MUST NOT 覆盖官方目标中的单个传输并制造混连。

#### Scenario: DEV login resolves both transports

- **WHEN** 登录门选择 DEV 且 DEV 登录与环境范围验证成功
- **THEN** 后续 customer-auth/data 请求与自动化引擎均使用 DEV 目标目录

#### Scenario: OL login resolves both transports

- **WHEN** 登录门选择 OL 且 OL 登录与环境范围验证成功
- **THEN** 后续 customer-auth/data 请求与自动化引擎均使用 OL 目标目录

#### Scenario: Legacy independent URL cannot override one transport

- **WHEN** 安装包仍含旧 `aidcpClientAuthUrl` 或外壳继承旧 `AIDCP_CLIENT_AUTH_URL`/`AIDCP_CLOUD_URL`
- **THEN** 官方 DEV/OL 会话忽略这些单传输覆盖并使用所选目标的成对目录

### Requirement: Switching deployment target requires a new authenticated session

已认证客户端 MUST NOT 通过保存设置或只重绑 automation WebSocket 来切换部署目标。切换 SHALL 停止旧目标自动化、清除旧目标客户会话与权威投影、返回登录门，并仅在新目标登录与环境范围刷新成功后建立新目标主界面。物理浏览器配置 MAY 保留，但 MUST NOT 在新目标授权前启动。

#### Scenario: Authenticated user requests a target switch

- **WHEN** 已登录客户选择切换部署环境
- **THEN** 客户端停止自动化并退出旧目标会话，返回登录门供客户选择新目标
- **AND** 不执行仅 WebSocket 重绑

#### Scenario: New-target login fails

- **WHEN** 客户选择新目标但登录、续签或环境范围刷新失败
- **THEN** 客户端停留在登录门且所有环境保持停止，MUST NOT 回用旧目标令牌或花名册授权

### Requirement: Current deployment target and automation receipt are visible and honest

登录门与已认证主界面 SHALL 显示当前选择/认证的部署目标。运行中的自动化 SHALL 独立显示核心已确认连接的目标；只有连接回执成功后才能标记实际 DEV/OL。等待浏览器槽位的活动文案 SHALL 命名已确认的 automation 目标，MUST NOT 把所选目标、数据请求成功或包默认值冒充自动化已连接。

#### Scenario: Authenticated target with stopped automation

- **WHEN** 客户已登录 OL 但自动化引擎未启动
- **THEN** 主界面显示认证目标 OL，并显示自动化未启动而不是已连接 OL

#### Scenario: Waiting slot after confirmed automation connection

- **WHEN** automation 核心已确认连接 DEV 且浏览器仍在等待槽位
- **THEN** 活动流显示“自动化通道已连接 DEV，等待浏览器槽位”

#### Scenario: OL is marked as production

- **WHEN** 登录选择、认证目标或 automation 实际目标为 OL
- **THEN** 对应标签醒目标注为正式/线上环境

### Requirement: Switching to OL requires confirmation

在登录门把持久化目标从 DEV 改为 OL 时，客户端 SHALL 明确提示将连接线上生产环境；未确认则保持原目标。首次安装默认预选 OL 时 SHALL 直接把“正式环境”含义显示在选择器与登录按钮上，不以隐藏默认代替告知。

#### Scenario: Existing DEV selection changes to OL

- **WHEN** 客户在登录门把已保存 DEV 目标切换为 OL
- **THEN** 客户端要求确认；确认后方可随登录提交保存，取消则保持 DEV

### Requirement: Authenticated deployment target controls Facebook automatic browse mode

Facebook 自动浏览模式 SHALL 以自动化引擎实际连接的官方目标为准，且该目标必须等于当前已认证 `deploymentTarget`。目标不一致、未知或连接未确认时 MUST NOT 启动 Facebook 自动浏览。浏览器是否打开与目标确认状态正交。

#### Scenario: Confirmed DEV engine uses DEV mode

- **WHEN** 客户已认证 DEV 且自动化引擎确认连接 DEV
- **THEN** 浏览器准备完成后的 Facebook 会话使用 DEV 模式

#### Scenario: Mismatch fails closed

- **WHEN** 已认证目标与自动化连接回执目标不一致或任一目标未知
- **THEN** 客户端停止自动浏览并显示目标不一致，MUST NOT 选择任一目标继续
