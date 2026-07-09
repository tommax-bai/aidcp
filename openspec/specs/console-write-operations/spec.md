# console-write-operations Specification

## Purpose
TBD - created by archiving change aidcp-console-panel-mvp. Update Purpose after archive.
## Requirements
### Requirement: 写操作只经拥有该写的进程内对象，绝不 raw UPDATE，绝不乐观假成功

来自管理后台的所有写操作 SHALL 只经过已经拥有该写的进程内对象（风控 controller / 调度器 / 共享命令闭包 / 共享审批写回），MUST NOT 用 raw SQL UPDATE 绕过这些所有者，MUST NOT 报告乐观成功。每个写 SHALL 返回写后真态（如 `getState()` 写回、`{written}`/`{alreadyDecided}`、真实下发边缘数），且拒绝/无效 SHALL 与成功**可区分地**呈现。

#### Scenario: 写后回真态
- **WHEN** 任一面板写操作完成
- **THEN** 接口返回从所有者对象读回的写后真实状态，而非提交即返回的乐观「ok」

#### Scenario: 绝不 raw UPDATE 风控
- **WHEN** 面板需要改风控状态或档位
- **THEN** 改动经风控 controller 进行，面板层不持有也不使用对风控状态表的 raw UPDATE 能力

### Requirement: 风控 STATUS 改动经 applySignal 且限于枚举化运营信号种类

风控**状态**（normal/warned/restricted/frozen）改动 SHALL 经 `RiskController.applySignal`，且 MUST 限于一组枚举的、命名的运营信号种类（如 `manual_restrict` / `manual_freeze` / `operator_override_recover`）；接口 MUST 拒绝枚举外的种类。状态机是约束图而非 setter：时间门控的或非法的迁移 SHALL 被拒绝，且该拒绝 MUST 经 `getState()` 写回**作为「refused」**清晰呈现，绝不静默 no-op 成「ok」。`operator_override_recover`（绕过恢复窗口）MUST 要求审计理由。

#### Scenario: 非法迁移渲染为 refused
- **WHEN** 运营发起一个被恢复窗口时间门控拒绝的状态迁移
- **THEN** 接口返回 `getState()` 写回并把结果标为「refused」，状态未变，绝不报成功

#### Scenario: 枚举外种类被拒
- **WHEN** 状态写请求带了枚举集合之外的信号种类
- **THEN** 接口拒绝该请求，不调用 `applySignal`

### Requirement: 风控 QUOTA-TIER 改动经新 setQuotaLevel，controller 保持唯一写者

风控**档位**（conservative/normal/aggressive，`quotaLevel` 字段）改动 SHALL 经一个新的一等方法 `RiskController.setQuotaLevel(level)`，它 MUST 在 controller 内部完成「改 + 持久（`saveState`）+ emit」，使 controller 保持对风控状态的唯一写者。MUST NOT 用 `applySignal` 改档位（状态机从不触碰 `quotaLevel`，那样会静默无事发生），MUST NOT 从面板对 `quotaLevel` 做 raw UPDATE。

#### Scenario: 档位经 controller 单写
- **WHEN** 运营从面板改账号档位
- **THEN** 改动经 `RiskController.setQuotaLevel` 完成内部改+持久+emit，并返回写回的新档位

#### Scenario: 不借 applySignal 改档位
- **WHEN** 收到改档位请求
- **THEN** 系统调用 `setQuotaLevel` 而非 `applySignal`，避免「选了档位却什么都没变、也不报错」的静默无效

### Requirement: 每账号风控写串行化，无丢更新

`RiskController` SHALL 为每账号维护一个内部 async mutation 队列，使「迁移 + 持久」与「setQuotaLevel + 持久」原子。**所有**写者——live `record()` 触发的 `applySignal`、验证码协调器、新的 Web 状态/档位写——MUST 经该队列。并发的手动写与 live 写 MUST NOT 互相覆盖（无 lost update）。

#### Scenario: 并发手动写与 live 写串行
- **WHEN** 一个手动 `applySignal` 与一个 live `quota_exceeded` `applySignal` 几乎同时到达同一账号
- **THEN** 二者经 mutation 队列串行组合，最终状态是合法串行结果，无一方的 `saveState` 覆盖另一方

### Requirement: 发布审批写回经唯一共享函数、first-writer-wins、共享逐字节契约

Web 发布审批 SHALL 与飞书审批调用**同一个** `writeApprovalSignal(requestId, approved, payload)`，写**逐字节一致**的 `/tmp/aidcp-publish-approve-<requestId>.json`（AC-PUB-*），用卡铸造时的同一个 `requestId`。写 MUST 是 first-writer-wins 的原子写（temp + rename，`O_EXCL`）：第二个决定（Web vs 飞书 vs 重复点击）MUST 快速失败、接口返回 `{alreadyDecided:<approved>}`。接口 SHALL 返回 `{written:true}` 或 `{alreadyDecided}`，MUST NOT 返回 `{published:true}`（edge 对文件的动作才是真相）。系统 MUST NOT 接 `publish-executor.ts` 那条缺 `requestId`、属未激活 `activate-publish-pipeline` 的审批分支。

#### Scenario: 二次决定不覆盖首个
- **WHEN** 一个 `requestId` 已被飞书审批写定，随后 Web 又对同一 `requestId` 提交一个决定
- **THEN** 第二次写快速失败，接口返回 `{alreadyDecided}` 携首个决定值，信号文件不被覆盖

#### Scenario: 返回 written 而非 published
- **WHEN** Web 审批成功写出信号文件
- **THEN** 接口返回 `{written:true}`，绝不返回 `{published:true}`（是否真的发布由 edge 读取信号后决定）

### Requirement: pause/resume/dispatch 复用共享命令闭包并回报真实结果

账号 pause/resume（及 V1 的 dispatch start/stop）SHALL 复用一组共享 `CommandActions` 闭包，飞书命令路由与面板 `POST /api/accounts/:id/command`（及 `/dispatch`）共用同一实现。pause/resume 的运营暂停态 MUST durable（经 `accounts.status`），与传输层 `pausedEdges`（验证码硬停）保持区分。接口 MUST 回报真实结果——真实下发到几个在线 edge、或为何未下发的原因，绝不乐观假成功。

#### Scenario: 暂停回报真实下发事实
- **WHEN** 运营从面板暂停一个账号且其边缘当前不在线
- **THEN** 接口诚实返回「已记录暂停意图、当前 0 个在线 edge 收到」，而非假报已生效

#### Scenario: 运营暂停与验证码硬停区分
- **WHEN** 一个账号被运营暂停（`accounts.status`）
- **THEN** 该暂停与传输层 `pausedEdges` 验证码门控相互独立，二者不互相覆盖语义

### Requirement: 待审草稿编辑经拥有者对象一等单写、乐观 CAS、诚实非乐观

「待审正文草稿」的编辑 MUST 经拥有 `publish_log` 的进程内对象的一等单写方法完成，面板 MUST NOT 发任何裸 SQL。该方法 MUST 以乐观并发方式落库——`UPDATE … SET content_version = content_version + 1, … WHERE id = $id AND status = 'pending_approval' AND content_version = $expectedVersion RETURNING`，匹配 0 行时 MUST 经补充查询消歧为可区分拒因（`not_found` / `not_pending` / `version_conflict`），并在编辑前探测授权签名是否已存在（在途授权则拒 `already_decided`）。该方法 MUST NOT 乐观假成功、MUST 写后回读真态返回，且 MUST NOT 为不存在的记录 seed 行。审计以 `edited_by`（JWT 主体）/ `edited_at` 就地记录「谁 / 何时」。

#### Scenario: 并发编辑乐观拒绝
- **WHEN** 两个运营基于同一版本并发编辑同一草稿
- **THEN** 先到者版本自增成功，后到者匹配 0 行、得到可区分的 `version_conflict`，须刷新后重试，且无丢更新

#### Scenario: 授权在途拒绝编辑
- **WHEN** 编辑时该草稿的授权签名已存在（授权在途）
- **THEN** 编辑被拒 `already_decided`、不改动记录；该拦截为暂态——过期签名被下发兜底删除后草稿回可编辑

#### Scenario: 写后回读真态
- **WHEN** 编辑成功
- **THEN** 方法返回写回后的真实版本号与字段（非乐观回显），面板据此渲染，绝不假成功

### Requirement: 授权出口加写时活版本预检，共享逐字节写入函数保持不变

在共享的 Web + 飞书授权写回出口之上，系统 MUST 在**调用侧**（写签名之前）对 `publish-` 类 requestId 加一道活版本预检：读取记录当前版本与「人授权的版本」比对，不一致则 MUST 拒绝该授权、MUST NOT 写任何签名（O_EXCL 槽位留空、记录留待审可编辑）。该预检 MUST 保持既有唯一共享写入函数 `first-writer-wins`、逐字节契约不变——版本比对留在调用侧，`contentVersion` 仅作为字段随既有签名 payload 附带；同版本并发授权仍在 O_EXCL 上无害相撞（先到胜、后到 `alreadyDecided`）。

#### Scenario: 写时版本不符拒绝且不写签名
- **WHEN** 授权携带的版本与记录当前版本不一致（例如卡片上是旧版）
- **THEN** 授权被拒、不写任何签名，控制台回可区分的 `version_stale{currentVersion}`，飞书回一张就地替换卡「请到控制台重新审批」

#### Scenario: 共享出口字节不变
- **WHEN** 版本一致、授权写回
- **THEN** 仍经唯一共享函数写同一逐字节契约的签名（payload 多带一个 `contentVersion` 字段），Web 与飞书两路出口保持字节一致

#### Scenario: 同版本并发授权无害相撞
- **WHEN** 两路授权基于同一版本几乎同时写回
- **THEN** first-writer-wins：先到者写成功，后到者得 `alreadyDecided`，既有行为不变

### Requirement: 账号分组标签编辑经账号存储单写、写后回真态、诚实可区分

来自管理后台的账号分组标签（`accounts.group_label`）编辑 SHALL 只经账号存储（`accounts` 表行属性的拥有者）的一等单写方法 `setGroupLabel(accountId, label)` 完成，与既有 `setNickname` 同构。面板层 MUST NOT 持有或使用对 `accounts` 表的 raw SQL UPDATE 能力，MUST NOT 报告乐观成功。

分组写 SHALL 经受既有 JWT 保护的写路由（`PUT /api/accounts/:id/group-label`，body `{ groupLabel }`）触发，且：

- 写方法 SHALL 用 UPDATE-only 语义（`WHERE account_id`），MUST NOT 在账号行不存在时 seed 造行；行不存在 SHALL 作为「未找到」**与成功可区分地**返回，绝不静默成功。
- 写方法 SHALL 对入参做 `trim`：trim 后为空（空串 / 纯空白 / 缺省）SHALL 写入 NULL（即**清空分组**），MUST NOT 存入纯空白脏值。
- 写方法 SHALL 拒绝退役保留账号 `default`（`RETIRED_ACCOUNT_ID`），不写、不静默成功。
- 接口 SHALL 返回从存储回读的写后真实分组值（`RETURNING`），而非提交即返回的乐观「ok」。

该编辑 MUST NOT 触碰风控最终状态单写路径、MUST NOT 走边-云协议、MUST NOT 涉及边缘端——是纯账号属性编辑。前端「分组」列编辑 SHALL 非乐观：round-trip 成功后重新拉取账号列表以显示真态，只读账号视图（不传保存回调）SHALL 保持纯文本、不受影响。

#### Scenario: 写后回读真态而非乐观 ok
- **WHEN** 运营在账号列表点击「分组」单元格、输入一个分组名并保存
- **THEN** 接口经账号存储 `setGroupLabel` 落库并返回 `RETURNING` 回读的分组值，前端 round-trip 后重新拉取账号列表显示该真态，绝不提交即报成功

#### Scenario: 空输入清空分组
- **WHEN** 运营把某账号的「分组」输入清空（空串 / 纯空白）并保存
- **THEN** 账号存储把 `group_label` 写为 NULL（分组被清除），MUST NOT 存入纯空白脏值

#### Scenario: 不存在的账号可区分为未找到
- **WHEN** 分组写请求的 `account_id` 在 `accounts` 表无对应行
- **THEN** UPDATE-only 影响 0 行，接口把结果作为「未找到」返回、与成功可区分，MUST NOT seed 造出幽灵账号行、MUST NOT 静默成功

#### Scenario: 拒绝退役保留账号
- **WHEN** 分组写请求针对退役保留账号 `default`
- **THEN** `setGroupLabel` 拒绝该写、不落库、不静默成功

#### Scenario: 面板层绝不 raw UPDATE 绕过所有者
- **WHEN** 面板需要写账号分组标签
- **THEN** 改动经账号存储的 `setGroupLabel` 单写方法进行，面板层不持有也不使用对 `accounts` 表的 raw SQL UPDATE 能力

### Requirement: 内容排期写入经一等单写通道，UPSERT 前校验账号存在，默认 fail-closed

内容排期的写入——每账号 `PUT /api/content-schedule/:accountId` 与全局 `PUT /api/content-schedule/global`——SHALL 经受 JWT 保护的一等单写通道（内容排期存储的专属方法），MUST NOT 用 raw SQL UPDATE 绕过，MUST NOT 报告乐观成功。每账号写为 UPSERT，且写前 SHALL 先校验 `accounts` 中确有该账号行（无行 → 具名拒 `unknown_account`，绝不为不存在 / 退役账号造幽灵排期行），退役保留账号 `default` SHALL 拒。非法值（掩码非 168 位 '0'/'1'、日上限非非负整数、坏结构）SHALL **整块拒**、绝不部分落库。写后 SHALL 回读真态返回，且拒绝与成功 MUST **可区分**呈现。缺省与非法一律 fail-closed（归「不自动」）。此与本 spec「写只经拥有者对象、诚实非乐观」核心不变量同构。

#### Scenario: 写后回真态
- **WHEN** 运营经面板保存某账号或全局的内容排期
- **THEN** 接口返回从内容排期存储读回的写后真实状态，而非提交即返回的乐观「ok」

#### Scenario: 未知账号拒、不造幽灵行
- **WHEN** 对一个 `accounts` 中不存在或已退役的账号 PUT 内容排期
- **THEN** 接口具名拒绝（如 `unknown_account` / 退役拒），绝不 UPSERT 出一条孤儿排期行

#### Scenario: 非法值整块拒
- **WHEN** 提交的内容掩码非 168 位 '0'/'1'、或日上限为负 / 非整数
- **THEN** 整块拒绝、绝不部分落库，接口以可区分于成功的方式呈现拒绝

### Requirement: 内容排期评论字段写入与发帖字段严格同构

内容排期写通道（`PUT /api/content-schedule/:accountId`）SHALL 新增 `commentEnabled`（布尔）与 `commentDailyCap`（0..50 整数）两字段，校验与既有发帖字段严格同构：非法值（类型错 / 越界 / 非整数）SHALL 整块拒、绝不部分落库；写后 SHALL 回读真态；未配 / 默认一律 fail-closed（评论不自动）。写仍只经内容排期存储的一等单写方法，MUST NOT raw UPDATE、MUST NOT 乐观假成功。

#### Scenario: 评论字段合法写回读真态
- **WHEN** 运营为某账号打开自动评论并设日上限 2
- **THEN** UPSERT 经单写方法完成，接口返回回读的真实行（commentEnabled=true、commentDailyCap=2）

#### Scenario: 非法评论上限整块拒
- **WHEN** 提交 `commentDailyCap` 为 -1、1.5 或 51
- **THEN** 整块拒绝、绝不部分落库，拒绝与成功可区分呈现

### Requirement: 节奏兜底配置写操作经拥有对象单写、诚实非乐观、服务端夹逼

面板 API SHALL 暴露写端点 `PUT /api/pacing`，用于编辑每类操作的兜底 floor 区间。该写 SHALL 只经拥有该配置的进程内 facade 对象（UPSERT `ON CONFLICT DO UPDATE` + 先写库后刷内存镜像 + 审计），MUST NOT raw UPDATE、MUST NOT 乐观假成功——写后 SHALL 返回真实落库态（console 侧写后 invalidate 重取，非乐观更新）。服务端 SHALL 二次校验并诚实映射错误：未知 `operation` → `404 unknown_operation`；`minMs`/`maxMs` 非法（非负整数、`min ≤ max`、`max ≥ min × 1.5` 最小展宽、`≤ CAP`）任一不满足 → `400 invalid_value`；无合法字段 → `400 no_valid_fields`；整块拒绝、MUST NOT 部分落库。写入的兜底值 MUST 经读出口 `clamp(防呆下限, CAP)` 后才对边缘生效，保证配置**只能抬高延迟、抬不穿非零下限**（绝不零延迟红线不可经配置绕过）。审计 `updatedBy` SHALL 取自校验通过的调用者身份（JWT `sub`）。

#### Scenario: 写后回读真态

- **WHEN** 运营 `PUT /api/pacing` 调大 `action` 区间成功
- **THEN** 返回体为落库后的真实生效值（含夹逼护栏），console 侧 invalidate 后重取到该真态，非乐观显示

#### Scenario: 非法值整块拒绝

- **WHEN** 提交的 `maxMs < minMs × 1.5`（展宽不足）或 `minMs` 为负
- **THEN** 返回 `400 invalid_value`，不落库任何字段（整块拒绝、非部分写）

#### Scenario: 未知操作拒绝

- **WHEN** 提交的 `operation` 不在白名单（非 `action`/`scroll`/`card_gap`/`detail_dwell`）
- **THEN** 返回 `404 unknown_operation`，不写库

#### Scenario: 配置抬不穿非零下限

- **WHEN** 运营提交某 op `minMs = 0`
- **THEN** 即便通过表单，读出口 `clamp` 使对边缘生效的值 ≥ 非零防呆下限，边缘实测间隔不为零

### Requirement: 待审草稿配图删除经同一乐观 CAS 编辑通道、只删不注入、诚实非乐观

待审草稿（`pending_approval`）的**逐张删配图** MUST 经拥有 `publish_log` 的进程内对象的**同一个**一等单写编辑方法完成（与标题 / 正文 / 可见范围 / 话题共用 `editDraft`），面板 MUST NOT 发任何裸 SQL、MUST NOT 乐观假成功。删配图以一个 `images` 补丁字段表达——调用方提交「**保留下来的配图 URL 列表**」，写方法 SHALL：

- **只删不注入（红线）**：提交列表中的每个 URL MUST 是该记录当前 `images`（同一 `FOR UPDATE` 事务内读出）的成员；写方法 SHALL 按当前顺序过滤出保留项，任一提交项非当前成员即整块拒 `invalid_field`，MUST NOT 把任意外部 URL 写进待发帖、MUST NOT 部分落库。
- 以既有乐观并发语义落库——`UPDATE … SET images = <kept>, image_url = <kept[0] ?? null>, content_version = content_version + 1, … WHERE id = $id AND status = 'pending_approval' AND content_version = $expectedVersion RETURNING`；匹配 0 行 SHALL 经补充消歧为可区分拒因（`not_found` / `not_pending` / `version_conflict`），并在编辑前探测授权签名（在途则拒 `already_decided`）。
- 封面 `image_url` SHALL 随 `images` 重算为保留列表首项（空列表 → NULL）；`content_version + 1` 使原飞书审核卡失效、维持「审=发」版本闸。
- 删到 0 张（清空配图）SHALL 合法：记录 `images = '{}'`、`image_url = NULL`，交由既有发布下发段按纯文字（M=0）处理，MUST NOT 因此报错或静默塞回旧图。
- 写方法 SHALL 只从发布记录移除配图引用，MUST NOT 删除底层 OSS / 存储实体对象（孤儿对象可接受）。
- 写后 SHALL 回读真态返回（含更新后的 `images` 与自增 `content_version`），拒绝与成功 MUST **可区分**呈现；审计以 `edited_by` / `edited_at` 就地记录。

前端「内容」页待审详情的配图区 SHALL 非乐观：仅 `pending_approval`（可编辑态）显示逐张删除入口且删除前二次确认，删除成功后 MUST 以后端回读真态（新 `images` + 新版本）刷新浮层与列表，MUST NOT 先行乐观移除缩略图再回填；查看态 / 已发布记录 SHALL NOT 显示删除入口。

#### Scenario: 删除一张配图成功

- **WHEN** 审核人在待审草稿详情里删除某张配图并确认，前端携带「保留下来的配图 URL 子集」与打开时快照的 `expectedVersion` 调用编辑通道
- **THEN** 写方法在同一事务内校验子集合法、落 `images = 保留列表`、`image_url = 保留列表首项`、`content_version + 1`，回读真态返回新 `images` 与新版本，原飞书审核卡失效

#### Scenario: 防注入——提交含非当前成员的 URL

- **WHEN** `images` 补丁里出现任何不属于该记录当前配图集合的 URL
- **THEN** 写方法整块拒 `invalid_field`，绝不落库、绝不把该 URL 写进待发帖

#### Scenario: 版本冲突无丢更新

- **WHEN** 提交的 `expectedVersion` 与活 `content_version` 不符
- **THEN** 写方法拒 `version_conflict`，不改任何配图，前端提示后重取真态

#### Scenario: 非待审记录不可删配图

- **WHEN** 目标记录状态不是 `pending_approval`（如已发布 / 已否决）
- **THEN** 写方法拒 `not_pending`，配图不变，且前端对这些记录不显示删除入口

#### Scenario: 删空配图 = 纯文字帖

- **WHEN** 审核人删除该草稿的全部配图（提交空保留列表）并二次确认
- **THEN** 记录落 `images = '{}'`、`image_url = NULL`，发布下发段按纯文字（M=0）处理，绝不报错或静默塞回旧图

#### Scenario: 在途授权时拒绝编辑

- **WHEN** 该记录的发布授权签名已存在（审批在途）
- **THEN** 删配图编辑拒 `already_decided`，配图不变

#### Scenario: 只改记录、不删存储实体

- **WHEN** 删配图成功、某 URL 从记录移除
- **THEN** 系统只更新发布记录，MUST NOT 删除底层 OSS 对象（该对象成孤儿，可接受）

### Requirement: 账号「联系方式」编辑经账号存储单写、诚实非乐观、且 verbatim 存储

账号「联系方式」（`contact_info`）编辑 SHALL 经账号存储的一等单写方法完成（按 `account_id` upsert、写后回读真态），面板层受既有 JWT 保护、MUST NOT 用 raw SQL UPDATE 绕过、MUST NOT 报告乐观成功。写路由（`PUT /api/accounts/:id/contact-info`）SHALL 返回写后回读的真态；未注入该写依赖时 SHALL 503；未知账号 SHALL 404；坏类型（非 string/null）SHALL 400；退役保留账号 `default` SHALL 被拒且与成功可区分。空 / 空白输入 SHALL 归 NULL（清空）。与既有分组标签写入刻意相反：该值 MUST **verbatim 存储**——MUST NOT `trim`、MUST NOT 截断、MUST 保留 emoji 与换行。该 Requirement 与本 spec「写只经拥有者对象、绝不 raw UPDATE、绝不乐观假成功」的核心不变量同构。

#### Scenario: 写后回真态
- **WHEN** 面板保存某账号的联系方式
- **THEN** 接口经账号存储单写方法落库并返回从存储回读的真态，而非提交即返回的乐观「ok」

#### Scenario: verbatim 不 trim / 不截断
- **WHEN** 保存一串含 emoji、换行、首尾空白的联系方式
- **THEN** 回读值与输入字节一致，未被 trim、未被截断、emoji 完整

#### Scenario: 清空与拒绝可区分
- **WHEN** 分别对某账号提交空输入、对未知账号提交、对退役账号 `default` 提交、提交坏类型
- **THEN** 空输入归 NULL 清空并回真态；未知账号 404；退役账号被拒且与成功可区分；坏类型 400——各自诚实呈现，无一乐观假成功

### Requirement: 内容排期联系评论字段写入与开启校验（无联系方式硬拒、共用放行 + 提示）

内容排期写通道（`PUT /api/content-schedule/:accountId`）SHALL 新增 `contactCommentEnabled`（布尔）与 `contactCommentDailyCap`（0..10 整数，硬上限与发帖 / 评论的 50 刻意分开）两字段，非法值整块拒、写后回读真态、默认 fail-closed（联系评论不自动）。写入 `contactCommentEnabled=true` 时 SHALL 执行开启联系方式校验，含两支：

- **无联系方式硬拒**：该账号未配联系方式 → 具名拒 `no_contact_info`，整块不落库。该硬校验 MUST 在每次开启写入时重跑，MUST NOT 以警告放行、MUST NOT 静默降级、MUST NOT 部分落库。
- **共用放行 + 提示**（一码一号从硬阻断放松，change `loosen-group-comment-shared-code`）：该账号联系方式与任一其它账号 verbatim 相同时，MUST NOT 再具名拒绝——SHALL 照常放行落库，并在成功响应带 `sharedContactInfoWarning: true`。上层 MUST 据此如实提示防关联封号风险，MUST NOT 静默把「共用联系方式 = 最强跨账号关联指纹」的风险咽下去。放松为运营知情决策，靠小日上限 + 错峰 + 人审 + 明示提示压制、诚实声明非零风险。

#### Scenario: 无联系方式账号开启被拒
- **WHEN** 为一个未配联系方式的账号提交 `contactCommentEnabled=true`
- **THEN** 具名拒绝 `no_contact_info`、整块不落库，拒绝与成功可区分呈现

#### Scenario: 同联系方式账号开启放行并回带风险警告（一码一号放松）
- **WHEN** 该账号的联系方式与另一账号的联系方式逐字节相同、提交 `contactCommentEnabled=true`
- **THEN** 开关照常落库、成功响应带 `sharedContactInfoWarning: true`；上层 MUST 弹一条防关联封号风险提示，MUST NOT 静默放行

#### Scenario: 联系评论上限越界整块拒
- **WHEN** 提交 `contactCommentDailyCap` 为 -1、0.5 或 11
- **THEN** 整块拒绝、绝不部分落库

