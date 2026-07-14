# publish-draft-client-edit Specification

## Purpose
TBD - created by archiving change client-preview-image-delete. Update Purpose after archive.
## Requirements
### Requirement: 客户端待审草稿编辑经账号绑定的边-云请求应答通道、复用同一乐观 CAS 单写方法

客户端（Electron 陪伴客户端，身份为边-云 WS 握手确立的账号连接）对**自己账号名下**待审草稿（`pending_approval`）的编辑 SHALL 经**边→云请求 / 云→边应答**的一对协议消息完成（按信封 id 关联，与既有应用内审批动作同型），MUST NOT 经管理后台的运营 HTTP 通道、MUST NOT 由渲染层直接访问网络。

云端处理该请求 SHALL 复用拥有发布记录的进程内对象的**同一个一等单写编辑方法**（与管理后台改标题 / 正文 / 删配图共用的乐观 CAS 方法），MUST NOT 新起裸 SQL、MUST NOT 绕开其事务内的行锁与版本比对。写入者审计 SHALL 就地记为可识别的客户端身份（含账号标识），与运营编辑相区分。

本期该通道**只承载「逐张删配图」一种编辑**：MUST NOT 提供新增配图、替换配图、重排配图、改封面、改标题 / 正文的能力。

#### Scenario: 客户端删除一张配图成功

- **WHEN** 客户在客户端稿件预览里删除某张配图并确认，客户端携带 `requestId`（`publish-<recordId>` 口径）、当时展示的 `contentVersion`、以及该张配图的 URL 发起请求
- **THEN** 云端在通过全部准入闸后，于同一份数据库真态上算出「保留子集」并交由既有乐观 CAS 单写方法落库：`images` 写为保序保留子集、封面重算为保留列表首项、`content_version + 1`（使原飞书审核卡失效、维持「审=发」版本闸）
- **AND** 应答 SHALL 回带**写后回读的真态**（新 `images` 与自增后的 `contentVersion`），`ok:true` 的语义严格等于「该配图已从待审稿件中移除」，MUST NOT 被理解为「已发布」

#### Scenario: 保留子集由云端在真态上算出，不采信客户端提交的列表

- **WHEN** 客户端只表达「删除这一张（URL）」的意图
- **THEN** 云端 SHALL 以数据库中该记录的**当前**配图列表为基准算出保留子集，MUST NOT 直接落库客户端提交的任意列表；任何使配图变化的写都会推进 `content_version`，因此持旧版本号的请求 SHALL 先撞版本闸而非误删他图

### Requirement: 客户端编辑通道的准入闸序与可区分拒因

云端处理客户端草稿编辑请求 SHALL 按下列闸序逐道校验，任一道不过即以**可区分的具名拒因**诚实拒绝，MUST NOT 静默假成功、MUST NOT 部分落库：

- **入参合法**：`requestId` 须匹配既定的 `publish-<recordId>` 形状、目标配图 URL 非空、`contentVersion` 为非负整数 —— 否则 `invalid_request`
- **会话账号可用**：握手会话须已确立 `accountId` —— 否则 `account_unavailable`
- **记录存在** —— 否则 `not_found`
- **账号归属（红线）**：草稿的 `accountId` MUST 等于**握手确立的**会话 `accountId` —— 否则 `account_mismatch`。此闸 MUST NOT 被省略：管理后台的编辑通道只校验运营身份、不校验记录归属，客户端通道 MUST NOT 复制该宽松，否则任一客户端可猜记录号去改他人租户的稿件
- **决定未落**：若该稿的审批签名已存在（无论通过 / 驳回）—— 拒 `already_decided`，MUST NOT 再改已被审定的内容
- **状态可编辑**：仅 `pending_approval` 可编辑 —— 否则 `not_pending`
- **版本新鲜（红线）**：请求携带的 `contentVersion` MUST 等于库中活版本 —— 否则拒 `version_stale` 并**回带当前版本**，守「客户看到的就是被改的那一版」
- **目标须为当前成员（只删不注入）**：待删 URL MUST 是该记录当前配图列表的成员 —— 否则 `image_not_found`；本通道 MUST NOT 具备把任何外部 URL 写入待发帖的能力

上述前置校验与实际落库之间的时间窗 SHALL 由单写方法事务内的行锁 + 版本比对兜底：事务内复检失败 SHALL 映射回同一套具名拒因（版本不符 → `version_stale`、非成员 → `image_not_found`、非待审 → `not_pending`），MUST NOT 降级为泛化错误。

#### Scenario: 越权——删别人账号名下稿件的配图

- **WHEN** 请求里的 `requestId` 指向的草稿其 `accountId` 与握手会话的 `accountId` 不一致
- **THEN** 云端 SHALL 拒 `account_mismatch`、MUST NOT 读改该稿任何内容

#### Scenario: 版本过期——客户端手上是旧稿

- **WHEN** 客户端携带的 `contentVersion` 与库中活版本不符（例如运营已在后台删过一张）
- **THEN** 云端 SHALL 拒 `version_stale` 并回带当前版本，MUST NOT 按旧视图删图

#### Scenario: 决定已落——审批签名已存在

- **WHEN** 该稿的审批信号（通过或驳回）已被任一通道写下
- **THEN** 云端 SHALL 拒 `already_decided`，MUST NOT 修改已审定内容

#### Scenario: 目标配图已不在稿件里

- **WHEN** 待删 URL 不属于该记录当前的配图列表
- **THEN** 云端 SHALL 拒 `image_not_found`，MUST NOT 删除任何其他配图、MUST NOT 把该 URL 注入稿件

### Requirement: 客户端 MUST NOT 把待审稿件的配图删空

因图文帖在配图为空（M=0）时会被发布下发段诚实判失败（见 `publish-image-required`：无图时 MUST NOT 继续驱动注定失败的纯文字路径），客户端编辑通道 SHALL 拒绝会使配图归零的删除请求，拒因 `last_image`。

该拦截 MUST 由**云端**执行（服务端为权威），客户端 UI 的「最后一张不给删除入口」只是配套的前置提示，MUST NOT 作为唯一防线。系统 MUST NOT 向客户提供一个「删掉最后一张 → 审批 → 稿件被判失败」的路径，那等同于把「静默假成功 / 自残」外包给用户。

#### Scenario: 删除仅剩的最后一张配图

- **WHEN** 待审草稿当前只有一张配图，而客户端请求删除该张
- **THEN** 云端 SHALL 拒 `last_image`、配图与版本 MUST 保持不变；客户端 SHALL 呈现「至少保留一张配图」的说明且不提供该张的删除入口

### Requirement: 编辑成功后客户端手上的稿件真态必须立即刷新

删配图必然推进 `content_version`。若客户端持有的版本不同步刷新，其随后的审批动作会撞版本闸被弹回。因此编辑成功后系统 SHALL 以**应答回带的真态为主**刷新客户端所持稿件（新配图列表 + 新版本号），并 SHALL 另行沿用既有的预览重推通道下发一帧新快照作为**辅助**。

预览重推是 best-effort（账号无在线连接或下发未达时会被丢弃且不重试），故 MUST NOT 被当作唯一刷新手段。客户端 SHALL NOT 乐观地本地移除缩略图，SHALL 以服务端回读的真态重绘。

#### Scenario: 删除成功后立即再点发布

- **WHEN** 客户删掉一张配图，随即对同一稿件点「发布」
- **THEN** 客户端携带的 SHALL 是刷新后的版本号，审批 SHALL NOT 因 `version_stale` 被弹回

#### Scenario: 预览重推落空

- **WHEN** 编辑成功但云端的预览重推因该账号无在线连接而被丢弃
- **THEN** 客户端 SHALL 仍以应答回带的真态完成刷新，界面 MUST NOT 停留在删除前的旧稿

