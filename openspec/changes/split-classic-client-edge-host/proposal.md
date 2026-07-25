## Why

当前 `aidcp-edge` 同时承载传统 Electron 客户端、环境监督器、Edge Core、平台执行适配和桌面安装包组装。这使客户端界面与执行引擎必须同仓、同版本、同节奏发布，也让未来其他客户端只能复制或侵入传统客户端代码才能复用 Edge 能力。

在实现 `agent-client` 前先完成边界拆分，可以用现有 `classic-client` 验证共享 Host 合同，同时保持 Cloud 自动化到 Edge 执行的既有边界不变。拆分目标不是增加一个常驻机器服务，而是把可嵌入、可版本化、无产品 UI 依赖的 Edge Host 沉淀成独立仓库和包。

## What Changes

- 将现有 `aidcp-edge` 的 Git 历史和执行侧职责迁移到独立仓库 `aidcp-edge-host`；最终不保留一个同时含客户端与 Host 的第三个长期仓库。
- 新建独立仓库 `aidcp-classic-client`，承接现有传统 Electron 外壳、渲染层、客户登录与普通数据访问、环境管理界面、托盘、通知、自动更新和桌面安装包。
- `aidcp-edge-host` 负责 `@aidcp/edge-host` 包、环境监督器、Edge Core、Native Page Engine、平台驱动、AdsPower 运行时适配、Cloud↔Edge 自动化协议实现，以及生命周期、结构化状态、双向人工介入和机器级 Runtime Coordinator；它不得依赖 Classic renderer 或产品导航。
- `aidcp-classic-client` 通过精确版本引用不可变的 `@aidcp/edge-host` 产物，并在构建期组装对应平台与架构的 Host、Core、Native 和 AdsPower 资源；安装后不得从开发仓库或在线源码拉取运行时。
- Host 对客户端只暴露环境发现、启动、暂停、恢复、关闭、状态订阅和人工介入等控制面能力；搜索、浏览、点赞、评论、发布等平台动作仍由 Cloud Automation 下发给 Edge Core，客户端不得通过 Host API 直接驱动页面原子动作。
- 拆仓 SHALL 保持现有自动化生命周期：登录和 roster 刷新不启动引擎；用户启动/恢复自动化时启动引擎并准备浏览器执行器；暂停/关闭按现有合同停止引擎与浏览器。把浏览器改成真正按任务启动属于后续独立行为 change，不夹带在仓库拆分中。
- 将机器级执行资源协调下沉到 Host：不同客户端实例可并存，但同一 AdsPower 分身同一时刻只能被一个 Host 实例持有；所有 Host 还必须跨进程协调机器级 AdsPower runtime 初始化、版本兼容和 Local API 全局限频，冲突必须具名失败，不得依靠运营约定或静默接管。
- Classic 提供的环境描述只表达本机 profile 和产品选择，不构成客户归属、权威账号、风险状态或平台动作授权；这些事实继续由 Cloud customer-auth / automation handshake 和真实页面身份复核确定。
- Host SHALL 通过带 `requestId/envId/generation` 的结构化事件主动上报登录挑战、页面身份不匹配等人工介入请求；Classic 只负责呈现浏览器和回传用户处理动作，Core 必须重新验证后才能继续。
- Host release manifest 增加 Electron major、Node modules ABI、runtime format、AdsPower runtime/protocol compatibility，并明确 Host 只作为 Classic 构建期精确依赖随安装包升级，不在已安装客户端中自行在线更新。
- 更新 control repo 的仓库清单、worktree/helper、协议同步和验证入口，使 `aidcp-classic-client` 与 `aidcp-edge-host` 成为独立可检出、可测试、可发版的 sibling repo。
- 采用分阶段迁移：先等待并收口当前正在改动 Edge 主进程、AdsPower runtime、自动更新、安装包和跨进程风控的 change，冻结一个可验证 `split-base`，再建立 Host 包与 Classic 仓库，随后做源码、开发态、安装包和回滚验证，最后才切换下载与发布入口。
- 本 change 明确不创建、不实现、不打包 `agent-client`，也不引入机器级常驻 Edge daemon、Cloud 业务协议变更或新的平台自动化策略。

## Capabilities

### New Capabilities

- `edge-host-package-contract`: 定义独立 Edge Host 仓库的所有权、可嵌入包合同、受限控制面 API、现有生命周期兼容、非权威环境输入、双向人工介入、运行资源清单和 ABI/version 兼容。
- `classic-client-edge-host-assembly`: 定义独立 Classic Client 仓库如何引用、启动、投影和打包 Edge Host，保持客户数据面与自动化执行面分离，并区分 Host 本机事实与 Cloud durable automation 真相。

### Modified Capabilities

- `edge-desktop-packaging`: 桌面安装包改由 `aidcp-classic-client` 组装，并必须精确锁定、校验和随包携带一个 Electron/Node ABI 与 runtime format 兼容的 Edge Host 发行物。
- `edge-multi-instance-isolation`: 用 Host 管理的 MachineRuntimeCoordinator 和环境租约替代“分身不重叠仅由运营保证”的前置约束，同时保留不同 userData 客户端实例可并存。

## Impact

- **Repositories:** 新增 `aidcp-classic-client`；现有 `aidcp-edge` 保留历史并迁移/重命名为 `aidcp-edge-host`；`aidcp` 更新跨仓工具与架构文档。两个业务仓默认分支继续遵循 sibling repo 的 `master` 约定。
- **Packaging and release:** Host 先产出带版本、平台、架构、Electron/Node ABI、runtime compatibility、文件清单和校验和的不可变包；Classic 只消费精确版本并产出最终 `dmg` / `zip` / `nsis`。Host 与 Classic 不再隐式同版本，但每个 Classic 安装包可反查其 Host 版本；已安装 Host 不独立热更新。
- **Protocol:** Cloud↔Edge protocol v2 的行为不变；原先需要在 `aidcp-edge` 与 Automation 同步的协议实现迁移为在 `aidcp-edge-host` 与 `aidcp-automation` 同步。
- **Runtime:** Classic 仍是当前唯一产品客户端，Host 作为其 Electron main/Node 进程内的受控组件及每环境子进程监督器运行；Host 本身不常驻、不监听端口，但通过跨进程原子协调安全复用机器级 AdsPower daemon。Cloud 新建的自动化任务在引擎停止时只能等待 Edge，不能由本 change 远程唤醒已退出客户端。
- **Security and safety:** 客户令牌与普通客户数据仍归 Classic；客户归属、权威账号、自动化授权、页面身份复核、风控和结果诚实性仍归既有 Cloud/Core 执行链。Host API 和本地 `LocalEnvironmentDescriptor` 都不得成为绕过 Cloud 授权的新通道。
- **Migration risk:** 主要风险是 ASAR/Resources 路径、Electron ABI、native module 签名、跨仓版本漂移、机器级 runtime 争用、进程退出语义与分身重复占用。切换前必须先冻结所有 Edge 热点 change，保留旧安装包回滚点，并分别证明源码迁移、开发态运行和已签名安装包运行，不能用其中一项替代另一项。
