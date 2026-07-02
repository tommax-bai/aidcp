## ADDED Requirements

### Requirement: 待审正文草稿可就地编辑，编辑就地改同一记录且下发照旧重读不重生成

系统 SHALL 允许对处于 `pending_approval` 状态的正文草稿就地编辑其标题、正文、可见范围、话题；编辑 MUST 就地 UPDATE **同一条** `publish_log` 记录，MUST NOT 新起草稿行、MUST NOT 触发重生成、MUST NOT 改动配图 / 来源血缘 / `account_id` / `mode` / `publishTime`。下发段 MUST 照旧从该记录重读草稿并逐字发出（保持「下发从落库草稿重建、绝不重生成」不变），从而编辑后的内容原样发布。非 `pending_approval` 状态的记录 MUST 诚实拒绝编辑（`not_pending`），绝不静默改写。

#### Scenario: 就地编辑待审草稿并原样发布
- **WHEN** 运营对一条 `pending_approval` 草稿改动标题 / 正文 / 可见范围 / 话题并保存成功
- **THEN** 系统就地 UPDATE 同一条记录、不新起草稿行、不重生成，且此后下发从该记录重读、逐字发出编辑后的内容

#### Scenario: 拒绝编辑非待审记录
- **WHEN** 目标记录已是 `published` / `failed` / `needs_review`
- **THEN** 编辑被诚实拒绝并返回可区分的 `not_pending`，记录内容不被改写

### Requirement: 每条草稿带内容版本号，作「审核所见即真实发布」的授权凭证

系统 SHALL 为每条 `publish_log` 记录维护一个每行内容版本号（`content_version`，既有行默认 0），每次成功编辑 MUST 使其自增 1。授权（通过 / 驳回）MUST 携带「人当时所见的那一版」版本号；真正触发下发的那次授权，其携带版本 MUST 等于下发那一行的当前版本——即「授权者所见字节 == 真实发布字节」按构造成立。版本一致性是唯一保真判据，签名中的来源字段仅供审计、MUST NOT 作保真闸。

#### Scenario: 编辑自增版本
- **WHEN** 一条草稿被成功编辑
- **THEN** 其 `content_version` 自增 1，并作为后续授权须携带的凭证

#### Scenario: 授权凭证锚定所见版本
- **WHEN** 运营在某一版草稿上点授权
- **THEN** 该授权携带的是当时所见的版本号，而非点击时从活缓存重取的版本

### Requirement: 下发前版本一致性闸，版本不符作废过期签名并留待审

下发段 MUST 在既有「已授权」判定之后再比对授权签名所载版本与记录当前版本：一致 → 照常下发；不一致 → MUST NOT 下发任何内容、MUST 删除该过期授权签名、并将记录**留在 `pending_approval`**（自愈回可重审，带当前内容）。版本作废 MUST NOT 落 `needs_review`、MUST NOT 自毁或改判（与「无授权绝不下发、待审无限期、绝不超时自毁」一致）。缺失版本号在飞书按钮与下发闸两处 MUST 一律当 0（部署向后兼容）。

#### Scenario: 版本一致照常下发
- **WHEN** 授权签名所载版本等于记录当前版本
- **THEN** 下发照旧从落库草稿重建并发出

#### Scenario: 版本不符作废并自愈
- **WHEN** 授权签名所载版本不等于记录当前版本（例如授权后又落了一次编辑）
- **THEN** 系统不发任何内容、删除该过期签名、记录留 `pending_approval` 可被重新审批，且不落 `needs_review`、不自毁

#### Scenario: 缺版本号部署兼容
- **WHEN** 一条部署前在飞的老审批其签名与按钮均无版本号
- **THEN** 两处一律当 0，未编辑草稿（0 == 0）照常发布，不被 deploy 卡死

### Requirement: 编辑标题仍在云端一处收口且合并授权动作遇截断须二次确认

编辑标题 MUST 仍只在云端一处跑 `clampTitle`（≤18 字素、拒空），面板 MUST NOT 写裸标题，以保「记录 == 下发 == 审批面 == 真实发布」收敛。当「保存并批准」这类合并动作把编辑与授权串起时：若收口后标题与提交标题不同（被截断），系统 MUST 中止自动批准、回显截断后的字节、要求人就该版再显式授权一次；仅当标题未被截断改变时方可自动串接授权。

#### Scenario: 编辑标题超长收口
- **WHEN** 运营把标题改到超过 18 字素
- **THEN** 云端 `clampTitle` 截断至 ≤18 字素（拒空），且截断只发生在这一处

#### Scenario: 合并动作遇截断二次确认
- **WHEN** 「保存并批准」发现收口后标题被截断
- **THEN** 自动批准被中止、回显截断后字节，人须就该版再点一次批准，绝不出现「授权的是截断前、发布的是截断后」

### Requirement: 编辑深合并元数据、保留合规字节、不重算合规棘轮

编辑 MUST 以读-改-写方式深合并 `publish_metadata`，只拼接本期可编辑的 `visibility` 与 `topics`，而 `compliance` / `permissions` / `mentions` / `location` / `collection` / `metadataScore` 等未改键 MUST 逐字保留。编辑 MUST NOT 重跑 aiEnforced 合规棘轮、MUST NOT 下调 AI 声明（本期合规不可编辑），从而与合规归一化链解耦。

#### Scenario: 深合并只动可编辑键
- **WHEN** 运营改动 `visibility` 或 `topics`
- **THEN** 系统只更新这两项，`compliance`/`permissions`/`mentions`/`location`/`collection` 前后字节一致

#### Scenario: 合规不可下调
- **WHEN** 编辑请求试图携带更低的合规声明
- **THEN** 编辑忽略合规字段、逐字保留原合规值，不重算棘轮、不下调 AI 声明
