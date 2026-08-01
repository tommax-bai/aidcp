# adspower-environment-provisioning Specification

## Purpose
TBD - created by archiving change adspower-auto-create-env. Update Purpose after archive.
## Requirements
### Requirement: 程序化创建一个指纹环境（委托生成 + 挑整机模板 + 薄护栏 + OS 四者一致断言）

`adspower` 模式下，桌面外壳 SHALL 经 AdsPower 本地 API `user/create` **程序化创建一个**浏览器指纹环境，指纹的生成 SHALL **最大化委托 AdsPower 按 OS 自动生成自洽整套**（`ua_auto` 匹配内核、`canvas`/`webgl_image`/`audio`/`client_rects` 噪声开启），aidcp 侧 MUST NOT 逐字段手搓整套 `fingerprint_config`。aidcp 侧 SHALL 只承担三件事：① 由运维（或按模板轮换）挑一个「整机模板」，**OS 为第一锁定字段**，`device_memory`/`hardware_concurrency`/`screen_resolution` 等折进模板、MUST NOT 逐字段独立随机；② 一层薄静态护栏——`device_memory` SHALL 只允 2 的幂且封顶 8（**MUST NOT 提交 `6`** 等非 2 的幂）、`hardware_concurrency` SHALL 取真实值、`webgl` 模式 SHALL 不自相取消（`webgl='3'` 时 MUST NOT 同传会被忽略的 `webgl_config`）、`webrtc` SHALL 为替换成代理 IP 的模式、字体 MUST NOT 跨 OS 混装、**时区 SHALL based-on-IP；语言 SHALL 钉死规范 `en-US`**（`language_switch` 关闭 + 显式 `language=['en-US']`，与代理 IP 派生语言解耦，理由：界面语言随 IP 漂反而制造「美国代理号突现越南语 UI」的不自洽，且钉死英文让下游文字识别语言稳定）、「每次启动重随机指纹」SHALL 关闭；③ 提交前 SHALL 做「声明 OS == 下发 UA 的 OS == 字体的 OS == renderer 家族的 OS」四者一致断言，任一不符 SHALL **诚实拒绝创建**、MUST NOT 提交一个自相矛盾的环境。**`language` MUST NOT 进入该四者一致断言集**——钉死 en-US 不因与 OS/IP 不一致而被拒建（语言不是 OS 一致性字段）。aidcp 侧 MUST NOT 为「让检测方看着均衡」而强行匹配「CPU 性能档 == GPU 性能档」（检测方不查此项）。

#### Scenario: 委托生成 + 护栏放行合法自洽环境
- **WHEN** 运维选定一个整机模板（含 OS）点「创建环境」，且模板经护栏与四者一致断言校验通过
- **THEN** 桌面外壳以委托生成为主 + 模板锁定的 OS/整机字段构造 `fingerprint_config`，经 `user/create` 建号成功并返回分身 id

#### Scenario: 非法取值在提交前被护栏拦下
- **WHEN** 待提交的 `fingerprint_config` 含 `device_memory=6`（或其它非 2 的幂 / 超 8 的值）
- **THEN** 护栏在提交前诚实拒绝，MUST NOT 把该值发给 `user/create`

#### Scenario: OS 不自洽在提交前拒建
- **WHEN** 模板声明 Windows 但下发 UA / 字体 / renderer 家族任一不是 Windows（四者一致断言不符）
- **THEN** 桌面外壳诚实拒绝创建并说明不一致点，MUST NOT 提交该矛盾环境

#### Scenario: 语言钉死规范 en-US、时区仍随 IP
- **WHEN** 构造 `fingerprint_config` 时护栏落定语言与时区
- **THEN** `language_switch` 关闭且 `language=['en-US']`（不随代理 IP），而时区仍 based-on-IP；`language` 不参与四者一致断言，pin en-US 不因与 IP/OS 语言不符而被拒建

### Requirement: 写能力经独立写客户端 + 硬编码 allowlist，绝不触碰浏览器生命周期

程序化创建 SHALL 经一个与只读 `ads-local-api` **分离的**「写客户端」发起，该写客户端 SHALL 用**硬编码 allowlist** 只放行 `user/create`、`user/delete` 与 `user/update`，并 MUST NOT 放行 `group/create`；任何 `browser/start` / `browser/stop` / `browser/active` 等浏览器生命周期路径 SHALL 在该客户端内**直接抛错**（生命周期仍是核心子进程单写职责），并 SHALL 有回归断言证明该写客户端到不了分组创建与生命周期端点（红线靠测试守、不靠注释）。`user/update` 的放行 SHALL **仅限改代理或改环境名两种用途**：写客户端 SHALL 只提供两个 update 封装——改代理封装只构造 `{ user_id, user_proxy_config }` 两键 body，改名封装只构造 `{ user_id, name }` 两键 body；两者 MUST NOT 接受或透传任何其他字段（fingerprint / remark / 分组一概不经此口，代理与名字亦互不混入对方 body），使「放行 update ≠ 打开整张写面」仍为结构性保证，并 SHALL 有回归断言分别覆盖两个封装的 body 键集。写客户端对本地 API 的调用 SHALL 复用与只读侧相同的 ≥1 秒串行节流；本机核心子进程活跃时 SHALL NOT 并发跑批量写（避免与核心的启动/回收调用叠加撞每秒限速），撞限速 SHALL 诚实降级、MUST NOT 假成功。

#### Scenario: 写客户端拒绝分组创建与生命周期端点
- **WHEN** 代码路径尝试经写客户端调用 `group/create` 或 `browser/start`（或 stop/active）
- **THEN** 写客户端直接抛错、不发出该请求，且有回归断言覆盖这些禁令

#### Scenario: 改代理封装只能带代理两键
- **WHEN** 代码路径经写客户端的改代理封装提交（无论调用方传入什么额外字段）
- **THEN** 发出的 body 只含 `user_id` 与 `user_proxy_config` 两键，`name` 及其他字段不出现在请求中，且有回归断言覆盖

#### Scenario: 改名封装只能带改名两键
- **WHEN** 代码路径经写客户端的改名封装提交（无论调用方传入什么额外字段）
- **THEN** 发出的 body 只含 `user_id` 与 `name` 两键，`user_proxy_config` / `fingerprint_config` / `remark` 及其他字段不出现在请求中，且有回归断言覆盖

#### Scenario: 核心活跃时不并发批量写
- **WHEN** 本机核心子进程正在运行且运维触发创建
- **THEN** 写客户端串行、与核心的本地 API 调用不在同秒并发；若仍撞每秒限速则诚实降级提示重试，MUST NOT 假成功

### Requirement: 凭据只内存持有、绝不明文落盘、日志脱敏

AdsPower API key 与代理账号密码 SHALL 仅在创建 / 改代理批处理期间**内存持有**，MUST NOT 明文写入 `settings.json` 或任何台账/文档；台账 SHALL 只存非密的代理摘要。`user/create` 与 `user/update` 的 POST 请求体 SHALL NOT 被整体 stringify 进日志/错误，日志与错误透传层 SHALL 显式脱敏 `proxy_user`/`proxy_password` 与 `Authorization`。渲染层 MUST NOT 回显已存代理密码（`user/list` 本就不回传密码，编辑表单密码位以空态呈现）。确需持久化敏感值时 SHALL 用 OS keychain（如 `safeStorage`），MUST NOT 写明文设置。

#### Scenario: 代理账密不落盘不进日志
- **WHEN** 创建或改代理时携带了代理账号密码，且某条 `user/create` / `user/update` 返回错误
- **THEN** 账密只内存持有、不写入 settings/台账，错误信息中 `proxy_password`/`Authorization` 被脱敏，MUST NOT 出现在日志/UI

### Requirement: 删除环境仅经界面逐个二次确认触发，绝不自动 / 批量

桌面外壳 MAY 提供删除环境（`user/delete`）功能，但 SHALL 仅由运维在桌面界面上**逐个、二次确认**触发：第一次点击仅进入待确认态（如「确认删除?」，短时后自动收回）、**第二次点击才执行**删除。删除前 SHALL 明确警示**不可恢复**（若该环境已登录账号，其登录态 / cookie 一并丢失）。删除 MUST NOT 自动触发、MUST NOT 批量执行、MUST NOT 由本机 ledger / 过期状态驱动。管理后台、Cloud、远程 maintenance、客户端 outbox 与 Cloud→Edge 命令 MUST NOT 触发 AdsPower 环境删除。桌面写客户端对 `user/delete` 放行、但对浏览器生命周期（`browser/start|stop|active`）SHALL 仍**直接抛错**（M7 不变）。桌面凭据只在内存持有，日志须脱敏。

#### Scenario: 桌面删除需二次确认
- **WHEN** 运维在桌面客户端点击某环境的删除按钮
- **THEN** 第一次点击仅进入「确认删除?」待确认态、不发任何删除请求；第二次点击才执行本地 `user/delete`，删前已警示不可恢复

#### Scenario: 管理后台不提供删除来源
- **WHEN** 管理员查看 Cloud 环境资产或直接请求曾存在的 Panel 删除路径
- **THEN** 系统不触发 AdsPower `user/delete`，不创建 Edge maintenance 责任且不发送 Cloud→Edge 删除命令

#### Scenario: 绝不自动 / 批量删
- **WHEN** 任何非桌面界面逐环境明确二次确认的路径（自动清理 / 批量 / ledger / Cloud 管理后台）尝试删除
- **THEN** MUST NOT 触发 `user/delete`

#### Scenario: 写客户端仍禁浏览器生命周期
- **WHEN** 代码路径尝试经桌面写客户端调用 `browser/start|stop|active`
- **THEN** 直接抛错、不发出，保留 M7 生命周期红线

### Requirement: 代理可在客户端配置：创建可选填、已有环境可增改、无代理如实标注

桌面外壳 SHALL 允许在客户端环境管理中完成代理配置：创建时表单提供可选代理区块；已有环境在环境行提供“代理”入口。代理类型 SHALL 为 `http`、`https`、`socks5` 或显式“无代理”，结构化输入包含 host、port 与可选账密。单环境编辑 SHALL 额外提供“快速粘贴”，接受与批量建号一致的 `host:port`、`host:port:username:password` 和 `host----port----username----password` 单行格式，解析成功后回填结构化字段供确认和修改。

单行与多行代理 SHALL 共用主进程通用解析/归一真源，校验类型枚举、host 非空、port 为 1-65535 整数以及有密码必须有用户名。任一不合法 SHALL 诚实拒绝并只返回安全行号和字段原因，MUST NOT 回显原始代理行、静默降级成 `no_proxy` 或截断非法字段后照发。密码中的后续冒号或 `----` SHALL 归入密码尾部。已保存代理密码 MUST NOT 以明文呈现；系统 MAY 在重新校验当前客户作用域后精确读取并仅回填到 `type=password` 遮蔽输入，以便修改其它字段时保留密码，但 MUST NOT 将其写入列表摘要、消息或日志。

保存已有环境代理 SHALL 经写客户端的 `user/update` 两键封装下发；选择“无代理” SHALL 显式下发 `{ proxy_soft: 'no_proxy' }`。未配代理 MUST NOT 阻止创建或其它环境操作。编辑已配代理的环境 SHALL 提示出口 IP、时区和地理画像变化风险；成功只 SHALL 表示 AdsPower 配置已写入并按“下次启动该环境生效”提示，MUST NOT 宣称真实出口已经验证。

#### Scenario: 单环境快速粘贴回填结构化字段
- **WHEN** 运维选择 HTTPS 并粘贴一条合法 `host:port:username:password`
- **THEN** 主进程通用解析器返回规范化 host、port、用户名和密码并回填现有编辑字段，用户仍需显式保存后才写入 AdsPower

#### Scenario: 两种分隔格式与密码尾部得到保留
- **WHEN** 运维粘贴冒号或 `----` 格式且密码包含额外同类分隔符
- **THEN** 系统把固定的 host、port、username 之后内容完整归入密码，并继续经统一归一校验

#### Scenario: 非法快速粘贴安全拒绝
- **WHEN** 单行输入缺 host、端口越界或只有密码没有用户名
- **THEN** 系统只说明格式或字段原因，不回显原始行或凭据，不修改现有结构化字段且不发出 `user/update`

#### Scenario: 已有环境改代理经受限 update 下发
- **WHEN** 运维在某环境行编辑并保存合法代理
- **THEN** 写客户端仅以 `{ user_id, user_proxy_config }` 两键 body 调用 `user/update`，成功后提示下次启动生效并刷新配置摘要

#### Scenario: 已保存密码只在遮蔽输入中保留
- **WHEN** 运维打开当前客户可见环境的代理编辑，并只修改 host 或端口
- **THEN** 系统可将精确读取的原密码回填到 `type=password` 输入后随保存原样提交，但列表、提示和日志均不显示密码明文

#### Scenario: 显式清除代理
- **WHEN** 运维在编辑中选择“无代理”并保存
- **THEN** 系统下发 `{ proxy_soft:'no_proxy' }`，环境列表摘要回到无代理状态且不阻止其它操作

### Requirement: New AdsPower profiles block geolocation permission prompts by default
The desktop shell SHALL include `location='block'` in the `fingerprint_config` sent through AdsPower `user/create` for every newly provisioned profile. It SHALL also retain `location_switch='1'` so the profile's fingerprint location follows the proxy IP. The shell MUST NOT represent `location='block'` as disabling IP-based fingerprint location, and MUST NOT broaden the proxy-only `user/update` wrapper to retrofit existing profiles.

#### Scenario: New profile receives both location settings
- **WHEN** the operator creates an AdsPower environment from any supported device template
- **THEN** the `user/create` payload contains `fingerprint_config.location='block'`
- **AND** it contains `fingerprint_config.location_switch='1'`

#### Scenario: Existing profile is not silently rewritten
- **WHEN** the application loads an AdsPower profile created before this change
- **THEN** it does not send a fingerprint update through the proxy-only `user/update` path
- **AND** the existing profile remains unchanged unless the operator explicitly recreates or configures it outside that path

### Requirement: 环境名跟随真实账号昵称——建号不写死模板名、登录后渐进改名

桌面外壳 SHALL 使 AdsPower 环境名向该环境登录账号的**真实平台昵称**看齐，作为运维辨识环境的显示名，具体：

① **建号不写死模板名**：创建环境时 SHALL NOT 把整机模板标识（如 `win11-intel`）写作环境名——`user/create` MUST NOT 下发一个等于设备模板 key 的 `name`，交由 AdsPower 默认命名或留空（登录前空窗期的显示名由左栏兜底，见 `edge-fleet-console`）。

② **登录后改名跟随昵称**：当核心读出该环境的真实登录昵称（`account-identity-resolution` 定义的显示名，昵称仅作显示、非账号主键）后，若 AdsPower 环境名与该昵称不一致，桌面外壳 SHALL 经写客户端的改名封装把该环境名改为昵称。视频号 SHALL 在冷启动恢复已保存会话或首次扫码绑定后，只有当前会话身份已验证匹配时才把 `identity.displayName` 作为真实平台昵称送入同一改名链；身份未验证、昵称为空或身份不匹配时 MUST NOT 触发改名。

③ **幂等去抖**：AdsPower 环境名已与昵称一致时 MUST NOT 重复发起 `user/update` 改名。

④ **限速合规**：改名 SHALL 复用写客户端 ≥1s 串行节流，MUST NOT 与核心的本地 API 调用同秒并发撞每秒限速。

⑤ **诚实降级**：改名失败（不可达 / `code≠0` / 撞限速）SHALL 诚实降级——保持原名、后续再有机会重试，MUST NOT 假成功、MUST NOT 阻塞或中断该环境的浏览闭环。

⑥ **存量渐进、不即时批量、不依赖云端**：既有环境 SHALL 靠同一「登录读昵称 → 按需改名」路径**随正常运营渐进**改到位；本 change MUST NOT 引入即时一次性批量改名，MUST NOT 引入云端侧 profile→昵称导出依赖（改名所需昵称由该环境自身的身份读取本地提供）。

#### Scenario: 建号不写死模板名
- **WHEN** 运维经客户端创建一个新指纹环境
- **THEN** `user/create` 的 body 不含等于设备模板 key 的 `name`（不下发 name 或用 AdsPower 默认命名），左栏该环境登录前的显示名不呈现设备模板名

#### Scenario: 登录后改名跟随昵称
- **WHEN** 某环境登录后核心读出真实登录昵称，且当前 AdsPower 环境名与该昵称不一致
- **THEN** 桌面外壳经改名封装把该环境改名为昵称，下次 `user/list` 读回该环境名即为昵称

#### Scenario: 视频号冷启动验证身份后改名
- **WHEN** 视频号环境冷启动恢复已保存会话或完成首次扫码绑定，并验证当前会话身份匹配且昵称为“tom白”
- **THEN** 核心向桌面外壳上报真实身份昵称，桌面外壳沿用既有改名封装把该 AdsPower 环境名更新为“tom白”

#### Scenario: 视频号身份未验证时不改名
- **WHEN** 视频号环境仍在身份验证、昵称为空或当前会话身份不匹配
- **THEN** 核心 MUST NOT 发出可驱动环境改名的身份事件，AdsPower 环境名保持不变

#### Scenario: 名字已一致不重复写
- **WHEN** 某环境的 AdsPower 名已等于其真实昵称，核心再次上报同一昵称
- **THEN** 桌面外壳 MUST NOT 再发起 `user/update` 改名

#### Scenario: 改名失败诚实降级
- **WHEN** 改名的 `user/update` 不可达或返回 `code≠0` 或撞每秒限速
- **THEN** 该环境保持原名、不假成功、不阻塞其浏览闭环，后续有机会再试改名

#### Scenario: 存量渐进而非即时批量
- **WHEN** 一批既有环境的名字仍是模板名 / AdsPower 默认名
- **THEN** 它们各自在下次登录读出昵称时被逐个改名，桌面外壳 MUST NOT 触发一次性批量改名或云端昵称导出

### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、预置分组/备注、单飞互斥

本 change 建的所有平台分身 SHALL 归入运营预先创建且名称严格等于 `aidcp` 的 AdsPower 分组。每次桌面应用会话第一次建立托管 AdsPower 运行时时，桌面外壳 SHALL 先经随包 CLI 自身的 `status`/`stop` 控制路径有界停止其登记的既有 CLI daemon，并确认停止完成后再用当前托管配置启动新 daemon；查询失败、停止失败或停止超时 SHALL 阻止继续创建并给出可操作错误。该受控重置每个成功建立的应用会话 SHALL 至多执行一次，MUST NOT 通过进程名扫描、`pkill` 或任意 PID 猜测去关闭独立 AdsPower 桌面应用或其他进程。

托管运行时建立后，CLI 实际上报的 API base SHALL 是本会话创建路径的单一权威；历史 renderer/settings `apiBase` MUST NOT 覆盖该 base 或把 `group/list`、`user/create` 导向其他端口。桌面外壳 SHALL 经该权威 base 的 `group/list` 解析预置分组当前 id，并以名称严格等于 `aidcp` 作为任何 `user/create` 前的自证。桌面外壳 MUST NOT 调用 `group/create`、MUST NOT生成后缀分组、MUST NOT 因分组查询失败或查无分组而继续 `user/create`。查询失败 SHALL 保留真实查询错误；查询成功但新建立的当前运行时仍未找到 `aidcp` SHALL 明确提示当前运行时账号/权限空间缺少该预置分组，不得把它表述成已经创建成功。

创建时 SHALL 把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入、随 `user/list` 读回）。「有哪些分身、各绑什么代理」SHALL 以 AdsPower `user/list` 为**唯一账本**读取，MUST NOT 另建本机 write-ahead 台账（与 AdsPower 自身记录重复，徒增丢失 / 损坏 / 与 AdsPower 走样的同步面）。理由：号一旦登录、edge 一起即经握手把账号↔分身↔机器上报云端（见「握手载荷携带并持久化」需求），该上报已有、不重造；仅「创建后、登录前」空壳期云端不可见，而这段 AdsPower `user/list` 本就记着分身 + 各自代理，是现成账本。代理 SHALL 为**创建时可选项**：表单填了合法代理即随 `user/create` 下发 `user_proxy_config`，不填 SHALL 默认 `no_proxy` 建号（与历史行为逐位等价）；代理输入的归一与校验见「代理可在客户端配置」需求。创建动作在主进程 SHALL **单飞互斥**（同一时刻只一个创建在途，重入诚实返回「进行中」），渲染层触发控件 SHALL 在请求在途时禁用。崩溃后 SHALL 据下次 `user/list` 直接看见已建分身（在预置 `aidcp` 分组、带 `remark`，不丢账）。

#### Scenario: 既有 CLI daemon 在新会话中被有界重置
- **WHEN** 新桌面应用会话第一次建立托管 AdsPower 运行时，且随包 CLI 的 `status` 发现已登记 daemon
- **THEN** 桌面外壳先调用该 CLI 的 `stop` 并确认 daemon 已停止，再用当前托管配置启动新 daemon
- **AND** 本次成功建立的应用会话后续确保运行时时不重复停止该 daemon

#### Scenario: 已登记 daemon 无法停止时停止创建
- **WHEN** 首次托管运行时建立中的 CLI `stop` 失败，或有界确认后 daemon 仍在运行
- **THEN** 桌面外壳诚实提示 CLI daemon 无法停止及原始原因，并且不调用 `group/list`、`group/create` 或 `user/create`

#### Scenario: 独立 AdsPower 桌面占用默认端口时使用托管实际端口
- **WHEN** 独立 AdsPower 桌面或其他进程占用 `50325`，随包 CLI 启动后实际上报另一端口，且历史表单仍保存 `50325`
- **THEN** 创建路径以 CLI 实际上报端口为权威调用 `group/list` 与 `user/create`
- **AND** 桌面外壳不关闭独立 AdsPower 桌面，也不把创建请求发往历史表单端口

#### Scenario: 所有平台的新环境进入同一个预置分组
- **WHEN** 运维选择任一受支持平台并创建新环境
- **THEN** 桌面外壳在当前托管运行时解析名称严格等于 `aidcp` 的现有分组 id，并把该 id 传给 `user/create`
- **AND** 桌面外壳不调用 `group/create`

#### Scenario: 新建立运行时仍缺少预置分组时停止创建
- **WHEN** 当前托管运行时已重新建立且 `group/list` 查询成功，但仍看不到名称严格等于 `aidcp` 的分组
- **THEN** 桌面外壳明确报告当前运行时账号/权限空间缺少预置分组，并且不调用 `group/create` 或 `user/create`

#### Scenario: 崩溃后据 user/list 不丢账
- **WHEN** `user/create` 已成功建出分身但紧接着进程崩溃 / 关窗
- **THEN** 下次读 `user/list` 直接看见该分身（在预置 `aidcp` 分组、带 `remark`），无需本机台账即可续接

#### Scenario: 重复点击不双建
- **WHEN** 运维在创建在途时再次点击「创建环境」
- **THEN** 主进程单飞互斥拒绝重入、渲染层控件已禁用，MUST NOT 交错跑出两个各绑同一代理的分身

### Requirement: 预置分组失效时只重新解析一次

When AdsPower rejects `user/create` because the cached pre-provisioned `aidcp` group is deleted or archived, the desktop app SHALL clear the cached group id, re-resolve the exact pre-provisioned group through AdsPower `group/list`, and retry environment creation at most once only when a different current group id is visible. The app MUST NOT call `group/create`, MUST NOT generate a replacement group name, MUST NOT retry unrelated creation failures, and MUST still surface the final AdsPower failure honestly if the retry fails.

#### Scenario: Cached pre-provisioned group was replaced
- **WHEN** the desktop app attempts to create an AdsPower environment using a cached `aidcp` group id
- **AND** AdsPower rejects `user/create` with `group is deleted or archived`
- **AND** a subsequent `group/list` exposes a different current `aidcp` group id
- **THEN** the app clears the cached id and retries `user/create` once with the current id without calling `group/create`

#### Scenario: No current pre-provisioned group is visible
- **WHEN** AdsPower rejects `user/create` because the cached group is deleted or archived
- **AND** re-resolving does not expose a different current `aidcp` group id
- **THEN** the app reports that the pre-provisioned group is unavailable and does not call `group/create` or retry `user/create`

#### Scenario: Unrelated creation failure remains honest
- **WHEN** AdsPower rejects `user/create` for a reason unrelated to deleted or archived groups
- **THEN** the app reports the failure without clearing group cache or retrying

### Requirement: AdsPower-first environment creation is constrained by OS family

When creating an AdsPower environment, the desktop shell SHALL treat the operator selection as an OS-family constraint rather than a fixed complete-machine template. The shell SHALL call AdsPower `user/create` with a minimal `fingerprint_config` that constrains the requested desktop OS family and required safety policy, and it SHALL let AdsPower generate the remaining fingerprint details. The shell MUST NOT pin a small fixed set of complete machine shapes such as stable CPU, memory, screen, and renderer combinations for every new profile.

The minimal `fingerprint_config` SHALL keep only fields required for consistency and safety: the requested desktop OS family through AdsPower-supported UA OS constraints, proxy-safe WebRTC, IP-based timezone/location, blocked geolocation prompts, required noise fields, language policy, and browser kernel compatibility when required by the bundled runtime. The shell MAY keep deterministic validation for the requested OS family and for mutually exclusive WebGL modes, but it MUST NOT use that validation to reintroduce a fixed list of complete machine templates.

#### Scenario: Windows creation does not pin one complete machine shape
- **WHEN** the operator selects Windows and creates an environment
- **THEN** the `user/create` payload constrains the fingerprint to a Windows desktop UA OS family
- **AND** the payload does not include fixed `device_memory`, `hardware_concurrency`, `screen_resolution`, or fixed WebGL renderer fields from one of a small set of complete templates
- **AND** AdsPower is left responsible for generating those remaining fingerprint details

#### Scenario: macOS creation does not pin one complete machine shape
- **WHEN** the operator selects macOS and creates an environment
- **THEN** the `user/create` payload constrains the fingerprint to a macOS desktop UA OS family
- **AND** the payload does not include fixed `device_memory`, `hardware_concurrency`, `screen_resolution`, or fixed WebGL renderer fields from one of a small set of complete templates
- **AND** AdsPower is left responsible for generating those remaining fingerprint details

#### Scenario: unsafe OS requests are rejected before AdsPower writes
- **WHEN** the creation request names an unsupported OS family
- **THEN** the shell rejects the request before calling `user/create`
- **AND** it reports the unsupported OS honestly instead of falling back to a different OS

### Requirement: Facebook batch creation chooses OS families, not fixed machine templates

Facebook batch creation SHALL assign each planned account an OS family independently from the supported OS-family set. The batch planner MUST ignore renderer-provided fixed machine-template values, and MUST NOT sample from a five-item complete-machine template list. The selected OS family SHALL be carried through the same single-profile creation path and the same AdsPower-first fingerprint construction used by ordinary single creation.

#### Scenario: batch planning samples only OS families
- **WHEN** Facebook batch planning is requested for multiple accounts
- **THEN** each planned item carries one supported OS-family key
- **AND** no planned item carries a fixed complete-machine template key such as CPU/memory/screen/renderer shape

#### Scenario: renderer template values cannot override batch OS-family planning
- **WHEN** the renderer submits a stale fixed machine-template value with a Facebook batch request
- **THEN** the main process ignores that value
- **AND** it uses only the supported OS-family set for each planned account

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

### Requirement: Facebook 单建与批量建环境默认开启环境级慢启动

桌面外壳经官方程序化创建链路新建 Facebook 环境时，单个创建与批量创建 SHALL 都提供一个三选一的显式运行方式——普通 / 冷启动 / 规则——并把该选择翻译成提交给 Cloud 的权威归属完成意图：选择冷启动 SHALL 提交「开启环境级慢启动」意图；选择普通或规则 MUST NOT 提交该意图；选择规则 SHALL 额外提交该环境的规则模式开启意图。三者互斥，界面 MUST NOT 允许同时选中，主进程也 MUST 拒绝同时携带慢启动与规则模式开启意图的请求。

是否允许提交这些意图 SHALL 只由主进程归一后的 `platform === 'facebook'` 决定，MUST NOT 由 renderer 自报平台能力、账号输入行数或创建模式单独决定。小红书与视频号创建 MUST NOT 提交、显示或宣称慢启动、运行方式或规则模式配置。批量创建时该选择 SHALL 对本批全部环境一致生效，逐环境提交各自的完成请求。

未选择冷启动时，创建回执 MUST 如实反映该环境未配置慢启动，MUST NOT 沿用「Facebook 创建默认开启慢启动」的旧表述。运行方式是运营的显式选择，界面 MUST NOT 为未选冷启动增加解释性告警或 Tooltip。

只有在 Cloud 已原子确认环境归属与本次提交的配置后，创建回执才 MAY 声明该环境已按所选运行方式配置。若本地环境已经创建但 Cloud 未确认，回执 MUST 如实区分本地创建、客户归属与各项配置，不得假成功，也不得为模拟事务回滚而自动删除环境。慢启动只改变每日额度上限，任何创建说明 MUST NOT 暗示动作速度、拟人程度或账号风险状态被改变。

#### Scenario: 选择冷启动的 Facebook 创建

- **WHEN** 运维选择 Facebook、运行方式选择冷启动，并以单个或批量方式创建环境
- **THEN** 每个计划项的归属完成请求都提交慢启动开启意图且不提交规则模式开启意图
- **AND** Cloud 确认后回执如实标记该环境慢启动已配置
- **AND** 每个已确认环境使用各自首次完成时的同一上海自然日起点

#### Scenario: 选择普通或规则不开启慢启动

- **WHEN** 运维选择 Facebook 且运行方式选择普通或规则
- **THEN** 归属完成请求不提交慢启动开启意图，选择规则时另提交规则模式开启意图
- **AND** 回执如实呈现该环境未配置慢启动，不出现慢启动成功声明
- **AND** 界面不为该选择追加风险告警或 Tooltip

#### Scenario: 运行方式三选一互斥

- **WHEN** 调用方绕过界面提交同时携带慢启动与规则模式开启意图的创建请求
- **THEN** 主进程诚实拒绝该请求，不发出环境创建调用，也不静默丢弃其中一项

#### Scenario: 其它平台没有运行方式概念

- **WHEN** 运维创建小红书或视频号环境
- **THEN** renderer 与主进程均不展示或提交运行方式、慢启动或规则模式选项，创建回执也不出现相关成功声明

#### Scenario: 归属失败不冒充配置成功

- **WHEN** Ads CLI / SunBrowser 环境已创建，但 Cloud 归属完成失败
- **THEN** 客户端说明该环境尚未完成权威归属，且所选运行方式与免审设置均未确认
- **AND** 不自动删除已经创建的环境

### Requirement: Facebook 新建环境提供显式批量模式且平台门禁双层生效

桌面外壳 SHALL 仅在新建环境的平台为 Facebook 时展示“单个新建 / 批量新建”方式。批量模式 SHALL 隐藏环境模板选择并接受多行 Facebook 账号资料，一行对应一个待创建环境，每行沿用既有 `email----password----2FA----cookie` 格式；其他平台 MUST NOT 展示批量入口，主进程也 MUST 拒绝任何非 Facebook 的批量创建请求，不能只依赖渲染层隐藏。

#### Scenario: Facebook 展示并进入批量模式
- **WHEN** 运维在新建环境中选择 Facebook 并切换到“批量新建”
- **THEN** 客户端展示多行账号与批量代理输入、隐藏环境模板选择，并把显式批量意图交给主进程

#### Scenario: 其他平台无批量能力
- **WHEN** 当前平台不是 Facebook，或调用方绕过界面直接提交非 Facebook 批量请求
- **THEN** 界面不展示批量入口且主进程诚实拒绝该请求，不发出 `user/create`

### Requirement: 批量账号和代理在写入前完成整批校验且凭据不泄露

批量模式 SHALL 忽略空白行并在第一条 `user/create` 前解析、校验全部非空账号行。代理类型 SHALL 只选择一次，允许 `http`/`https`/`socks5` 或显式 `no_proxy`；实际代理类型下每条代理资料 SHALL 独占一行，支持 `host:port`、`host:port:username:password` 以及等价的 `----` 分隔形式，并复用统一代理归一层校验 host、port 与可选账密。选择实际代理类型但列表为空、任一账号/代理行非法、或批次数超过剩余账号容量时 SHALL 整批拒绝且不创建任何环境。账号、2FA、cookie 与代理账密 MUST 仅在内存持有，错误、日志和 UI 回执 MUST NOT 回显原始敏感行。

#### Scenario: 合法多行输入在创建前形成计划
- **WHEN** 运维粘贴多条合法 Facebook 账号资料，选择一种代理类型并粘贴多条合法代理
- **THEN** 主进程在任何写请求前完成所有行校验并形成不落盘的内存创建计划

#### Scenario: 后置坏行不会产生部分预校验写入
- **WHEN** 账号或代理列表的任一后置行格式非法
- **THEN** 主进程以安全行号说明拒绝原因，不调用任何 `user/create`，且回执不包含该行原文或凭据

#### Scenario: 批次超过剩余账号容量时整批拒绝
- **WHEN** 已挂载账号数加本批账号数超过当前账号上限
- **THEN** 主进程在创建前拒绝整批并说明剩余容量，不创建任何环境

### Requirement: 每个批量账号随机分配完整模板并按轮次循环分配代理

批量模式 MUST 忽略调用方提供的单个模板值，并为每个账号从当前合法 `DEVICE_TEMPLATES` 清单中独立随机选择一个完整模板 key；随机单位 MUST 是整套模板，MUST NOT 独立随机拼装 OS、UA、字体、CPU、GPU 或 renderer 字段。若有 `P` 条代理，第 `i` 个账号 SHALL 使用第 `i mod P` 条代理，使第一轮依序使用全部代理后才从第一条开始第二轮；同一代理 MAY 在后续轮次对应多个账号。选择 `no_proxy` 时所有账号 SHALL 显式使用无代理配置。

#### Scenario: 五个账号轮询两条代理
- **WHEN** 批量计划包含 5 个账号和按顺序粘贴的代理 A、B
- **THEN** 账号 1-5 的代理依次为 A、B、A、B、A，第二次使用 A 只发生在第一轮 A、B 都已分配之后

#### Scenario: 每个账号只取得合法整套模板
- **WHEN** 主进程为批量账号生成创建计划
- **THEN** 每个账号独立取得 `DEVICE_TEMPLATES` 中的一个完整模板 key，渲染层模板值不影响结果，现有一致性护栏仍逐项生效

### Requirement: 批量创建保持串行单飞并诚实呈现部分成功

批量创建 SHALL 继续受主进程单飞互斥和 AdsPower 串行限速约束，并对每个计划项分别执行创建意图签发、`user/create`、客户归属确认与花名册权威回读。某一项失败时系统 SHALL 立即停止后续创建，返回失败序号、已创建的安全摘要和真实 `createdCount`；客户端 SHALL 刷新列表并保留账号/代理输入以便核对。全部成功后客户端 SHALL 显示真实创建数量并清空一次性输入。系统 MUST NOT 为模拟事务回滚而自动或批量删除已经创建的环境，也 MUST NOT 把“已创建”与“已完成客户归属/加入花名册”合并成同一成功状态。

#### Scenario: 第三项失败保留前两项真相
- **WHEN** 前两个环境已由 AdsPower 成功创建而第三项创建失败
- **THEN** 系统停止第四项及后续项，回执说明已创建 2 个及第三项失败，刷新列表、保留输入，且不自动删除前两个环境

#### Scenario: 全批成功后清空一次性输入
- **WHEN** 所有计划项均创建成功且各自归属结果已返回
- **THEN** 客户端显示真实总数、分别保留归属/花名册状态语义，并清空本次账号与代理文本

### Requirement: 环境创建不隐式触发人设设置

桌面外壳 SHALL 让 Facebook 单个/批量环境创建只负责创建与客户归属，MUST NOT 展示“创建后补齐人设”开关、批次人设语言或在创建结果后提交人设运行。客户需要批量设置人设时 SHALL 从环境栏 Facebook 筛选入口显式进入并人工确认一份人设。

#### Scenario: Facebook 批量创建环境
- **WHEN** 客户导入账号资料并批量创建 Facebook 环境
- **THEN** Edge 只创建与归属环境，不提交人设内容、补齐意图或独立语言字段

#### Scenario: 部分创建或创建失败
- **WHEN** Facebook 批量创建只完成部分环境或中途失败
- **THEN** 创建回执只表达真实环境结果，不夹带人设补齐受理、失败或等待绑定状态

### Requirement: 批量代理只作用于明确关闭环境并按预览顺序轮询分配

环境管理 SHALL 提供按需“批量代理”模式，默认环境列表 MUST NOT 常驻复选框。进入该模式后，运维 SHALL 显式选择一个或多个当前客户可见且已关闭的环境，选择一次代理类型并逐行粘贴代理。运行中、启动中或清理中的环境 SHALL 不可选择并说明原因，系统 MUST NOT 为批量改代理自动关闭环境。

renderer SHALL 冻结去重有序的明确 `user_id` 列表并在确认前展示目标数量、合法代理数量、去密映射摘要，以及“其中 N 个环境复用代理”的重复分配说明，其中 `N = max(0, targetCount - proxyCount)`；MUST NOT 使用容易被误解为循环轮数的“循环复用 N 次”。主进程 SHALL 在任何 `user/update` 前重新校验目标列表、当前客户可见范围、已知运行状态及全部代理行；若有 `P` 条代理，第 `i` 个明确目标 SHALL 使用第 `i mod P` 条代理。目标顺序 MUST 来自冻结列表，MUST NOT 因 DOM 状态分组、随后筛选变化或当前选中环境而改变。

批量写入 SHALL 复用 AdsPower 写客户端限速并串行执行。主进程只 SHALL 在某个 `user/update` 明确成功后发送当前请求的单调进度，renderer SHALL 显示 `已完成 N/M` 和简洁进度条；进度事件 MUST 绑定一次性请求标识且 MUST NOT 包含环境 ID、代理原文或凭据。任一项失败 SHALL 立即停止后续项，返回真实成功数、失败序号/原因与未执行数；系统 MUST NOT 自动回滚已成功配置、跳过失败继续扩大写入面或宣称整批原子成功。全部成功后才清空一次性代理输入；部分失败时 SHALL 保留选择和输入供核对，错误和回执 MUST NOT 包含代理原文或密码。

#### Scenario: 默认环境页不展示批量控件
- **WHEN** 运维普通打开环境管理
- **THEN** 环境列表不显示复选框；只有点击“批量代理”后才进入临时选择态

#### Scenario: 运行环境不可作为批量目标
- **WHEN** 某环境正在运行、启动或清理中
- **THEN** 批量模式将该环境标为不可选择并提示先关闭，系统不自动执行任何关闭动作

#### Scenario: 五个环境轮询两条代理
- **WHEN** 冻结目标顺序为五个环境且代理顺序为 A、B
- **THEN** 确认预览和主进程写入计划均为 A、B、A、B、A，并显示“其中 3 个环境复用代理”，不把 3 表述成循环轮数

#### Scenario: 执行中只按确认成功项推进
- **WHEN** 共修改 11 个环境且主进程已收到前 4 个 `user/update` 的成功结果
- **THEN** 当前请求显示“正在按顺序修改… 已完成 4/11”和对应进度条，MUST NOT 提前计入第 5 个环境或显示估算剩余时间

#### Scenario: 失败后进度停在实际成功数
- **WHEN** 前 4 个环境成功而第 5 个环境失败
- **THEN** 最终界面保留“已完成 4/11”的真实进度并说明第 5 个失败及未执行数量，旧请求进度不得覆盖该结果

#### Scenario: 筛选变化不能扩大批量目标
- **WHEN** 运维选定目标后平台筛选、状态分组或当前环境发生变化
- **THEN** 最终请求仍只包含冻结的明确 ID 顺序，MUST NOT 把新出现或新可见环境自动加入批次

#### Scenario: 后置坏代理在写入前拒绝整批
- **WHEN** 代理列表任一后置行端口或鉴权格式非法
- **THEN** 主进程在第一条 `user/update` 前按安全行号拒绝整批，不修改任何环境且不回显凭据

#### Scenario: 中途失败诚实停止并保留部分成功
- **WHEN** 前两个环境更新成功而第三个环境被 AdsPower 拒绝
- **THEN** 系统停止第四个及后续环境，回执说明成功 2 个、第三项失败和真实未执行数，不自动回滚前两个，也不清空输入

#### Scenario: 全批成功只声明配置写入
- **WHEN** 所有目标的 `user/update` 都返回成功
- **THEN** 系统显示真实成功数并清空一次性输入，文案只说明代理配置已更新且下次启动生效，MUST NOT 宣称出口 IP 已验证

### Requirement: Environment proxy creation and editing SHALL synchronize the Cloud authority
The user-entered proxy configuration SHALL remain the creation input sent to AdsPower. After AdsPower creates the profile, Edge SHALL include the same configured or explicit no-proxy authority in provisioning completion. For an existing environment edit, Edge SHALL commit the Cloud authority with revision comparison before updating the AdsPower execution copy.

#### Scenario: New environment preserves the entered proxy
- **WHEN** a user creates an environment with a validated proxy
- **THEN** Edge SHALL create the AdsPower profile with that proxy
- **AND** SHALL complete Cloud provisioning with the same original proxy authority

#### Scenario: New environment explicitly has no proxy
- **WHEN** a user creates an environment without a proxy
- **THEN** Edge SHALL create the AdsPower profile without a proxy
- **AND** SHALL complete Cloud provisioning with explicit `no_proxy`

#### Scenario: Existing environment edit is Cloud-first
- **WHEN** a user saves a new proxy for an owned existing environment
- **THEN** Edge SHALL first write the exact Cloud authority using the observed revision
- **AND** only after Cloud accepts the write SHALL Edge update AdsPower

#### Scenario: AdsPower update fails after Cloud commit
- **WHEN** Cloud accepts an existing-environment proxy edit but AdsPower rejects the execution-copy update
- **THEN** Edge SHALL report that Cloud is authoritative and AdsPower synchronization failed
- **AND** the next managed start SHALL overwrite AdsPower from the Cloud authority

#### Scenario: Cloud write fails
- **WHEN** Cloud rejects or cannot persist a creation completion or proxy edit
- **THEN** Edge SHALL NOT report the proxy authority as saved
- **AND** an existing-environment edit SHALL NOT update AdsPower

### Requirement: Facebook 创建提供可选的全局免审并随归属完成原子写入

桌面外壳 SHALL 在 Facebook 单个与批量创建表单中提供一个可选的全局免审开关，默认关闭。勾选 SHALL 使归属完成请求携带该环境的评论审批覆盖模式 `auto_approve_all`，未勾选 MUST NOT 携带该字段或以任何形式提交 `source_rules` 之外的扩权意图。批量创建时该开关 SHALL 对本批全部环境一致生效。

该开关 MUST 仅在归一平台为 Facebook 时展示与提交；其它平台 MUST NOT 展示，主进程也 MUST 拒绝非 Facebook 的免审创建意图，不能只依赖渲染层隐藏。它与运行方式三选一相互独立，任一运行方式下都 MAY 勾选。

免审只免去评论提交前的第二次人工审核。创建界面与回执 MUST NOT 暗示它放宽风险控制、每日配额、去重、目标复核或平台确认，也 MUST NOT 在 Cloud 未确认前声明该环境已免审。

#### Scenario: 批量创建统一开启免审

- **WHEN** 运维在 Facebook 批量创建中勾选全局免审并粘贴多行账号资料
- **THEN** 每个计划项的归属完成请求都携带 `auto_approve_all`
- **AND** Cloud 逐环境确认后回执才标记该环境免审已配置

#### Scenario: 默认不勾选不提交扩权意图

- **WHEN** 运维创建 Facebook 环境但未勾选全局免审
- **THEN** 归属完成请求不携带审批模式字段，环境保持按来源规则
- **AND** 回执不出现任何免审声明

#### Scenario: 其它平台没有免审入口

- **WHEN** 当前平台不是 Facebook，或调用方绕过界面直接提交非 Facebook 的免审创建意图
- **THEN** 界面不展示该开关且主进程诚实拒绝该请求

#### Scenario: 云端未确认不宣称免审生效

- **WHEN** 环境已在本机创建但 Cloud 归属完成未确认
- **THEN** 客户端如实说明免审未确认，MUST NOT 呈现为已生效

### Requirement: Facebook provisioning persists the selected primary surface

The client provisioning request for a Facebook environment SHALL carry one primary browse surface independent from the selected operation mode. Cloud SHALL validate the value, persist it atomically with the environment's operation policy and ownership, and return the committed surface projection. The client creation form SHALL preselect Reels.

#### Scenario: Default creation persists Reels

- **WHEN** a user creates a Facebook environment without changing the preselected surface control
- **THEN** the request carries `reels`
- **AND** Cloud returns the committed Reels surface with the new environment

#### Scenario: Explicit Feed creation persists Feed

- **WHEN** a user selects Feed before creating the Facebook environment
- **THEN** Cloud persists and returns Feed without changing the selected operation mode

#### Scenario: Non-Facebook creation rejects a surface intent

- **WHEN** a provisioning request for another platform carries a Facebook primary surface
- **THEN** Cloud rejects the request without partially creating or assigning the environment

### Requirement: Facebook first-login TOTP is brokered as a profile-bound one-time value

Electron main SHALL provide a named first-login TOTP operation only to the currently managed child and bind it to that child's exact AdsPower profile id. The operation SHALL query AdsPower V2 for exactly that profile, require one successful exact-id match, extract the stored `fakey` only in main-process memory, compute the TOTP for the caller's validated Facebook server-time window, and return only the six-digit code and non-secret validity timestamps. It MUST NOT return the username, password, 2FA key, cookies, proxy fields, or raw AdsPower response to the child, and MUST NOT add the sensitive V2 profile-list response to the generic AdsPower child broker.

#### Scenario: Exact managed profile receives one fresh code
- **WHEN** the current managed child requests TOTP for its bound Facebook AdsPower profile and a validated current server-time window
- **THEN** Electron requires exactly one matching V2 profile record, computes a six-digit code for that window, and returns only the code plus validity timestamps over the private correlated IPC reply

#### Scenario: Child cannot select another profile
- **WHEN** a managed child supplies, implies, or attempts to query a profile id different from its bound environment
- **THEN** Electron rejects the request without reading or returning login material for either profile

#### Scenario: Raw profile material never crosses the broker boundary
- **WHEN** AdsPower returns a profile record containing username, password, `fakey`, cookies, proxy fields, or other metadata
- **THEN** Electron projects only a generated code and validity timestamps into the reply
- **AND** raw response bodies and secret fields MUST NOT appear in child messages, settings, logs, UI receipts, Cloud messages, errors, or OpenSpec task records

#### Scenario: Missing or ambiguous 2FA material fails closed
- **WHEN** AdsPower is unavailable, returns a nonzero code, returns zero or multiple matches, returns a mismatched profile id, or the exact profile lacks a valid Base32 `fakey`
- **THEN** Electron returns only a safe bounded failure reason
- **AND** edge MUST NOT use another profile, a persisted copy, an old code, or a guessed key

#### Scenario: Server-time request is outside the current bounded window
- **WHEN** the requested Facebook server time is malformed or outside the allowed skew from the current request
- **THEN** Electron rejects code generation and returns no secret-derived value

