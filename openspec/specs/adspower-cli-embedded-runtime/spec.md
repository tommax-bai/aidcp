# adspower-cli-embedded-runtime Specification

## Purpose
TBD - created by archiving change edge-bundled-adspower-cli-runtime. Update Purpose after archive.
## Requirements
### Requirement: 伴侣端拉起并看护随包分发的 AdsPower 运行时

edge 桌面伴侣端 MUST 用应用自带的 Node 运行时（Electron 的 `ELECTRON_RUN_AS_NODE` 执行体）拉起随安装包分发的 AdsPower CLI 运行时，并在其存活期内看护它。adspower 形态下运行 MUST NOT 依赖目标机上单独安装的 AdsPower 桌面客户端、MUST NOT 依赖目标机的 npm / 独立 Node / 全局安装。运行时启动所需的 api-key MUST 从配置/环境读取，MUST NOT 硬编码或写入文档/提交/进度文件。运行时起不来或中途死亡时，伴侣端 MUST 诚实呈现失败（守「不静默假成功」红线），MUST NOT 停在「运行中」外观而实际运行时未在跑。

#### Scenario: 干净机器无桌面客户端也能起运行时

- **WHEN** 目标机只装了 edge 桌面应用、未安装 AdsPower 桌面客户端、也无 npm/独立 Node
- **THEN** 伴侣端用自带 Node 拉起内嵌 AdsPower 运行时并确认其 Local API 就绪，随后才继续起 edge 核心

#### Scenario: 运行时启动失败诚实可见

- **WHEN** 内嵌运行时启动失败（如缺 api-key、端口不可用、引擎异常）
- **THEN** 伴侣端明确呈现失败原因，MUST NOT 装作已在运行，MUST NOT 静默把 edge 核心带进注定失败的启动

#### Scenario: 运行时中途死亡被看护

- **WHEN** 内嵌运行时进程在会话期内异常退出
- **THEN** 伴侣端按有界重起语义尝试恢复或诚实下线，MUST NOT 无视其死亡而让核心继续依赖已挂的 Local API

### Requirement: edge 核心连内嵌运行时的 Local API

edge 核心 MUST 经可配的 Local API 基址连接内嵌运行时（沿用 `AIDCP_ADS_API_BASE`）。伴侣端 MUST 以运行时实际监听端口（经其状态查询获取）设置该基址，MUST NOT 把端口硬编码为固定值。运行时 Local API 不可达时，核心 MUST 诚实失败（不握手、不连云端），MUST NOT 回落到 `self` 或伪装成功。

#### Scenario: 端口非默认值时仍正确对接

- **WHEN** 内嵌运行时因默认端口被占而监听于回退端口
- **THEN** 伴侣端读取其实际端口并据此设置 `AIDCP_ADS_API_BASE`，edge 核心连上该端口的 Local API

#### Scenario: Local API 不可达时核心诚实停手

- **WHEN** edge 核心启动时内嵌运行时的 Local API 不可达
- **THEN** 核心诚实报错并以可重起语义退出，MUST NOT 回落 `self`、MUST NOT 静默假成功

### Requirement: 启动时条件式内核预检门控核心启动

伴侣端在起 edge 核心之前 MUST 检查该机所需浏览器内核是否已就绪。内核已就绪时 MUST 直接放行、不显示下载进度。内核缺失时，伴侣端 MUST 先下载该内核并以确定型进度（真实下载进度驱动）呈现，且 MUST 在下载完成后才放行 edge 核心启动。下载失败时 MUST 诚实停在可重试的失败态、MUST NOT 起 edge 核心。伴侣端 MUST NOT 依赖 edge 核心在浏览器启动调用里惰性下载内核。

#### Scenario: 内核已就绪则秒过

- **WHEN** 启动时所需内核在运行时的可用内核清单中已标记为已下载
- **THEN** 伴侣端不显示下载进度、直接放行 edge 核心启动

#### Scenario: 内核缺失则带进度下载并门控

- **WHEN** 启动时所需内核未下载
- **THEN** 伴侣端进入准备态、下载内核并以确定型进度条呈现，直到下载完成后才放行 edge 核心启动

#### Scenario: 下载失败诚实可重试、不起核心

- **WHEN** 内核下载中途失败（如断网）
- **THEN** 伴侣端呈现「准备失败」并提供重试，MUST NOT 静默继续、MUST NOT 起 edge 核心

#### Scenario: 绝不惰性下载撑爆启动超时

- **WHEN** 所需内核缺失
- **THEN** 内核下载在伴侣端预检阶段完成，MUST NOT 推迟到 edge 核心的浏览器启动调用内触发（避免大内核下载撑爆核心的启动/就绪超时而伪失败）

### Requirement: 内核按需下载并落用户可写目录、不进安装包

浏览器内核 MUST NOT 随主安装包分发，MUST 在首次需要时按需下载并缓存到用户可写目录（后续启动复用、不重复下载）。内嵌运行时的工作目录与缓存 MUST 位于用户可写位置，MUST NOT 依赖对只读且已签名的应用包目录的写入。

#### Scenario: 内核只在首次下载、之后复用

- **WHEN** 同一机器第二次及以后启动、所需内核已在用户目录缓存中
- **THEN** 伴侣端直接复用缓存内核、不再下载

#### Scenario: 运行时写入落在可写目录

- **WHEN** 内嵌运行时需要写入缓存或自更新数据
- **THEN** 写入发生在用户可写目录，MUST NOT 写入只读的应用安装包目录

### Requirement: Ads CLI 运行时模板按内容身份刷新

Edge MUST 为完成全部兼容补丁后的 Ads CLI 运行时模板生成稳定内容身份，并把该身份纳入用户目录暂存判定。模板内容身份变化时，即使 Edge 应用版本与 Ads CLI 包版本未变，Edge 也 MUST 刷新用户目录副本；开发态 MUST 以当前 `build/ads-runtime` 模板为准，MUST NOT 让历史用户目录副本遮蔽当前兼容补丁。若旧 daemon 正从待替换副本运行，Edge MUST 先有界停止它再交换目录；停止、复制或交换失败 MUST 诚实阻断启动，MUST NOT 继续接管身份不符的旧运行时。

#### Scenario: 同版本兼容补丁变化触发刷新

- **WHEN** Edge 应用版本和 Ads CLI 包版本未变，但随包运行时模板的内容身份发生变化
- **THEN** Edge 刷新用户目录运行时副本并从新模板启动，MUST NOT 因旧二元版本 stamp 相同而继续运行旧 hook

#### Scenario: 开发态当前模板优先于历史副本

- **WHEN** 开发态 `build/ads-runtime` 与用户目录中的历史运行时副本内容身份不同
- **THEN** Edge 以当前 build 模板刷新用户目录副本，随后运行当前兼容补丁

#### Scenario: 旧 daemon 阻碍刷新时诚实失败

- **WHEN** 内容身份变化且旧 Ads CLI daemon 无法有界停止或运行时目录无法安全交换
- **THEN** Edge 明确报告运行时暂存失败并阻断环境核心启动，MUST NOT 静默复用旧模板

### Requirement: Ads CLI daemon 生命周期归属 Edge 真正退出

Edge 在本次进程中启动或接管 Ads CLI daemon 后，MUST 记录其管理会话。Edge 真正退出时 MUST 先有界停止各环境核心并等待既有浏览器清理，再有界停止所管理的 Ads CLI daemon，最后退出 Electron；无环境核心运行时也 MUST 执行 daemon 停止。普通窗口关闭到托盘不属于真正退出，MUST NOT 因此停止 daemon。

#### Scenario: 真正退出停止所管理 daemon

- **WHEN** Edge 已启动或接管 Ads CLI daemon，随后用户执行真正退出
- **THEN** Edge 在环境停机后执行 Ads CLI stop，确认或有界等待 daemon 停止后再退出

#### Scenario: 无运行环境仍清理 daemon

- **WHEN** Ads CLI daemon 已由本次 Edge 管理，但当前没有环境核心子进程
- **THEN** `before-quit` 仍进入运行时清理流程，MUST NOT 因环境列表为空直接放行并留下 daemon

#### Scenario: 关闭窗口到托盘保持运行时

- **WHEN** 用户只关闭桌面窗口而应用按既有语义常驻托盘
- **THEN** Edge 与所管理 Ads CLI daemon 继续运行，不执行真正退出清理

