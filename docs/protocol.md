# 边-云 WebSocket 协议

边缘端（aidcp-edge）与云端（aidcp-cloud）之间的唯一通信契约。传输层为
**WebSocket**；每帧为一个 JSON **信封（Envelope）**。本文档与
`aidcp-cloud/src/comm/protocol.ts`（边侧 `aidcp-edge/src/comm/protocol.ts` 为同名投影）
一一对应，是两侧实现的权威来源。

- 当前协议版本：`PROTOCOL_VERSION = 2`
- 默认服务端监听：`0.0.0.0:8787`（可由 `AIDCP_PORT` 覆盖）
- 编码：UTF-8 JSON 文本帧

> **v1 → v2 演进**：v1 只覆盖"单线规划"链路（`hello/plan/select/anchor/action/ping`）。
> v2 在保持这条链路向后兼容的同时，新增了三大块：
> 1. **浏览会话编排**（`note.content`/`browse.*`/`note.open` 等）——云端逐条驱动边缘刷信息流；
> 2. **角色驱动指令 + 结构化上报**（`page.cards`/`note.detail` 上报，`interaction.like`/`page.scroll` 等下发）——
>    对应云端从单体 Planner 重构为**事件驱动多 Agent**（`RoleDispatcher` + 多角色，`RoleName` 穷举现 43 项，分核心浏览闭环 / 会话守护 / 评论支线 / 通知巡视 / 概念抽取等类；权威清单见 `event-bus/types.ts` 的 `RoleName` 与 `role-dispatcher.ts`）后的实时控制面；
> 3. **风控预算与发布审批**（`session.budget`/`risk.canDo`/`publish.*`）——把"做多少、能不能做、发布前要不要人审"纳入协议。
>
> v2 共 **74 个消息类型**（含 `pacing.update`），下表按职能分组列全。计数与表为人工维护，以两端 `protocol.ts` 的 `MessageType` 穷举为准（可能滞后于代码）。

## 1. 信封（Envelope）

所有消息共用同一信封结构：

```jsonc
{
  "v": 2,                 // number  协议版本（PROTOCOL_VERSION）
  "type": "plan.request", // string  消息类型（见下表）
  "id": "req-42",         // string  请求/响应关联 id（响应回填请求的 id）
  "ts": 1717113600000,    // number  发送方毫秒时间戳
  "payload": { /* ... */ }// object  随 type 而定，见各消息定义
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `v` | number | 协议版本，便于演进。当前为 `2`。 |
| `type` | string | 消息类型（`MessageType`）。 |
| `id` | string | 关联 id。请求方生成，响应方原样回填，用于请求/响应配对。 |
| `ts` | number | 发送时间戳（毫秒）。由发送方填充（不在库内部读时钟，便于测试）。 |
| `payload` | object | 消息体。结构由 `type` 决定。 |

**校验规则**（`isEnvelope` / `parseEnvelope`）：`v` 为 number、`type` 为 string、
`id` 为 string、`ts` 为 number，且存在 `payload` 字段。任一不满足视为非法帧，
服务端回 `error`（code=`bad_envelope`）。构造信封统一走 `makeEnvelope(type, id, ts, payload)`，
它自动填入 `v = PROTOCOL_VERSION`。

## 2. 消息类型一览（MessageType）

### 2.1 单线规划链路（v1 起，向后兼容）

| type | 方向 | 关联响应 | 用途 |
| --- | --- | --- | --- |
| `hello` | edge → cloud | `welcome` | 边缘上线握手，声明平台、账号与能力 |
| `welcome` | cloud → edge | — | 握手确认，下发 sessionId |
| `ui.snapshot` | cloud → edge | — | 陪伴界面数据回填（昵称/最近发布/审批状态/账号今日用量；hello 注册完成后全量 + 审批变化时增量） |
| `plan.request` | edge → cloud | `plan.response` | 高层目标拆解为步骤 |
| `plan.response` | cloud → edge | — | 返回有序步骤清单 |
| `select.request` | edge → cloud | `select.response` | 元素清单 + 目标，请云端选一个 |
| `select.response` | cloud → edge | — | 返回选中元素 index |
| `anchor.get` | edge → cloud | `anchor.get.result` | 按 actionId 取主缓存锚点 |
| `anchor.get.result` | cloud → edge | — | 锚点或 null |
| `anchor.report` | edge → cloud | —（无回包） | 上报命中/校验，驱动反污染晋升 |
| `action.result` | edge → cloud | —（无回包） | 上报最终 ActionResult（观测/训练） |
| `error` | 双向 | — | 错误信息 |
| `ping` | 双向 | `pong` | 心跳 |
| `pong` | 双向 | — | 心跳应答 |

### 2.2 浏览会话编排（v2 新增，云端逐条驱动边缘刷流）

| type | 方向 | 用途 |
| --- | --- | --- |
| `note.content` | edge → cloud | 上报一条笔记的标题/摘要/指标，供评估与概念抽取 |
| `note.ack` | cloud → edge | 确认收到笔记，异步处理中 |
| `browse.next` | cloud → edge | 滚动/滑到下一条笔记 |
| `browse.scroll` | cloud → edge | 在当前页面滚动 |
| `note.open` | cloud → edge | 打开一条笔记 |
| `note.close` | cloud → edge | 关闭当前笔记 |
| `search.execute` | cloud → edge | 执行一次关键词搜索 |
| `session.end` | cloud → edge | 结束本次浏览会话 |

### 2.3 角色/命令式驱动指令（v2 新增，cloud → edge）

| type | 方向 | 用途 |
| --- | --- | --- |
| `page.scroll` | cloud → edge | 页面滚动（`reason`: feed_scroll / search_scroll；可选 `dwellMs`：feed 翻页按本次新卡数算的停留兜底，返回未刷新时省略） |
| `feed.refresh` | cloud → edge | 主 feed 浏览深度到阈值后，点右下「刷新」按钮回到顶部换出全新一批（`reason`: feed_refresh；可选 `thinkMs`；边缘诚实回执 `action.completed{action:'refresh'}`，非 feed 页 / 无按钮 / 点后未换新批均如实失败，绝不假成功） |
| `pacing.update` | cloud → edge | 会话中途风控档位变化推送新 `tempo`（payload `{tempo}`）；边缘刷新兜底节奏（最小间隔 + 停留兜底）、**不重置**操作间隔锚点、不入队/不唤醒会话（change pacing-fallback-hardening） |
| `interaction.like` | cloud → edge | 点赞指定笔记 |
| `interaction.collect` | cloud → edge | 收藏指定笔记 |
| `interaction.follow` | cloud → edge | 关注作者 |
| `interaction.comment` | cloud → edge | 在当前笔记发评论（`text` 正文；云端已撰写/去AI味/人审通过）。可选 `groupChatCode`=账号「联系方式」，非空则 verbatim 追加到评论末尾（wire 名历史保留，概念=contact info，change generalize-contact-info） |
| `interaction.like_comment` | cloud → edge | 给详情页内某条评论点赞（`commentAnchorId` 稳定锚点定位，绝不按序号） |
| `group.join` | cloud → edge | Facebook 加群原子指令：导航到群、回传结构化 observation；仅 `click:true` 时点击 Join 一次，必须走 Facebook `join` 能力，绝不复用 `browse` |
| `navigation.back` | cloud → edge | 返回上一页（feed / search） |
| `note.browse_images` | cloud → edge | 浏览笔记图片（`count` 张；DeepReader 决策下发） |
| `note.scroll_comments` | cloud → edge | 滚动评论区（CommentReviewer 决策下发） |
| `profile.open` | cloud → edge | 进入作者主页（专用指令，取代 `open_note{type:'profile'}`） |
| `notification.open` | cloud → edge | 导航到通知首页（仅导航；落地后边缘上报 `notification.home`） |
| `notification.browse_comments` | cloud → edge | 进「评论和@」+ 滚动加载 + 抽取（→ `notification.items`） |
| `notification.browse_likes` | cloud → edge | 进「赞和收藏」（清未读 + 抽取点赞/收藏发送者 → `notification.items`） |
| `notification.browse_follows` | cloud → edge | 进「新增关注」（清未读 + 抽取关注者 → `notification.items`） |
| `notification.back_home` | cloud → edge | 返回通知首页（重报各类未读） |

### 2.4 结构化上报（v2 新增，edge → cloud，`RoleDispatcher` 消费）

| type | 方向 | 用途 |
| --- | --- | --- |
| `page.cards` | edge → cloud | 上报当前可见卡片列表（index/title/author/计数） |
| `note.detail` | edge → cloud | 上报笔记详情（正文/作者/计数） |
| `profile.detail` | edge → cloud | 上报作者主页数据（粉丝数/作品数） |
| `action.completed` | edge → cloud | 确认某个 action 执行完成 |
| `notification.detected` | edge → cloud | 检测到「消息」有未读（仅信号；`epoch` 每次由无变有 +1，去重用） |
| `notification.home` | edge → cloud | 通知首页各类未读快照（评论/赞收藏/关注计数，喂分诊） |
| `notification.items` | edge → cloud | 上报本次巡视抽取的通知项（`NotificationItem`：`kind`=comment/mention/like/collect/follow、`fromUser`昵称、`fromUserId?`主页ID稳定身份、`content`、`noteTitle?`、`itemKey?`；是否通知由云端判，发送者沉淀进通知联系人名册） |

### 2.5 风控预算与互动判定（v2 新增）

| type | 方向 | 关联响应 | 用途 |
| --- | --- | --- | --- |
| `session.budget.request` | edge → cloud | `session.budget` | 请求本次 browse session 预算 |
| `session.budget` | cloud → edge | — | 下发预算（时长/动作数/档位/只读） |
| `risk.canDo` | edge → cloud | `risk.canDo.result` | 互动前请求是否允许执行 action |
| `risk.canDo.result` | cloud → edge | — | allow / deny + 原因 |
| `risk.record` | edge → cloud | `risk.record.result` | 互动成功后记录 action |
| `risk.record.result` | cloud → edge | — | 记录结果 |
| `risk.captcha_detected` | edge → cloud | — | 检测到验证码/未知阻断弹窗（已本地暂停），通知云端置风控态 + 停发命令 + 通知人工 |
| `risk.captcha_cleared` | edge → cloud | — | 验证码/未知阻断弹窗已清除，已恢复浏览 |
| `captcha.assist.capture` | cloud → edge | `captcha.assist.snapshot` | 请求原 edge 的原浏览器会话捕获当前验证码现场截图；captcha 暂停期间允许穿透 |
| `captcha.assist.snapshot` | edge → cloud | — | 返回截图、snapshotId、crop/viewport 坐标映射和 fresh 遮罩元数据 |
| `captcha.assist.click` | cloud → edge | `captcha.assist.click_result` | 将人工点位发送给原 edge，由 edge 映射并派发真实输入事件 |
| `captcha.assist.click_result` | edge → cloud | — | 返回点击后 fresh 复检结果；只有清除时 edge 另发 `risk.captcha_cleared` |

### Edge 页面写任务租约（同一 edge/CDP 单写）

| type | 方向 | 说明 |
|---|---|---|
| `edge.task.acquire` | cloud → edge | 申请任务级执行权，携 `taskId/kind/priority/leaseMs/acquireTimeoutMs?`；edge 在该等待上限内未 quiesce 时取消排队申请；这不是“已暂停”的事实 |
| `edge.task.acquired` | edge → cloud | edge 已在命令安全边界 quiesced、已取消未开始的普通浏览命令并授予租约；cloud 收到后才可发首条业务命令 |
| `edge.task.release` | cloud → edge | 幂等释放指定 `taskId`，携可选 `outcome` |
| `edge.task.released` | edge → cloud | 释放/过期/非 owner 的收敛回执；`cdp_unhealthy` 表示 edge 仍在线但浏览器控制不可安全接管 |

### 2.6 发布编排（v2 新增，Publish Agent 驱动）

| type | 方向 | 用途 |
| --- | --- | --- |
| `publish.request` | cloud → edge | 请求在浏览器中发布一篇帖子 |
| `publish.approval_request` | edge → cloud | 请求云端发送发布审批卡片（飞书） |
| `publish.approval_action` | edge → cloud | 客户端稿件预览内提交发布/取消审批动作，携稿件版本 |
| `publish.approval_action.result` | cloud → edge | 返回审批动作受理结果；不代表已完成发帖 |
| `publish.result` | edge → cloud | 发布结果回传（ok / postId / error；v1 整页路径） |
| `publish.command` | cloud → edge | 下发一条参数化发布原子指令（`taskId` 为当前发布租约；`recordId+seq` 关联键，`kind` ∈ E1-E10） |
| `publish.command.result` | edge → cloud | 单条发布指令执行结果回传（按 `recordId+seq` 关联；`ok/value/error/details`，红线不静默假成功） |

### 2.7 Persona 生成（v2 新增，建号关键词驱动，客户自助 onboarding）

**edge 发起的请求/响应**，回包走 pending-id 命中——不经 `command-bridge` 动作映射、不经 edge `onMessage` 主动命令白名单。大模型/密钥/校验/序列化/落库/记账全在云端；边缘只收关键词、显示草稿、回确认。

| type | 方向 | 关联响应 | 用途 |
| --- | --- | --- | --- |
| `persona.generate` | edge → cloud | `persona.generate.result` | 按客户勾选关键词请求云端生成账号 persona 草稿（带 `idempotencyKey` 防重连/重试双计费；云端以握手绑定 `accountId` 为准） |
| `persona.generate.result` | cloud → edge | — | 返回生成的 soul.yaml + 身份摘要；失败带 `reason`，MUST NOT 返回半成品（fail-closed、宁缺毋假） |
| `persona.persist` | edge → cloud | `persona.persist.result` | 请求持久化客户确认后的 soul.yaml（复用云端现有校验写入通道，不新造写路径） |
| `persona.persist.result` | cloud → edge | — | 持久化结果；失败带 `reason`（`unknown_account` / `persona_required` / `persona_invalid`） |

## 3. 各消息 payload 定义

### 3.1 握手

**`hello`**（edge → cloud）
```jsonc
{
  "edgeId": "edge-01",        // string  边缘节点标识
  "platform": "xiaohongshu",  // string? 运行时平台标识；缺省按历史 xhs 兼容，cloud 会与 accounts.platform 校验
  "app": "xhs",               // string? 业务/站点标识
  "capabilities": ["click", "input", "scroll"], // string[]? 能力声明
  "accountId": "acc-01",      // string? 账号标识；多账号运行时要求真实账号，default 已退役
  "accountNickname": "小张测评", // string? 账号可读昵称；仅用于展示补充，不参与身份确立或路由
  "machineLabel": "win-aliyun-3", // string? 人类可读机器标签
  "remoteAddr": "rdp://..."   // string? 人工处置入口/远程地址说明
}
```

`platform` 和 `accountNickname` 都是平台抽象层的 type-only payload 扩展，不新增消息类型、不改变 v2 的 74 个消息类型计数。cloud 在握手建运行时前以 `accounts.platform` 为事实源校验 edge 上报平台；不一致时返回 `error`，不会让 xhs edge 接管 Facebook 账号或反向混跑。`accountNickname` 只能作为展示补充，不能用于身份确立、平台校验或命令路由。

**`welcome`**（cloud → edge）
```jsonc
{
  "sessionId": "sess-1",      // string  云端分配的会话 id
  "serverVersion": "0.1.0",   // string  服务端版本
  "pacing": {                 // object?  可选节奏快照（change pacing-floor-config-min-interval）；旧端忽略
    "tempo": 1.0,             //   number  风控档全局节奏乘子（normal=1.0/warned=1.3/restricted=1.6），边缘乘算
    "opFloorsMs": {           //   object  每类操作兜底 floor 默认区间（已含云端读出口 clamp 护栏、非零）；逐字段可缺、边缘逐项回落内置默认
      "action":       { "minMs": 1500, "maxMs": 4000 }, // note.open/profile.open/interaction.*
      "scroll":       { "minMs": 500,  "maxMs": 1500 }, // note.scroll_comments
      "card_gap":     { "minMs": 3000, "maxMs": 7000 }, // note.browse_images
      "detail_dwell": { "minMs": 2500, "maxMs": 5000 }  // ensureDetailDwell 兜底 floor
    }
  }
}
```
> `pacing` 承载**全局节奏兜底**，供边缘做「操作间**最小间隔** gating」（记上次操作完成时刻，收到下一操作时若距上次已达 floor 则立即执行、**不累加**、吸收云端往返；否则只补差额）与详情页停留兜底。数值后台（console）可配、存云端 PostgreSQL、下次握手/重连热加载。与 `session.budget.pacing`（`PacingDefaultsPayload`，边缘从不消费的**死通道**）区分——本快照走 `welcome` 请求/响应，永不经主动命令白名单。**红线**：配置只能抬高延迟、经三道夹（facade 校验含 `max≥min×1.5` + 云端读出口 `clamp(防呆下限,CAP=15000ms)` + 边缘 `Math.max` 二次夹）永远抬不穿非零下限，绝不零延迟。

**`ui.snapshot`**（cloud → edge，主动推送；change edge-companion-ui 8.1）
```jsonc
{
  "account": { "id": "acc-1", "nickname": "晚风手作" },   // 可选；昵称空则整个字段不带（宁缺毋假）
  "personaBound": true,   // 可选（change persona-wizard-onboarding-fixes）；账号是否已绑人设，仅 true 时下发；边缘据此把徽标翻「已设置」并跳过建号人设向导
  "lastPublish": { "title": "上一篇", "at": 1730000000000 }, // 可选；最近一次成功发布（at=epoch ms，为草稿入库时间近似）
  "publish": { "state": "submitted", "title": "候审笔记", "code": "#83" }, // 可选；审批/提交状态增量
  "publishPreview": { // 可选；当前待审稿件只读预览，不含原稿标题/作者/正文/链接
    "recordId": 83,
    "code": "#83",
    "kind": "rewrite", // rewrite | generated
    "title": "洗稿后的标题",
    "content": "洗稿后的正文",
    "topics": ["生活方式", "周末去哪儿"],
    "images": ["https://cdn.example.com/1.jpg"],
    "contentVersion": 0,
    "updatedAt": 1730000000000,
    "imageReferenceAudit": { "requestedCount": 3, "usableCount": 3, "status": "used", "generatedCount": 3 }
  },
  "dailyUsage": { // 可选；账号用量与限额窗口，边缘优先用它替代本机实时计数
    "asOf": 1730000001000,
    "quotaLevel": "normal", // conservative / normal / aggressive
    "totals": { "view": 10, "like": 3, "collect": 1, "comment": 0, "follow": 2, "publish": 1 },
    "quotas": { "view": 150, "like": 50, "collect": 25, "comment": 8, "follow": 15, "publish": 1 },
    "saturated": ["publish"], // 向后兼容：以上三项是 day 窗口别名
    "windows": {
      "session": {
        "active": true,
        "startedAt": 1730000000000,
        "windowMs": 600000,
        "expiresAt": 1730000600000,
        "totals": { "view": 3, "like": 1, "collect": 0, "comment": 0, "follow": 0, "publish": 0 },
        "quotas": { "like": 10, "collect": 5, "comment": 2, "follow": 3 },
        "saturated": []
      },
      "minute": {
        "startedAt": 1729999941000,
        "windowMs": 60000,
        "expiresAt": 1730000061000,
        "totals": { "view": 3, "like": 3, "collect": 0, "comment": 0, "follow": 0, "publish": 0 },
        "quotas": { "view": 8, "like": 3, "collect": 2, "comment": 1, "follow": 1, "publish": 1 },
        "saturated": ["like"]
      },
      "hour": {
        "startedAt": 1729996401000,
        "windowMs": 3600000,
        "expiresAt": 1730003601000,
        "totals": { "view": 10, "like": 3, "collect": 1, "comment": 0, "follow": 2, "publish": 1 },
        "quotas": { "view": 60, "like": 13, "collect": 7, "comment": 2, "follow": 4, "publish": 1 },
        "saturated": []
      },
      "day": {
        "startedAt": 1729958400000,
        "windowMs": 86400000,
        "expiresAt": 1730044800000,
        "totals": { "view": 10, "like": 3, "collect": 1, "comment": 0, "follow": 2, "publish": 1 },
        "quotas": { "view": 150, "like": 50, "collect": 25, "comment": 8, "follow": 15, "publish": 1 },
        "saturated": ["publish"]
      }
    }
  },
  "browserStandby": { // 可选；长等待时的浏览器冷待机建议，旧边缘忽略
    "enabled": true,
    "eligible": true,
    "reason": "view_quota:hour", // disabled / no_wait / short_wait / hard_blocker / view_quota:*
    "waitMs": 1800000,
    "wakeAt": 1730001801000,
    "generatedAt": 1730000001000,
    "source": "risk",
    "minWaitMs": 1200000,
    "warmupMs": 90000
  }
}
```
发送时机：① 边缘 hello 注册完成后（连接进推送表且 `welcome` 已回发之后，避开「hello 处理中推送
sent=0」前科）回填全量快照；② 发布审批生命周期变化时增量推送（`pending`=草稿候审、`approved`=授权
已核、`submitted`=页面已接受提交但同页尚未取得帖子链接、`rejected`=拒绝发布、`failed`=云端终判失败）。
`published` 不经此通道——边缘仅在同页 `capture_postId` 成功后本地打 `[ui-event]` 行；正常链路不得为确认而
刷新页面。`reminded` 枚举保留但云端当前无再提醒机制、不会出现。`code` 与
飞书审批卡「编号」字段同源（发布记录 id，如 `#83`），供界面对暗号。边缘核心收到后转成 `[ui-event]`
结构化行打到 stdout，由 Electron 壳解析驱动标题带与发布卡（解析器 `src/electron/ui-events.cjs`）。
已拒草稿在 hello 快照不回放（拒绝时刻已实时推过，重启不翻旧账）。推送为 best-effort：账号无在线
边缘即如实放弃，持久态由下次 hello 快照补齐。

`dailyUsage.totals` / `quotas` / `saturated` 保持为日窗口别名，用于旧边缘兼容；新客户端优先读取 `windows`。
`windows.minute|hour|day` 由云端按账号聚合风险流水：浏览/点赞/收藏/评论/关注来自 `risk_counters`，发帖来自发布日志；
分钟 / 小时窗口为滚动窗口；日窗口为 Asia/Shanghai 本地自然日（00:00 至次日 00:00），与风控 `quota:day` 判定同源；
`quotas` 来自该账号当前风控档位的有效窗口上限，`saturated` 表示对应维度已达到或超过当前窗口上限。
`windows.session` 来自当前在线连接的单场预算快照；没有活跃会话时可带 `active:false` 作为配置上下文，但不代表正在消耗预算。
字段可缺省，旧边缘会忽略；新 Electron 客户端在该字段到达前回落展示本机实时计数，缺窗口元数据时不臆造分钟/小时/单场上限。

`startedAt/windowMs/expiresAt` 为窗口时效元数据；分钟/小时是滚动窗口，日窗口是本地自然日窗口，Electron 可在过期且未收到新快照时停止展示过期的“已达上限”。`windows.session.totals` 可包含浏览/发帖等无单场上限动作的真实计数，但不得为这些动作复制其他窗口的上限。

`browserStandby` 是 cloud 对“下一个自动浏览动作还要等多久”的确定性建议，不是强制命令。`eligible=true` 只在 cloud 能从风控/配额等确定性来源算出有限长等待、且等待超过阈值时出现；验证码、登录、人工干预、环境占用或未知调度状态不得伪装成可恢复等待。Electron 仍会用本地开关、会话状态、关闭/暂停中标志和预热时间做二次判断；通过后才会在等待期间关闭浏览器，并在 `wakeAt - warmupMs` 前后恢复。

### 3.2 任务规划

> **现状**：`plan.request/response` 仍是协议契约的一部分，由云端 `SimplePlanner`（规则优先 + LLM
> 兜底）服务。但**浏览会话**已不再通过一次性 `plan.response` 驱动，而是由 `RoleDispatcher`
> 按结构化上报实时下发角色驱动指令（见 §3.6/§3.7）。`plan.*` 适用于"一句话目标→原子步骤"的
> 定向场景（如外部直接下发"给当前笔记点赞并关注"）。

**`plan.request`**（edge → cloud）
```jsonc
{
  "goal": "给当前这条笔记点赞并关注作者", // string  高层自然语言目标
  "context": { "url": "https://...", "app": "xhs" } // object? 可选上下文（值均为 string）
}
```

**`plan.response`**（cloud → edge）
```jsonc
{
  "steps": [
    {
      "actionId": "note.like_button", // string  稳定业务标识
      "op": "click",                  // "click" | "input" | "scroll"
      "goal": "点赞当前笔记的点赞按钮",  // string  给元素选择器的自然语言目标
      "value": "..."                  // string? 仅 input 操作需要
    }
  ],
  "reason": "rule_matched"            // string  规划说明（rule_matched | llm_planned | ...）
}
```

### 3.3 元素选择（缓存缺口时的"选择题"）

**`select.request`**（edge → cloud）
```jsonc
{
  "goal": "点赞当前这条笔记的点赞按钮",
  "elements": [                       // RemoteElement[]：ElementDescriptor 的网络投影
    {
      "index": 0,                     // number  清单序号（LLM 选它）
      "role": "button",              // string  推导角色
      "tag": "button",               // string  标签名（小写）
      "text": "赞",                   // string  可见文本/可访问名（已裁剪）
      "attributes": { "aria-label": "like" } // object  稳定属性子集
    }
  ]
}
```

**`select.response`**（cloud → edge）
```jsonc
{
  "index": 0,        // number | null  选中元素 index；无合适项为 null
  "reason": "llm_selected" // llm_selected | llm_no_match | empty_element_list
                           //  | unparsable_output:<...> | index_out_of_range:<n> | llm_error:<...>
}
```
> 防幻觉：云端校验 LLM 返回的编号必须落在 `elements` 范围内，越界一律置 `index=null`。

### 3.4 锚点缓存

**`anchor.get`**（edge → cloud）
```jsonc
{ "actionId": "note.like_button" }    // string
```

**`anchor.get.result`**（cloud → edge）
```jsonc
{
  "anchor": {                         // RemoteAnchor | null
    "actionId": "note.like_button",
    "role": "button",                // string?
    "text": "赞",                     // string?
    "textMatch": "contains",         // "exact" | "contains"  （可选）
    "attributes": { "aria-label": "like" }, // object?
    "scope": {                        // object?  结构作用域
      "role": "article",
      "containsText": "笔记标题",
      "attributes": { "data-id": "n123" }
    }
  }
}
```

**`anchor.report`**（edge → cloud，无回包）——驱动反污染晋升
```jsonc
{
  "actionId": "note.like_button",
  "source": "llm",                    // "cache" | "llm"  本次解析来源
  "validated": true,                  // boolean  后置校验是否通过
  "candidate": {                      // RemoteAnchor?  source=llm 且 validated 时附带
    "actionId": "note.like_button",
    "role": "button",
    "text": "赞"
  }
}
```
云端处理规则（见 `DefaultMessageHandler.onAnchorReport`）：
- `source=cache` & `validated=true` → `recordHit`
- `source=cache` & `validated=false` → `recordFailure`
- `source=llm` & `validated=true` & 有 `candidate` → `stage` 后 `confirmStaged`（连续达阈值晋升主缓存）
- `source=llm` & 其余 → `dropStaged`（丢弃，不污染主缓存）

### 3.5 执行结果上报

**`action.result`**（edge → cloud，无回包）
```jsonc
{
  "actionId": "note.like_button",
  "ok": true,                         // boolean
  "outcome": "success",              // "success" | "escalated" | "no_target" | "guard_blocked"
  "attempts": 1,                      // number  重试次数
  "reason": "cache_hit_validated",   // string
  "escalation": "systemic_revision"  // string?  outcome=escalated 时
}
```

### 3.6 浏览会话编排

**`note.content`**（edge → cloud）——上报一条笔记内容投影，供评估与概念抽取
```jsonc
{
  "noteId": "n123",       // string  笔记唯一标识（去重/记录来源）
  "title": "周末好去处",   // string
  "summary": "正文摘要…",  // string  边缘截取，控制长度
  "likeCount": 1234,      // number
  "collectCount": 200,    // number
  "author": "小张"        // string?
}
```

**`note.ack`**（cloud → edge）：`{ "received": true }`

**`browse.next` / `browse.scroll`**（cloud → edge）：`{ "reason": "继续刷的原因" }`（均可选）

**`note.open`**（cloud → edge）
```jsonc
{ "noteId": "n123", "index": 0, "reason": "值得打开" } // 字段均可选
// url?（change facebook-scheduled-comment，可选）：完整 permalink 直驱打开（Facebook 定向评论候选帖直达详情页），
//   非空时边缘按此链接直接导航、不依赖 feed 卡片索引/noteId；缺省=走原有 index/noteId 卡片定位（小红书旧行为）。
{ "url": "https://www.facebook.com/groups/123/posts/456" }
```

**`note.close`**（cloud → edge）：`{ "reason": "..." }`（可选）

**`search.execute`**（cloud → edge）
```jsonc
{
  "keyword": "露营装备",   // string  搜索关键词
  "source": "extract_from_liked", // ? extract_from_liked | random_from_interests | new_concept | manager
  "maxResults": 10,       // number? 本次搜索最多浏览的结果数
  "sort": "most_collected",  // ?（change comment-search-command）搜索结果排序：如 most_collected（最多收藏）。边缘用原生排序 tab/筛选面板实现；缺省=默认（综合）排序。
  "timeWindow": "one_day",   // ?（change comment-search-command）时间窗筛选：如 one_day（一天内）。缺省=不限时间。
  // container?（change facebook-scheduled-comment，可选）：站内搜索容器。非空时边缘只在该容器内搜索、绝不全站搜。
  //   Facebook 定向评论：容器为运营方自己/已加入的主页或群完整链接；边缘先校验其为白名单合法 Facebook 链接，
  //   非法/非成员则 honest permission_gated、绝不回退全站。缺省=无容器约束（小红书全站搜旧行为）。
  "container": "https://www.facebook.com/groups/123"
}
```

**`session.end`**（cloud → edge）
```jsonc
{
  "reason": "budget_exhausted",
  "stats": { "likedCount": 5, "skippedCount": 12, "searchCount": 2, "durationMs": 540000 } // 可选
}
```

### 3.7 角色驱动指令（cloud → edge）

大部分浏览闭环动作由云端 `RoleDispatcher` 产出语义动作 `EdgeCommand`，经 `command-bridge`
（`edgeCommandToEnvelope`）翻译为以下协议消息下发；`group.join` 由 Facebook 加群调度器按同一信封格式直发到目标 edge。

```jsonc
// page.scroll
{ "reason": "feed_scroll" }                  // feed_scroll | search_scroll
{ "reason": "feed_scroll", "dwellMs": 1350 } // feed 出新卡：翻页前按新卡数看一会（feed-scroll-card-floor）；返回未刷新则省略 dwellMs
// feed.refresh（feed 浏览深度到阈值改点右下「刷新」回顶换新批，change feed-refresh-on-depth）
{ "reason": "feed_refresh", "thinkMs": 700 } // 边缘点后校验「回顶 + 首卡换新」才回 ok:true 并上报新一批 page.cards
// interaction.like
{ "noteId": "n123", "reason": "高质量内容", "thinkMs": 900 }
// interaction.collect
{ "noteId": "n123", "reason": "值得收藏", "thinkMs": 900 }
// interaction.follow
{ "authorId": "u456", "reason": "持续优质", "thinkMs": 900 } // authorId 可选
// interaction.comment
{ "noteId": "n123", "text": "今天的分享很有启发", "thinkMs": 900, "groupChatCode": "..." } // text 必填；groupChatCode 可选=账号「联系方式」(contact info)，非空则边缘逐字敲完 text 后整段追加「\n+该串」，verbatim 不 trim
// 注（change generalize-contact-info）：本字段承载的概念已正名为「联系方式」，内部变量为 contactInfo；wire 字段名保留 groupChatCode 作历史兼容（Method A），物理改名属后续协调步骤。
// group.join（Facebook 加群；click 缺省/false=只观察不点击，true=cloud 已判定可点后才点击一次）
{ "groupUrl": "https://www.facebook.com/groups/123", "click": false, "thinkMs": 900 }
// navigation.back
{ "reason": "quality_rejected", "targetPage": "feed", "dwellMs": 2200 } // targetPage: feed | search
// note.open
{ "index": 0, "noteId": "n123", "reason": "值得打开", "thinkMs": 800 }
// note.close
{ "reason": "...", "dwellMs": 2200 }
// note.browse_images（DeepReader 决策；count 为目标张数，边缘按实际可见数截断）
{ "noteId": "n123", "count": 3, "thinkMs": 700, "dwellMs": 2000 }
// note.scroll_comments（CommentReviewer 决策）
{ "noteId": "n123", "thinkMs": 700, "dwellMs": 2000 }
// profile.open（进入作者主页；边缘点详情页作者头像进入，authorId 仅观测/兜底）
// direct?: boolean — 云端直驱（change account-real-nickname）：true=直接 navi 到 /user/profile/<authorId>、不抓取当前页；缺省/false 维持点头像进入
{ "authorId": "u456", "reason": "作者值得关注评估", "thinkMs": 800, "direct": false }
```

> **深读动作的回报**：`note.browse_images` / `note.scroll_comments` 经 `action.completed` 如实回报——
> 命中则 `ok:true` 且 `reason` 记实际量（`browsed=N` / `scrolled=N`），未命中目标则 `ok:false, reason:'no_target'`
> （不再 `count||1` 假报成功）。`profile.open` 进主页后由边缘抽取作者资料并经 `profile.detail` 上报
> （含 `extracted` 标记，抽取失败也上报以便云端区分"数据缺失"与"真 0 粉丝"）。

> **时间指令（timing directive，指令级节奏 Command Pacing）**：上列决策指令携带**可选**时间字段，
> 由云端基于**已上报内容**（`note.detail.content` 长度）+ 风控状态（`tempo`：normal=1.0 /
> warned=1.3 / restricted=1.6）+ 会话进度（疲劳曲线）算出的**中心值**：
> - `thinkMs`：执行该动作**前**的犹豫 / 感知时间（`interaction.*` / `note.open`）；
> - `dwellMs`：离开当前页前应达到的**总停留时间**（`navigation.back` / `note.close`），治详情页"秒退"。
>
> §3 时间系数收口在云端一处，**不下发系数**。边缘收到中心值后叠一层 lognormal 抖动（防确定性指纹）
> 再执行：`thinkMs` → 动作前等待；`dwellMs` → 保证当前页实际停留达标（真实阅读已超过则不叠加）。
> 字段缺失（旧云端 / 自主动作）→ 边缘走内置默认下限兜底，**绝不零延迟**。向后兼容（旧端忽略）。

`EdgeCommand.action` → 协议 `type` 映射（`command-bridge.ts`）：
`scroll→page.scroll`、`open_note→note.open`、`close_note→note.close`、
`like→interaction.like`、`collect→interaction.collect`、`follow→interaction.follow`、`comment→interaction.comment`、`comment_like→interaction.like_comment`、
`search→search.execute`、`back→navigation.back`、`browse_images→note.browse_images`、
`scroll_comments→note.scroll_comments`、`profile_open→profile.open`、`session.end→session.end`。
Facebook 加群不经 `EdgeCommand` 映射；join scheduler 直接下发 `group.join`，edge active-command 白名单必须放行。

### 3.8 结构化上报（edge → cloud）

**`page.cards`**——上报当前可见卡片列表
```jsonc
{
  "cards": [
    {
      "index": 0, "title": "周末好去处", "author": "小张",
      "likeCount": 1234, "collectCount": 200,
      "coverDesc": "封面描述", "noteId": "n123",  // coverDesc / author / noteId 可选
      "isVideo": false                            // 可选：卡片是否为视频；供后续 note.detail 推导媒体类型
    }
  ],
  "startupId": "ads-k1e0ero8:12345:lz7abc"        // 可选：完整 core/browser 启动代号；同一次启动内稳定，完整重启后变化，用于云端限定启动期昵称采集
}
```

**`note.detail`**——上报笔记详情
```jsonc
{
  "noteId": "n123", "title": "周末好去处", "content": "完整正文…",
  "mediaType": "image_text",                      // 可选：image_text / video；缺省按 image_text 兼容老边端
  "author": "小张", "authorId": "u456",       // author / authorId 可选
  "likeCount": 1234, "collectCount": 200,
  "publishedAtText": "3小时前",                 // 可选（change feed-hot-lead-group-comment）：发布相对时刻原始文本
                                               // （刚刚/X小时前/昨天/07-05）。边缘只从正文列底部日期容器抽原始串、不解析、不污染正文；
                                               // 云端解析成距今小时数并算「每小时点赞」热度速率（判引流线索）。缺则诚实置空、绝不臆造。
  "authorFollowed": true,                      // 可选：作者区关注按钮当下真实态（已关注/互关→true）。
                                               // 边缘在 note.open 探测、只读取上报；云端据此在评估进主页前短路已关注作者。缺省→回退原流程。
  "url": "https://www.xiaohongshu.com/explore/n123?xsec_token=…",
                                               // 可选（change interaction-feed-enrichment）：带 xsec_token 的详情页链接，供面板「按笔记互动」可点跳转。
                                               // 诚实置空：地址栏无 token 时不带、绝不用裸 id 拼假链。
  "images": [
    { "index": 0, "url": "https://sns-img-qc.xhscdn.com/...", "width": 1080, "height": 1440, "alt": "封面图" }
  ],                                           // 可选（change curated-reference-images）：图文轮播图片引用，按视觉顺序、去重、有界。
                                               // 只上报 URL/基础元数据；边缘不下载，抓不到则省略/空数组，不编造。
  "refreshOnly": true                          // 可选（change complete-curated-reference-image-capture）：仅用于翻图后的图片快照刷新。
                                               // 云端 MUST NOT 计为新的 view，也不触发普通详情决策链。
}
```

**`profile.detail`**——上报作者主页数据
```jsonc
{ "authorId": "u456", "postsCount": 87, "followersCount": 12000, "extracted": true,
  "nickname": "小张",                          // 可选（change interaction-feed-enrichment）：主页真实昵称，供面板关注记录显示真名；抓不到则置空。
  "url": "https://www.xiaohongshu.com/user/profile/u456" } // 可选：作者主页链接，供面板关注记录可点跳转；抓不到则置空。
// extracted:false → 进了主页但未抽到数字；云端 FollowAgent 据此保守 skip，不当作真 0 粉丝
```

**`action.completed`**——确认某 action 执行完成
```jsonc
{ "action": "like", "ok": true, "reason": "..." } // reason 可选
// group.join 回执：ok=true 只表示点击后观测到 member-now；observe-only / already_member / pending / questionnaire_required 均不计成功加群
{
  "action": "join_group",
  "ok": false,
  "reason": "observation_only",
  "groupUrl": "https://www.facebook.com/groups/123",
  "clicked": false,
  "observation": { "mainCtaText": "Join group", "modalText": null }
}
```

### 3.9 风控预算与互动判定

**`session.budget.request`**（edge → cloud）：`{ "accountId": "acc-01" }`（可选）

**`session.budget`**（cloud → edge）——下发本次会话预算
```jsonc
{
  "durationMs": 600000,            // number  会话时长上限
  "maxActions": 30,                // number  最多执行的动作数
  "quotaLevel": "normal",          // "conservative" | "normal" | "aggressive"
  "viewOnly": false,               // boolean  仅浏览不互动
  "startedAt": 1717113600000,      // number   会话开始时间戳
  "pacing": {                      // object?  极薄节奏默认块（指令级节奏；仅边缘自主动作/断连兜底用）
    "tempo": 1.0,                  //   number  全局节奏乘子（风控状态驱动）
    "dwellFloorMs": { "min": 1200, "max": 2600 } // 详情页最小停留下限区间
  }
}
```
> `pacing` 可选、向后兼容（旧端忽略）。它**只含兜底参数**（`tempo` / `dwellFloorMs`），**不含**
> 内容相关的 read / pause / fatigue 系数——那些收口在云端，随决策指令以 `dwellMs`/`thinkMs` 下发
> （见 §3.7 时间指令）。缺失时边缘用内置默认。

**`risk.canDo`**（edge → cloud）：互动前请求许可
```jsonc
{ "action": "like", "accountId": "acc-01" }
// action: view | like | collect | comment | follow | publish；accountId 可选
```

**`risk.canDo.result`**（cloud → edge）
```jsonc
{ "action": "like", "allowed": false, "reason": "quota:hour" } // reason 可选
```
> 拒绝原因来自 `RiskController.explain()`：`state:frozen` / `state:restricted` /
> `quota:minute|hour|day` / `ratio:like_view` 等。

**`risk.record`**（edge → cloud）：`{ "action": "like", "accountId": "acc-01" }`（accountId 可选）

**`risk.record.result`**（cloud → edge）：`{ "action": "like", "recorded": true, "reason": "..." }`

**`risk.captcha_detected`**（edge → cloud，fire-and-forget）：检测到验证码/未知阻断弹窗
```jsonc
{
  "edgeId": "edge-1",            // string?  边缘标识
  "kind": "captcha",            // 'captcha' | 'unknown'：unknown=可见阻断遮罩但本地未归类
  "url": "https://...",        // string?  触发时页面 URL（best-effort）
  "accountId": "acc-01",       // string?  关联账号
  "reason": "..."              // string?  简短说明
}
```
> 边缘旁路监测体在「类别翻转进 captcha/unknown」时发一次（已先本地暂停）。云端据此置归属账号
> 风控态（captcha→restricted / unknown→warned）、按 edge 暂停下发、(edgeId,account) 去重后通知飞书。
> 检测/暂停/恢复全在 edge 本地完成，本消息只是通知，云端从不回查边缘动作。

**`risk.captcha_cleared`**（edge → cloud，fire-and-forget）：`{ "edgeId": "edge-1", "url": "...", "accountId": "acc-01" }`（均可选）
> 边缘弹窗清除、已恢复浏览。云端解除该 edge 暂停；风控态不因清除自动回滚（由恢复窗口/人工恢复驱动）。

**`captcha.assist.capture`**（cloud → edge）：请求原 edge 捕获验证码现场截图
```jsonc
{
  "incidentId": "cap_01H...",    // string  cloud 侧远程协助 incident id
  "reason": "initial",           // 'initial'|'refresh'|'retry'?
  "requestedAt": 1717113600000,   // number?
  "maxImageWidth": 1280,          // number?  edge 可继续 clamp
  "maxImageHeight": 960,          // number?
  "quality": 80,                  // number?  JPEG 质量建议值
  "live": {                       // object?  实时抓帧（change captcha-assist-live-snapshot）；缺省=单次抓帧（零回归）
    "intervalMs": 800,            // number?  抓帧间隔 hint，edge 钳到安全区间（约 600..2000）
    "maxDurationMs": 30000,       // number?  循环时长上界 hint，edge 钳制
    "maxFrames": 40               // number?  循环帧数上界（iteration-bounded 自终止）
  }
}
```
> 该消息只允许定向发给 incident 绑定的 edge。captcha 暂停期间它可穿透传输层暂停闸；
> 普通浏览、互动、发布页面动作仍必须被暂停闸拦截。
> 带 `live` 时 edge 进入**有界、内容去重、自终止**的实时抓帧循环：只在挑战画面变化时才推新
> `captcha.assist.snapshot`；自主判"已清除"须连续多次无遮罩确认后才发 `risk.captcha_cleared`（绝不单次误清）。
> live 的 snapshotId 语义：edge 每 incident 保留最近 N 帧、云端亦保留最近 N 帧集，`submitClick` 允许提交
> **最近集内的稍旧 snapshotId**（运营冻结选点用），edge 按被点帧自己的 crop 落点。无新增 MessageType。

**`captcha.assist.snapshot`**（edge → cloud）：返回现场截图和坐标映射
```jsonc
{
  "taskId": "task-recovery-01H...", // system_recovery 租约；acquired 后才派发点击
  "incidentId": "cap_01H...",
  "edgeId": "edge-1",
  "accountId": "acc-01",
  "snapshotId": "snap_01H...",
  "capturedAt": 1717113601000,
  "expiresAt": 1717113631000,
  "kind": "captcha",             // 'captcha'|'unknown'
  "url": "https://...",
  "viewport": { "width": 1440, "height": 980, "deviceScaleFactor": 1 },
  "crop": { "x": 0, "y": 0, "width": 821, "height": 810 },
  "image": {
    "mime": "image/jpeg",         // 'image/png'|'image/jpeg'
    "data": "<base64>",           // short-lived；不得写普通日志
    "width": 821,
    "height": 810
  },
  "overlay": { /* BlockingOverlaySnapshotPayload，可选 */ }
}
```
> 截图必须来自原 edge 的原浏览器会话，cloud 不得另开浏览器生成。MVP 只在 cloud 进程内保留每个
> incident 的最新截图并依赖短 TTL 过期；不写入数据库、对象存储、Feishu 卡片或普通告警列表。扩大到
> 多人运营或 ol 前，如需审计，只能新增 append-only 元数据表，仍不得长期保存截图二进制。

**`captcha.assist.click`**（cloud → edge）：把人工点位派发到原浏览器
```jsonc
{
  "incidentId": "cap_01H...",
  "snapshotId": "snap_01H...",
  "points": [
    { "x": 0.35, "y": 0.42, "label": "image-1" },
    { "x": 0.70, "y": 0.44, "label": "image-2" }
  ],
  "requestedAt": 1717113605000,
  "settleMs": 1500,
  "trajectory": {                 // object?  运营真实鼠标轨迹（change captcha-assist-trajectory-replay），无/无效→edge 回落合成
    "v": 1,
    "samples": [                  // 归一化 {x,y}∈[0,1] + 相对首样本毫秒 t，时间序（≤250，超限判无效）
      { "x": 0.20, "y": 0.30, "t": 0 },
      { "x": 0.35, "y": 0.42, "t": 180 }
    ],
    "clicks": [1]                 // 每个 points[i] 对应的按下样本下标；length===points.length、下标∈[0,samples)
  }
}
```
> 点位是相对 snapshot 图片的归一化坐标 `[0,1]`。edge 必须校验 incident/snapshot/current overlay
> 和坐标边界后，再映射到当前 viewport 并派发真实输入事件；不得用 DOM 状态篡改替代点击。
> `trajectory` 可选：落点权威仍取 `points`，样本只供"怎么移动/何时按下"。edge 回放时**每次 press 前
> 必须补一帧 move 到权威落点**（消 mousedown 无前驱 move 的瞬移伪影）、只裁剪长停顿不等比压缩、叠 dt
> 抖动+亚像素；`clicks` 长度≠点数 / 样本超限 / 坐标越界等一律判无效→回落合成拟人路径（change
> captcha-assist-humanize-click），绝不硬回放、绝不谎称用了轨迹。无新增 MessageType。

**`captcha.assist.click_result`**（edge → cloud）：点击后的 fresh 复检结果
```jsonc
{
  "incidentId": "cap_01H...",
  "snapshotId": "snap_01H...",
  "edgeId": "edge-1",
  "accountId": "acc-01",
  "status": "still_blocked",      // 'cleared'|'still_blocked'|'stale_snapshot'|'not_blocked'|'invalid_target'|'failed'
  "reason": "captcha overlay still visible",
  "checkedAt": 1717113608000,
  "snapshot": { /* CaptchaAssistSnapshotPayload，可选，用于刷新仍阻断现场 */ },
  "replayMode": "synthetic"       // 'trajectory'|'synthetic'（change captcha-assist-trajectory-replay）：本次实际用的输入模式，供度量
}
```
> `status:'cleared'` 只是协助命令结果；恢复下发仍只由 edge 额外发送的 `risk.captcha_cleared`
> 触发。cloud 不得因为点击命令送达、Feishu 链接打开、协助页按钮点击或告警手动解决而 `resumeEdge`。
> 运行兜底：未配置远程协助、scoped token 过期、edge 离线或截图失败时，飞书告警仍保留原远程桌面处置路径；
> 操作员应远程连到原机器处理，随后等待 edge fresh probe 上报 `risk.captcha_cleared`，cloud 不能手动伪造清除。

### 3.10 Edge 页面写任务租约

申请与确认：

```jsonc
// edge.task.acquire  cloud → edge
{
  "taskId": "task-01H...",
  "kind": "publish", // publish|comment_prepare|comment_commit|notification|group_join|system_recovery
  "priority": "human", // system_recovery|human|automatic
  "leaseMs": 600000,
  "acquireTimeoutMs": 45000 // edge 本地等待 quiesce 的上限；届满不再授予该任务
}

// edge.task.acquired  edge → cloud
{
  "taskId": "task-01H...",
  "kind": "publish",
  "cancelledBrowseCommands": 2
}
```

`acquired` 是唯一的 quiesced 事实：它表示当前浏览原子动作已到命令边界，尚未开始的普通浏览命令已取消，且该 `taskId` 已成为唯一页面写 owner。cloud 在此前不得发送该任务第一条业务命令。普通浏览不带 `taskId`；独占任务的 `publish.command`、评论 `search.execute/note.open/note.scroll_comments/interaction.comment`、`notification.*`、`group.join` 与验证码点击必须携当前 `taskId`。

释放与确认：

```jsonc
// edge.task.release  cloud → edge
{ "taskId": "task-01H...", "outcome": "completed" }

// edge.task.released  edge → cloud
{ "taskId": "task-01H...", "reason": "released" } // released|expired|duplicate|not_owner|cdp_unhealthy
```

edge 按 `system_recovery > human > automatic` 授予；同级 FIFO。发布从 `navigate_entry` 到提交后捕获全程持有一份租约。小红书评论的搜索/读取为 prepare 租约，撰写/LLM/人审期间释放，批准后 commit 重新抢占并按稳定 `noteId` 重开复检。最后一份独占任务释放后才恢复浏览并重报当前页面；被取消的旧浏览命令永不重放。

### 3.11 发布编排

**`publish.request`**（cloud → edge）——请求在浏览器中发布
```jsonc
{
  "title": "测评｜入门露营装备清单",   // string
  "content": "正文 200–500 字…",      // string
  "tags": ["露营", "装备", "新手"],    // string[]  3–5 个
  "images": ["https://..."]           // string[]? 可选配图
}
```

**`publish.approval_request`**（edge → cloud）——请求云端发飞书审批卡片
```jsonc
{
  "requestId": "edge-1718025823456-a1b2c3d4", // string  单次发布唯一标识
  "title": "测评｜入门露营装备清单",
  "content": "正文…",
  "tags": ["露营", "装备", "新手"],
  "edgeId": "edge-01"                          // string? 观测用
}
```
> 边缘发出后进入等待：轮询审批信号文件 `/tmp/aidcp-publish-approve-<requestId>.json`
> （由云端飞书卡片回调写入，含 `approved` 字段）。`approved=true` 才执行本地发布流程。

**`publish.approval_action`**（edge → cloud）——客户端稿件预览内提交审批
```jsonc
{
  "requestId": "publish-89", // string；仅接受 publish-<数字>
  "approved": true,           // boolean；true=发布，false=取消
  "contentVersion": 0         // number?；客户端所见版本，云端写信号前复核
}
```
云端按连接握手的真实 `accountId` 校验稿件归属，并复用飞书/控制台共用的
first-writer-wins 审批信号。动作成功只表示审批决定已受理：`approved=true` 后仍由
发布调度器异步下发，最终结果以 `publish.command.result` / `publish.result` 为准。

**`publish.approval_action.result`**（cloud → edge）
```jsonc
{
  "requestId": "publish-89",
  "ok": true,
  "state": "approved",       // approved | rejected
  "alreadyDecided": false,    // 可选；重复动作命中既有决定时为 true
  "reason": "version_stale", // 可选；失败原因
  "currentVersion": 1         // 可选；版本过期时返回当前版本
}
```

**`publish.result`**（edge → cloud）
```jsonc
{ "ok": true, "postId": "p789", "error": null } // postId / error 二选一
```

### 3.12 通用

**`error`**（双向）
```jsonc
{
  "code": "bad_envelope",  // string  错误码：bad_envelope | unsupported_type | handler_error | ...
  "message": "无法解析的协议帧" // string  人读说明
}
```

**`ping` / `pong`**：payload 为空对象 `{}`；服务端收到 `ping` 回 `pong`（回填同一 `id`）。

## 4. 典型时序

### 4.1 浏览会话闭环（v2 主路径：结构化上报 + 角色驱动）

```
edge                                          cloud（RoleDispatcher + 多角色/RoleName 43 + EventBus）
 │  hello {edgeId}                             │
 │ ───────────────────────────────────────────►│  分配 session
 │  welcome {sessionId}                         │
 │ ◄───────────────────────────────────────────│
 │  session.budget.request {accountId}          │
 │ ───────────────────────────────────────────►│  RiskController 估算预算
 │  session.budget {durationMs,maxActions,...}  │
 │ ◄───────────────────────────────────────────│
 │                                              │
 │  page.cards {cards[]}                         │  ContentEvaluator 评估卡片价值
 │ ───────────────────────────────────────────►│   → 有价值: 发 note.open；无价值: 发 page.scroll
 │  note.open {index} | page.scroll             │
 │ ◄───────────────────────────────────────────│
 │  note.detail {noteId,content,...}            │  ContentCurator 质量关卡 → InteractionAppraiser 决策
 │ ───────────────────────────────────────────►│
 │  interaction.like {noteId} | navigation.back │  （角色事件 → command-bridge → 协议消息）
 │ ◄───────────────────────────────────────────│
 │  action.completed {action:"like",ok:true}    │  记录互动；BackToFeed 决定返回列表
 │ ───────────────────────────────────────────►│
 │                  …闭环往复…                    │  SessionMonitor 超时/超预算 → session.end
 │  session.end {reason,stats}                  │
 │ ◄───────────────────────────────────────────│
```

> 互动前可选地穿插 `risk.canDo → risk.canDo.result` 询问许可、成功后 `risk.record`
> 落账（边缘主动风控路径）；与"云端角色主动下发 `interaction.like`"两条路径并存。

### 4.2 单步定位（规划 / 锚点 / 选择，v1 兼容链路）

```
edge                                cloud
 │  plan.request {goal}               │  SimplePlanner.plan()
 │ ─────────────────────────────────►│
 │  plan.response {steps[]}           │
 │ ◄─────────────────────────────────│
 │  anchor.get {actionId}             │  PgAnchorCache.get()
 │ ─────────────────────────────────►│
 │  anchor.get.result {anchor|null}   │
 │ ◄─────────────────────────────────│
 │  （缺口）select.request {goal,els}  │  文本 LLM 选编号 + 范围校验
 │ ─────────────────────────────────►│
 │  select.response {index|null}      │
 │ ◄─────────────────────────────────│
 │  执行 + 后置校验后：                 │
 │  anchor.report {source,validated}  │  反污染晋升（无回包）
 │ ─────────────────────────────────►│
 │  action.result {outcome}           │  观测/训练（无回包）
 │ ─────────────────────────────────►│
```

### 4.3 发布审批

```
cloud（Publish Agent）          edge                         飞书（云端 Bot）
 │ publish.request {title,...}   │                            │
 │ ─────────────────────────────►│ 生成 requestId             │
 │                               │ publish.approval_request   │
 │                               │ ──────────────────────────►│ buildPublishApprovalCard()
 │                               │                            │ 发卡到默认群/FEISHU_CHAT_ID
 │                               │ 轮询信号文件…               │ 运营点[授权发布]
 │                               │ ◄── 写 /tmp/aidcp-publish-approve-<id>.json (approved=true)
 │                               │ approved → publishPost()    │
 │ publish.result {ok,postId}    │ （进入→标题→正文→标签→提交→校验）
 │ ◄─────────────────────────────│                            │
```
客户端稿件预览的“发布 / 取消”按钮走 `publish.approval_action`，与飞书按钮共享同一
审批信号和 first-writer-wins 规则；预览内的“查看稿件 ↗”只打开本地抽屉，不再跳转飞书。

## 5. 错误与兼容性

- **未知 type**：服务端回 `error`（code=`unsupported_type`）。
- **handler 抛错**：被兜成 `error`（code=`handler_error`），不崩连接。
- **坏帧**：`parseEnvelope` 返回 null → `error`（code=`bad_envelope`）。
- **版本演进**：`v` 用于灰度；新增字段应保持向后兼容（旧端忽略未知字段）。v2 对 v1
  的全部消息保持兼容，新增消息类型旧端可安全忽略。
