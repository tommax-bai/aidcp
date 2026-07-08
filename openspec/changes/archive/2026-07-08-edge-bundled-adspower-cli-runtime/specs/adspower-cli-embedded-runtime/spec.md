## ADDED Requirements

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
