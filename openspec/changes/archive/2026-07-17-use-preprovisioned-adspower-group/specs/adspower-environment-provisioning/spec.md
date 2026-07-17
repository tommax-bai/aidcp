## RENAMED Requirements

<!-- 「专用分组」→「预置分组」是本 change 的用意本身（分组由运营预置、客户端不再自建），
     但 openspec 的 MODIFIED 按需求名逐字匹配 ⇒ 不先声明改名，archive 会以
     「MODIFIED failed for header ... not found」失败（validate --strict 查不出，它只校验 delta 内部结构）。 -->

- FROM: `### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、专用分组/备注、单飞互斥`
- TO: `### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、预置分组/备注、单飞互斥`

- FROM: `### Requirement: 专用分组失效时自动恢复一次`
- TO: `### Requirement: 预置分组失效时只重新解析一次`

## MODIFIED Requirements

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

### Requirement: 幂等与生命周期——以 AdsPower user/list 为账本、预置分组/备注、单飞互斥

本 change 建的所有平台分身 SHALL 归入运营预先创建且名称严格等于 `aidcp` 的 AdsPower 分组。桌面外壳 SHALL 经 `group/list` 解析该预置分组的当前 id，MUST NOT 调用 `group/create`、MUST NOT生成后缀分组、MUST NOT 因分组查询失败或查无分组而继续 `user/create`。查询失败 SHALL 保留真实查询错误；查询成功但未找到 `aidcp` SHALL 提示检查当前 AdsPower 运行时、API key 与分组权限。创建时 SHALL 把「意图账号 / 模板 / 建号机」写进分身 `remark`（随 `user/create` 一次写入、随 `user/list` 读回）。「有哪些分身、各绑什么代理」SHALL 以 AdsPower `user/list` 为**唯一账本**读取，MUST NOT 另建本机 write-ahead 台账（与 AdsPower 自身记录重复，徒增丢失 / 损坏 / 与 AdsPower 走样的同步面）。理由：号一旦登录、edge 一起即经握手把账号↔分身↔机器上报云端（见「握手载荷携带并持久化」需求），该上报已有、不重造；仅「创建后、登录前」空壳期云端不可见，而这段 AdsPower `user/list` 本就记着分身 + 各自代理，是现成账本。代理 SHALL 为**创建时可选项**：表单填了合法代理即随 `user/create` 下发 `user_proxy_config`，不填 SHALL 默认 `no_proxy` 建号（与历史行为逐位等价）；代理输入的归一与校验见「代理可在客户端配置」需求。创建动作在主进程 SHALL **单飞互斥**（同一时刻只一个创建在途，重入诚实返回「进行中」），渲染层触发控件 SHALL 在请求在途时禁用。崩溃后 SHALL 据下次 `user/list` 直接看见已建分身（在预置 `aidcp` 分组、带 `remark`，不丢账）。

#### Scenario: 所有平台的新环境进入同一个预置分组
- **WHEN** 运维选择任一受支持平台并创建新环境
- **THEN** 桌面外壳解析名称严格等于 `aidcp` 的现有分组 id，并把该 id 传给 `user/create`
- **AND** 桌面外壳不调用 `group/create`

#### Scenario: 预置分组不可用时停止创建
- **WHEN** `group/list` 查询失败，或查询成功但当前运行时看不到名称严格等于 `aidcp` 的分组
- **THEN** 桌面外壳诚实报告查询错误或预置分组缺失/权限错误，并且不调用 `group/create` 或 `user/create`

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
