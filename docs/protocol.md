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
>    对应云端从单体 Planner 重构为**事件驱动多 Agent**（`RoleDispatcher` + 15 角色）后的实时控制面；
> 3. **风控预算与发布审批**（`session.budget`/`risk.canDo`/`publish.*`）——把"做多少、能不能做、发布前要不要人审"纳入协议。
>
> v2 共 **55 个消息类型**，下表按职能分组列全。

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
| `hello` | edge → cloud | `welcome` | 边缘上线握手，声明能力 |
| `welcome` | cloud → edge | — | 握手确认，下发 sessionId |
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

### 2.3 角色驱动指令（v2 新增，cloud → edge，`RoleDispatcher` 经 `command-bridge` 下发）

| type | 方向 | 用途 |
| --- | --- | --- |
| `page.scroll` | cloud → edge | 页面滚动（`reason`: feed_scroll / search_scroll） |
| `interaction.like` | cloud → edge | 点赞指定笔记 |
| `interaction.collect` | cloud → edge | 收藏指定笔记 |
| `interaction.follow` | cloud → edge | 关注作者 |
| `interaction.comment` | cloud → edge | 在当前笔记发评论（`text` 正文；云端已撰写/去AI味/人审通过） |
| `navigation.back` | cloud → edge | 返回上一页（feed / search） |
| `note.browse_images` | cloud → edge | 浏览笔记图片（`count` 张；DeepReader 决策下发） |
| `note.scroll_comments` | cloud → edge | 滚动评论区（CommentReviewer 决策下发） |
| `profile.open` | cloud → edge | 进入作者主页（专用指令，取代 `open_note{type:'profile'}`） |
| `notification.open` | cloud → edge | 导航到通知首页（仅导航；落地后边缘上报 `notification.home`） |
| `notification.browse_comments` | cloud → edge | 进「评论和@」+ 滚动加载 + 抽取（→ `notification.items`） |
| `notification.browse_likes` | cloud → edge | 进「赞和收藏」（v1 看一眼清未读，不抽取） |
| `notification.browse_follows` | cloud → edge | 进「新增关注」（v1 看一眼清未读，不抽取） |
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
| `notification.items` | edge → cloud | 上报本次巡视抽取的评论/@ 项（用户名/内容/笔记标题/itemKey；是否通知由云端判） |

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

### 2.6 发布编排（v2 新增，Publish Agent 驱动）

| type | 方向 | 用途 |
| --- | --- | --- |
| `publish.request` | cloud → edge | 请求在浏览器中发布一篇帖子 |
| `publish.approval_request` | edge → cloud | 请求云端发送发布审批卡片（飞书） |
| `publish.result` | edge → cloud | 发布结果回传（ok / postId / error；v1 整页路径） |
| `publish.command` | cloud → edge | 下发一条参数化发布原子指令（A 阶段1 指令驱动；`recordId+seq` 关联键，`kind` ∈ E1-E10） |
| `publish.command.result` | edge → cloud | 单条发布指令执行结果回传（按 `recordId+seq` 关联；`ok/value/error/details`，红线不静默假成功） |

## 3. 各消息 payload 定义

### 3.1 握手

**`hello`**（edge → cloud）
```jsonc
{
  "edgeId": "edge-01",        // string  边缘节点标识
  "app": "xhs",               // string? 业务/站点标识
  "capabilities": ["click", "input", "scroll"] // string[]? 能力声明
}
```

**`welcome`**（cloud → edge）
```jsonc
{
  "sessionId": "sess-1",      // string  云端分配的会话 id
  "serverVersion": "0.1.0"    // string  服务端版本
}
```

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
```

**`note.close`**（cloud → edge）：`{ "reason": "..." }`（可选）

**`search.execute`**（cloud → edge）
```jsonc
{
  "keyword": "露营装备",   // string  搜索关键词
  "source": "extract_from_liked", // ? extract_from_liked | random_from_interests | new_concept | manager
  "maxResults": 10        // number? 本次搜索最多浏览的结果数
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

由云端 `RoleDispatcher` 产出语义动作 `EdgeCommand`，经 `command-bridge`
（`edgeCommandToEnvelope`）翻译为以下协议消息下发：

```jsonc
// page.scroll
{ "reason": "feed_scroll" }            // feed_scroll | search_scroll
// interaction.like
{ "noteId": "n123", "reason": "高质量内容", "thinkMs": 900 }
// interaction.collect
{ "noteId": "n123", "reason": "值得收藏", "thinkMs": 900 }
// interaction.follow
{ "authorId": "u456", "reason": "持续优质", "thinkMs": 900 } // authorId 可选
// interaction.comment
{ "noteId": "n123", "text": "今天的分享很有启发", "thinkMs": 900 } // text 必填
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
{ "authorId": "u456", "reason": "作者值得关注评估", "thinkMs": 800 }
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
`like→interaction.like`、`collect→interaction.collect`、`follow→interaction.follow`、`comment→interaction.comment`、
`search→search.execute`、`back→navigation.back`、`browse_images→note.browse_images`、
`scroll_comments→note.scroll_comments`、`profile_open→profile.open`、`session.end→session.end`。

### 3.8 结构化上报（edge → cloud）

**`page.cards`**——上报当前可见卡片列表
```jsonc
{
  "cards": [
    {
      "index": 0, "title": "周末好去处", "author": "小张",
      "likeCount": 1234, "collectCount": 200,
      "coverDesc": "封面描述", "noteId": "n123"   // coverDesc / author / noteId 可选
    }
  ]
}
```

**`note.detail`**——上报笔记详情
```jsonc
{
  "noteId": "n123", "title": "周末好去处", "content": "完整正文…",
  "author": "小张", "authorId": "u456",       // author / authorId 可选
  "likeCount": 1234, "collectCount": 200
}
```

**`profile.detail`**——上报作者主页数据
```jsonc
{ "authorId": "u456", "postsCount": 87, "followersCount": 12000, "extracted": true }
// extracted:false → 进了主页但未抽到数字；云端 FollowAgent 据此保守 skip，不当作真 0 粉丝
```

**`action.completed`**——确认某 action 执行完成
```jsonc
{ "action": "like", "ok": true, "reason": "..." } // reason 可选
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

### 3.10 发布编排

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

**`publish.result`**（edge → cloud）
```jsonc
{ "ok": true, "postId": "p789", "error": null } // postId / error 二选一
```

### 3.11 通用

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
edge                                          cloud（RoleDispatcher + 15 角色 + EventBus）
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
 │  （缺口）select.request {goal,els}  │  Qwen 选编号 + 范围校验
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

## 5. 错误与兼容性

- **未知 type**：服务端回 `error`（code=`unsupported_type`）。
- **handler 抛错**：被兜成 `error`（code=`handler_error`），不崩连接。
- **坏帧**：`parseEnvelope` 返回 null → `error`（code=`bad_envelope`）。
- **版本演进**：`v` 用于灰度；新增字段应保持向后兼容（旧端忽略未知字段）。v2 对 v1
  的全部消息保持兼容，新增消息类型旧端可安全忽略。
