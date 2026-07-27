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
>    对应云端从单体 Planner 重构为**事件驱动多 Agent**（`RoleDispatcher` + 多角色，覆盖浏览闭环、会话守护、评论、通知、概念和平台专题等职责；权威清单见 `event-bus/types.ts` 的 `RoleName` 与 `role-dispatcher.ts`）后的实时控制面；
> 3. **风控预算与发布审批**（`session.budget`/`risk.canDo`/`publish.*`）——把"做多少、能不能做、发布前要不要人审"纳入协议。
>
> 下表按职能整理 v2 消息。准确枚举以两端 `protocol.ts` 的 `MessageType`、协议 acceptance
> 契约测试、已注册 handler/routing 与 capability 协商为准；本文不复制易漂移的消息总数。

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
| `ui.snapshot` | cloud → edge | — | 自动化控制投影；新能力客户端仅接收 `browserStandby` 等控制提示，旧客户端兼容接收昵称/发布/今日用量等历史字段 |
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
| `note.open` | cloud → edge | 打开一条笔记（可选 `surface`:'feed'\|'detail'、`purpose`:'read'\|'navigate'；Facebook 还可用 `url` 直达，或用 `selection:'first_commentable_group_post'` + `container` 选择群讨论流首条稳定可评论帖） |
| `note.close` | cloud → edge | 关闭当前笔记 |
| `search.execute` | cloud → edge | 执行一次关键词搜索；协商 `search_activity_receipt_v1` 时携稳定 `activityId` 与 purpose/scope，Edge 回诚实提交边界和结果终态 |
| `session.end` | cloud → edge | 结束本次浏览会话 |

### 2.3 角色/命令式驱动指令（v2 新增，cloud → edge）

| type | 方向 | 用途 |
| --- | --- | --- |
| `page.scroll` | cloud → edge | 页面滚动（`reason`: feed_scroll / search_scroll；Facebook 首页显式空态或有界续滚后仍有物理卡但不可可靠上报时，Cloud 可下发 `empty_feed_reels_fallback` 单次授权进入 Reels；可选 `dwellMs`） |
| `feed.refresh` | cloud → edge | 主 feed 浏览深度到阈值后，点右下「刷新」按钮回到顶部换出全新一批（`reason`: feed_refresh；可选 `thinkMs`；边缘诚实回执 `action.completed{action:'refresh'}`，非 feed 页 / 无按钮 / 点后未换新批均如实失败，绝不假成功） |
| `pacing.update` | cloud → edge | 会话中途风控档位变化推送新 `tempo`（payload `{tempo}`）；边缘刷新兜底节奏（最小间隔 + 停留兜底）、**不重置**操作间隔锚点、不入队/不唤醒会话（change pacing-fallback-hardening） |
| `interaction.like` | cloud → edge | 点赞指定笔记 |
| `interaction.collect` | cloud → edge | 收藏指定笔记 |
| `interaction.follow` | cloud → edge | 关注作者 |
| `interaction.comment` | cloud → edge | 在当前笔记发评论（`text` 正文；云端已撰写/去AI味/人审通过）。可选 `groupChatCode`=账号「联系方式」，非空则 verbatim 追加到评论末尾（wire 名历史保留，概念=contact info，change generalize-contact-info）；可选 `fastReturnToFeed=true` 仅承载手工 `/comment --feed`：提交派发后不等平台确认，500ms 后直回平台首页，并诚实回 submitted-unconfirmed / verification_ambiguous（绝不冒充平台确认成功） |
| `interaction.like_comment` | cloud → edge | 给详情页内某条评论点赞（`commentAnchorId` 稳定锚点定位，绝不按序号） |
| `group.join` | cloud → edge | Facebook 加群原子指令：导航到群、回传结构化 observation；仅 `click:true` 时点击 Join 一次，必须走 Facebook `join` 能力，绝不复用 `browse` |
| `navigation.back` | cloud → edge | 返回上一页（feed / search） |
| `note.browse_images` | cloud → edge | 浏览笔记图片（`count` 张；DeepReader 决策下发） |
| `note.scroll_comments` | cloud → edge | 滚动评论区（CommentReviewer 决策下发） |
| `profile.open` | cloud → edge | 进入普通作者主页；不得承载本人身份采集或 `direct` |
| `identity.read_current` | cloud → edge | 就地读取会话绑定账号身份；禁止导航，payload 仅含 Cloud 生成的 `captureId` |
| `identity.read_self_profile` | cloud → edge | 导航到 Edge 会话绑定账号本人主页读取身份；Cloud 不得提供目标账号 ID |
| `notification.open` | cloud → edge | 导航到通知首页（仅导航；落地后边缘上报 `notification.home`） |
| `notification.browse_comments` | cloud → edge | 进「评论和@」+ 滚动加载 + 抽取（→ `notification.items`） |
| `notification.browse_likes` | cloud → edge | 进「赞和收藏」（清未读 + 抽取点赞/收藏发送者 → `notification.items`） |
| `notification.browse_follows` | cloud → edge | 进「新增关注」（清未读 + 抽取关注者 → `notification.items`） |
| `notification.back_home` | cloud → edge | 返回通知首页（重报各类未读） |

### 2.4 结构化上报（v2 新增，edge → cloud，`RoleDispatcher` 消费）

| type | 方向 | 用途 |
| --- | --- | --- |
| `page.cards` | edge → cloud | 上报当前可见卡片列表；可选 `listKind`/`listState` 是页面形态与内容状态观察，缺省 `feed/ready`，不扩展 `feed/detail` Surface |
| `note.detail` | edge → cloud | 上报笔记详情（正文/作者/计数） |
| `profile.detail` | edge → cloud | 上报作者主页数据（粉丝数/作品数） |
| `identity.observed` | edge → cloud | 上报与 `captureId` 关联的本人身份观察；独立于普通作者 `profile.detail` |
| `action.completed` | edge → cloud | 确认某个 action 执行完成（可选 `noteId`=从被点 article DOM 派生的规范 postId、MUST NOT 抄命令 payload；可选 `observation`=独立见证包 {surface?/listKey?/author?/textPreviewHead?/reactionText?/articleIndex?}，供云端归账仲裁逐字段比对选中卡；search 另可携 `activityId/purpose/scope/actuated/searchOutcome/resultCount`；均 optional，旧端缺省按兼容路径处理） |
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
| `edge.task.released` | edge → cloud | 释放/过期/非 owner 的收敛回执；`cdp_unhealthy`=在线但浏览器控制不可安全接管，`browser_wake_failed`=冷待机停靠的浏览器在唤醒死线内唤不醒（可恢复、别与 `cdp_unhealthy` 混淆），`preempted_by_task`=被严格更高档任务抢占（云端**不得判失败**，保持待审待抢占方释放后重投），`window_busy`=holder 处不可抢占的提交窗口（携 `windowRemainingMs` 剩余预算，供云端精确等待而非空转），`yield_timeout`=收到取消仍不停手→判控制面故障（需人工重启客户端，非自愈） |

### 2.6 发布编排（v2 新增，Publish Agent 驱动）

| type | 方向 | 用途 |
| --- | --- | --- |
| `publish.request` | cloud → edge | 请求在浏览器中发布一篇帖子 |
| `publish.approval_request` | edge → cloud | 请求云端发送发布审批卡片（飞书） |
| `publish.approval_action` | edge → cloud | 客户端稿件审批页提交批准/取消，批准可携立即/定时发布计划与稿件版本 |
| `publish.approval_action.result` | cloud → edge | 返回审批动作受理结果；不代表已完成发帖 |
| `publish.draft_image_remove` | edge → cloud | 客户端稿件预览内删除待审稿件的某张配图，携稿件版本 |
| `publish.draft_image_remove.result` | cloud → edge | 返回删配图结果（成功回带写后真态 images + 新版本）|
| `publish.result` | edge → cloud | 发布结果回传（ok / postId / error；v1 整页路径） |
| `publish.command` | cloud → edge | 下发一条参数化发布原子指令（`taskId` 为当前发布租约；`recordId+seq` 关联键；`kind` 复用通用 command 映射，含 `capture_scheduled` / `reconcile_scheduled`，不新增 `MessageType`） |
| `publish.command.result` | edge → cloud | 单条发布指令执行结果回传（按 `recordId+seq` 关联；`ok/value/error/details`，红线不静默假成功；`submitDispatched`=提交「按下」事件已真正派发——`ok:false` 但该位为真时帖子可能已发出，云端按「已提交待确认」处置、绝不烧 failed、绝不自动重投） |

### 2.7 Persona 生成（v2 新增，建号关键词驱动，客户自助 onboarding）

**edge 发起的请求/响应**，回包走 pending-id 命中——不经 `command-bridge` 动作映射、不经 edge `onMessage` 主动命令白名单。大模型/密钥/校验/序列化/落库/记账全在云端；边缘只收关键词、显示草稿、回确认。

| type | 方向 | 关联响应 | 用途 |
| --- | --- | --- | --- |
| `persona.generate` | edge → cloud | `persona.generate.result` | 按客户勾选关键词请求云端生成账号 persona 草稿（Facebook 另带受控 `writingLanguage`；带 `idempotencyKey` 防重连/重试双计费；云端以握手绑定 `accountId` 与平台为准） |
| `persona.generate.result` | cloud → edge | — | 返回生成的 soul.yaml + 身份摘要；失败带 `reason`，MUST NOT 返回半成品（fail-closed、宁缺毋假） |
| `persona.persist` | edge → cloud | `persona.persist.result` | 请求持久化客户确认后的 soul.yaml（复用云端现有校验写入通道，不新造写路径） |
| `persona.persist.result` | cloud → edge | — | 持久化结果；失败带 `reason`（`unknown_account` / `persona_required` / `persona_invalid`）；本次确实首次建立账号级首作状态时可带 `firstPostOnboarding:true` |

`persona.generate` 请求 payload：
```jsonc
{
  "accountId": "acc-1",
  "keywordSelections": ["咖啡", "亲切接地气", "like_affinity:normal"],
  "writingLanguage": "vi", // 仅 Facebook；zh-CN | en | vi。FB 新建/更新必填，非 FB 携带即拒绝
  "idempotencyKey": "persona-..."
}
```
语言是独立账号配置，不得混入 `keywordSelections`。Cloud 按握手会话的平台校验：Facebook 缺失/非法分别返回
`writing_language_required` / `writing_language_invalid`，非 Facebook 携带返回 `writing_language_not_supported`。

`persona.persist.result` 成功 payload：
```jsonc
{
  "ok": true,
  "firstPostOnboarding": true // 可选；仅本次原子建立账号终身唯一的首作状态时为 true
}
```
该字段不是“当前有没有人设”的别名。更新人设、重复请求、解绑后重绑或账号已经建立过首作状态时为
`false`/缺省；Edge 只有看到明确的 `true` 才展示“人设已成形”后的第一篇作品引导。

### 2.8 视频号入站互动管理（v2 扩展）

> 精确合同见 `docs/contracts/wechat-channels-interaction/v1/`。基础消息要求双方确认 `interaction_inbox_v1`；恢复、offboard、账号开关与浏览器显隐消息还分别要求 `interaction_reply_recovery_v1`、`interaction_offboarding_v1`、`interaction_runtime_controls_v1`、`interaction_browser_control_v1`。

| type | 方向 | 关联响应 | 用途 |
| --- | --- | --- | --- |
| `interaction.auth.status` | edge → cloud | — | 上报视频号 auth/browser/capability/identity 真态 |
| `interaction.sync.batch` | edge → cloud | `interaction.sync.ack` | 按账号、渠道、scope 上报可重放批次 |
| `interaction.sync.ack` | cloud → edge | — | 确认整批 accepted/duplicate/rejected；只有前两者可推进 checkpoint |
| `interaction.reply.result` | edge → cloud | `interaction.reply.result.ack`（协商 recovery 时） | 先 durable 落盘，再回 confirmed/failed/ambiguous 真态 |
| `interaction.reply.result.ack` | cloud → edge | — | exact accepted/duplicate 后 Edge 才清 result outbox |
| `interaction.reply.reconcile` | cloud → edge | `interaction.reply.reconcile.result` | 启动/重连后仅核验已有 attempt，不得触发平台写 |
| `interaction.reply.reconcile.result` | edge → cloud | — | 逐 attempt 回 result_replayed/not_found/binding_conflict |
| `interaction.sync.request` | cloud → edge | 后续 `interaction.sync.batch` | 触发用户请求、恢复、定时或回查同步 |
| `interaction.reply.send` | cloud → edge | `interaction.reply.result` | 下发带稳定幂等键的 text 回复指令 |
| `interaction.auth.reopen` | cloud → edge | 后续 `interaction.auth.status` | 请求在原 Edge 打开所属登录/挑战现场 |
| `interaction.browser.control` | cloud → edge | 后续 `interaction.auth.status` | active 会话打开可见浏览器或转回 API-only 后台；投递不等于已显隐 |
| `interaction.runtime.controls` | cloud → edge | 后续 `interaction.auth.status` | 只向匹配账号下发单调版本的有效开关快照；投递不等于应用 |
| `interaction.offboard.command` | cloud → edge | `interaction.offboard.result` | 撤权后停同步/写、drain、清 scope 密文并关 sidecar |
| `interaction.offboard.result` | edge → cloud | `interaction.offboard.ack` | durable cleared/already_cleared/failed 结果，可重连补发 |
| `interaction.offboard.ack` | cloud → edge | — | exact accepted/duplicate 后 Edge 才清 offboard outbox |

## 3. 各消息 payload 定义

### 3.1 握手

**`hello`**（edge → cloud）
```jsonc
{
  "edgeId": "edge-01",        // string  边缘节点标识
  "platform": "xiaohongshu",  // string? 运行时平台标识；缺省按历史 xhs 兼容，cloud 会与 accounts.platform 校验
  "app": "xhs",               // string? 业务/站点标识
  "capabilities": ["click", "input", "scroll", "captcha_assist_text_v1", "client_core_browser_executor_v1", "facebook_reel_follow_v1", "search_activity_receipt_v1", "interaction_inbox_v1", "interaction_reply_recovery_v1", "interaction_offboarding_v1", "interaction_runtime_controls_v1", "interaction_browser_control_v1"], // string[]? 能力声明（构建能力位由 EdgeClient 构造函数统一并入）
  "accountId": "acc-01",      // string? 账号标识；多账号运行时要求真实账号，default 已退役
  "accountNickname": "小张测评", // string? 账号可读昵称；仅用于展示补充，不参与身份确立或路由
  "machineLabel": "win-aliyun-3" // string? 人类可读机器标签（change captcha-assist-text-answer：已移除背后无能力的 remoteAddr/远程桌面入口，design D13）
}
```

`platform` 和 `accountNickname` 都是平台抽象层的 type-only payload 扩展，不新增消息类型。cloud 在握手建运行时前以 `accounts.platform` 为事实源校验 edge 上报平台；不一致时返回 `error`，不会让 xhs edge、Facebook edge 或视频号 edge 跨平台接管账号。`accountNickname` 只能作为展示补充，不能用于身份确立、平台校验或命令路由。`client_core_browser_executor_v1` 是可选的结构能力位：双方回显只说明客户端能把 core/Cloud transport 与浏览器执行器分别管理，不改变任何旧消息类型；旧 Cloud 不回显时 Edge 保持旧协议兼容。`facebook_reel_follow_v1` 表示该 Edge 构建包含绑定规范 Reel、唯一作者和后置 Following 状态的关注执行器；Cloud 未看到此位时不得掷自动 Reel 关注概率或下发对应命令。`search_activity_receipt_v1` 表示 Edge 能为每条 search 命令回传稳定关联、真实提交边界与唯一终态；只有双方在 welcome 中协商成功时，Cloud 才以该回执记 search 风控事实并延后概念池 `markSearched`。未协商的旧 Edge 继续沿用历史搜索/关键词尝试记账，不得由 Cloud 伪造已执行 search 风控事实。五项 interaction capability 都是 optional；四个扩展 capability 依赖 `interaction_inbox_v1`，新 Edge 只有收到相应 `welcome.capabilities` 回显后才启用对应消息。回显 `interaction_offboarding_v1` 时，Cloud 还必须在 welcome 带当前 account 的 `interactionRecovery.offboardPending`；回显 `interaction_runtime_controls_v1` 时必须带 `interactionRuntime`。任一查询失败都按 all-off/pending 处理，不能沿用别的账号或旧连接的能力。

**`welcome`**（cloud → edge）
```jsonc
{
  "sessionId": "sess-1",      // string  云端分配的会话 id
  "serverVersion": "0.1.0",   // string  服务端版本
  "capabilities": ["client_core_browser_executor_v1", "search_activity_receipt_v1", "interaction_inbox_v1", "interaction_reply_recovery_v1", "interaction_offboarding_v1", "interaction_runtime_controls_v1", "interaction_browser_control_v1"], // string[]? Cloud 确认双方支持；旧端忽略
  "interactionRecovery": { "offboardPending": false }, // object? 协商 offboard 时必带；缺失/true=Edge 不恢复 connector
  "interactionRuntime": { // object? 协商账号开关时必带；缺失=Edge 全能力关闭
    "accountId": "acc-01", "envKey": "env-01", "version": 7,
    "commentsReadEnabled": true, "commentsReplyEnabled": false,
    "dmReadEnabled": true, "dmSendTextEnabled": false, "dmSendImageEnabled": false
  },
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

### 3.1.1 客户端数据面与自动化引擎边界

新客户端能力位为 `client_data_plane_automation_engine_v1`。Electron 应用是客户端；普通 Edge 子进程是按需自动化引擎；浏览器/CDP 是页面执行器。客户会话有效时，AIDCP 自有数据通过 Electron main 的 customer-auth HTTP 逐请求读写，不存在全局 `cloudState` 准入，也不依赖环境引擎、automation WebSocket 或浏览器在线。

操作必须先进入中心注册表并恰好归入一个类别：`local`、`cloud_data`、`automation_control`、`platform_api_automation`、`browser_lifecycle`、`page_automation`。`cloud_data` 只允许 customer-auth HTTP，禁止进入 automation WebSocket；`platform_api_automation` 需要已启用引擎但不申请浏览器槽位；`page_automation` 才申请槽位、启动 provider、附着 CDP 并获取页面任务租约。未知 Cloud 主动消息按 `operation_unclassified` 拒绝，不能回落成页面命令。

**出站红线**：Cloud/管理后台不得经 per-environment automation WebSocket 推送人设、配置、稿件、审批、环境管理或其他普通数据命令。后台数据变更应先写权威存储，客户端后续主动 HTTP 拉取。未来若增加独立用户级通知，只能发送 invalidation/refetch 提示，不能夹带非自动化业务写，也不能因为某环境引擎离线就把客户端视为离线。

新客户端公开 `clientSessionState`、`automationState`、`browserState`；`engineLinkState` 只作自动化诊断。`coreState`、`cloudState` 仅为 `client_core_browser_executor_v1` 旧客户端兼容投影，不得被新客户端用作数据管理入口准入。

客户人设、待审稿读取/删图/批准/拒绝使用 customer-auth 的环境级窄接口，客户端只提交 `envKey`，Cloud 在每次请求内复核客户归属并解析权威 `accountId`。对应接口为：

- `GET|POST|PUT /environments/:envKey/persona[/draft]`
- `GET /environments/:envKey/overview`
- `POST /environments/:envKey/publish/draft-image-remove`
- `POST /environments/:envKey/publish/approval`

旧 Edge WS 的 `persona.*`、`publish.approval_action` 和 `publish.draft_image_remove` 只为旧能力客户端保留兼容；新能力客户端不得由 Cloud 主动推送这些 `cloud_data` 操作。两条历史传输必须复用同一领域方法。批准接口返回 `accepted_pending_execution` 只表示决策已受理、等待自动化执行，不表示平台已发布。

`GET /environments/:envKey/overview` 是客户端首页业务数据的单一读源，返回 `dailyUsage`、`currentPublishState`、`lastPublished` 与 `meta.asOf`。它不接收也不返回 `accountId`，不检查引擎、automation WebSocket、浏览器/CDP 或槽位；Cloud 从客户环境归属与持久绑定解析账号，再复用既有风控计数和发布日志。自动化结果只允许使该 HTTP 缓存失效并触发重拉，不得直接覆盖已确认概览。首次失败不得物化 0 或“从未发布”，刷新失败时保留上次确认缓存并标明陈旧。

Cloud 切换通过 Electron→core 的本地 `lifecycle.cloud_rebind` 控制协议逐环境重绑 WS：先在安全边界排空当前页面写，停止旧 Cloud intake，再完成新 hello/welcome。该动作不得启停 provider、CDP、浏览器或变更槽位所有权；实际 Cloud、目标 Cloud 与失败原因分别投影。

**`ui.snapshot`**（cloud → edge，主动推送；change edge-companion-ui 8.1）

> 兼容边界：下列 `personaBound`、`personaWritingLanguage`、`lastPublish`、`publish`、`publishPreview`、`dailyUsage` 只对未协商 `client_data_plane_automation_engine_v1` 的旧客户端下发。新客户端的 `ui.snapshot` 仅保留 `browserStandby` 等自动化控制投影；今日进展、最近发布、人设、稿件和审批真态由客户端 customer-auth HTTP 主动拉取。Cloud 按 capability 过滤，Edge 同时丢弃旧 Cloud 夹带的数据字段，形成双向防线。

```jsonc
{
  "account": { "id": "acc-1", "nickname": "晚风手作" },   // 可选；昵称空则整个字段不带（宁缺毋假）
  "personaBound": true,   // 可选；true=已绑，false=云端确认未绑，字段缺省=未知；边缘只对 false 打开建号向导
  "personaWritingLanguage": "vi", // 可选；仅在 personaBound=true 且 Cloud 提供读取口时出现；zh-CN | en | vi，null=存量人设尚未配置
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
    "totals": { "view": 10, "search": 2, "like": 3, "collect": 1, "comment": 0, "follow": 2, "publish": 1 },
    "quotas": { "view": 150, "search": 10, "like": 50, "collect": 25, "comment": 8, "follow": 15, "publish": 1 },
    "saturated": ["publish"], // 向后兼容：以上三项是 day 窗口别名
    "firstPost": { // 可选；仅账号终身首作状态正在寻找/生成时出现
      "state": "searching", // searching | generating
      "viewed": 7,          // 从首作状态 startedAt 起累计的真实 view 数
      "target": 20,         // 新手首轮展示预期，不是风控配额或成功保证
      "startedAt": 1730000000000,
      "sourceId": "note-9" // 可选；generating 时已原子认领的精选源内容
    },
    "slowStart": { // 可选（change environment-level-slow-start）；当前环境的慢启动配置/生效投影
      // **字段整体缺省 = 未知（云端还没说）→ 边缘整行不渲染**，照 personaBound 三态判例：MUST NOT 把「未知」当「关」
      "state": "active",     // off | active | graduated（graduated=已完成，上限已放开但库里开关仍为真，显式告知而非静默消失）
      "day": 3,              // 仅 active；1..totalDays
      "totalDays": 7,        // 曲线总天数（恒 7）
      "since": 1729900800000, // 环境起点（epoch ms，已对齐上海日起点）；不随账号换绑重置
      "binding": true,       // 仅有唯一当前账号时有意义；clamp 是否至少收紧一项
      "eligible": true,      // false 表示当前无法作用到唯一账号；binding_unknown/conflict 时环境开关仍可配置
      "ineligibleReason": "platform_unknown" // 可选：platform_unsupported | platform_unknown | globally_disabled | binding_unknown | binding_conflict
    },
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
已核、`scheduled`=平台已接受定时稿、等待公开对账、`submitted`=页面已接受立即提交但同页尚未取得帖子链接、
`rejected`=拒绝发布、`failed`=云端终判失败）。`published` 不经此通道——立即发布仅在同页
`capture_postId` 成功后本地打 `[ui-event]` 行；正常链路不得为确认而
刷新页面。`reminded` 枚举保留但云端当前无再提醒机制、不会出现。`code` 与
飞书审批卡「编号」字段同源（发布记录 id，如 `#83`），供界面对暗号。边缘核心收到后转成 `[ui-event]`
结构化行打到 stdout，由 Electron 壳解析驱动标题带与发布卡（解析器 `src/electron/ui-events.cjs`）。
已拒草稿在 hello 快照不回放（拒绝时刻已实时推过，重启不翻旧账）。推送为 best-effort：账号无在线
边缘即如实放弃，持久态由下次 hello 快照补齐。

`dailyUsage.totals` / `quotas` / `saturated` 保持为日窗口别名，用于旧边缘兼容；新客户端从 HTTP `overview.dailyUsage` 读取同一数据结构。
`dailyUsage.firstPost` 是首作新人首轮的独立投影：只有字段存在时 Edge 才固定显示 `/20`；字段缺失时继续使用
账号真实的今日或当前窗口计划。`20` 不写入 `quotas`、不停止浏览，也不表示必定筛出灵感；浏览达到或超过
20 条仍未有真实精选命中时，客户端只能如实表达“继续寻找合适方向”。当第一条非空图文/视频源内容进入
精选池后，Cloud 将 `state` 切为 `generating` 并复用现有参照创作与发布确认链；评论精选不触发首作生成。
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
// selection/container?（change facebook-join-contact-first-post，可选）：不配置搜索关键词时，
//   Cloud 不发 search.execute，而发下面的选择请求。Edge 打开群讨论流，选择第一条同时具备稳定群帖 permalink
//   与评论入口的顶层帖子，再进入该 permalink 读取正文/评论，并以实际 permalink 回 note.detail.noteId。
//   首帖不合格或已去重时不得顺延第二帖、不得回退搜索；旧的 url/index/noteId 行为保持不变。
{
  "selection": "first_commentable_group_post",
  "container": "https://www.facebook.com/groups/123"
}
```

**`note.close`**（cloud → edge）：`{ "reason": "..." }`（可选）

**`search.execute`**（cloud → edge）
```jsonc
{
  "activityId": "search-7f3d", // string? 协商 search_activity_receipt_v1 时必填；同一条逻辑命令重试保持稳定
  "purpose": "discovery",      // ? discovery | task_targeting | operator
  "scope": "global",           // ? global | container；container 时须同时给合法 container
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

协商 `search_activity_receipt_v1` 后，Cloud 在下发前同时检查账号 `search` 风控配额、会话 search 预算和关键词限流；任一闸拒绝都不下发，也不生成已执行事实。purpose 只描述业务来源：自主概念发现为 `discovery/global`，评论等定向任务为 `task_targeting`（Facebook 群内为 `container`），人工命令为 `operator`；operator 仍计真实风控用量，但不触发自主节奏告警。

旧 Edge 可以忽略新增可选字段。Cloud 对旧 Edge 保留历史关键词尝试/概念池兼容行为，但不得把“命令送达”推断成 search 已真实执行；升级后只认下述 terminal receipt。

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
{ "reason": "empty_feed_reels_fallback" }    // 仅 Cloud 收到 Facebook 首页 feed/empty 或 feed/present_unreportable 观察后授权一次；Edge 不得自行切列表
// feed.refresh（feed 浏览深度到阈值改点右下「刷新」回顶换新批，change feed-refresh-on-depth）
{ "reason": "feed_refresh", "thinkMs": 700 } // 边缘点后校验「回顶 + 首卡换新」才回 ok:true 并上报新一批 page.cards
// interaction.like
{ "noteId": "n123", "reason": "高质量内容", "thinkMs": 900 }
// interaction.collect
{ "noteId": "n123", "reason": "值得收藏", "thinkMs": 900 }
// interaction.follow
{ "authorId": "u456", "reason": "持续优质", "thinkMs": 900 } // 既有主页关注：authorId 可选
{ "noteId": "https://www.facebook.com/reel/1964804494173822", "reason": "明确关注当前 Reel 作者", "thinkMs": 900 } // Facebook Reels：noteId 必填并绑定当前活动 Reel；不以 DOM 顺序或“当前页”兜底
// interaction.comment
{ "noteId": "n123", "text": "今天的分享很有启发", "thinkMs": 900, "groupChatCode": "...", "fastReturnToFeed": true } // text 必填；groupChatCode 可选=账号「联系方式」；fastReturnToFeed 仅手工 --feed 置 true：提交后 500ms 直回首页、结果保持未确认
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
// profile.open（普通作者主页；不得用于本人身份采集）
{ "authorId": "u456", "reason": "作者值得关注评估", "thinkMs": 800 }
// identity.read_current（Facebook；只允许当前页读取，禁止导航）
{ "captureId": "capture-018f..." }
// identity.read_self_profile（XHS；目标账号由 Edge 会话绑定值注入，Cloud 不传 accountId）
{ "captureId": "capture-0190..." }
```

本人身份采集分三层，禁止再把平台差异塞进通用 `profile.open`：

| 平台 | Cloud 选择 | Edge 握手能力 | 页面副作用 | 完成后恢复 |
| --- | --- | --- | --- | --- |
| Xiaohongshu | `identity.read_self_profile` | `identity_read_self_profile_v1` | 只导航到 Edge 当前会话绑定账号的规范本人主页 | `identity.observed.pageEffect=navigated_self_profile` 后返回 feed |
| Facebook | `identity.read_current` | `identity_read_current_v1` | 当前页读取，Native 执行路径不得调用导航 | 无；Cloud 不发 back / refresh / scroll |
| WeChat Channels | 不支持 | 无 | 无 | 无 |

Edge 启动握手所需的身份读取是本地 `identity_bootstrap`，不属于 Cloud 可下发消息，也不能与上述运行期命令
共用 Native kind。两个运行期命令都回：

```jsonc
{
  "captureId": "capture-018f...",
  "accountId": "61591824155856",
  "nickname": "Gi Vo",                  // 可选；空值不写库
  "source": "current_page",             // current_page | self_profile
  "pageEffect": "none"                  // none | navigated_self_profile
}
```

Cloud 只接受同时匹配当前连接 `accountId` 与在途 `captureId` 的结果。新 Cloud 连接旧 Edge 时，缺少对应握手能力
即跳过这次可选二次采集并留可观测日志，绝不回落 `profile.open`；新 Edge 收到遗留
`profile.open{direct:...}` 必须在 CDP 前以 `legacy_profile_direct_unsupported` 拒绝。平台不支持的身份命令同样
在 Native adapter 支持矩阵/CDP 前拒绝，不做跨平台 fallback。

`interaction.follow.noteId` 是向后兼容的可选扩展：非 Reels 调用方仍可只携 `authorId`。Facebook
Reels 执行器仅在会话确处于 Reels 模式、且 `noteId` 与立即重探的规范活动 Reel 完全一致时才允许定位作者区
关注按钮；命令延迟后若已滑到下一条则回 `no_target`、零点击。该字段只接通执行能力，不等于云端已经选择了
自动关注策略；普通 Facebook Feed / 作者主页关注在本 change 中仍为 `capability_unsupported`。

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
`scroll_comments→note.scroll_comments`、`profile_open→profile.open`、
`identity_read_current→identity.read_current`、`identity_read_self_profile→identity.read_self_profile`、
`session.end→session.end`。
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
  "startupId": "ads-k1e0ero8:12345:lz7abc",       // 可选：完整 core/browser 启动代号；同一次启动内稳定，完整重启后变化，用于云端限定启动期昵称采集
  "documentGeneration": "1784628123456",          // 可选：当前 performance.timeOrigin；用于同一启动内空态/不可上报态去重，不是帖子身份
  "listKind": "feed",                              // 可选：feed / reels；缺省 feed。页面形态观察，不是 feed/detail 控制流 surface
  "listState": "ready"                             // 可选：ready / empty / present_unreportable；缺省 ready。后两者只允许 cards=[]
}
```

Facebook 首页空态的兼容握手：Edge 必须先确认顶层 Facebook 首页、认证/主区域就绪、无登录/checkpoint/consent/captcha，
且在同一 URL + `performance.timeOrigin` generation、document age ≥8s、无真卡/loading 时，同一紧凑容器的显式空态
语义连续命中 3 次并通过最终复检，才可上报 `cards:[], listKind:'feed', listState:'empty'`。仅 Cloud 将该观察翻译为
`page.scroll{reason:'empty_feed_reels_fallback'}`；普通 0 卡、加载中、未知布局及其它平台不得触发。Reels 卡仍以现有
`page.cards → note.open{surface:'feed'} → note.detail → interaction.like/page.scroll` 链运行，`feed/detail` Surface union 不新增 `reels`。

Facebook 首页有内容但不可可靠解析的兼容握手：Edge 先按既有规则连续滚动最多 8 轮；仍无可信卡片身份时，必须重新
读取同一完整页面样本。仅在 canonical 首页、主壳就绪、无登录/checkpoint/consent/captcha/loading，且可见物理 Feed
卡仍在场时，才可上报 `cards:[], listKind:'feed', listState:'present_unreportable'`（可携带 `startupId` 与
`documentGeneration`）。Cloud 不把它送入内容评估，也不把它冒充空 Feed；仅复用同一
`page.scroll{reason:'empty_feed_reels_fallback'}` 做本场单次 Reels 授权。页面仍在加载、未知或受阻时失败关闭。

**`note.detail`**——上报笔记详情
```jsonc
{
  "noteId": "n123", "title": "周末好去处", "content": "完整正文…",
  "mediaType": "image_text",                      // 可选：image_text / video；缺省按 image_text 兼容老边端
  "author": "小张", "authorId": "u456",       // author / authorId 可选
  "likeCount": 1234, "collectCount": 200,
  "publishedAtText": "3小时前",                 // 可选（change feed-hot-lead-group-comment）：发布相对时刻原始文本
                                               // （刚刚/X小时前/昨天/07-05）。边缘只从正文列底部日期容器抽原始串、不解析、不污染正文；
                                               // 云端以 note.detail.arrived 事件时刻为锚做统一标准化，再派生帖龄/热度并供精选池复用。
                                               // 缺失或不可解析时保留诚实未知语义，绝不以首次发现/记录更新时间代替。
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

`publishedAtText` 的线上协议仍只有这一个 Edge 原始字段；标准时间属于 Cloud 派生事实，不回写协议。Cloud 标准化结果
同时保留原文、事件观测锚、`parsed|unparseable` 状态、可选 epoch 时间与 `minute|hour|day` 精度。日精度只表示来源
自然日，展示不得补造时分；精选池保存这组证据时，本次没有新原文不得擦除旧值，历史行也不得用 `first_seen_at`、
`updated_at` 或 `counts_captured_at` 猜测回填。

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
// search_activity_receipt_v1：每个 activityId 正好一个终态；actuated 只在真实提交键/搜索导航已派发后为 true
{
  "action": "search",
  "ok": true,
  "activityId": "search-7f3d",
  "purpose": "discovery",
  "scope": "global",
  "actuated": true,
  "searchOutcome": "results_ready", // results_ready | no_results | failed_after_submit | not_submitted
  "resultCount": 8                    // 非负整数? 当前已验证可见结果数；no_results 时为 0
}
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

search 回执的计数边界是 `actuated=true`，而不是 `ok=true`：`results_ready`、`no_results` 和 `failed_after_submit` 都说明平台已接收一次搜索尝试，应各记一笔；`not_submitted` 必须是 `actuated=false`，不得扣 search 风控配额或把概念标成已搜。Cloud 按连接内 `activityId` 有界去重，重复/矛盾终态只消费第一次；search 事实进入独立内部事件，不进入点赞、收藏、评论等互动 feed。

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
// action: view | search | like | collect | comment | follow | publish | comment_like | join_group | dm_reply；accountId 可选
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
  "taskId": "task-recovery-01H...", // string? system_recovery 租约；acquired 后才派发（原样例漏了此字段）
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
  },
  "text": "3f7k",                 // string? 验证码答案明文（change captcha-assist-text-answer）。带 text ⇒ points 必须恰好 1 个（聚焦那个框）
  "submit": "enter"              // 'enter'? 键入后提交手势，只 enter（跟随焦点、免疫聚焦滚动，不做「点第 2 个点提交」）
}
```
> 点位是相对 snapshot 图片的归一化坐标 `[0,1]`。edge 必须校验 incident/snapshot/current overlay
> 和坐标边界后，再映射到当前 viewport 并派发真实输入事件；不得用 DOM 状态篡改替代点击。
> `trajectory` 可选：落点权威仍取 `points`，样本只供"怎么移动/何时按下"。edge 回放时**每次 press 前
> 必须补一帧 move 到权威落点**（消 mousedown 无前驱 move 的瞬移伪影）、只裁剪长停顿不等比压缩、叠 dt
> 抖动+亚像素；`clicks` 长度≠点数 / 样本超限 / 坐标越界等一律判无效→回落合成拟人路径（change
> captcha-assist-humanize-click），绝不硬回放、绝不谎称用了轨迹。无新增 MessageType。
> `text` 可选（change captcha-assist-text-answer，扩既有 click 载荷、**不新增 MessageType**）：模糊数字图片类字符识别码
> 的人工答案。**SENSITIVE——明文答案，MUST NOT 落日志/库/incident/回执/URL**（比照 `image.data` 口径）；只活在
> `submitClick` 调用栈、装进本信封即发走，审计只留 actor+时刻+字符数、never what。带 `text` 时 `points` 必须恰好 1 个
> （聚焦那个输入框；聚焦会滚动页面 ⇒ 第 2 个「提交按钮」落点会失效，故只用 Enter 提交）；仅 ASCII 可见字符
> `[0x20,0x7E]`、长度 1..24，畸形=整单拒绝（与 trajectory「丢装饰保留 points」策略刻意相反）。edge 用**真实键盘事件**
> 逐字派发（绝不 `Input.insertText`：零键事件是厂商成熟判据），先强制清空焦点字段、再键入、按顺序 type→read→submit。
> 边缘须先声明构建能力 `captcha_assist_text_v1`，否则云端 fail-closed 拒绝（老客户端会忽略 `text`、只点击=静默假成功）。

**`captcha.assist.click_result`**（edge → cloud）：点击后的 fresh 复检结果
```jsonc
{
  "incidentId": "cap_01H...",
  "snapshotId": "snap_01H...",
  "edgeId": "edge-1",
  "accountId": "acc-01",
  "status": "still_blocked",      // 'cleared'|'still_blocked'|'stale_snapshot'|'not_blocked'|'invalid_target'|'no_target'|'failed'（no_target=点空了，与坐标越界 invalid_target 区分，change captcha-assist-text-answer）
  "reason": "captcha overlay still visible",
  "checkedAt": 1717113608000,
  "snapshot": { /* CaptchaAssistSnapshotPayload，可选，用于刷新仍阻断现场 */ },
  "replayMode": "synthetic",      // 'trajectory'|'synthetic'（change captcha-assist-trajectory-replay）：本次实际用的输入模式，供度量
  "inputMode": "click_type",      // 'click'|'click_type'?（change captcha-assist-text-answer）：'click' 纯点击 / 'click_type' 含键入。云端据此测版本偏斜（下发了 text 却回 click=老边缘忽略了 text）
  "typeReport": {                 // object?（change captcha-assist-text-answer）键入取证，**绝不含答案本身**——运营 MUST 能区分「答案打错了」与「字根本没打进去」
    "focus": "editable",          // 'editable'|'opaque'|'none'：字符派发时的焦点分级（none=没点到输入框）
    "focusTag": "INPUT",          // string? 持焦元素 tag，供事后取证，MUST NOT 据此分支
    "cleared": "verified",        // 'verified'|'attempted'? 键入前强制清空的结果
    "typed": 4,                   // number 实际派发字符数，如实回报（绝不回退到意图长度）
    "verified": "match",          // 'match'|'mismatch'|'unverifiable'? 回读判定（opaque 焦点=unverifiable）
    "submitted": true             // boolean 是否已回车提交
  }
}
```
> `status:'cleared'` 只是协助命令结果；恢复下发仍只由 edge 额外发送的 `risk.captcha_cleared`
> 触发。cloud 不得因为点击命令送达、Feishu 链接打开、协助页按钮点击或告警手动解决而 `resumeEdge`。
> 运行兜底：未配置远程协助、scoped token 过期、edge 离线或截图失败时，飞书告警只发 notify-only 提示、
> 操作员到原机器处理，随后等待 edge fresh probe 上报 `risk.captcha_cleared`，cloud 不能手动伪造清除。
> （change captcha-assist-text-answer：**已移除背后无任何能力的「远程桌面」入口**——`remoteAddr`、飞书卡「远程地址」行、
> console 按钮全删；那从来只是个放第三方工具链接的空位、其真机验收自 2026-06-21 起一直 DEFERRED、从未填过，design D13。）

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
{ "taskId": "task-01H...", "reason": "released" } // released|expired|duplicate|not_owner|cdp_unhealthy|browser_wake_failed|preempted_by_task|window_busy|yield_timeout（window_busy 携 windowRemainingMs 剩余预算）
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
  "approved": true,           // boolean；true=批准，false=取消
  "contentVersion": 0,        // number?；客户端所见版本，云端写信号前复核
  "publishMode": "scheduled",// "immediate" | "scheduled"；批准时可选
  "publishTime": 1784383200000 // number | null；scheduled=北京时间对应 epoch ms，immediate=null
}
```
云端按连接握手的真实 `accountId` 校验稿件归属，并复用飞书/控制台共用的
first-writer-wins 审批信号。动作成功只表示审批决定已受理：`approved=true` 后仍由
发布调度器异步下发，最终结果以 `publish.command.result` / `publish.result` 为准。

- `publishMode` 与 `publishTime` 必须同时出现或同时省略；旧客户端同时省略时保持草稿现有发布计划。
- `approved=false` 不得携带这两个字段。`immediate` 必须配 `publishTime:null`；`scheduled` 必须配有限 epoch ms，且仍由 Cloud 权威校验平台能力与未来 1 小时至 14 天窗口。
- 如果批准时的计划不同于草稿现状，Cloud 先用 `contentVersion` 对同一稿件执行 CAS 更新并取得新版本，再让审批信号绑定该新版本。预检、计划校验或 CAS 冲突任一失败都不得写审批信号。

**`publish.approval_action.result`**（cloud → edge）
```jsonc
{
  "requestId": "publish-89",
  "ok": true,
  "state": "approved",       // approved | rejected
  "alreadyDecided": false,    // 可选；重复动作命中既有决定时为 true
  "reason": "version_stale", // 可选；失败原因
  "currentVersion": 1,        // 可选；版本过期时返回当前版本
  "dispatchState": "pending_dispatch",       // 可选；pending_dispatch | dispatching | blocked
  "dispatchBlockedReason": "edge_offline_waiting"  // 可选；下发阻塞原因
}
```

- `dispatchState` / `dispatchBlockedReason` 是 change `publish-approval-signal-to-database` 新增的**增量可选字段**：与 `state` 是两个轴——`state` 是审批结论，它们是「批完之后走到哪了」，使客户端稿件卡能把「已批准·待下发」与「待审批」区分开，杜绝批准后界面毫无变化的静默停滞。
- `state` 的既有取值 **MUST NOT** 变更：给 `state` 加新取值会让旧客户端落进 else 分支显示为失败；加**可选字段**则被旧客户端安全忽略、行为不变。
- 本消息按信封 id 应答、由客户端 pending 表 resolve，**不进** `edge-client.ts` 的主动命令路由白名单。
- `dispatchBlockedReason` 取值：`edge_offline_waiting` / `browser_slot_waiting` / `breaker_open` / `captcha_paused` / `approval_unreadable`。

**`publish.draft_image_remove`**（edge → cloud）——客户端稿件预览内删除某张配图
```jsonc
{
  "requestId": "publish-89",          // string；仅接受 publish-<数字>
  "contentVersion": 0,                 // number；客户端所见版本（必填，云端落库前复核）
  "imageUrl": "https://.../2.jpg"     // string；待删的那张，MUST 是该稿当前 images 成员
}
```
只表达“删这一张”的意图：**保留子集由云端在库内真态上算出**，绝不采信客户端提交的列表。
云端闸序（任一不过即具名拒因）：`invalid_request` → `account_unavailable` → `not_found` →
`account_mismatch`（草稿须属于握手确立的会话账号）→ `already_decided` → `not_pending` →
`version_stale` → `image_not_found`（只删不注入）→ `last_image`（**最后一张不可删**：无图的
图文帖会被下发段诚实判 failed）。落库复用与控制台编辑同一个乐观 CAS 单写方法
（事务内 FOR UPDATE + `content_version` CAS），成功即 `content_version + 1`、原飞书审核卡失效。

**`publish.draft_image_remove.result`**（cloud → edge）
```jsonc
{
  "requestId": "publish-89",
  "ok": true,
  "images": ["https://.../1.jpg", "https://.../3.jpg"], // 成功：写后回读真态（保序）
  "contentVersion": 1,                                    // 成功：自增后的版本
  "reason": "last_image",                                 // 可选；失败原因
  "currentVersion": 2                                     // 可选；版本过期时返回当前版本
}
```
`ok:true` 仅表示“该配图已从待审稿件移除”，**不代表已发布**。客户端 MUST 以本应答回带的真态
刷新所持稿件（云端另会 best-effort 重推一帧 `ui.snapshot` 预览，但可能落空，不可作为唯一刷新手段）。

**`publish.result`**（edge → cloud）
```jsonc
{ "ok": true, "postId": "p789", "error": null } // postId / error 二选一
```

**定时发布原子指令语义（小红书）**

- 编排顺序固定为「标题/正文/图片/话题及其它发布选项 → `set_schedule` → `submit_publish` → `capture_scheduled`」。`set_schedule` 必须验证开关已开启、北京时间值精确一致、提交按钮已切为“定时发布”；任一证据缺失即失败关闭，不得回退为立即发布。
- 小红书定时时间必须位于当前时刻后 1 小时至 14 天（含边界）。平台不支持定时发布时，云端在下发前拒绝。
- `capture_scheduled` 成功只表示平台定时列表中存在唯一匹配稿；`value` 可携平台内部定时句柄，但该值不得写入 `platform_post_id`、不得拼接公开 URL，也不要求当场 `capture_postId`。
- 云端将记录转为 `scheduled`，目标时间前不消耗发布次数。目标时间后由有界 `reconcile_scheduled` 对账；只有取得真实公开 `postId + postUrl` 并以 CAS 将 `scheduled → published` 后才记一次发布。未公开时退避重试，次数耗尽转 `needs_review`，不得伪造链接或自动重投。

### 3.12 通用

**`error`**（双向）
```jsonc
{
  "code": "bad_envelope",  // string  错误码：bad_envelope | unsupported_type | handler_error | ...
  "message": "无法解析的协议帧" // string  人读说明
}
```

**`ping` / `pong`**：payload 为空对象 `{}`；服务端收到 `ping` 回 `pong`（回填同一 `id`）。

### 3.13 视频号入站互动管理

本节只给出 wire 语义；字段、required、枚举、上限与条件约束的唯一机器合同是
`docs/contracts/wechat-channels-interaction/v1/schemas/ws-v2.schema.json`，对应正常和降级样例在同目录 `fixtures/ws/`。所有时间均为 epoch milliseconds，payload 不重复 envelope 的 `type`。

**`interaction.auth.status`**（edge → cloud）

```jsonc
{
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "status": "active", "browserState": "closed",
  "capabilities": {
    "commentsRead": true, "commentsReply": false,
    "dmRead": true, "dmSendText": false, "dmSendImage": false
  },
  "runtimeControlsVersion": 7,
  "identity": { "externalId": "finder-demo-001", "displayName": "示例视频号", "identityHash": "sha256:1111111111111111111111111111111111111111111111111111111111111111" },
  "checkedAt": 1784044801000, "reasonCode": null
}
```

`active + closed` 是合法组合。已有加密会话通过身份校验和已启用读取探针时，Edge 必须直接进入该 API-only 状态，不得为例行启动打开浏览器。capability 表示该账号此刻有效可用，不是 build 可能支持；`runtimeControlsVersion` 是 Edge 已接受的账号开关版本，未收到/未应用时为 `null`。身份错配、挑战、schema 漂移、scope/version 不匹配或开关关闭时必须降级且 fail closed。凭证、二维码和调试地址不得进入 payload。

若加密会话不能复用、Edge 确需重新授权，且 AdsPower `browser-profile/start` 返回已核实的 profile 占用签名，Edge 必须结束 `authenticating` 并上报 `status=reauth_required`、`browserState=unavailable`、`reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE`。Cloud 按普通文本 reason code 持久化并原样投影；历史读取仍可见，所有写能力保持关闭。原始占用者标识只能以掩码写入本机日志，不得进入 WS、Cloud 存储或客户 API。用户释放占用后可显式触发 `interaction.auth.reopen`；命令受理不代表恢复成功，只有后续 `active` 快照才算恢复。机器样例见 `fixtures/ws/auth-status-profile-in-use.json`。

**`interaction.runtime.controls`**（cloud → edge）

payload 与 `welcome.interactionRuntime` 相同。Cloud 只定向到 `accountId` 匹配且协商 `interaction_runtime_controls_v1` 的在线 Edge；保存成功但无在线目标时内部 API 返回 `edgeDelivery=deferred`，不得声称 Edge 已应用。Edge 断线先清快照，重连只接受 scope 完全匹配且版本不倒退的 welcome/在线更新，并用后续 `interaction.auth.status.runtimeControlsVersion` 回报已应用证据。

**`interaction.sync.batch` / `interaction.sync.ack`**

```jsonc
// edge -> cloud
{
  "batchId": "batch-comment-001", "requestId": null,
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "channel": "comment", "scopeExternalId": "video-demo-001",
  "cursorBefore": null, "cursorAfter": "opaque-platform-cursor", "hasMore": false,
  "threads": [], "messages": [], "observedAt": 1784044802000
}

// cloud -> edge，envelope id 原样回填 batch 的 id
{
  "batchId": "batch-comment-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "channel": "comment", "scopeExternalId": "video-demo-001",
  "status": "accepted", "cursorAfter": "opaque-platform-cursor",
  "persisted": { "threads": 1, "messages": 1 },
  "errorCode": null, "receivedAt": 1784044802100
}
```

一个 batch 只能含一个 account/env/channel/scope。Cloud 在同一事务完成 scope 校验、batch/thread/message 幂等写和 cursor 推进后才回 `accepted`；已落库重放回 `duplicate`。`rejected`、断连、部分失败或 ack cursor 不一致都不能推进 Edge checkpoint。

**`interaction.sync.request`**（cloud → edge）

```jsonc
{
  "requestId": "sync-request-comment-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "channel": "comment", "scopeExternalId": "video-demo-001",
  "reason": "user_requested", "requestedAt": 1784044838000
}
```

后续 batch 以 payload `requestId` 关联该请求；不使用 envelope id 作为跨多个 batch 的唯一关联键。

**`interaction.reply.send` / `interaction.reply.result`**

```jsonc
// cloud -> edge
{
  "jobId": "job_comment_100", "attemptId": "attempt_comment_100_1",
  "idempotencyKey": "e0e055e5abfced94f0e808eb5745a36b5f9f7aecc75c2d0377f5b2f692ae2ae9",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "channel": "comment",
  "target": {
    "threadExternalId": "comment_msg_100", "inboundMessageExternalId": "comment_msg_100",
    "parentExternalId": null
  },
  "content": { "type": "text", "text": "谢谢你的喜欢，欢迎继续交流。" },
  "expiresAt": 1784044900000
}

// edge -> cloud，envelope id 原样回填 send 的 id
{
  "jobId": "job_comment_100", "attemptId": "attempt_comment_100_1",
  "idempotencyKey": "e0e055e5abfced94f0e808eb5745a36b5f9f7aecc75c2d0377f5b2f692ae2ae9",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "channel": "comment", "status": "confirmed", "externalMessageId": "reply-comment-100",
  "errorCategory": null, "errorCode": null, "verification": "comment_lookup",
  "retryAfterMs": null, "finishedAt": 1784044824000
}
```

`confirmed` 只允许来自平台 ack 或回查证据；超时、断连、解析失败或落地无法确认必须回 `ambiguous`，不能回 `failed` 触发盲重试。v1 只允许 text，`dmSendImage` 恒 false。

**`interaction.reply.result.ack` / `interaction.reply.reconcile*`**

```jsonc
// cloud -> edge，envelope id 原样回填 result 的 id
{
  "jobId": "job_comment_100", "attemptId": "attempt_comment_100_1",
  "idempotencyKey": "e0e055e5abfced94f0e808eb5745a36b5f9f7aecc75c2d0377f5b2f692ae2ae9",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "status": "accepted", "errorCode": null, "receivedAt": 1784044824100
}

// cloud -> edge，启动或 Edge 重连时仅核验已有 execution
{
  "reconcileId": "reconcile-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "attempts": [{
    "cloudStatus": "dispatched",
    "command": { /* 原 jobId/attemptId/idempotencyKey/scope/target/content；同 ReplySendPayload */ }
  }],
  "requestedAt": 1784044825000
}

// edge -> cloud，envelope id 原样回填 reconcile 的 id
{
  "reconcileId": "reconcile-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "attempts": [{
    "jobId": "job_comment_100", "attemptId": "attempt_comment_100_1",
    "idempotencyKey": "e0e055e5abfced94f0e808eb5745a36b5f9f7aecc75c2d0377f5b2f692ae2ae9",
    "state": "result_replayed", "observedAt": 1784044825050
  }],
  "finishedAt": 1784044825100
}
```

Edge 必须在发送 result 前写入 durable outbox，只在 ack 为 `accepted|duplicate` 且 job/attempt/idempotency/env/account/platform 全部一致时清除。断线、Cloud 崩溃、超时、`rejected` 或错绑 ack 均保留并在重连后补发。reconcile 只能读取 durable execution/result 或做平台历史核验：本地 `not_found` 绝不能转成新的平台写。Cloud 对 `created + not_found` 可明确失败；对 `dispatched|ambiguous + not_found` 必须保持 `ambiguous`；`result_replayed` 仍由正常 durable result 推进终态。

**`interaction.offboard.command` / `interaction.offboard.result` / `interaction.offboard.ack`**

```jsonc
// cloud -> edge
{
  "offboardId": "offboard-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "reason": "environment_unbind", "requestedAt": 1784044830000, "expiresAt": 1786550430000
}

// edge -> cloud，先 durable 落盘
{
  "offboardId": "offboard-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "status": "cleared", "errorCode": null, "finishedAt": 1784044831000
}

// cloud -> edge，envelope id 原样回填 result 的 id
{
  "offboardId": "offboard-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "status": "accepted", "errorCode": null, "receivedAt": 1784044831100
}
```

执行顺序固定为：Cloud 事务撤权/停同步写并创建 durable offboard → 为新版客户端签发短期单用途 cleanup grant → 受限 browserless core durable claim → connector stop + drain → 清 scope-bound encrypted session → 关 sidecar → durable result → Cloud exact ack → Cloud tombstone → `requestedAt + 30 days` 内 purge。`failed` 必须保留任务并重试；Edge 离线时 Cloud 只保留 pending cleanup，不得跳过凭证清理。普通 pause/close/standby/logout 不是 offboard，不得删除密文。Cloud/Edge 审计与日志都不得记录消息正文、模板最终文本或凭证。

cleanup grant 由 customer-auth `DELETE /environments/:envKey` 在客户端同时提交稳定 `edgeId` 时签发，绑定 `offboardId/envKey/accountId/edgeId/userId`，默认 10 分钟有效。Electron main 可持久化 bearer，但不得投影给 renderer；恢复时经 `POST /offboarding/:offboardId/cleanup-bootstrap` 原子核验并作废。Cloud 只保存 `jti` 哈希、有效期、使用时间和审计事件。受限 core 只声明 `interaction_inbox_v1 + interaction_offboarding_v1 + browser_absent_v1`，只接受绑定的 `interaction.offboard.command/ack`。过期、复用或任一 scope 不匹配必须转人工，绝不降级到普通 `queueStartEnv` 或打开浏览器。

**`interaction.auth.reopen`**（cloud → edge）

```jsonc
{
  "requestId": "auth-reopen-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "reason": "user_requested", "requestedAt": 1784044840000
}
```

Edge 必须只打开该 env/account 所属 sidecar，并用后续 `interaction.auth.status` 报 `authenticating`、`active` 或挑战真态；不得把“已打开浏览器”当登录成功。

**`interaction.browser.control`**（cloud → edge）

```jsonc
{
  "requestId": "browser-control-001",
  "envKey": "env_wc_demo", "accountId": "acct_wc_demo", "platform": "wechat_channels",
  "action": "open", "requestedAt": 1784044845000
}
```

该控制只服务于已经 `active` 的视频号环境：`open` 启动或保留所属 AdsPower sidecar，并尽力把页面带到前台；`close` 只关闭 sidecar、回到加密会话驱动的 API-only 后台，不删除会话，也不触发客户登出/offboard。Edge 必须校验 env/account/platform 精确匹配，并串行执行重复请求。HTTP/WS 投递成功只表示 accepted；客户端只有读回 `interaction.auth.status.browserState=open|closed` 后才能显示“已打开/已转入后台”。旧 Edge 或未协商 `interaction_browser_control_v1` 时 Cloud 必须 fail closed，不得假装已执行。

## 4. 典型时序

### 4.1 浏览会话闭环（v2 主路径：结构化上报 + 角色驱动）

```
edge                                          cloud（RoleDispatcher + 多角色 + EventBus）
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
客户端稿件审批页的“批准并发布 / 批准并定时发布 / 取消”走 `publish.approval_action`，
与飞书按钮共享同一审批信号和 first-writer-wins 规则。多条待审批内容先按灵感池式卡片列表
展示，单条直接进入详情；“查看稿件 ↗”打开客户端主内容区，不再跳转飞书。

### 4.4 视频号评论确认与私信待核验

评论完整合同走读见 `docs/contracts/wechat-channels-interaction/v1/fixtures/walkthroughs/comment-confirmed-flow.json`：只有双方协商能力、Cloud 整批落库并 ack、人工批准、Edge 回 `confirmed` 且 Cloud durable 接收结果后，job 才能成为 `sent`；Edge 收到 exact result ack 后才清 outbox。

私信降级走读见 `docs/contracts/wechat-channels-interaction/v1/fixtures/walkthroughs/dm-ambiguous-flow.json`：Edge 派发后无法取得平台证据时必须回 `ambiguous`，Cloud 保持阻断且不自动重投，客户界面显示“待核验”。两条 fixture 都只证明合同，不代表真实账号执行过写操作。

### 4.5 视频号开发测试数据重置

`interaction.sync.request.reason` 在既有 `user_requested | resume | scheduled | recovery` 基础上增加 `test_reset`。该原因只允许 Cloud 在显式 `dev` 测试开关开启、当前账号写入暂停、所选渠道没有任何发送记录，且唯一在线 Edge 同时协商 `interaction_inbox_v1` 与 `interaction_test_data_reset_v1` 后下发。

收到 `test_reset` 后，Edge 必须在该渠道既有同步锁内先清除本地 checkpoint 与 thread-source 缓存，再从空 cursor 执行正常只读同步。Cloud 必须先清除同账号、同环境、同渠道的 inbox 副本、sync batch 与 cursor，否则稳定 batch id 会被当成 duplicate。该流程只重置 aidcp 的测试读取状态，不删除微信平台评论/私信，不触发回复发送，也不复用会清授权与配置的 offboarding。

## 5. 错误与兼容性

- **未知 type**：服务端回 `error`（code=`unsupported_type`）。
- **handler 抛错**：被兜成 `error`（code=`handler_error`），不崩连接。
- **坏帧**：`parseEnvelope` 返回 null → `error`（code=`bad_envelope`）。
- **版本演进**：`v` 用于灰度；新增字段应保持向后兼容（旧端忽略未知字段）。v2 对 v1
  的全部消息保持兼容，新增消息类型旧端可安全忽略。
- **视频号互动能力协商**：Edge 与 Cloud 都确认 `interaction_inbox_v1` 前不得发送基础 interaction 消息；恢复/offboard/账号开关/浏览器显隐类型还分别要求 `interaction_reply_recovery_v1`、`interaction_offboarding_v1`、`interaction_runtime_controls_v1`、`interaction_browser_control_v1`。旧 Edge 不收账号开关或浏览器控制推送；新 Edge 遇旧 Cloud 或 welcome 缺快照时保持全部互动能力关闭。offboard capability 缺失时 Cloud 已撤权并停写，但任务必须保持 pending，不能提前 tombstone。未知 type 不得导致连接崩溃或重试风暴。
