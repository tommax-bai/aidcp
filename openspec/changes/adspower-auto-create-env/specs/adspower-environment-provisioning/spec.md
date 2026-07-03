## ADDED Requirements

### Requirement: 程序化创建一个指纹环境（委托生成 + 挑整机模板 + 薄护栏 + OS 四者一致断言）

`adspower` 模式下，桌面外壳 SHALL 经 AdsPower 本地 API `user/create` **程序化创建一个**浏览器指纹环境，指纹的生成 SHALL **最大化委托 AdsPower 按 OS 自动生成自洽整套**（`ua_auto` 匹配内核、`canvas`/`webgl_image`/`audio`/`client_rects` 噪声开启），aidcp 侧 MUST NOT 逐字段手搓整套 `fingerprint_config`。aidcp 侧 SHALL 只承担三件事：① 由运维（或按模板轮换）挑一个「整机模板」，**OS 为第一锁定字段**，`device_memory`/`hardware_concurrency`/`screen_resolution` 等折进模板、MUST NOT 逐字段独立随机；② 一层薄静态护栏——`device_memory` SHALL 只允 2 的幂且封顶 8（**MUST NOT 提交 `6`** 等非 2 的幂）、`hardware_concurrency` SHALL 取真实值、`webgl` 模式 SHALL 不自相取消（`webgl='3'` 时 MUST NOT 同传会被忽略的 `webgl_config`）、`webrtc` SHALL 为替换成代理 IP 的模式、字体 MUST NOT 跨 OS 混装、时区/语言 SHALL based-on-IP、「每次启动重随机指纹」SHALL 关闭；③ 提交前 SHALL 做「声明 OS == 下发 UA 的 OS == 字体的 OS == renderer 家族的 OS」四者一致断言，任一不符 SHALL **诚实拒绝创建**、MUST NOT 提交一个自相矛盾的环境。aidcp 侧 MUST NOT 为「让检测方看着均衡」而强行匹配「CPU 性能档 == GPU 性能档」（检测方不查此项）。

#### Scenario: 委托生成 + 护栏放行合法自洽环境
- **WHEN** 运维选定一个整机模板（含 OS）点「创建环境」，且模板经护栏与四者一致断言校验通过
- **THEN** 桌面外壳以委托生成为主 + 模板锁定的 OS/整机字段构造 `fingerprint_config`，经 `user/create` 建号成功并返回分身 id

#### Scenario: 非法取值在提交前被护栏拦下
- **WHEN** 待提交的 `fingerprint_config` 含 `device_memory=6`（或其它非 2 的幂 / 超 8 的值）
- **THEN** 护栏在提交前诚实拒绝，MUST NOT 把该值发给 `user/create`

#### Scenario: OS 不自洽在提交前拒建
- **WHEN** 模板声明 Windows 但下发 UA / 字体 / renderer 家族任一不是 Windows（四者一致断言不符）
- **THEN** 桌面外壳诚实拒绝创建并说明不一致点，MUST NOT 提交该矛盾环境

### Requirement: 写能力经独立写客户端 + 硬编码 allowlist，绝不触碰浏览器生命周期

程序化创建 SHALL 经一个与只读 `ads-local-api` **分离的**「写客户端」发起，该写客户端 SHALL 用**硬编码 allowlist** 只放行 `user/create` 与 `group/create`，任何 `browser/start` / `browser/stop` / `browser/active` 等浏览器生命周期路径 SHALL 在该客户端内**直接抛错**（生命周期仍是核心子进程单写职责），并 SHALL 有回归断言证明该写客户端到不了生命周期端点（红线靠测试守、不靠注释）。写客户端对本地 API 的调用 SHALL 复用与只读侧相同的 ≥1 秒串行节流；本机核心子进程活跃时 SHALL NOT 并发跑批量写（避免与核心的启动/回收调用叠加撞每秒限速），撞限速 SHALL 诚实降级、MUST NOT 假成功。

#### Scenario: 写客户端拒绝生命周期端点
- **WHEN** 代码路径尝试经写客户端调用 `browser/start`（或 stop/active）
- **THEN** 写客户端直接抛错、不发出该请求，且有回归断言覆盖此禁令

#### Scenario: 核心活跃时不并发批量写
- **WHEN** 本机核心子进程正在运行且运维触发创建
- **THEN** 写客户端串行、与核心的本地 API 调用不在同秒并发；若仍撞每秒限速则诚实降级提示重试，MUST NOT 假成功

### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、专用分组/备注、单飞互斥

本 change 建的分身 SHALL 归入一个专用分组，创建时 SHALL 把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入、随 `user/list` 读回）。「有哪些分身、各绑什么代理」SHALL 以 AdsPower `user/list` 为**唯一账本**读取，MUST NOT 另建本机 write-ahead 台账（与 AdsPower 自身记录重复，徒增丢失 / 损坏 / 与 AdsPower 走样的同步面）。理由：号一旦登录、edge 一起即经握手把账号↔分身↔机器上报云端（见「握手载荷携带并持久化」需求），该上报已有、不重造；仅「创建后、登录前」空壳期云端不可见，而这段 AdsPower `user/list` 本就记着分身 + 各自代理，是现成账本。代理全程手工、本按钮 MUST NOT 碰（不下发 / 不校验 / 不去重——见「代理为软提示、非创建硬闸」需求）。创建动作在主进程 SHALL **单飞互斥**（同一时刻只一个创建在途，重入诚实返回「进行中」），渲染层触发控件 SHALL 在请求在途时禁用。崩溃后 SHALL 据下次 `user/list` 直接看见已建分身（在专用分组、带 `remark`，不丢账）。

#### Scenario: 崩溃后据 user/list 不丢账
- **WHEN** `user/create` 已成功建出分身但紧接着进程崩溃 / 关窗
- **THEN** 下次读 `user/list` 直接看见该分身（在专用分组、带 `remark`），无需本机台账即可续接

#### Scenario: 重复点击不双建
- **WHEN** 运维在创建在途时再次点击「创建环境」
- **THEN** 主进程单飞互斥拒绝重入、渲染层控件已禁用，MUST NOT 交错跑出两个各绑同一代理的分身

### Requirement: 凭据只内存持有、绝不明文落盘、日志脱敏

AdsPower API key 与代理账号密码 SHALL 仅在创建批处理期间**内存持有**，MUST NOT 明文写入 `settings.json` 或任何台账/文档；台账 SHALL 只存非密的代理摘要。`user/create` 的 POST 请求体 SHALL NOT 被整体 stringify 进日志/错误，日志与错误透传层 SHALL 显式脱敏 `proxy_user`/`proxy_password` 与 `Authorization`。确需持久化敏感值时 SHALL 用 OS keychain（如 `safeStorage`），MUST NOT 写明文设置。

#### Scenario: 代理账密不落盘不进日志
- **WHEN** 创建时携带了代理账号密码，且某条 `user/create` 返回错误
- **THEN** 账密只内存持有、不写入 settings/台账，错误信息中 `proxy_password`/`Authorization` 被脱敏，MUST NOT 出现在日志/UI

### Requirement: 代理为软提示、非创建硬闸，无代理如实标注

桌面外壳 SHALL NOT 因未配代理而阻止创建：未配代理时 SHALL 给出提醒，但仍允许创建。桌面外壳 SHALL 在环境列表如实呈现「无代理」状态（`no_proxy` 可从 `user/list` 读出），使无代理环境不被误当作已配好独立代理；该标注 MUST NOT 拦截任何操作。代理供给本身 SHALL 由运维手动完成，桌面外壳 MUST NOT 自动采购/管理代理池。

#### Scenario: 未配代理仍可创建但给提醒并标注
- **WHEN** 运维未给环境配代理即点「创建环境」
- **THEN** 桌面外壳给出「未配置代理」提醒但仍允许创建，成功后该环境在列表如实标「无代理」，不阻止任何后续操作

### Requirement: MUST NOT 程序化删除任何分身

桌面外壳 MUST NOT 接线任何程序化 `user/delete`。需清理的孤儿分身 SHALL 仅**暴露其 user_id 并引导运维在 AdsPower 中手动删除**，MUST NOT 由 aidcp 自动删除。删除已登录暖号不可逆且云端零审计，故此红线 SHALL 不在本 change 放开。

#### Scenario: 孤儿只暴露不自动删
- **WHEN** 从 `user/list` 认出若干疑似残留分身
- **THEN** 桌面外壳列出其 user_id 引导运维去 AdsPower 手动删，MUST NOT 调用任何删除接口
