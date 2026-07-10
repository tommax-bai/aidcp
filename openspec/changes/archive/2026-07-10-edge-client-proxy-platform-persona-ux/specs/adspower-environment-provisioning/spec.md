## RENAMED Requirements

- FROM: `### Requirement: 代理为软提示、非创建硬闸，无代理如实标注`
- TO: `### Requirement: 代理可在客户端配置：创建可选填、已有环境可增改、无代理如实标注`

## MODIFIED Requirements

### Requirement: 写能力经独立写客户端 + 硬编码 allowlist，绝不触碰浏览器生命周期

程序化创建 SHALL 经一个与只读 `ads-local-api` **分离的**「写客户端」发起，该写客户端 SHALL 用**硬编码 allowlist** 只放行 `user/create`、`group/create`、`user/delete` 与 `user/update`，任何 `browser/start` / `browser/stop` / `browser/active` 等浏览器生命周期路径 SHALL 在该客户端内**直接抛错**（生命周期仍是核心子进程单写职责），并 SHALL 有回归断言证明该写客户端到不了生命周期端点（红线靠测试守、不靠注释）。`user/update` 的放行 SHALL **仅限改代理用途**：写客户端的 update 封装 SHALL 只构造 `{ user_id, user_proxy_config }` 两键 body、MUST NOT 接受或透传任何其他字段（fingerprint / remark / 分组等一概不经此口），使「放行 update ≠ 打开整张写面」成为结构性保证并有回归断言覆盖。写客户端对本地 API 的调用 SHALL 复用与只读侧相同的 ≥1 秒串行节流；本机核心子进程活跃时 SHALL NOT 并发跑批量写（避免与核心的启动/回收调用叠加撞每秒限速），撞限速 SHALL 诚实降级、MUST NOT 假成功。

#### Scenario: 写客户端拒绝生命周期端点
- **WHEN** 代码路径尝试经写客户端调用 `browser/start`（或 stop/active）
- **THEN** 写客户端直接抛错、不发出该请求，且有回归断言覆盖此禁令

#### Scenario: user/update 只能带代理两键
- **WHEN** 代码路径经写客户端的 update 封装提交（无论调用方传入什么额外字段）
- **THEN** 发出的 body 只含 `user_id` 与 `user_proxy_config` 两键，额外字段不出现在请求中，且有回归断言覆盖

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
