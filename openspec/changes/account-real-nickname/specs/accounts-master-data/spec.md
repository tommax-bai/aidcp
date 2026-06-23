## ADDED Requirements

### Requirement: 账号平台真实昵称由边缘诚实采集、持久化并展示

系统 SHALL 采集**当前登录账号自身**的小红书真实昵称并用于后台展示，链路为「边缘 DOM 采集 → 上报 → 持久化 → 面板/console 展示」。

- **采集（边缘，DOM-first）**：边缘 SHALL 在已身处自己主页 / 顶部账号区时，从 DOM 读取**登录账号自身**昵称（MUST 与"被浏览笔记/主页作者"严格区分）。边缘 SHALL 经一条 **edge → cloud 上报消息**回报，payload 携带 `accountId`、`nickname` 与诚实标志 `extracted`。
- **诚实失败（红线）**：读不到昵称时边缘 MUST NOT 伪造/派生任何值（MUST NOT 用 `accountId` / `label` / 占位字符串充当 nickname），SHALL 不发或发 `extracted:false` 的空信号。
- **持久化（云端）**：`accounts` 表 SHALL 新增可空列 `nickname`（additive、可空、**不回填假值**，缺失即 NULL）。云端**仅当** `extracted===true` 且 `nickname` 非空时 SHALL upsert 该账号行的 `nickname`（覆盖最新真名）；否则 MUST 忽略、保持现值。
- **展示（面板 + console）**：面板 API `PanelAccount` SHALL 暴露 `nickname`；console 账号列 SHALL 按 `nickname → label → accountId` 回落链展示（无真名时回落运营标识，MUST NOT 展示假名）。

该要求 MUST NOT 改变 `account_id` 作为主键，MUST NOT 影响已按账号 keyed 的风控/发布/概念表，MUST NOT 引入 cloud → edge 新命令。

#### Scenario: 采到真实昵称则持久化并展示

- **WHEN** 边缘在登录账号自身主页/账号区成功读到昵称并上报 `extracted:true` 且 `nickname` 非空
- **THEN** 云端把该 `nickname` upsert 到对应 `accounts` 行，面板返回该 `nickname`，console 账号列显示真实昵称

#### Scenario: 读不到昵称绝不伪造

- **WHEN** 边缘进了账号区但未抽到昵称
- **THEN** 边缘 MUST NOT 上报伪造昵称（不发或发 `extracted:false`/空 `nickname`），云端不写入，该账号 `nickname` 保持 NULL（或上次真值）

#### Scenario: 无真名时 console 回落运营标识

- **WHEN** 某账号 `nickname` 为 NULL（从未采到真名）
- **THEN** console 账号列回落显示 `label`，`label` 也缺失时回落 `accountId`，绝不显示假名

#### Scenario: 上报为 edge→cloud 方向、不引入 cloud→edge 命令

- **WHEN** 昵称采集链路接入协议
- **THEN** 新消息为 edge → cloud 上报方向，不新增 cloud → edge 控制命令，不需改动边缘 onMessage 控制命令白名单

#### Scenario: 区分登录账号自身与被浏览作者

- **WHEN** 边缘在他人笔记详情/他人主页（含 `author`/`authorId` 字段的页面）
- **THEN** 边缘 MUST NOT 把被浏览作者昵称误报为登录账号的 `account.identity`
