## Context

文本出口 `QwenClient.chat()` 当前创建 `AbortController`，到 `timeoutMs` 只调用 `controller.abort()`，随后仍直接等待 `fetch()` / `res.json()`。2026-07-20 17:42 的 dev 事故里，一次 `browse:comment_composer` 调用至少悬空 19 分钟：180 秒计时器未使 Promise reject，角色 catch、统一 `[llm]` finally 日志与评论终局都不可达。相同火山模型在事故前 6 分钟和事后探针均亚秒成功；当前 Node 20.20.2 / Undici 6.24.1 对常规无响应头、半截响应体和 TLS 握手悬空也能正常 Abort，因此无法稳定复现或断言具体网络阶段。

现有 `bound-comment-subline-timeouts` 已为可选语料召回加 3 秒边界，并为整条评论支线加 15 分钟最后保险；它能防永久死锁，却不能让单次模型调用在配置 deadline 到达时自身收敛，而且 15 分钟对自动浏览是过长的可见停顿。

约束：

- 全局 180 秒默认承载合法慢 thinking 模型，本 change 不下调它。
- 超时只能诚实失败/跳过/回退，绝不能生成模板评论、自动授权或报告平台成功。
- 日志不得包含 prompt、响应正文或密钥。
- Cloud-only；不新增协议、数据库迁移或第三方运行时依赖。

## Goals / Non-Goals

**Goals:**

- 无论底层 fetch 是否响应 Abort，任一文本 LLM 调用都在其 `timeoutMs` 到达时向调用方 reject。
- 终局日志能回答调用是否开始、最后到达请求/响应头/响应体哪个阶段，以及厂商请求 ID（若取得）。
- 浏览评论评估、撰写、去 AI 味改写默认使用 30 秒 per-call deadline；合法 env 可覆盖。
- 评论支线最后保险默认从 15 分钟收紧到 5 分钟，仍保持单次结算与迟到事件 fail-closed。
- 覆盖“fetch 忽略 signal 且永不 settle”的确定性回归。

**Non-Goals:**

- 不宣称定位出火山或 Undici 的确定根因，不更换 HTTP 客户端。
- 不给超时模型调用自动重试；评论撰写的既有内容/语言补写只处理已收到的无效输出。
- 不修改角色 provider/model/temperature/thinking 配置。
- 不改变发布链与其它角色的 per-call deadline；它们继续使用全局默认或既有显式覆盖。

## Decisions

### D1：硬 deadline 与 Abort 双轨，调用方结算不依赖取消成功

`QwenClient.chat()` 把真实 HTTP/解析工作封装成一个 request Promise，并与独立 deadline Promise 做 `Promise.race`。deadline 到达时先以稳定 `LlmTimeoutError` reject 竞速，再调用 `controller.abort()` best-effort 释放 socket。request Promise 始终被竞速分支挂上 resolve/reject 消费器，因此迟到 rejection 不形成 unhandled rejection；即使底层永不 settle，外层调用、`finally` 和角色终局也已按时继续。

备选“只用 `AbortSignal.timeout()`”仍把结算押在 fetch 对 signal 的实现上，不能覆盖本次事故。备选“仅在 CommentComposer 外包一层 race”会让其它文本角色继续暴露同一出口缺陷，也无法在统一出口记录真实阶段。

### D2：一个可变阶段快照贯穿请求，开始与终局分开记录

每次调用在发 HTTP 前触发只含 account/role/provider/model/timeout 的 `onStart` 元数据；内部阶段依次为 `request_started`、`headers_received`、`body_parsed`。拿到响应头后尝试读取常见厂商请求 ID 头（含 `x-tt-logid` / `x-request-id`），不读取或日志化正文。统一 `onCall` 终局追加 `stage`、`requestId` 与 `timedOut`，原有字段顺序和 token 记账保持。

不为每次 headers/body 另打一行常驻日志，避免将高频模型日志放大三倍；阶段在终局/超时行上呈现，开始行证明调用已真正越过本地同步准备。

### D3：评论角色经 BaseRole 显式传短 deadline

`RoleOptions` 增加可选 `llmTimeoutMs`，`BaseRole.decide()` 仅在配置时把它作为 per-call `timeoutMs` 传给共享客户端。`RoleDispatcher` 只给 `CommentAppraiser`、`CommentComposer`、`CommentDeAiFlavor` 注入同一个评论专用值，生产默认 30,000ms，并由 `AIDCP_COMMENT_LLM_TIMEOUT_MS` 正数覆盖。

评论撰写遇到 LLM transport/timeout error 后立即 `llm_error` 跳过，不为同一网络错误再发第二次；第二次补写仍只用于模型已返回但内容为空、过长或发言语言不符。去 AI 味模型失败继续回退原草稿，保持既有诚实语义。

### D4：总保险默认 5 分钟，不替代局部 deadline

`DEFAULT_COMMENT_SUBLINE_TIMEOUT_MS` 从 15 分钟调为 5 分钟；合法 `AIDCP_COMMENT_SUBLINE_TIMEOUT_MS` 仍优先。5 分钟覆盖评论评估、最多两次有效输出补写、最多两次去 AI 味改写与 90 秒人审的保守上界；正常路径依靠 30 秒局部失败更早结算，总保险只兜未知悬空点。

### D5：测试注入永不 settle 的 fetch，不依赖真实网络

QwenClient 回归桩故意忽略 `signal` 并返回永不 settle Promise，断言在短 deadline 内抛 `LlmTimeoutError`、`onCall` 恰好一次且 `ok=false/timedOut=true/stage=request_started`。另覆盖 headers 后 body 永不 settle 的阶段、迟到 resolve/reject 不产生第二终局，以及 BaseRole/dispatcher 把 30 秒覆盖传给三个评论角色。

## Risks / Trade-offs

- [底层 fetch 永不 settle 时仍可能暂存网络资源] → deadline 同时 Abort best-effort；外层已释放业务锁。若后续出现频繁复现，再评估独立 Undici dispatcher + destroy，而不在本 change 引入连接池重构。
- [硬 deadline 与真实响应同毫秒竞态] → 以事件循环先结算者为准；统一 `finally` 只执行一次，迟到分支无业务副作用。
- [30 秒误杀偶发合法慢评论] → 评论模型现场常见耗时低于 2 秒，评论是低优先级可跳过互动；全局 thinking 角色仍保留 180 秒。
- [开始日志增加量] → 每次只增加一行元数据，绝不含正文；成功终局仍沿用原 `[llm]` 行。
- [总保险收紧使迟到审批作废] → 授权不等于已发；已有墓碑机制丢弃迟到 approved，安全优先。

## Migration Plan

1. 在独立 Cloud worktree 实现硬 deadline、阶段元数据、评论短 deadline 与 5 分钟总保险。
2. 跑 Qwen/评论/dispatcher 聚焦测试，再跑 acceptance、全量测试与 typecheck。
3. OpenSpec 严格校验，提交并 fast-forward 集成到 Cloud `master`；从干净 canonical checkout 部署 dev。
4. 在 dev 用同模型 8 秒探针验证成功路径，并用本地永不响应端点验证硬结算日志；不触发真实平台评论。
5. 回滚只需恢复前一 Cloud master 并重启 `aidcp-cloud.service`；无数据迁移。

## Open Questions

无。
