# Design — notification-contact-registry

> 设计经多代理对抗评审（红线 / YAGNI / 失败模式三视角），下列 D7–D10 为评审直接驱动的修法。

## D1. 骨架：事件流水 + 人工侧表 + 读时聚合（不存「一人一行」聚合）

三件套：
1. `notification_event` —— 只追加的事件流水，机器写，**真相**。
2. `notification_contact_meta` —— 人工字段（微信/标签/备注）唯一落点，只有人能改。
3. 「联系人列表」—— 读时 `GROUP BY 人` 现算的投影（不物化）。

**为什么不「一人一行直接 upsert」**（基于代码，非审美）：系统**没有写入时就稳定的人键**。巡视去重键是 per-评论锚点、且显式排除主页链接（`notification-deduper.ts:39-43`），即使本变更新抽了主页ID，它仍是「可能缺失、可能改名」的弱标识。若一人一行，就得在**写入侧**拿弱标识当主键 upsert，巡视扫描会和人工标签抢同一行、可能覆盖人工数据；同名/改名在写入侧静默合并或拆分且不可逆。改用「事件流水 + 读时聚合」：身份模糊性变成**读时**的事，将来抽到更强标识只改读取、**无需迁移、不丢数据**。

## D2. 身份键（识别「人」）：主页ID 优先

- edge 从通知行头像 `a.user-avatar[href=/user/profile/<id>]` 解析 `<id>` → `NotificationItem.fromUserId`（取不到留空）。
- 投影分组键 `sender_key = COALESCE(from_user_id, from_user, dedup_key)`。
- 效果：同一人「又评论又点赞又关注」**正确并为一条**；同名不同人**不再误合并**、改名**不再被拆**。
- 代价：要存别人的平台ID（第三方标识，隐私上 D8 留存上限兜底）；协议多带一个可选字段。
- `notification_contact_meta.sender_key` 必须与投影分组键同口径（同为该 `COALESCE`），否则人工字段连不上联系人。

## D3. 去重键按 kind 计算（红线：同人不同评论绝不撞键丢失）

事件流水的 `dedup_key` 是**本变更自定义**、与飞书去重水位**解耦**（两者目的不同）：

- `comment` / `mention`：锚点 + **内容判别**（如 `notificationItemKey(it) + '|' + 短哈希(content)`）。`notification-deduper.ts:37` 标注「itemKey 究竟 per-comment 还是 per-note 待真机校准」——若真机为 per-note，纯锚点会把同人同篇两条评论撞掉第二条 = **丢真实数据**；掺内容判别后，同篇不同评论各自独立、同一条重扫仍折叠。
- `like` / `collect`：`身份键 + note锚点 + kind`（一人对一篇的一次赞/藏唯一）。
- `follow`：`身份键 + 'follow'`（一人关注你一次；取关再关属罕见，折叠可接受）。

`ON CONFLICT (account_id, dedup_key) DO NOTHING` ⇒ 重扫幂等、进程重启后仍 exactly-once（不靠内存水位）。「同一人点赞 50 篇」= 50 个不同锚点 = 50 行 → 投影聚为 1 个联系人、`event_count=50`。

## D4. 记录钩子：`notification.items.arrived`（事件到达处，统一、与飞书解耦）

不挂在飞书通知成功路径（那只覆盖评论且会被飞书未配置/失败影响），改挂每连接 `notification.items.arrived`（`comm/handler.ts:255` 翻译而来）：

- 评论/@ 已走此通道；点赞/关注补边缘抽取后**同一通道**带回 ⇒ 一个钩子记全五类。
- 该订阅在每连接私有 bus 上，账号 = 连接真实账号（`multi-account-node-support`），天然按账号、不广播。
- 记录前最小有效性闸（诚实、非静默吞）：必须有身份（`fromUserId`/`fromUser`/稳定锚点之一）；评论类内容与昵称皆空的结构异常行丢弃（边缘已结构化过滤，此为兜底）。
- **预览调度器不误记**：它无边缘会话、收不到 `notification.items.arrived`（对齐 a38fb96 的「未激活会话不接线」红线）。

## D5. 读时投影（修掉笛卡尔放大；见 D7）

```sql
SELECT e.account_id,
       COALESCE(e.from_user_id, e.from_user, e.dedup_key) AS sender_key,
       MAX(e.from_user)                                   AS nickname,
       MAX(e.from_user_id)                                AS user_id,
       MIN(e.seen_at)                                     AS first_seen,   -- 添加时间
       MAX(e.seen_at)                                     AS last_seen,
       COUNT(*)                                           AS event_count,  -- 实算，无计数列
       (array_agg(e.reason ORDER BY e.seen_at ASC))[1]    AS first_reason, -- 加入原因=最早
       array_agg(DISTINCT e.reason)                       AS reasons,
       m.wechat, m.note, m.tags, m.updated_by, m.updated_at
FROM notification_event e
LEFT JOIN notification_contact_meta m
  ON m.account_id = e.account_id
 AND m.sender_key = COALESCE(e.from_user_id, e.from_user, e.dedup_key)
WHERE e.account_id = $1
GROUP BY e.account_id, COALESCE(e.from_user_id, e.from_user, e.dedup_key),
         m.wechat, m.note, m.tags, m.updated_by, m.updated_at
ORDER BY MAX(e.seen_at) DESC
LIMIT $2 OFFSET $3;
```

`reason` 与 `kind` 同值（`comment|mention|like|collect|follow`），读时映射中文标签：评论 / @提及 / 点赞 / 收藏 / 关注。

## D6. 诚实的范围边界（必须在 UI 明示，不藏）

1. **只记通知里可直接取到的人**（用户定的口径）。
2. **无历史回填**：上线前的通知从未持久化（只有内存水位，进程重启即丢），且平台通知页本身只显示近期窗口 → 名册只能从上线后巡视扫到起往后长。
3. **添加时间 = 云端首次扫到时间**，非平台「2天前/05-15」（`notification-monitor.ts:147` 故意不抽平台时间以保扫描稳定）。上线后首轮巡视会把存量未读集中记到上线时间附近 —— UI Alert 须明示，免运营误读。
4. **同名且无主页ID 时仍可能并人**（罕见、有界）：身份读时推导，将来补强标识无需迁移。

## D7.〔评审·高〕标签用 `TEXT[]` 列，不用独立标签表

独立标签表会让投影**同时**左连「一对多的事件流水」和「一对多的标签表」→ 笛卡尔放大，`COUNT(*)` 变成 `事件数 × 标签数`（加 3 个标签后「互动次数」翻 3 倍，正好砸掉本设计主打的计数）。改用 `notification_contact_meta.tags TEXT[]`（对齐本仓既有 `TEXT[]` 惯例：`publish_log.source_concepts`、`valuable_comments.topics`），投影只剩 事件流水 × 资料表（1:1），计数正确，且少一张表一个索引一段事务删改。

## D8.〔评审·高〕第三方 PII 留存上限

事件流水存别人昵称 + 评论原文、只增不减。直接同形先例 `valuable-comment-store.ts:111-116` 对同类 PII 设了**每账号留存上限**（默认 1000，按账号删最旧）+ 表头 PII 理由注释。本变更照搬：`appendEvents` 后按 `account_id` 删超额最旧（如每账号 5000）。**注意**：删旧会让被删联系人的「添加时间(MIN)」与「次数(COUNT)」变成「最早保留」口径 —— 文档/Alert 注明，或按联系人保留而非按行裸删（V1 取按行裸删 + 文档注明，YAGNI）。

## D9.〔评审·中〕砍冗余列

- 去 `item_key`（可由 `dedup_key` 推出，无信息损失）。
- `note_title`：点赞类有目标笔记标题、评论类边缘当前不产出 → **保留列但标注「评论类 V1 恒空、点赞类填充」**，不在 console 表面化。
- `kind` 与 `reason` 同值：保留 `reason`（读时主用、无 CHECK 便于将来扩）；`kind` 仅作协议字段映射来源，落库只存 `reason`（一列）。

## D10.〔评审·中〕记录语义诚实表述

「记录 == 已通知」在飞书未配置时不成立。本设计改挂 `notification.items.arrived`（非飞书成功路径），语义直白为「**边缘巡视抽到并上报的发送者即记录**」，与飞书是否发送无关。钩子处一行注释点明，避免后人误读为「漏记 = bug」。

## D11. 落地与回归

- 迁移 0016 additive + 幂等 + store 内嵌同源 DDL（fresh deploy 先于迁移脚本也安全）。无回填，名册诚实从空起。
- 协议改动后**先 `npm run test:acceptance`（AC-PROTO 两份 protocol.ts 不漂移）再全量 `npm test` 再 typecheck**（edge + cloud 双仓）。
- 真机校准门：点赞/关注两栏 DOM 行结构 + 主页ID 解析须真机校验；并验「同人同篇两条评论 = 两行事件」（D3 防丢）。
