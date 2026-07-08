## ADDED Requirements

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
