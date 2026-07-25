## Context

`aidcp-edge` 目前是一个 Electron 应用仓库，但内部同时存在四种不同变化节奏：

1. Classic 产品层：窗口、renderer、客户登录、普通数据访问、环境管理、托盘、通知和更新；
2. Host 控制层：环境 roster 投影、每环境进程监督、生命周期、状态聚合、人工介入和本机资源管理；
3. Edge 执行层：Cloud 自动化命令、Edge Core、平台驱动、CDP / API 执行和结果回执；
4. 发行组装层：预编译产物、ASAR、Native Page Engine、AdsPower CLI 资源、签名和安装包。

当前 Classic 既是产品客户端，又直接知道 Core 入口、子进程环境变量、运行时路径和 stdout
状态解析。这一结构在只有一个客户端时可工作，但会产生两个问题：

- UI 或客户数据面的改动与执行引擎改动必须同仓发布；
- 未来客户端无法复用 Edge，而不复制 Classic 主进程代码或直接获得页面原子动作入口。

Cloud 正在拆分 Data、Automation 和 Creation 服务。本 change 不改变该拆分：Edge Host 只承接本机
执行边界，Cloud Automation 仍负责策略、流程编排、持久化、主要节奏和平台动作授权。

约束如下：

- 当前唯一产品客户端仍是 Classic；本阶段不实现 Agent Client。
- 目标机不得依赖 Node、npm、tsx 或 TypeScript。
- macOS `x64` / `arm64` 与 Windows 安装包能力必须保留。
- Core、Native、AdsPower runtime 和 native modules 的 Resources / ASAR / 签名边界必须可验证。
- 客户普通数据面与 Cloud↔Edge 自动化连接继续分离。
- 现有行为以 `separate-client-data-plane-automation-engine` 为准：客户登录不启动自动化引擎；
  用户启动/恢复自动化时启动引擎并准备浏览器，暂停/关闭释放当前约定的执行资源。
- AdsPower CLI 已被定义为机器级共享 daemon，而当前主进程与 Core 的 Local API 限频队列仅在各自
  进程内有效；拆分后多个 Host 必须补上跨进程协调，不能只保护单个 profile。
- Host event 只表达本机运行事实；Cloud durable automation 状态、平台确认结果和客户可见业务数据
  仍须通过权威 Cloud API 读取，事件只能触发推进或 refetch。
- 源码迁移、开发态运行、安装包运行和真实账号结果是四种不同证据，不能互相替代。

## Goals / Non-Goals

**Goals:**

- 最终形成两个独立、可单独检出、测试、版本化和发布的业务仓库：
  `aidcp-classic-client` 与 `aidcp-edge-host`。
- 将 Edge Host 固化为无产品 UI 依赖的可嵌入包，Classic 成为它的第一个消费者。
- 让 Host 统一拥有 Core、浏览器执行器、环境监督和本机排他资源，客户端只依赖稳定控制面合同。
- 让 Host 通过 MachineRuntimeCoordinator 安全复用机器级 AdsPower daemon，包括跨进程 runtime
  初始化、版本兼容、全局 Local API 限频与每 profile 排他。
- 让登录挑战、页面身份不匹配等人工介入形成 Core→Host event→Classic 呈现→Core 复核的闭环。
- 通过不可变版本、资源 manifest 和契约测试消除跨仓隐式耦合。
- 在不改变用户可见 Classic 行为和 Cloud 自动化语义的前提下完成迁移。
- 为未来其他客户端预留复用边界，但不为尚未出现的 Agent Client 设计额外协议或 daemon。

**Non-Goals:**

- 不创建或实现 `aidcp-agent-client`。
- 不把 Edge Host 做成开机自启、机器全局常驻或可远程访问的网络服务。
- 不允许客户端直接调用搜索、浏览、点赞、评论、发布等平台原子动作。
- 不改变 Cloud Automation 的策略、工作流、风险状态或 durable work 模型。
- 不在本 change 中创建 `persona.updated` 等新触发器、AutomationDefinition 或新的 Cloud 自动化状态机；
  只明确引擎停止时 Cloud work 不能被本地假装执行，未来触发流程必须在独立 change 中定义等待 Edge
  和唤醒策略。
- 不改变 protocol v2 的业务语义；仓库重命名引起的引用更新除外。
- 不在本 change 中重新设计 Classic UI、客户鉴权、环境领域模型或自动更新产品策略。
- 不以源码测试代替签名、公证、安装和目标机 smoke test。

## Decisions

### 1. 最终仓库拓扑为两个仓库，现有 `aidcp-edge` 不成为第三个长期仓库

最终职责如下：

| 仓库 | 拥有 | 不拥有 |
| --- | --- | --- |
| `aidcp-classic-client` | Electron shell/renderer、客户登录与普通数据、环境 UI、托盘/通知、更新、最终安装包 | Core、平台驱动、Cloud 自动化命令实现、浏览器/CDP 原子动作 |
| `aidcp-edge-host` | Host package、环境监督器、Core、Native Page Engine、平台驱动、AdsPower runtime 适配、Cloud↔Edge 执行协议 | Classic renderer、产品导航、客户内容工作区、最终桌面安装包 |

现有 `aidcp-edge` 远端保留完整历史并迁移/重命名为 `aidcp-edge-host`。新的
`aidcp-classic-client` 以明确的 `split-base` commit 为来源导入相关历史。迁移后不维护一个
同时包含两者的兼容仓库；Git hosting 的仓库重命名 redirect 只用于迁移已有 clone，不构成运行时
兼容层。

**为何不是三个仓库：** 再拆一个 Edge Core 仓库会立即增加 Host↔Core 的第二套发布合同，而当前
Core 只通过 Host 被本机客户端使用。先把 Host 与 Core 保持同仓，可以稳定客户端边界；只有出现
独立部署、语言边界或明显不同发布节奏时，才重新评估 Core 仓库。

**为何不是 monorepo workspace：** 用户要求两个仓库独立发布；workspace 会继续让 Classic 与
Host 共享提交和依赖解析，无法证明独立版本合同。

### 2. Edge Host 是嵌入式包，不是 localhost daemon

`aidcp-edge-host` 发行 `@aidcp/edge-host`。Classic 在 Electron main 的 Node 上下文中创建一个
Host controller；Host 再监督每环境 Core 子进程和浏览器执行器。仓库拆分只迁移 ownership，不修改
现有生命周期：登录/roster reconcile 不启动引擎；`start` / `resume` 启动引擎并按当前合同准备浏览器；
`pause` / `close` 按当前合同停止引擎并释放浏览器资源。未来把浏览器改成真正按 page task 获取，必须
另建行为 change。

```text
aidcp-classic-client
├── renderer / product UI
├── customer-auth HTTP / local secure storage
├── Electron main adapter
└── @aidcp/edge-host
    ├── Host controller
    ├── environment supervisor
    ├── Edge Core worker(s)
    ├── browser / API executors
    └── Native + AdsPower runtime resources
```

Host 与 Classic 在同一主进程内使用 typed API；renderer 仍只经 Classic 定义的 Electron IPC
访问主进程。Host 不监听 TCP 端口，也不持有对外可达的本机 API。

**为何不先做 daemon：** 当前只有一个消费者。daemon 会提前引入安装、升级、服务发现、本机鉴权、
多用户会话和版本仲裁，而这些问题不是本次拆分的必要条件。

### 3. Host API 只提供控制面，不提供平台动作面

首版公开合同包含以下概念性能力，最终类型以导出的 TypeScript 声明为准：

```ts
interface EdgeHost {
  reconcileEnvironments(input: LocalEnvironmentDescriptor[]): Promise<ReconcileResult>;
  getSnapshot(envId?: string): HostSnapshot;
  start(envId: string): Promise<LifecycleResult>;
  pause(envId: string): Promise<LifecycleResult>;
  resume(envId: string): Promise<LifecycleResult>;
  close(envId: string): Promise<LifecycleResult>;
  presentHumanAssist(requestId: string): Promise<HumanAssistResult>;
  completeHumanAssist(requestId: string): Promise<HumanAssistResult>;
  subscribe(listener: (event: HostEvent) => void): () => void;
  shutdown(): Promise<ShutdownResult>;
}
```

创建 Host 时由 Classic 注入：

- 唯一 `clientInstanceId`；
- Host 机器级数据根目录与 Classic 实例级数据目录；
- 安装包真实 `resourceRoot`；
- Cloud target 与受限 credential provider；
- structured logger、notification bridge 和 clock 等明确 adapter。

事件至少携带 `clientInstanceId`、`envId`、单调 generation、事件类型、时间和结构化状态。需要人工
介入时，Core SHALL 通过 Host 发出带 `requestId/envId/generation/reason` 及可选
`automationRunId/stepId` 的 `human_assist_required`。Classic 只能据此呈现浏览器并回传
`present/complete`；用户声明“处理完成”后仍由 Core 重读真实页面身份，Classic 不得自行恢复命令。
Classic 不得通过解析 Core stdout 推断产品状态；stdout/stderr 只保留为诊断证据。

公开合同不得出现 `like()`、`comment()`、`publish()`、`search()`、`click()` 或 `input()`。
平台动作继续由 Cloud Automation 经 protocol v2 下发，经过现有身份、风控、审批和结果验证后由
Core 执行。

**为何不暴露统一 execute(command)：** 它会把内部协议和页面原子能力变成客户端 API，使任一 UI
可以绕过 Cloud 授权和可审计工作流。

### 4. Host 拥有运行时状态，Classic 拥有产品状态

Host 拥有：

- Core / browser executor 句柄和生命周期；
- 每环境运行时 snapshot、结构化活动事件和错误；
- AdsPower 本地 API 限速队列与机器资源排他；
- 临时执行文件、runtime 下载目录和 Core 日志；
- Cloud 自动化连接与命令处理。

Classic 拥有：

- customer token 的加密本地保存与普通 customer-auth HTTP；
- 客户可见的环境 roster、名称、排序和 UI 偏好；
- 窗口、托盘、通知、导航和更新；
- 将 Host snapshot 投影为用户可见状态，以及错误到文案的映射。

Classic 向 Host 提供冻结后的 `LocalEnvironmentDescriptor`，Host 不自行读取 Classic renderer
store。Host 返回事实状态和具名错误，不返回“成功”式 UI 文案。

Cloud Automation 拥有 durable run、step、等待原因、取消、平台提交未知和平台确认结果。Classic
如需展示这些业务状态 SHALL 经 customer-auth API 读取权威记录；Host event 只更新本机
`automation=stopped|starting|ready|running|paused|error`、浏览器和人工介入事实，并 MAY 触发一次
有界 refetch，MUST NOT 直接改写 Cloud 业务真相。

### 5. LocalEnvironmentDescriptor 不是授权事实

`LocalEnvironmentDescriptor` 只允许携带 Classic main 从客户可见 roster 与本机 provider 得到的
`envKey/provider/profileId`、展示信息和本机资源选择。renderer 自报或 descriptor 中出现的
`accountId/customerId/riskState/permission/executionTarget` MUST NOT 被 Host 当作权威事实。

客户环境归属和账号绑定继续由 customer-auth / automation handshake 逐次验证；durable work 的
`executionTarget` 继续由 Cloud 冻结；页面任务继续在执行前读取真实页面身份。Host SHALL 把
Cloud 返回的绑定冲突、授权拒绝和页面身份不匹配投影为具名事实错误，MUST NOT 通过本地 descriptor
改写或绕过。

**为何不在本 change 新增签名 launch grant：** 现有 Cloud handshake 已是执行准入真源。仓库拆分
只把“不信任本地输入”写入 Host 合同；只有现有握手无法覆盖新消费者时，才以独立 protocol change
引入新凭证。

### 6. Cloud work 与本机自动化可用性是两个状态域

Host 不拥有 Cloud durable automation 状态。登录/roster reconcile 后自动化保持 `stopped`；此时
Cloud MAY 已存在被用户或未来 trigger 创建的待执行 work，但本 change 不允许 Cloud 远程唤醒已退出
Classic，也不允许 Classic 把该 work 显示为正在执行或成功。

未来 Automation change 若引入 `persona.updated` 等触发流程，应把引擎未连接的 run 持久化为具名
`waiting_for_edge`，在用户启动/恢复自动化且 Core 完成权威 handshake 后再继续。该状态和
AutomationDefinition 不在本拆仓 change 中实现；本 change 只要求 Host/Classic 不破坏或伪造这条
边界。

### 7. MachineRuntimeCoordinator 统一机器级资源，profile lease 只是一层

不同 `AIDCP_USER_DATA_DIR` 的 Classic 实例仍可并存。由于 AdsPower CLI 是机器级共享 daemon，而
每个 Host 进程内的 `1.1s` 队列不能互相协调，Host SHALL 提供使用跨进程原子原语的
MachineRuntimeCoordinator，至少管理：

1. `runtime-init`：跨 Host 串行 stage/status/start，避免并发初始化同一个 daemon；
2. `runtime-version`：校验正在运行的 AdsPower runtime/protocol 与本 Host manifest 兼容；有活跃
   owner 时不得停止或替换不兼容 daemon，具名失败 `ads_runtime_version_conflict`；
3. `ads-api-rate-gate`：所有 Host 共享 Local API 最小调用间隔，不能各用一条进程内队列；
4. `profile:<provider>:<physicalId>`：在启动 Core、浏览器或 profile 生命周期动作前取得物理环境
   排他租约。

profile 租约键优先使用不可变物理执行身份，例如 `provider=adspower + adsUserId`；不得仅使用客户端
内可重命名展示名、Cloud target 或局部 envId。该租约跨 Classic userData 生效，且不因连接 dev 或
ol 而允许同一物理分身被双重占用。

所有协调均须使用跨进程原子排他原语。owner metadata 只用于诊断，至少包含随机
`clientInstanceId`、PID、启动时间、Host/runtime version 和非敏感产品标识；不得只凭 PID 文件或
超时时间静默接管。进程死亡后由 OS 锁语义释放，或在同时证明原 owner 已死亡后有界清理。

同一 Host owner 对相同环境重复 `start` 应返回当前状态或同一在途结果；不同 owner 冲突返回
`environment_in_use`，不启动 Core、不触碰浏览器。正常 `close` / `shutdown` 先停止自己拥有的环境
资源，再释放自己的 profile lease；Host 退出不得停止仍被其他 Host 使用的机器级 AdsPower daemon。

**为何不建立新的 Edge Host daemon：** MachineRuntimeCoordinator 只提供跨进程原子锁、共享限频
事实和 owner metadata；Host 仍嵌入各客户端、不监听网络端口。机器级常驻进程仍只有既有 AdsPower
CLI。若未来证明文件锁/OS mutex 无法安全表达协调，再以独立 change 评估本机 broker。

### 8. Host 以一个不可变 release unit 发布，Classic 精确锁定

Host release 至少包含：

- 编译后的 `@aidcp/edge-host` JavaScript 与 `.d.ts`；
- 编译后的 Core entry；
- Native Page Engine 与 AdsPower runtime 所需的受支持平台资源；
- `edge-host-manifest.json`。

manifest 至少记录：

```json
{
  "hostVersion": "x.y.z",
  "gitSha": "<commit>",
  "hostApiMajor": 1,
  "protocolVersion": 2,
  "runtimeFormatVersion": 1,
  "electronMajor": 37,
  "nodeModulesAbi": "<abi>",
  "adsRuntimeVersion": "2.1.0",
  "adsRuntimeProtocolVersion": 2,
  "platforms": ["darwin-arm64", "darwin-x64", "win32-x64"],
  "assets": [{"path": "...", "sha256": "..."}]
}
```

开发集成可使用由 Host 仓库当前 commit 执行 `npm pack` 产生的 tarball。正式构建从批准的私有 npm
registry 获取不可变版本。Classic 的 `package.json` 和 lockfile 必须锁定精确版本，不使用
`^`、`~`、branch、workspace symlink 或运行时 latest 解析。

Classic 构建和启动均校验代码版本、manifest、Electron major、Node modules ABI、runtime format、
AdsPower runtime/protocol compatibility、平台/架构与资源 hash。任一不一致均具名失败为
`edge_host_artifact_mismatch`，不得退回旧资源、联网取源码或继续伪运行。

Host 的“独立版本”是仓库和构建输入的版本边界，不表示已安装 Host 可以绕过 Classic installer
自行热更新。客户机器上的 Host/Core/Native/AdsPower template 版本由当前 Classic 安装包固定；升级
必须经过新的 Classic package、签名、公证、安装和回滚验证。

**为何不复制源码或 Git submodule：** 两者都会绕过清晰的 release unit，并让 Classic 的 lockfile
无法表达实际安装包包含的 Host 版本。

### 9. Classic 是最终桌面产物的唯一组装者

`aidcp-classic-client` 运行 Electron compile 与 renderer build，然后从精确锁定的 Host 包中选择
当前平台/架构资源：

- Host JS 可按 Electron main 的加载约束进入 ASAR；
- 需要 spawn 或 native load 的 Core、Native 和 AdsPower 资源进入 `process.resourcesPath`
  下的确定性目录；
- Host 由 Classic 显式注入真实 `resourceRoot`，不得把 `app.getAppPath()` 当作可作为子进程
  `cwd` 的目录；
- macOS native 资源随 hardened runtime 签名和公证；
- 安装包内写入 Classic version、Host version、两者 commit 和 manifest hash。

目标机不进行 npm install，不解释 TypeScript，也不动态选择 Host 版本。Host 仓库可独立产出并
测试其 package，但不直接产出面向客户的 `dmg` / `zip` / `nsis`。

### 10. 兼容性由合同与场景矩阵证明，不做双实现 fallback

Host 使用 semver 表达 Host API；Cloud protocol version 继续独立表达。Classic CI 覆盖：

1. 以本次 Host commit 的 `npm pack` tarball 做开发态集成；
2. 以 lockfile 中正式 Host 版本做重复构建；
3. 校验 manifest、Electron/Node ABI、runtime format、AdsPower compatibility、资源 hash 和 package
   provenance；
4. 运行 Classic↔Host lifecycle / event / failure / human-assist contract acceptance；
5. 运行跨进程 runtime-init、全局 Local API 限频、runtime version conflict 和 profile lease 竞争；
6. 证明登录/roster reconcile 不启动引擎，`start/resume` 按当前行为准备浏览器，`pause/close`
   释放当前约定资源；
7. 证明 Host event 不覆盖 customer-auth HTTP 取得的 Cloud durable run/result；
8. 运行无系统 Node 的打包 smoke；
9. 覆盖 macOS arm64、macOS x64 与 Windows x64。

迁移期间允许旧 monolith 安装包作为回滚产物存在，但新 Classic 不保留“新 Host 失败就加载旧内置
Host”的运行时 fallback。否则新边界永远无法被真实验证。

### 11. Control repo 与协议责任同步迁移

`aidcp` 的 sibling repo inventory、task preflight、worktree helper、landing helper、部署/发行文档和
协议同步清单必须改为识别：

- `../aidcp-classic-client`
- `../aidcp-edge-host`

原先要求 `aidcp-edge` 与 Cloud Automation 同步的 protocol v2 类型、命令 mapping 和 active-command
routing，迁移后要求 `aidcp-edge-host` 与 `aidcp-automation` 同步。Classic 不成为 protocol v2
实现者。

Cloud、Console 或下载页只有在最终安装包切换时才改变 artifact 来源；仓库拆分本身不授权 dev/ol
部署、签名或发布。

## Risks / Trade-offs

- **[跨仓版本漂移]** → Classic 精确锁定 Host 版本，构建与启动双重校验 manifest/hash，并在安装包
  中记录 provenance。
- **[ASAR 或资源路径在安装后失效]** → 由 Classic 注入 `process.resourcesPath` 下真实路径，并执行
  安装后、无开发工具链 smoke test。
- **[native module 未随应用签名]** → runtime manifest 标注 native 资产，Classic 打包检查和 macOS
  签名验证缺一即失败。
- **[Electron/Node ABI 与 native 资源不兼容]** → manifest 固定 Electron major、Node modules ABI 和
  runtime format；Classic 构建与安装后启动均校验，不兼容不出包、不启动。
- **[拆分时遗漏隐式 renderer↔Core 耦合]** → 先盘点所有 IPC、环境变量、stdout parser、文件路径和
  child-process 调用，再只允许经 typed Host adapter 跨边界。
- **[两个 Host 的独立 1.1s 队列同时打到机器级 AdsPower daemon]** → MachineRuntimeCoordinator
  提供跨进程 runtime-init、version、Local API rate gate 和 profile lease；仅有 per-profile lock
  不算完成。
- **[Host 退出误杀另一个 Host 使用的 AdsPower daemon]** → Host 只关闭自己拥有的 Core/profile，
  不因自身退出执行机器级 `ads stop`；不兼容 runtime 具名失败而非替换。
- **[拆仓顺便改变浏览器启动时机]** → parity acceptance 固定登录不启动、`start/resume` 准备浏览器
  和 `pause/close` 释放资源；真正按任务启动浏览器另开 change。
- **[本地 descriptor 被当作账号或授权真相]** → 类型与结构测试禁止权威账号/权限来自 renderer，
  Cloud handshake 和页面身份复核保持准入真源。
- **[Cloud work 存在但本机引擎停止]** → Host 保持 `stopped`，客户端从 Cloud API 显示真实等待状态；
  不远程唤醒、不把 queued/waiting 画成 running。
- **[人工处理完成被误当作身份验证成功]** → Human Assist 使用关联 request，用户完成后必须由 Core
  重读页面身份才能恢复。
- **[Host 包过大]** → 首版优先一个可审计 release unit；只有观测到 registry/CI/安装包成本后再评估
  平台子包，避免现在引入组合版本矩阵。
- **[旧 installer 与新仓库切换不可回退]** → 保留最后一个已验证 monolith 签名安装包和下载元数据，
  新 Classic 完成观察窗口后才移除回滚入口。
- **[仓库重命名影响现有 worktree/helper]** → 先更新并验证 control repo 的 sibling inventory，再
  切换 canonical remote；依赖 Git hosting redirect 仅帮助已有 clone 迁移。
- **[私有 package registry 尚未绑定]** → 源码迁移阶段用可校验的本地 `npm pack`；正式 Classic
  构建和发布前必须确定 registry、只读安装凭证和不可覆盖策略。未完成时不得发布安装包。

## Migration Plan

### Phase 0: 冻结基线与所有权清单

1. 列出所有正在修改 Edge 主进程、AdsPower runtime、proxy secret、risk cross-process、自动更新与
   installer distribution 的活跃 change；在它们完成或由明确 owner 排除冲突前，不创建 split-base。
2. 在相关 change 集成、验证且 default branch 稳定后，在现有 `aidcp-edge` 记录
   `split-base` commit/tag。
3. 盘点 Electron main、renderer、Core、Native、AdsPower、IPC、环境变量、路径、日志、credential 和
   packaging files，并将每项唯一归属到 Classic 或 Host。
4. 记录当前开发态、focused tests、typecheck 和各平台最新已验证安装包结果，作为 parity 基线；明确
   记录登录/start/resume/pause/close、Human Assist、AdsPower daemon 复用与退出行为。
5. 定义 Host API、event schema、Human Assist correlation、MachineRuntimeCoordinator、manifest 和
   error catalog；在迁移代码前完成 contract tests。

### Phase 1: 建立两个独立仓库

1. 将现有 `aidcp-edge` 远端重命名/迁移为 `aidcp-edge-host`，保留完整历史和 `master`。
2. 从同一 `split-base` 创建 `aidcp-classic-client`，保留与 Classic 文件相关的历史。
3. 为两个仓库分别建立 AGENTS、CI、CODEOWNERS、版本和 release 规则。
4. 更新 `aidcp` 的 sibling repo 与 worktree/helper，但尚不改变客户下载入口。

### Phase 2: 形成 Host release unit

1. 将 supervisor、Core、平台驱动、Native 和 runtime ownership 收敛到 Host。
2. 用 typed events 替换 Classic 对 stdout 的状态解析。
3. 实现 MachineRuntimeCoordinator 的跨进程 runtime-init、version compatibility、Local API rate
   gate 与 profile lease，并证明一个 Host 退出不影响另一个 Host。
4. 实现非权威 LocalEnvironmentDescriptor、双向 Human Assist 和现有生命周期 parity。
5. 产出编译后的 npm tarball、ABI/runtime manifest、hash 和 provenance；运行 Host focused/full tests 与
   typecheck。

### Phase 3: Classic 消费 Host

1. Classic 移除 Core、驱动和 runtime 的重复源码，仅保留 Electron adapter 与产品投影。
2. 通过精确 tarball/version 接入 Host，不使用 symlink 或 workspace。
3. 证明 customer-auth 普通数据在 Host/Core/browser 未运行时仍可使用。
4. 证明 Host 本机 event 与 Cloud durable automation/result 分层，事件只更新本机事实或触发有界
   refetch。
5. 证明单环境、多环境、登录不启动、启动/恢复准备浏览器、暂停/关闭、人工介入、失败通知和退出
   清理与基线一致。

### Phase 4: 打包与发行验收

1. 构建 macOS arm64/x64 `dmg` + `zip` 与 Windows x64 `nsis`。
2. 在无系统 Node/npm/tsx 的目标环境安装并运行，校验资源路径、Electron/Node ABI、runtime format、
   native load、签名/公证、Host/Core provenance 和可见失败。
3. 执行一个明确 DEV 账号的有界真实验收；源码、UI 和握手证据不得冒充平台结果。
4. 只有全部 gate 通过后，才把下载/更新 artifact 来源切换到 `aidcp-classic-client`。

### Phase 5: 收口

1. 观察新 Classic release，保留最后一个 monolith 安装包作为有界回滚点。
2. 清除 control/CI/docs 中过期的 `aidcp-edge` canonical 名称。
3. 标记 split-base 与最后 monolith release，归档重复代码和临时迁移说明。
4. Agent Client 保持未创建；后续单独 OpenSpec 以 Host API v1 为输入评估接入。

### Rollback

- Phase 0–2 未触达用户发行，可回退仓库/包提交，不改变已安装客户端。
- Phase 3 的开发态失败直接固定回已验证 Host package，不在运行时自动 fallback。
- Phase 4 切换下载后若安装、启动或真实执行 gate 失败，恢复下载页指向最后一个已签名 monolith
  安装包；不得用仅源码回退声称客户已恢复。
- 回滚期间 Host 机器级租约继续生效，禁止新旧客户端同时驱动同一物理环境。
- 回滚期间 MachineRuntimeCoordinator MUST NOT 用旧 installer 替换或停止仍被新 Host 使用的机器级
  AdsPower daemon；若 runtime compatibility 不满足，先停对应环境并具名退出，不并跑。
- 待修复版本重新完成相同平台矩阵后才再次切换。

## Open Questions

1. 正式发布 `@aidcp/edge-host` 使用哪个私有 npm registry，以及 Classic CI/本地 release 的只读凭证
   如何配置？该选择不影响源码边界，但会阻塞正式安装包构建。
2. `aidcp-edge` 远端是原地重命名为 `aidcp-edge-host`，还是新建 Host remote 后归档旧 remote？本设计
   推荐原地重命名以保留 issue、release 和完整历史；执行前需确认仓库管理权限和现有下载链接影响。
