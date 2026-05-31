# 边-云 WebSocket 协议

边缘端（aidcp-edge）与云端（aidcp-cloud）之间的唯一通信契约。传输层为
**WebSocket**；每帧为一个 JSON **信封（Envelope）**。本文档与
`aidcp-cloud/src/comm/protocol.ts` 一一对应，是两侧实现的权威来源。

- 当前协议版本：`PROTOCOL_VERSION = 1`
- 默认服务端监听：`0.0.0.0:8787`（可由 `AIDCP_PORT` 覆盖）
- 编码：UTF-8 JSON 文本帧

## 1. 信封（Envelope）

所有消息共用同一信封结构：

```jsonc
{
  "v": 1,              // number  协议版本（PROTOCOL_VERSION）
  "type": "plan.request", // string  消息类型（见下表）
  "id": "req-42",      // string  请求/响应关联 id（响应回填请求的 id）
  "ts": 1717113600000, // number  发送方毫秒时间戳
  "payload": { /* ... */ } // object  随 type 而定，见各消息定义
}
```

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `v` | number | 协议版本，便于演进。当前必须为 `1`。 |
| `type` | string | 消息类型（`MessageType`）。 |
| `id` | string | 关联 id。请求方生成，响应方原样回填，用于请求/响应配对。 |
| `ts` | number | 发送时间戳（毫秒）。由发送方填充（不在库内部读时钟，便于测试）。 |
| `payload` | object | 消息体。结构由 `type` 决定。 |

**校验规则**（`isEnvelope` / `parseEnvelope`）：`v` 为 number、`type` 为 string、
`id` 为 string、`ts` 为 number，且存在 `payload` 字段。任一不满足视为非法帧，
服务端回 `error`（code=`bad_envelope`）。

## 2. 消息类型一览（MessageType）

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

**`plan.request`**（edge → cloud）
```jsonc
{
  "goal": "给当前这条笔记点赞并关注作者", // string  高层自然语言目标
  "context": { "url": "https://...", "app": "xhs" } // object? 可选上下文
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

### 3.6 通用

**`error`**（双向）
```jsonc
{
  "code": "bad_envelope",  // string  错误码：bad_envelope | unsupported_type | handler_error | ...
  "message": "无法解析的协议帧" // string  人读说明
}
```

**`ping` / `pong`**：payload 为空对象 `{}`；服务端收到 `ping` 回 `pong`（回填同一 `id`）。

## 4. 典型时序

```
edge                                cloud
 │  hello {edgeId}                    │
 │ ─────────────────────────────────►│  分配 session
 │  welcome {sessionId}               │
 │ ◄─────────────────────────────────│
 │                                    │
 │  plan.request {goal}               │
 │ ─────────────────────────────────►│  Planner.plan()
 │  plan.response {steps[]}           │
 │ ◄─────────────────────────────────│
 │                                    │
 │  （逐步执行；缓存命中则本地完成）     │
 │  anchor.get {actionId}             │
 │ ─────────────────────────────────►│  PgAnchorCache.get()
 │  anchor.get.result {anchor|null}   │
 │ ◄─────────────────────────────────│
 │                                    │
 │  （缺口）select.request {goal, els} │
 │ ─────────────────────────────────►│  Qwen 选编号 + 范围校验
 │  select.response {index|null}      │
 │ ◄─────────────────────────────────│
 │                                    │
 │  执行 + 后置校验后：                 │
 │  anchor.report {source,validated}  │  （无回包）
 │ ─────────────────────────────────►│  反污染晋升
 │  action.result {outcome}           │  （无回包，观测）
 │ ─────────────────────────────────►│
```

## 5. 错误与兼容性

- **未知 type**：服务端回 `error`（code=`unsupported_type`）。
- **handler 抛错**：被兜成 `error`（code=`handler_error`），不崩连接。
- **坏帧**：`parseEnvelope` 返回 null → `error`（code=`bad_envelope`）。
- **版本演进**：`v` 用于灰度；新增字段应保持向后兼容（旧端忽略未知字段）。
