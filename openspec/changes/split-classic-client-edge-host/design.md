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
- 源码迁移、开发态运行、安装包运行和真实账号结果是四种不同证据，不能互相替代。

## Goals / Non-Goals

**Goals:**

- 最终形成两个独立、可单独检出、测试、版本化和发布的业务仓库：
  `aidcp-classic-client` 与 `aidcp-edge-host`。
- 将 Edge Host 固化为无产品 UI 依赖的可嵌入包，Classic 成为它的第一个消费者。
- 让 Host 统一拥有 Core、浏览器执行器、环境监督和本机排他资源，客户端只依赖稳定控制面合同。
- 通过不可变版本、资源 manifest 和契约测试消除跨仓隐式耦合。
- 在不改变用户可见 Classic 行为和 Cloud 自动化语义的前提下完成迁移。
- 为未来其他客户端预留复用边界，但不为尚未出现的 Agent Client 设计额外协议或 daemon。

**Non-Goals:**

- 不创建或实现 `aidcp-agent-client`。
- 不把 Edge Host 做成开机自启、机器全局常驻或可远程访问的网络服务。
- 不允许客户端直接调用搜索、浏览、点赞、评论、发布等平台原子动作。
- 不改变 Cloud Automation 的策略、工作流、风险状态或 durable work 模型。
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
Host controller；Host 再监督每环境 Core 子进程及按需浏览器执行器。

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
  reconcileEnvironments(input: EnvironmentDescriptor[]): Promise<ReconcileResult>;
  getSnapshot(envId?: string): HostSnapshot;
  start(envId: string): Promise<LifecycleResult>;
  pause(envId: string): Promise<LifecycleResult>;
  resume(envId: string): Promise<LifecycleResult>;
  close(envId: string): Promise<LifecycleResult>;
  requestHumanAssist(envId: string): Promise<HumanAssistResult>;
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

事件至少携带 `clientInstanceId`、`envId`、单调 generation、事件类型、时间和结构化状态。Classic
不得通过解析 Core stdout 推断产品状态；stdout/stderr 只保留为诊断证据。

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

Classic 向 Host 提供冻结后的 `EnvironmentDescriptor`，Host 不自行读取 Classic renderer store。
Host 返回事实状态和具名错误，不返回“成功”式 UI 文案。

### 5. 同一物理环境使用 Host 机器级排他租约

不同 `AIDCP_USER_DATA_DIR` 的 Classic 实例仍可并存，但 Host 在启动任何 Core 或浏览器前必须取得
机器级执行租约。租约键优先使用不可变的物理执行身份，例如
`provider=adspower + adsUserId`；不得仅用客户端内可重命名的展示名。该租约跨 Classic userData
目录生效，且不因连接 dev 或 ol 而允许同一物理分身被双重占用。

租约实现必须使用跨进程原子排他原语。owner metadata 只用于诊断，至少包含随机
`clientInstanceId`、PID、启动时间和非敏感产品标识；不得只凭 PID 文件或超时时间静默接管。
进程死亡后由 OS 锁语义释放，或在同时证明原 owner 已死亡后有界清理。冲突返回
`environment_in_use` 与可展示的 owner 摘要，不启动 Core、不触碰浏览器。

同一 Host owner 对相同环境重复 `start` 应返回当前状态或同一在途结果；不同 owner 不得接管。
正常 `close` / `shutdown` 先停止受监督资源，再释放租约。

**为何现在加入而不是等 Agent Client：** 独立包已经使多个 Classic 实例成为真实消费者边界。
如果资源排他仍由 UI 或运营约定负责，Host 就不是完整的执行所有者，未来客户端接入时仍需破坏
合同。

### 6. Host 以一个不可变 release unit 发布，Classic 精确锁定

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
  "platforms": ["darwin-arm64", "darwin-x64", "win32-x64"],
  "assets": [{"path": "...", "sha256": "..."}]
}
```

开发集成可使用由 Host 仓库当前 commit 执行 `npm pack` 产生的 tarball。正式构建从批准的私有 npm
registry 获取不可变版本。Classic 的 `package.json` 和 lockfile 必须锁定精确版本，不使用
`^`、`~`、branch、workspace symlink 或运行时 latest 解析。

Classic 构建和启动均校验代码版本、manifest、平台/架构与资源 hash。任一不一致均具名失败为
`edge_host_artifact_mismatch`，不得退回旧资源、联网取源码或继续伪运行。

**为何不复制源码或 Git submodule：** 两者都会绕过清晰的 release unit，并让 Classic 的 lockfile
无法表达实际安装包包含的 Host 版本。

### 7. Classic 是最终桌面产物的唯一组装者

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

### 8. 兼容性由合同与矩阵测试证明，不做双实现 fallback

Host 使用 semver 表达 Host API；Cloud protocol version 继续独立表达。Classic CI 覆盖：

1. 以本次 Host commit 的 `npm pack` tarball 做开发态集成；
2. 以 lockfile 中正式 Host 版本做重复构建；
3. 校验 manifest、资源 hash 和 package provenance；
4. 运行 Classic↔Host lifecycle / event / failure contract acceptance；
5. 运行无系统 Node 的打包 smoke；
6. 覆盖 macOS arm64、macOS x64 与 Windows x64。

迁移期间允许旧 monolith 安装包作为回滚产物存在，但新 Classic 不保留“新 Host 失败就加载旧内置
Host”的运行时 fallback。否则新边界永远无法被真实验证。

### 9. Control repo 与协议责任同步迁移

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
- **[拆分时遗漏隐式 renderer↔Core 耦合]** → 先盘点所有 IPC、环境变量、stdout parser、文件路径和
  child-process 调用，再只允许经 typed Host adapter 跨边界。
- **[两个客户端/实例争用同一分身]** → Host 在任何进程或浏览器动作前取得机器级租约，冲突具名
  失败。
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

1. 在现有 `aidcp-edge` 记录 `split-base` commit/tag。
2. 盘点 Electron main、renderer、Core、Native、AdsPower、IPC、环境变量、路径、日志、credential 和
   packaging files，并将每项唯一归属到 Classic 或 Host。
3. 记录当前开发态、focused tests、typecheck 和各平台最新已验证安装包结果，作为 parity 基线。
4. 定义 Host API、event schema、manifest 和 error catalog；在迁移代码前完成 contract tests。

### Phase 1: 建立两个独立仓库

1. 将现有 `aidcp-edge` 远端重命名/迁移为 `aidcp-edge-host`，保留完整历史和 `master`。
2. 从同一 `split-base` 创建 `aidcp-classic-client`，保留与 Classic 文件相关的历史。
3. 为两个仓库分别建立 AGENTS、CI、CODEOWNERS、版本和 release 规则。
4. 更新 `aidcp` 的 sibling repo 与 worktree/helper，但尚不改变客户下载入口。

### Phase 2: 形成 Host release unit

1. 将 supervisor、Core、平台驱动、Native 和 runtime ownership 收敛到 Host。
2. 用 typed events 替换 Classic 对 stdout 的状态解析。
3. 实现机器级环境租约和结构化生命周期错误。
4. 产出编译后的 npm tarball、runtime manifest、hash 和 provenance；运行 Host focused/full tests 与
   typecheck。

### Phase 3: Classic 消费 Host

1. Classic 移除 Core、驱动和 runtime 的重复源码，仅保留 Electron adapter 与产品投影。
2. 通过精确 tarball/version 接入 Host，不使用 symlink 或 workspace。
3. 证明 customer-auth 普通数据在 Host/Core/browser 未运行时仍可使用。
4. 证明单环境、多环境、暂停/恢复/关闭、人工介入、失败通知和退出清理与基线一致。

### Phase 4: 打包与发行验收

1. 构建 macOS arm64/x64 `dmg` + `zip` 与 Windows x64 `nsis`。
2. 在无系统 Node/npm/tsx 的目标环境安装并运行，校验资源路径、native load、签名/公证、Host/Core
   provenance 和可见失败。
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
- 待修复版本重新完成相同平台矩阵后才再次切换。

## Open Questions

1. 正式发布 `@aidcp/edge-host` 使用哪个私有 npm registry，以及 Classic CI/本地 release 的只读凭证
   如何配置？该选择不影响源码边界，但会阻塞正式安装包构建。
2. `aidcp-edge` 远端是原地重命名为 `aidcp-edge-host`，还是新建 Host remote 后归档旧 remote？本设计
   推荐原地重命名以保留 issue、release 和完整历史；执行前需确认仓库管理权限和现有下载链接影响。
