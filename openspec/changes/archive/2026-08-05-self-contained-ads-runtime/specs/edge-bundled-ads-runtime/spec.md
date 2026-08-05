# edge-bundled-ads-runtime Specification

## ADDED Requirements

### Requirement: 托管运行时使用可写暂存副本和内容身份

在 `edge-desktop-packaging` 已提供随包 AdsPower CLI 模板的前提下，桌面外壳 SHALL 在使用前把模板暂存到 application `userData`。暂存身份 SHALL 同时包含应用版本、AdsPower CLI 包版本和模板内容身份。身份未变化 SHALL 复用现有副本；身份变化 SHALL 先复制候选、经 CLI 合同有界停止已登记 daemon、再原子替换。复制、停止或替换失败 SHALL 返回真实错误并保留或恢复上一副本，MUST NOT 继续使用身份不匹配的旧运行时。

#### Scenario: 模板内容变化

- **WHEN** 新安装包中的模板内容身份与已暂存副本不同
- **THEN** 桌面外壳停止已登记 daemon、原子换入新副本并记录新身份
- **AND** 任一步失败时保留可恢复副本并停止启动

### Requirement: 托管 CLI 是服务生命周期和 base 的唯一权威

桌面外壳 SHALL 经随包 CLI 的 status/start/stop 合同管理本会话运行时。每个 Electron 会话第一次成功建立前 SHALL 至多一次有界重置 CLI 自身登记的旧 daemon，再以当前密钥启动托管 daemon。CLI 实际上报的 LocalAPI base SHALL 覆盖表单和 settings base，供主进程和核心子进程共同使用。

运行时建立 MUST NOT 通过任意 HTTP 应答方接管外部 AdsPower 桌面服务。运行时缺失、启动失败或端口冲突无法由托管 CLI 解决时 SHALL 明确失败。应用退出 SHALL 先有界停止核心/浏览器，再停止本会话管理的 CLI daemon。

#### Scenario: 托管运行时成功建立

- **WHEN** 首个需要 LocalAPI 的操作到达
- **THEN** 桌面外壳暂存运行时、执行本会话至多一次的登记 daemon 重置、启动托管 CLI，并采用其上报 base

#### Scenario: 外部服务或端口冲突

- **WHEN** 独立 AdsPower 桌面服务造成托管 CLI 无法建立
- **THEN** 客户端报告冲突/启动失败并停止
- **AND** 客户端不因一个可连接端口而接管外部服务或宣称托管运行时已就绪

### Requirement: 服务确保与内核确保分离

服务确保 SHALL 为 settle 后清除的全局 single-flight；内核确保 SHALL 按内核版本 single-flight。环境创建、代理、删除、状态和对账只需要服务，不得下载内核；启动浏览器前才确保该 profile 所需内核。任何确保失败 SHALL 阻止后续动作并返回真实失败。

#### Scenario: 多环境并发需要同一内核

- **WHEN** 多个环境并发启动且需要同一内核版本
- **THEN** 它们共享一次该版本的内核确保
- **AND** 不同版本不会共享或覆盖彼此的确保结果

### Requirement: 已安装内核先由本地可执行文件证明

浏览器启动前，客户端 SHALL 先检查目标版本的平台可执行文件。该文件只有在非空、为普通文件且 POSIX 下可执行时才证明内核已安装；证明成功时 MUST NOT 查询云端目录。证明失败时才允许有界查询 `get-kernel-list` 并按需下载。网络、限流、空列表、异常响应和 CLI 失败 SHALL 返回安全分类，原始供应商输出或凭据 MUST NOT 进入 renderer 日志。

#### Scenario: 云端目录不可达但本地内核有效

- **WHEN** 固定版本的本地可执行文件证明成功且云端目录不可达
- **THEN** 客户端跳过目录查询并继续 V2 browser start

#### Scenario: 本地内核无效且目录不可达

- **WHEN** 本地证明失败且目录查询在有界重试后失败
- **THEN** 客户端停止启动并返回安全、可操作的失败原因

### Requirement: 浏览器生命周期使用 V2 并严格接管失联浏览器

核心 provider 与 Electron 检查/对账 SHALL 使用 V2 per-profile `active`、`start` 和 `stop`。V2 报告 `Inactive` 时，客户端只可检查该 profile 的缓存目录，并仅在 `DevToolsActivePort` 端口和 browser path 与 loopback `/json/version` 的 `webSocketDebuggerUrl` 完全一致时接管；否则 SHALL 调用 V2 `start`。停止后 SHALL 保留 CDP-dark 确认，未确认关闭不得报告成功。

#### Scenario: 精确匹配的 registry-lost browser

- **WHEN** V2 报告 `Inactive`，但 profile-scoped 缓存与 loopback `/json/version` 的端口和 browser path 完全一致
- **THEN** 客户端接管该浏览器且不重复 start

#### Scenario: 缓存候选不匹配

- **WHEN** 缓存缺失、地址非 loopback、端口不可达或 browser path 不一致
- **THEN** 客户端拒绝接管并走 V2 start

### Requirement: API key 使用单一解析器

运行时启动、主进程 LocalAPI 调用和核心子进程 SHALL 使用同一 key 解析次序：当前表单值、settings、`AIDCP_ADS_API_KEY`、随包数据。密钥完全缺失 SHALL 阻止运行时启动。密钥或原始供应商诊断 MUST NOT 写入 renderer 日志。

#### Scenario: 没有本机覆盖值

- **WHEN** 表单、settings 和环境变量都没有 key，但随包数据提供有效 key
- **THEN** 运行时、主进程和核心子进程使用该 key，且不要求运营输入

### Requirement: 运行状态按可解析时间单调前进

renderer 收到同一环境的 `status:update` 与 IPC 返回快照时，SHALL 拒绝 `updatedAt` 早于当前状态的快照。缺少或无法解析时间戳的旧形状 SHALL 保持兼容。

#### Scenario: 旧排队快照晚到

- **WHEN** 新运行时进度已上屏，随后到达时间更早的排队快照
- **THEN** renderer 忽略旧快照，不回放较早状态或重复记录其消息

### Requirement: Windows 开发 staging 使用当前 Node 工具链

Windows 开发 checkout 执行 `build:ads-runtime` 时 SHALL 通过当前 build-time Node 调用 npm CLI，MUST NOT 直接 spawn `npm.cmd`。Electron 开发 SHALL 优先解析已 stage 的补丁运行时，并继续用 `process.execPath` 加 `ELECTRON_RUN_AS_NODE=1` 执行 CLI。

#### Scenario: Node 24 在 Windows stage 运行时

- **WHEN** 开发者在 Windows Node 24 下运行 `build:ads-runtime`
- **THEN** staging 不出现 `spawnSync npm.cmd EINVAL`，并产出可由 Electron Node 执行的 CLI 入口
