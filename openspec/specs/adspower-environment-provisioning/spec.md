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

程序化创建 SHALL 经一个与只读 `ads-local-api` **分离的**「写客户端」发起，该写客户端 SHALL 用**硬编码 allowlist** 只放行 `user/create`、`group/create`、`user/delete` 与 `user/update`，任何 `browser/start` / `browser/stop` / `browser/active` 等浏览器生命周期路径 SHALL 在该客户端内**直接抛错**（生命周期仍是核心子进程单写职责），并 SHALL 有回归断言证明该写客户端到不了生命周期端点（红线靠测试守、不靠注释）。`user/update` 的放行 SHALL **仅限改代理或改环境名两种用途**：写客户端 SHALL 只提供两个 update 封装——改代理封装只构造 `{ user_id, user_proxy_config }` 两键 body，改名封装只构造 `{ user_id, name }` 两键 body；两者 MUST NOT 接受或透传任何其他字段（fingerprint / remark / 分组一概不经此口，代理与名字亦互不混入对方 body），使「放行 update ≠ 打开整张写面」仍为结构性保证，并 SHALL 有回归断言分别覆盖两个封装的 body 键集。写客户端对本地 API 的调用 SHALL 复用与只读侧相同的 ≥1 秒串行节流；本机核心子进程活跃时 SHALL NOT 并发跑批量写（避免与核心的启动/回收调用叠加撞每秒限速），撞限速 SHALL 诚实降级、MUST NOT 假成功。

#### Scenario: 写客户端拒绝生命周期端点
- **WHEN** 代码路径尝试经写客户端调用 `browser/start`（或 stop/active）
- **THEN** 写客户端直接抛错、不发出该请求，且有回归断言覆盖此禁令

#### Scenario: 改代理封装只能带代理两键
- **WHEN** 代码路径经写客户端的改代理封装提交（无论调用方传入什么额外字段）
- **THEN** 发出的 body 只含 `user_id` 与 `user_proxy_config` 两键，`name` 及其他字段不出现在请求中，且有回归断言覆盖

#### Scenario: 改名封装只能带改名两键
- **WHEN** 代码路径经写客户端的改名封装提交（无论调用方传入什么额外字段）
- **THEN** 发出的 body 只含 `user_id` 与 `name` 两键，`user_proxy_config` / `fingerprint_config` / `remark` 及其他字段不出现在请求中，且有回归断言覆盖

#### Scenario: 核心活跃时不并发批量写
- **WHEN** 本机核心子进程正在运行且运维触发创建
- **THEN** 写客户端串行、与核心的本地 API 调用不在同秒并发；若仍撞每秒限速则诚实降级提示重试，MUST NOT 假成功

### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、专用分组/备注、单飞互斥

本 change 建的分身 SHALL 归入一个专用分组，创建时 SHALL 把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入、随 `user/list` 读回）。「有哪些分身、各绑什么代理」SHALL 以 AdsPower `user/list` 为**唯一账本**读取，MUST NOT 另建本机 write-ahead 台账（与 AdsPower 自身记录重复，徒增丢失 / 损坏 / 与 AdsPower 走样的同步面）。理由：号一旦登录、edge 一起即经握手把账号↔分身↔机器上报云端（见「握手载荷携带并持久化」需求），该上报已有、不重造；仅「创建后、登录前」空壳期云端不可见，而这段 AdsPower `user/list` 本就记着分身 + 各自代理，是现成账本。代理 SHALL 为**创建时可选项**：表单填了合法代理即随 `user/create` 下发 `user_proxy_config`，不填 SHALL 默认 `no_proxy` 建号（与历史行为逐位等价）；代理输入的归一与校验见「代理可在客户端配置」需求。创建动作在主进程 SHALL **单飞互斥**（同一时刻只一个创建在途，重入诚实返回「进行中」），渲染层触发控件 SHALL 在请求在途时禁用。崩溃后 SHALL 据下次 `user/list` 直接看见已建分身（在专用分组、带 `remark`，不丢账）。

#### Scenario: 崩溃后据 user/list 不丢账
- **WHEN** `user/create` 已成功建出分身但紧接着进程崩溃 / 关窗
- **THEN** 下次读 `user/list` 直接看见该分身（在专用分组、带 `remark`），无需本机台账即可续接

#### Scenario: 重复点击不双建
- **WHEN** 运维在创建在途时再次点击「创建环境」
- **THEN** 主进程单飞互斥拒绝重入、渲染层控件已禁用，MUST NOT 交错跑出两个各绑同一代理的分身

### Requirement: 凭据只内存持有、绝不明文落盘、日志脱敏

AdsPower API key 与代理账号密码 SHALL 仅在创建 / 改代理批处理期间**内存持有**，MUST NOT 明文写入 `settings.json` 或任何台账/文档；台账 SHALL 只存非密的代理摘要。`user/create` 与 `user/update` 的 POST 请求体 SHALL NOT 被整体 stringify 进日志/错误，日志与错误透传层 SHALL 显式脱敏 `proxy_user`/`proxy_password` 与 `Authorization`。渲染层 MUST NOT 回显已存代理密码（`user/list` 本就不回传密码，编辑表单密码位以空态呈现）。确需持久化敏感值时 SHALL 用 OS keychain（如 `safeStorage`），MUST NOT 写明文设置。

#### Scenario: 代理账密不落盘不进日志
- **WHEN** 创建或改代理时携带了代理账号密码，且某条 `user/create` / `user/update` 返回错误
- **THEN** 账密只内存持有、不写入 settings/台账，错误信息中 `proxy_password`/`Authorization` 被脱敏，MUST NOT 出现在日志/UI

### Requirement: 删除环境仅经界面逐个二次确认触发，绝不自动 / 批量

桌面外壳 MAY 提供删除环境（`user/delete`）功能，但 SHALL 仅由运维在界面上**逐个、二次确认**触发：第一次点击仅进入待确认态（如「确认删除?」，短时后自动收回）、**第二次点击才执行**删除。删除前 SHALL 明确警示**不可恢复**（若该环境已登录账号，其登录态 / cookie 一并丢失）。删除 MUST NOT 自动触发、MUST NOT 批量执行、MUST NOT 由本机 ledger / 过期状态驱动。写客户端对 `user/delete` 放行、但对浏览器生命周期（`browser/start|stop|active`）SHALL 仍**直接抛错**（M7 不变）。凭据同建号：只内存持有、日志脱敏。

#### Scenario: 删除需二次确认
- **WHEN** 运维点击某环境的删除按钮
- **THEN** 第一次点击仅进入「确认删除?」待确认态、不发任何删除请求；第二次点击才执行 `user/delete`，删前已警示不可恢复

#### Scenario: 绝不自动 / 批量删
- **WHEN** 任何非「运维逐个二次确认」的路径（自动清理 / 批量 / ledger 驱动）
- **THEN** MUST NOT 触发删除

#### Scenario: 写客户端仍禁浏览器生命周期
- **WHEN** 代码路径尝试经写客户端调用 `browser/start|stop|active`
- **THEN** 直接抛错、不发出（放宽 `user/delete` 不动 M7 生命周期红线）

### Requirement: 代理可在客户端配置：创建可选填、已有环境可增改、无代理如实标注

桌面外壳 SHALL 允许在客户端内完成代理配置：**创建时**表单提供可选代理区块（类型 `http`/`https`/`socks5` + host/port + 可选账密，默认「无代理」）；**已有环境**提供逐环境的「代理」编辑入口，读回现配置的非密字段预填、保存经写客户端的 `user/update` 封装下发。代理输入 SHALL 经统一归一层校验（类型枚举、host 非空、port 为 1-65535 整数、有密码必须有用户名），任一不合法 SHALL **诚实拒绝提交**（创建时拒建、编辑时拒存并说明原因），MUST NOT 静默降级成 `no_proxy` 或砍掉非法字段后照发。选「无代理」保存 SHALL 显式下发 `{ proxy_soft: 'no_proxy' }`（支持清除既有代理）。桌面外壳 SHALL NOT 因未配代理而阻止创建：未配代理时 SHALL 给出提醒，但仍允许创建；环境列表 SHALL 如实呈现「无代理」状态，该标注 MUST NOT 拦截任何操作。编辑已配代理的环境时 SHALL 提示改代理对已养成账号画像的影响（出口 IP / 时区 / 地理随代理跳变）。桌面外壳 MUST NOT 自动采购/管理代理池、MUST NOT 引用/管理 AdsPower 侧已保存代理账本（`proxyid`/`global_config` 不做）。改代理的生效时机以 AdsPower 实际行为为准，UI SHALL 按「下次启动该环境生效」的保守口径提示，MUST NOT 承诺即时生效。

#### Scenario: 未配代理仍可创建但给提醒并标注
- **WHEN** 运维未填代理即点「创建环境」
- **THEN** 桌面外壳给出「未配置代理」提醒但仍允许创建，成功后该环境在列表如实标「无代理」，不阻止任何后续操作

#### Scenario: 创建时填合法代理随建号下发
- **WHEN** 运维在创建表单选择 socks5 并填合法 host/port（及可选账密）后点「创建环境」
- **THEN** `user/create` 的 `user_proxy_config` 携带 `{ proxy_soft:'other', proxy_type:'socks5', … }`，建成后列表如实显示该代理摘要

#### Scenario: 非法代理输入诚实拒绝
- **WHEN** 代理输入含非法 port（如 `70000`）或选了类型但 host 为空
- **THEN** 归一层在提交前诚实拒绝并说明原因，MUST NOT 发出请求、MUST NOT 静默按 `no_proxy` 处理

#### Scenario: 已有环境改代理经受限 update 下发
- **WHEN** 运维在某环境行打开「代理」编辑浮层、填入合法代理并保存
- **THEN** 写客户端以 `{ user_id, user_proxy_config }` 两键 body 调 `user/update`，成功后提示「下次启动该环境生效」并刷新列表摘要；失败按 AdsPower 返回诚实展示

#### Scenario: 显式清除代理
- **WHEN** 运维在编辑浮层选「无代理」并保存
- **THEN** 下发 `{ proxy_soft:'no_proxy' }`，列表摘要回到「无代理配置」

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

② **登录后改名跟随昵称**：当核心读出该环境的真实登录昵称（`account-identity-resolution` 定义的显示名，昵称仅作显示、非账号主键）后，若 AdsPower 环境名与该昵称不一致，桌面外壳 SHALL 经写客户端的改名封装把该环境名改为昵称。

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

#### Scenario: 名字已一致不重复写
- **WHEN** 某环境的 AdsPower 名已等于其真实昵称，核心再次上报同一昵称
- **THEN** 桌面外壳 MUST NOT 再发起 `user/update` 改名

#### Scenario: 改名失败诚实降级
- **WHEN** 改名的 `user/update` 不可达或返回 `code≠0` 或撞每秒限速
- **THEN** 该环境保持原名、不假成功、不阻塞其浏览闭环，后续有机会再试改名

#### Scenario: 存量渐进而非即时批量
- **WHEN** 一批既有环境的名字仍是模板名 / AdsPower 默认名
- **THEN** 它们各自在下次登录读出昵称时被逐个改名，桌面外壳 MUST NOT 触发一次性批量改名或云端昵称导出

