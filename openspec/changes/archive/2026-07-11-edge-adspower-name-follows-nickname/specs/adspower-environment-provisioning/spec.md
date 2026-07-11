## MODIFIED Requirements

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

## ADDED Requirements

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
