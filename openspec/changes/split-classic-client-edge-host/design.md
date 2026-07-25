## Context

`aidcp-edge` 目前是一个 Electron 应用仓库，但内部同时存在四种不同变化节奏：

1. Classic 产品层：窗口、renderer、客户登录、普通数据访问、环境管理、托盘、通知和更新；
2. Host 控制层：环境 roster 投影、每环境进程监督、生命周期、状态聚合、人工介入和本机资源管理；
3. Edge 执行层：Cloud 自动化命令、Edge Core、平台驱动、CDP / API 执行和结果回执；
4. 发行组装层：预编译产物、ASAR、Native Page Engine、AdsPower CLI 资源、签名和安装包。

当前 Classic 既是产品客户端，又直接知道 Core 入口、子进程环境变量、运行时路径和 stdout
状态解析。这一结构在只有一个客户端时可工作，但当第二个**面向不同客户群的独立产品客户端**出现时，
它只留下两条都不可接受的路：

- 把执行引擎复制成第二份 —— 两份实现之后会静默漂移，引擎级修复要靠人工记得同步到两边；
- 侵入式复用 Classic 主进程内部结构 —— Classic 的任何产品级重构都会随机弄坏另一个产品，
  且第二个客户端会顺带获得页面原子动作入口，绕开 Cloud 授权。

因此本设计的收益边界只有一条：**执行引擎成为一份被两个独立客户端产品共用的可嵌入包。**

**发布节奏不在收益内。** 已安装 Host 不独立热更新（见 Decision 8），Host 仓不产出面向客户的
安装包（见 Decision 9）。引擎侧修复仍须经每个客户端的 pin → 构建 → 签名 → 公证 → 分发。
拆仓的直接代价是：引擎修一次，安装包从发一个变成发两个。

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

⚠️ **上表只用于定位，不是所有权依据。** 权威所有权清单必须**按文件与行段**给出（见 tasks 0.C.5）。
按类别写的表格无法被检查——搬完之后没有任何机械手段能回答「这一段到底该在哪边」；按文件/行段写的
清单可以直接与拆分后两个仓的实际内容做差异比对。

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

⚠️ **下面这份九个动词的草稿已被逐通道盘点取代，只保留为最小骨架。**
权威的推导结果见 `docs/edge-split-ownership-inventory.md` §4：把五条传输与 82 条通道逐条盘完之后，
生命周期动词覆盖不到的操作还有二十余个，按引擎启停、机器级资源协调、浏览器窗口、指纹浏览器本机 API、
云端与批量、事件流六组给出。其中若干条**用生命周期动词表达就是错的**，例如——批量启动返回的是
**准入裁决**（已排队 / 仅控制面 / 因队列满被拒），逐环境的 `start` 表达不了这三种区别，而这正是
操作者看到的东西；「为人工查看打开一个分身」明确**不启动执行侧、不改写认证状态**，用 `start` 是
错的动词；停止必须能区分**诚实拒绝**（浏览器无法确证关掉）与**没响应**，今天的即发即忘做不到。

首版公开合同的最小骨架如下，最终类型以导出的 TypeScript 声明为准：

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

**禁令的范围是「平台原子动作」，不是「非 lifecycle 操作」。** 措辞必须精确到这一层，否则会误伤
两类已上线且正确的东西：一是客户端内的稿件预览与审批，二是环境管理类操作——它们都不经过执行侧，
禁令对它们无效（见下）。

#### 3.1 非 lifecycle 的产品↔执行通道（实测清单，非推测）

上一版设计只给了 9 个 lifecycle 动词，把指纹环境建号 / 改代理 / 删除、浏览器开关与显示、重新登录、
重启等操作留在「属执行侧却无处安放」的状态。**对着代码盘完之后，结论与预期相反：这些操作绝大多数
根本不到执行侧。** 现实分成四类，拆仓时的归属也就此确定：

**A 类 —— 真正命令运行中执行侧的非 lifecycle 操作。** 直接命令的有两个：`browser:showDriven`
（把被驱动的浏览器显示到客户端下方，**请求-应答**，带 requestId 与 3 秒超时）与
`browser:resetParking`（把浏览器还原到停放位，**单向无应答**）。
⇒ Host 公开合同**必须**为这两个各建一条具名 request/response 或具名单向通知，**不得**用通用
execute 承载。

⚠️ **但「只有这两个」是错的判断，边界必须按扇出画、不能按通道清单画。** 逐通道盘点后确认：
还有至少两条产品侧通道（改环境昵称、人设落库）**间接**写到了执行侧的标准输入——它们调用
「更新状态」那个函数，而该函数会连锁触发向执行侧推一条浏览器横幅指令。**真正的接缝是那个
状态更新函数的扇出**，任何未来调用它的产品侧通道都会自动继承这条通往执行侧的路径。
按通道清单画边界必然漏；必须按「谁写状态」画。完整台账见
`docs/edge-split-ownership-inventory.md`。

**B 类 —— 看着像非 lifecycle、其实就是 lifecycle 动词。** 重新登录与重启都实现为「停止并重启
执行侧」；打开浏览器实现为 `wake`；关闭浏览器实现为 `standby`；切换云端环境实现为一条带 requestId、
45 秒超时的重绑请求。⇒ 归入 lifecycle 面，但**重绑必须显式建模为请求-应答**，不能当成即发即忘。

**C 类 —— 完全绕过执行侧，客户端直连指纹浏览器本机 API。** 建环境（含批量）、读改代理（含批量与
进度回推）、列分身、读模板、查运行时状态。⇒ **归 Classic**，不进 Host 公开合同。
⚠️ 其中改代理在环境正在使用时**硬性拒绝**（当前没有对运行中执行侧做在途重配的路径）。这条现状
必须原样保留，拆仓不得顺手「改善」成在途重配。

**D 类 —— 完全绕过执行侧，客户端直连云端 HTTPS。** 人设读取/生成/落库、稿件审批与配图删除、
互动收件箱全家族、内容工作区全家族、环境风险与慢启动读写。⇒ **HTTP 调用那一半归 Classic**，
不进 Host 公开合同。

⚠️ **D 类里绝大多数并不能整块归 Classic，因为它们先要把环境 id 翻译成环境键，而那张翻译表在
执行侧。** 逐通道盘完后，82 条里**须切开的是 30 条，不是 10 条**，多出来的正是这一批。更要命的是
那个解析函数在找不到 id 时**回落到「当前选中环境」**——拆开后若 Classic 拿不到正确的解析器，
发布草稿编辑、发布队列取消这类写操作会**静默打到另一个账号上**。所以 Classic 必须有自己的
「环境 id → 环境键」解析器，数据源是产品侧名册，**不是执行侧的运行时注册表**。

⚠️ **「删除环境走云端、绕过执行侧」这条是错的，已订正。** 只有视频号那条走云端；其余平台的终局
直接调指纹浏览器本机删除，且删前要触发注册表 reconcile（会停掉该环境的执行侧、释放其占用的
浏览器槽位）。整块判 Classic 的话，删一个正在跑的环境会出现「云端撤销 + 名册移除成功，但它的
执行侧还活着、还占着槽位」。

**这里有一条必须写进设计的历史方向：产品侧操作正在被系统性地搬离执行侧，而不是相反。** 人设与
稿件审批两条链路曾经确实走执行侧的标准输入命令桥，现在已经迁到「客户端主进程直连云端」，其
客户端侧发送函数**已成为零调用点的死代码**，并且有测试断言禁止它们被重新引入。这么做的收益很实：
这些操作在引擎停止时依然可用。**因此本 change 绝不能把它们重新拉回 Host 合同**——那是在恢复一条
已经被有意拆掉的耦合，而且会当场撞红现有测试。

#### 3.2 跨边界传输有五条，不是一条，也不是四条

所有权盘点必须按传输逐条归属，遗漏任何一条都会在拆仓时变成「功能没了但没人发现」：

1. **标准输出/错误的行流**（执行侧→客户端）：日志 + 四种结构化前缀行（三种应答前缀 + 一种诊断
   前缀）+ 靠自由文本推断状态。⚠️ 标准错误**不是**独立通道，它与标准输出汇入同一个行处理器，
   且既有注释明确警告「不得把标准错误当作失败信号」。
2. **标准输入的按行 JSON**（客户端→执行侧）：仅剩浏览器显示/停放/提示三种。
3. **Node 进程间通道**（双向）：23 种 lifecycle 消息，**且不止 lifecycle**——它同时承载重绑
   请求-应答、临时浏览器租约的「请求→批准/拒绝」协商、唤醒的「请求→拒绝」协商。
4. **启动时的环境变量**（客户端→执行侧，仅进程创建时一次）：这是**一条真正的命令通道**，不只是
   配置。「删除环境并擦除凭证」这个操作在某个平台上**只能**通过它表达——客户端专门启动一个
   「只做清理」的执行侧进程，用环境变量告诉它清理哪一个，完成后经 Node 进程间通道回报。
   ⇒ Host 合同必须把它变成一个**具名操作**，而不是继续靠启动参数偷渡。
5. **POSIX 信号**（客户端→执行侧，带外）：在进程间通道已不可用时，终止信号是「暂停 = 引擎断开」
   的权威兜底。⇒ Host 合同必须保留一条「进程间通道不可用时仍能落实停止」的路径，不能假设
   typed API 永远可达。

**标准输入桥有一个与 CLAUDE.md §2「第 4 处白名单」同构的陷阱**：执行侧有三个各自独立的标准输入
消费者，每条行都投递给三者、各自按类型过滤、**不认识的类型被三者同时静默丢弃、任何地方都不报错**。
拆仓后若把这条桥变成 typed Host API，这个失败模式必须被类型系统消掉（穷举式类型 + 未知类型
具名失败），而不是照搬过来。

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

#### 7.0 真空点在哪（实测，不是推测）

上一版设计方向对，但没有指名任何跨进程原语，也**指错了入口**。对着代码盘出来的现实：

- **同机双驱的主入口不是「启动被拒」，而是「根本不走启动」。** 指纹浏览器自身的占用拒启只覆盖
  跨账号 / 跨设备；同机同账号的第二个实例走的是另一条路：先查分身是否活跃，是就直接取调试端口
  **附着上去**，启动调用从头到尾没被调用过，那条拒启错误路径永远不会触发。
- **这样的门有两道，不是一道。** 除了「已报告活跃→附着」，还有「报告非活跃、但缓存目录里的调试
  端口仍存活→孤儿接管」。第二道门有端口 / 浏览器路径 / 版本三重校验，但那些校验只能证明
  「这确实是该分身的浏览器」，**永远不能证明「没有别人正在驱动它」**。只加固其中一道等于没修。
- **后果比「两边同时驱动」更重。** 经任一道门附着上来的实例会把该浏览器记为「由本节点启动或接管」，
  于是在**自己退出时把它停掉并强制终止**。也就是说，后到者不但抢驱动，还会在收工时把先到者正在用
  的浏览器关掉。
- **第三条真空是守护进程本身。** 每个客户端实例在本次会话首次准备运行时，会**先停掉已在跑的守护
  进程再重启**。这个分支受一次性闩锁和 api-key 保护，但**分支内部零所有权、零健康、零在用检查**：
  它停掉它找到的任何守护进程，停不掉就直接放弃启动。第二个实例一启动，就把第一个实例正在用的
  守护进程掐了。
- **「占用查询接口已经有两个、只缺调用时机」这个判断需要订正。** 两个接口确实存在，但
  **都答不出「是谁在用」**：一个只返回活跃 / 非活跃与调试端口；另一个**必须由调用方传入名册**、
  无法枚举，因而对另一个实例名册里的分身**结构性失明**。唯一能拿到占用者身份的地方，是跨账号
  拒启消息里解析出来的那一条——而同机同账号那条路根本走不到拒启。⇒ 不能假设「调用现成接口即可」，
  占用事实必须由 Host 自己的租约建立。
- **词汇上不要另起一套。** 「环境被其它端占用」的呈现语义与「不可重起终局」的处置语义都已固化在
  既有 spec 里，其中还有一条现成红线：处置该终局时**不得对占用者的浏览器发起停止 / 强制终止 /
  调试附着**。本 change 要做的是把这条红线的约束时点从「处置一个已被识别的拒启」**前移到
  「决定是否附着」本身**，而不是发明新的结局类别。

#### 7.1 机制选型：文件的原子独占创建，且明确不用操作系统锁

跨进程原语**写死为文件的原子独占创建**（以「不存在才创建、已存在即失败」的方式打开一个文件）。
理由：零新依赖，macOS 与 Windows 语义一致，仓内已有先例。

⚠️ **先例只有一处半，另一处别引用错。** 仓内两处独占创建里，只有一处是真正的竞争仲裁（主密钥
首次创建，「败者读取胜者结果」），另一处只是给临时文件加的防覆盖硬化、EEXIST 之后没有任何仲裁。
而且那个真先例是**一次性创建竞争，不是持有型锁**：没有持有者身份、没有存活探测、没有释放路径。
⇒ **陈旧持有者的回收逻辑必须现设计，不能靠引用先例带过。**

**明确不用会随进程死亡自动释放的操作系统锁。** 被保护的东西不是客户端进程的内存，而是**守护进程
持有的浏览器**——客户端死了浏览器不会跟着死。锁自动释放，只会让第二个客户端「合法地」拿到锁，
去附着一个半驱动状态的浏览器，正好制造我们要防的那件事。

**因此租约回收必须同时满足两个条件**：① 证明原持有者进程已死；**且** ② 从浏览器侧证明那个浏览器
确已不在。只满足 ① 判定为**孤儿租约、不许接管**。

**全局限频闸用的是另一套判据，且绝不可复制粘贴。** 限频闸走「短临界区 + 时间戳文件」，那里
**超时接管是安全的**——因为它保护的只是一个数字，接管最坏结果是多放行一次调用。租约保护的是一个
物理浏览器，接管最坏结果是关掉别人正在用的浏览器。两者判据必须显式不同，代码上也不应共用同一个
接管实现。

⚠️ **不得引入常驻协调进程、锁服务或任何 broker**（对齐 2026-07-25「不引入 Redis」的决策）。
机器上的常驻进程仍然只有既有的指纹浏览器守护进程。

#### 7.2 协调范围

不同 `AIDCP_USER_DATA_DIR` 的 Classic 实例仍可并存。由于 AdsPower CLI 是机器级共享 daemon，而
每个 Host 进程内的 `1.1s` 队列不能互相协调，Host SHALL 提供使用跨进程原子原语的
MachineRuntimeCoordinator，至少管理：

1. `runtime-init`：跨 Host 串行 stage/status/start，避免并发初始化同一个 daemon；
2. `runtime-refcount`：**健康且版本兼容的守护进程 MUST NOT 被后来者停止**。当前行为正相反——
   每个实例本次会话首次准备运行时无条件先停再起，分支内零所有权 / 零健康 / 零在用检查。改为：
   先判定「已在跑 + 健康 + 版本兼容」，满足即**采纳**；只有被证明不健康或不兼容、**且**无存活
   owner、**且**无活跃分身时才允许停。Host 退出也不得因为「自己要走了」就停机器级守护进程；
3. `runtime-version`：校验正在运行的 AdsPower runtime/protocol 与本 Host manifest 兼容；有活跃
   owner 时不得停止或替换不兼容 daemon，具名失败 `ads_runtime_version_conflict`；
4. `ads-api-rate-gate`：所有 Host 共享 Local API 最小调用间隔，不能各用一条进程内队列。
   **现有的两条进程内队列保留、不删**，新闸叠在它们之后（本地队列是准入辅助，不是保护）；
5. `profile:<provider>:<physicalId>`：在启动 Core、浏览器或 profile 生命周期动作前取得物理环境
   排他租约。**该租约的判定点 MUST 前置于「取调试端口」这一步本身**，从而同时覆盖 7.0 里那两道
   门（已活跃→附着、报告非活跃但孤儿端口存活→接管）；只在启动调用上加闸对两道门都无效。

profile 租约键优先使用不可变物理执行身份，例如 `provider=adspower + adsUserId`；不得仅使用客户端
内可重命名展示名、Cloud target 或局部 envId。该租约跨 Classic userData 生效，且不因连接 dev 或
ol 而允许同一物理分身被双重占用。

所有协调均须使用跨进程原子排他原语。owner metadata 只用于诊断，至少包含随机
`clientInstanceId`、PID、启动时间、Host/runtime version 和非敏感产品标识；不得只凭 PID 文件或
超时时间静默接管。**回收判据按 7.1 写死：「原 owner 已死」与「浏览器侧证明浏览器已不在」必须
同时成立**；只满足前者是孤儿租约，具名拒绝、不许接管。**不采用「进程死亡即由操作系统释放」的
语义**——那正是 7.1 排除掉的方案。

同一 Host owner 对相同环境重复 `start` 应返回当前状态或同一在途结果；不同 owner 冲突返回
`environment_in_use`，**不启动 Core、不取调试端口、不附着、不停止、不强制终止**。正常
`close` / `shutdown` 先停止自己拥有的环境资源，再释放自己的 profile lease；Host 退出不得停止仍被
其他 Host 使用的机器级 AdsPower daemon。

**为何不建立新的 Edge Host daemon、也不引入任何 broker：** MachineRuntimeCoordinator 只提供跨进程
原子独占文件、共享限频事实和 owner metadata；Host 仍嵌入各客户端、不监听网络端口。机器级常驻进程
仍只有既有 AdsPower CLI。本 change **不接受**「先上一个本机 broker / 锁服务」作为备选方案——它与
2026-07-25「不引入 Redis」的决策同源：多一个常驻进程就多一份安装、升级、崩溃恢复和版本仲裁负担，
而本场景的协调对象数量是个位数、协调频率极低。若未来真的证明原子文件无法表达某项协调，那应当是
一个带独立论据的新 change，而不是本 change 预留的后门。

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

**分发机制：tarball + lockfile integrity，不建私有 registry。**

Host 仓 CI 对一个 clean 的 eligible commit 执行 `npm pack`，产出 `.tgz` 与 `edge-host-manifest.json`，
经 GitHub Release 发布（复用现有 `desktop-v<ver>` prerelease → ECS `/opt/aidcp/downloads/` 那条已经
跑通的分发链路，不新建基础设施）。Classic 的 `package.json` 依赖一个**精确的 tarball URL**，
`package-lock.json` 随之记录该 tarball 的 `integrity: sha512-…`。

**不可覆盖性由 lockfile 的 sha512 强制，而不是由服务端策略强制。** 已实测：安装 tarball URL 后
lockfile 带 `integrity: sha512-…`；若该 URL 背后的字节被替换，`npm ci` 直接以 `EINTEGRITY` 非零
失败。这比 registry 的服务端「拒绝覆盖同版本号」更硬——registry 策略是一个可以被管理员改掉的
配置，lockfile 校验和是一个必须改代码提交才能改掉的事实，且改动会出现在 diff 里。

**为何不建私有 registry：** 它需要新增托管、账号、只读凭证与轮换流程，而它买到的唯一保证
（同版本号不可覆盖）已经被 lockfile 校验和更强地覆盖了。**为何不用阿里云 OSS：** 桶 `aidcp` 的
匿名读返回 403（非公读桶），该问题已经卡住另外两个 change 数周；本 change 不引入对它的新依赖。

Classic 的 `package.json` 和 lockfile 必须锁定精确 tarball URL 与其 integrity，不使用
`^`、`~`、branch、workspace symlink、`file:` 相对路径或运行时 latest 解析。开发期集成同样走
tarball，只是来源换成本地 `npm pack` 产物——开发态与正式态的**机制相同、只有来源不同**，
不存在「开发用一套、发布用另一套」的未验证切换。

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

原先要求 `aidcp-edge` 与 `aidcp-cloud` 同步的 protocol v2 类型、命令 mapping 和 active-command
routing，迁移后要求 `aidcp-edge-host` 与 `aidcp-cloud` 同步。Classic 不成为 protocol v2
实现者。

**协议对端只写 `aidcp-cloud`，不写任何云端拆仓后的仓名。** 云端逐进程出仓（`aidcp-api` /
`aidcp-content` / `aidcp-automation`）是另一条 6 步串行链的第 5 步、尚未开始（见
`docs/cloud-decomposition-execution-plan.md`），且云端评审结论明确反对为它预建空仓。**本 change
既不依赖也不预设云端拆仓结果。** 这条不是措辞洁癖：CLAUDE.md §2 的协议四处同步是铁律，把其中
一处指向一个不存在的仓，等于让那道纪律在改名当天失去落点；本仓历史上两次「命令被静默丢弃」正是
同步清单漏项造成的。若云端拆仓先于本 change 完成，协议同步清单由云端那条链更新，本 change
不提前认领。

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
- **[Host 发行物被替换或漂移]** → 不建 registry；Classic 依赖精确 tarball URL，lockfile 记录
  `integrity: sha512-…`，字节被换即 `npm ci` `EINTEGRITY` 非零失败。开发态与正式态用同一机制、
  只换来源。
- **[GitHub Release / ECS 下载目录不可达导致构建断供]** → tarball 与 manifest 是内容寻址的
  不可变文件，可镜像到任意可达位置而不改变其 integrity；构建失败是可见的硬失败，不会退化为
  「悄悄用了上一个 Host」。这是本 change 明确接受的运维依赖，不再引入第二套托管。

## Migration Plan

### Phase 0: 冻结基线与所有权清单

**冻结按文件冻，不按仓冻。** 全组停工既不可行也没必要（控制仓 120+ 活跃 change、edge 仓 36 个
worktree）。冻结范围恰好是这 5 个位置：

1. `src/electron/main.cjs`
2. `src/electron/ads-runtime.cjs`
3. `src/cdp/browser-provider.ts`
4. `.github/workflows/build-desktop.yml`
5. `package.json` 的 `build` 段，及配套 `scripts/after-pack.cjs`、`scripts/stage-ads-runtime.mjs`、
   `scripts/build-desktop-macos.sh`

**冻结清单必须由 git 反查得出，不得只靠在 change 文档里搜文件名。** 一个 change 完全可能改了主进程
却没在它的文档里提到文件名；按文档搜出来的清单只是**下界**。打 split-base 前的权威判据是：

```bash
git -C ../aidcp-edge log --since=<冻结起点> --oneline -- <上述 5 个位置>
git -C ../aidcp-edge worktree list   # 其中触及上述 5 个位置的 worktree 必须为 0
```

Phase 0 的第一步因此改为：

1. 用上面两条命令反查出触及冻结集的活跃工作，逐条要么等它集成、要么由明确 owner 声明不重叠并给出
   顺序；在冻结集上的未合并工作清零之前，不创建 split-base。按文档搜到的候选（`self-contained-ads-runtime`
   碰 ①②③、`browser-slot-scheduling` 碰 ①、原生页面引擎切换碰 ⑤）只作为起点，不作为完整清单。
2. 在相关 change 集成、验证且 default branch 稳定后，在现有 `aidcp-edge` 记录
   `split-base` commit/tag。
3. 盘点 Electron main、renderer、Core、Native、AdsPower、IPC、环境变量、路径、日志、credential 和
   packaging files，并将每项唯一归属到 Classic 或 Host，**按文件与行段成表**。
4. 记录当前开发态、focused tests、typecheck 和各平台最新已验证安装包结果，作为 parity 基线；明确
   记录登录/start/resume/pause/close、Human Assist、AdsPower daemon 复用与退出行为。
5. 定义 Host API、event schema、Human Assist correlation、MachineRuntimeCoordinator、manifest 和
   error catalog；在迁移代码前完成 contract tests。
6. **三项就地前置全部在现 `aidcp-edge` 内完成**（详见 tasks 第 0 节）：Windows 自包含出包弄绿并真出
   一次包；机器级排他按 Decision 7 实装；主进程就地拆开并逐通道定归属。**准入判据写死**：主进程
   文件 < 1500 行、归属引擎的模块零 renderer/window/navigation 引用（有边界测试）、82 条通道全部
   有归属且无「待定」、三套测试全绿。任一项不满足，不得进入 Phase 1。

**为何这三项必须在建仓之前、而不是之后：** 它们都不是「押后拆仓」的变体，修的是今天就在漏的洞。
Windows 那条尤其关键——拆仓设计里最没被验证的一块，恰恰是「引擎包携带 Windows 预编译二进制、
客户端消费它出安装包」，而今天连单仓单流水线的 Windows 自包含都没跑通过一次；不先弄绿，拆仓的
机械验收口径就只剩「mac 还能打」。主进程就地拆分那条同样关键：现在两条「Move」任务指向同一个
7396 行的文件，**没有任何一条任务是「先就地把它拆开」**——那等于要求一次搬运同时完成一次从未做过的
职责切分，失败时无法区分是搬错了还是本来就没分对。

### Phase 1: 建立两个独立仓库

1. **先**更新 `aidcp` 的 sibling inventory、helper 与门禁，使其**同时接受新旧仓名**，并补上「名单
   不得因改名而静默缩小」的硬化；尚不改变客户下载入口。**这一步必须先于任何改名**——门禁对
   「目录不存在」是跳过而非失败，改名瞬间旧路径消失即静默跳过，而两个新仓还不在名单里，守卫当场
   fail-open。
2. 将现有 `aidcp-edge` 远端重命名/迁移为 `aidcp-edge-host`，保留完整历史和 `master`。
3. 从同一 `split-base` 创建 `aidcp-classic-client`，保留与 Classic 文件相关的历史。
4. 为两个仓库分别建立 AGENTS、CI、CODEOWNERS、版本和 release 规则；把签名 / 公证流水线与其
   secret 迁到 Classic 仓（secret 值必须重建，不能拷贝）。

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

1. ~~正式发布 `@aidcp/edge-host` 使用哪个私有 npm registry~~ —— **已关闭（用户拍板）**：不建
   registry，走 tarball + GitHub Release，不可覆盖性由 lockfile `sha512` 强制。见 Decision 8。
2. `aidcp-edge` 远端是原地重命名为 `aidcp-edge-host`，还是新建 Host remote 后归档旧 remote？本设计
   推荐原地重命名以保留 issue、release 和完整历史；执行前需确认仓库管理权限和现有下载链接影响。
3. **冻结窗口开在什么时候、由谁负责**（用户已同意冻结原则，日期与负责人未定）。冻结范围见
   Migration Plan Phase 0 的**按文件**冻结清单。
4. **Windows 代码签名证书买不买** —— **暂缓（用户 2026-07-25 决定）**：先把 Windows 自包含出包打通、
   真出一次包，再按实际安装体验决定。当前 Windows 包本来就配置为不签名，因此在决定之前默认接受
   「未知发布者」提示。该选择只影响安装体验，不影响本 change 的边界与验收口径。
