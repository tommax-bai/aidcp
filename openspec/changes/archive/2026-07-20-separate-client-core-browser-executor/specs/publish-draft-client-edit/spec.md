## MODIFIED Requirements

### Requirement: 客户端待审草稿编辑经账号绑定的边-云请求应答通道、复用同一乐观 CAS 单写方法

客户端对自己环境绑定账号名下待审草稿（`pending_approval`）的编辑 SHALL 由 Electron 主进程经 customer-auth 窄接口完成，renderer MUST NOT 直接访问网络。请求只携带 `envKey` 与最小编辑意图；Cloud MUST 验证当前客户拥有该环境并从权威绑定解析 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。该操作 MUST NOT 要求浏览器、CDP、浏览器槽位或 Edge 活 WS 会话。旧客户端经边→云请求/云→边应答的协议路径 SHALL 在兼容窗口继续可用。

云端两条传输处理 SHALL 复用拥有发布记录的进程内对象的**同一个一等单写编辑方法**（与管理后台改标题/正文/删配图共用的乐观 CAS 方法），MUST NOT 新起裸 SQL、MUST NOT 绕开其事务内行锁与版本比对。写入者审计 SHALL 记录真实客户/客户端通道与账号标识，并与运营编辑相区分。

本期该通道只承载“逐张删配图”一种编辑：MUST NOT 提供新增配图、替换配图、重排配图、改封面、改标题/正文的能力。

#### Scenario: 浏览器关闭时删除一张配图成功

- **WHEN** 客户在客户端稿件预览删除某张配图并确认，携 `envKey`、`requestId`（`publish-<recordId>`）、当时展示的 `contentVersion` 和该配图 URL 发起请求，且浏览器关闭
- **THEN** Cloud 解析客户拥有环境和权威账号后，在数据库真态上算出保留子集并交由既有乐观 CAS 单写方法落库；应答回带新 `images` 与自增后的 `contentVersion`，且 `ok:true` 只表示配图已移除，不表示已发布

#### Scenario: 保留子集由云端在真态上算出，不采信客户端提交的列表

- **WHEN** 客户端只表达“删除这一张 URL”的意图
- **THEN** Cloud SHALL 以数据库当前配图列表算出保留子集，MUST NOT 直接落库客户端提交的任意列表；旧版本请求 SHALL 先撞版本闸而非误删他图

### Requirement: 客户端编辑通道的准入闸序与可区分拒因

Cloud 处理 customer-auth 客户端草稿编辑请求 SHALL 按下列闸序逐道校验，任一道不过即以可区分的具名拒因诚实拒绝，MUST NOT 静默假成功、MUST NOT 部分落库：

- **入参合法**：`envKey`、`requestId`、目标配图 URL 和 `contentVersion` 合法，否则 `invalid_request`
- **客户会话可用**：否则 `customer_unauthorized`
- **环境归属**：环境必须属于当前客户，否则 `environment_forbidden`
- **账号绑定可用**：Cloud 必须从环境权威绑定解析 `accountId`，否则 `account_unavailable`
- **记录存在**：否则 `not_found`
- **账号归属（红线）**：草稿 `accountId` MUST 等于权威绑定账号，否则 `account_mismatch`
- **决定未落**：审批签名已存在则 `already_decided`
- **状态可编辑**：仅 `pending_approval` 可编辑，否则 `not_pending`
- **版本新鲜（红线）**：请求版本必须等于活版本，否则 `version_stale` 并回带当前版本
- **目标须为当前成员**：待删 URL 必须是当前配图成员，否则 `image_not_found`

上述前置与落库之间 SHALL 由同一单写方法的事务行锁与版本比对兜底；事务内复检失败 MUST 映射为同一具名拒因。浏览器、CDP、槽位和 Edge 活会话不得出现在准入闸序中。

#### Scenario: 越权客户请求他人环境

- **WHEN** customer-auth 请求的 `envKey` 不属于当前客户
- **THEN** Cloud 拒绝 `environment_forbidden`，MUST NOT 解析或泄露该环境绑定和草稿信息

#### Scenario: 越权绑定账号请求他人稿件

- **WHEN** 目标草稿账号与 Cloud 从客户环境解析的权威账号不一致
- **THEN** Cloud 拒绝 `account_mismatch`，MUST NOT 读改该稿任何内容

#### Scenario: 版本过期

- **WHEN** 客户端携带的 `contentVersion` 与库中活版本不符
- **THEN** Cloud 拒绝 `version_stale` 并回带当前版本，MUST NOT 按旧视图删图

#### Scenario: 决定已落

- **WHEN** 该稿审批信号已存在
- **THEN** Cloud 拒绝 `already_decided`，MUST NOT 修改已审定内容

#### Scenario: 目标配图已不在稿件里

- **WHEN** 待删 URL 不属于记录当前配图列表
- **THEN** Cloud 拒绝 `image_not_found`，MUST NOT 删除其他配图或注入该 URL

## ADDED Requirements

### Requirement: 客户端审批决定受理 MUST 与后续平台发布分离

客户对待审稿执行通过或驳回 SHALL 由 Electron 主进程经 customer-auth 窄接口提交，Cloud MUST 复用既有审批签名、账号归属、活版本、幂等与单写闸。审批受理 MUST NOT 要求浏览器在线；通过决定只代表授权已记录并可排入后续页面执行，MUST NOT 表示帖子已在平台发布。驳回成功只代表决定已记录，不得派生浏览器任务。

#### Scenario: 浏览器关闭时批准待审稿

- **WHEN** 客户在浏览器关闭、槽位已满时批准自己环境账号的活版本待审稿
- **THEN** Cloud 记录幂等审批决定并返回“已受理/待执行”，客户端 MUST NOT 显示“已发布”且不得为受理动作启动浏览器

#### Scenario: 后续页面发布成功

- **WHEN** 已批准稿件之后取得浏览器执行器并经页面身份与版本闸成功发布
- **THEN** 系统在平台确认后更新发布成功真态，且该结果与先前审批受理回执保持可区分

#### Scenario: 驳回不产生浏览器任务

- **WHEN** 客户驳回一份待审稿且 Cloud 成功记录决定
- **THEN** 客户端显示已驳回，Cloud MUST NOT 申请浏览器槽位或排入页面发布队列
