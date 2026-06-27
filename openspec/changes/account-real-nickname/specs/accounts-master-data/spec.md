## ADDED Requirements

### Requirement: 账号平台真实昵称由边缘诚实且可证明属己地采集、持久化并展示

系统 SHALL 采集**当前登录账号自身**的小红书真实昵称并用于后台展示，链路为「边缘 DOM 采集（随握手带回）→ 持久化 → 面板/console 展示」。

- **采集（边缘，DOM-first，可证明属己）**：边缘 SHALL 在确立登录账号身份时（握手 / 重确立身份），从 DOM 读取**登录账号自身**昵称，且 MUST **限定在与可靠读出自己账号 ID 相同的作用域**（自己头像所在的导航容器）内读取，使该昵称**可证明属于登录账号自身**；MUST NOT 用无作用域的全局查询作为就地路径的昵称源（在含他人内容的页面会抓成被浏览作者的昵称）。边缘 SHALL 将昵称随**已有的握手消息**回报（作为可选字段），MUST NOT 为此新增 cloud → edge 命令。
- **诚实失败（红线）**：读不到昵称、或无法证明属己、或登录身份为覆盖值且与真实登录 id 不一致时，边缘 MUST NOT 伪造/派生/错配任何值（MUST NOT 用 `accountId` / `label` / 占位字符串、MUST NOT 用被浏览作者昵称充当登录账号昵称），SHALL **省略该字段**（不带 nickname）。
- **持久化（云端，单写、不阻塞握手）**：`accounts` 表 SHALL 新增可空列 `nickname`（additive、可空、**不回填假值**，缺失即 NULL）。云端 SHALL **按该连接已认证的账号**（非 payload 自报账号）持久化，**仅当** `nickname` 为非空字符串时 SHALL upsert 该账号行的 `nickname`（覆盖最新真名）；否则 MUST 忽略、保持现值（MUST NOT 用空值覆盖已有真名）。该持久化 MUST NOT 阻塞或致使握手失败（失败仅告警、仍返回握手响应）。
- **展示（面板 + console）**：面板 API `PanelAccount` SHALL 暴露 `nickname`；console 账号名各展示面 SHALL 按 `nickname → label → accountId` 回落链展示（无真名时回落运营标识，MUST NOT 展示假名）。

该要求 MUST NOT 改变 `account_id` 作为主键，MUST NOT 影响已按账号 keyed 的风控/发布/概念表，MUST NOT 引入 cloud → edge 新命令，MUST NOT 改变协议消息类型计数。

#### Scenario: 采到可证明属己的真实昵称则持久化并展示

- **WHEN** 边缘在自己头像所在作用域内成功读到登录账号自身昵称，并随握手带回非空 `nickname`
- **THEN** 云端按该连接已认证账号把 `nickname` upsert 到对应 `accounts` 行，面板返回该 `nickname`，console 账号名显示真实昵称

#### Scenario: 读不到昵称绝不伪造

- **WHEN** 边缘在账号区但未在自身作用域内抽到昵称
- **THEN** 边缘 MUST NOT 带回伪造昵称（省略 `nickname` 字段），云端不写入，该账号 `nickname` 保持 NULL（或上次真值）

#### Scenario: 绝不把被浏览作者昵称错配为登录账号

- **WHEN** 边缘在含他人内容的页面（推荐流 / 他人笔记 / 他人主页）确立身份
- **THEN** 边缘 MUST NOT 用无作用域全局查询命中的被浏览作者昵称充当登录账号昵称；若无法在自身作用域内读到，则省略 `nickname`

#### Scenario: 覆盖身份与真实登录不一致时不发昵称

- **WHEN** 边缘以 `AIDCP_ACCOUNT_ID` 覆盖值握手且该值与真实登录 id 不一致
- **THEN** 边缘 MUST NOT 把真实登录账号的昵称配到覆盖账号上，SHALL 省略 `nickname`

#### Scenario: 无真名时 console 回落运营标识

- **WHEN** 某账号 `nickname` 为 NULL（从未采到真名）
- **THEN** console 账号名回落显示 `label`，`label` 也缺失时回落 `accountId`，绝不显示假名

#### Scenario: 昵称随握手带回、不引入 cloud→edge 命令、不改消息计数

- **WHEN** 昵称采集链路接入协议
- **THEN** 昵称作为已有握手消息的可选字段带回（edge → cloud 方向），不新增消息类型、不改消息类型计数，不新增 cloud → edge 控制命令，不需改动边缘 onMessage 控制命令白名单
