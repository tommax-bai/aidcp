## Context

账号人设实际存放在 Cloud PostgreSQL `persona_config`，生成器、soul 校验、热加载和首次绑定引导也都在 Cloud。当前 Electron 却把单账号 `persona.generate` / `persona.persist` 写进目标环境 core 的 stdin，再由运行中 core 经 WebSocket 发给 Cloud；渲染层同时用 `auth==='logged in' && cloud==='connected'` 作为生成 gate，所以环境停止时连已有人设都无法读取。

客户鉴权域已经提供独立 JWT、每请求停用复核、客户环境归属以及 `envKey → accountId` 的持久绑定解析。慢启动、风险状态和客户工作区已证明这种环境级 HTTP 路径不依赖边缘在线，并能在归属未知、绑定未知、跨客户争用和底层不可用之间诚实区分。

本变更跨 `aidcp-cloud` 与 `aidcp-edge`，但不需要改协议 v2、数据库结构或 Console。用户界面仍是现有人设浮层和两步草稿确认，只把“查看当前人设”提升为默认状态并移除偶然的引擎在线前置。

## Goals / Non-Goals

**Goals:**

- 已建立持久账号绑定的环境在 core/浏览器停止时仍可查看当前人设、生成新草稿并确认更新。
- 客户端只提交 `envKey`；账号身份、平台、归属和人设真态由 Cloud 解析。
- HTTP 与旧 WebSocket 入口共用生成幂等、输入校验、落库校验、热加载与首次绑定引导。
- 已设置账号默认展示精简摘要；未设置账号直接进入向导；所有网络写先显示在途、真回执后才显示成功。
- 保留旧 Edge 的 WebSocket 兼容，Cloud-first 上线不破坏现有客户端。

**Non-Goals:**

- 不让从未握手的环境从本地环境名、导入账号资料、Cookie 或缓存推断账号。
- 不提供解绑、原始 YAML 直接编辑、批量覆盖、账号选择器或跨客户人设管理。
- 不改变人设 schema、生成模型/prompt、首次作品业务语义或 Console `/persona` 页。
- 不构建或发布 Edge 安装包，不部署到 `ol`。

## Decisions

### D1：新版界面统一走 customer-auth HTTP，运行中也不切回 WebSocket

新增三个具名环境级操作：读取当前人设、生成草稿、确认保存。Electron main 只接受本地 `envId` 与受控字段，解析目标 AdsPower `profileId` 作为 `envKey`，再携客户令牌调用固定路径；renderer 不获得令牌、URL、通用 fetch 或 `accountId`。

备选“停止时 HTTP、运行时 WS”会形成两套状态、超时和失败映射，环境在生成中启停还会切路，因此否决。旧 `persona.generate` / `persona.persist` 协议继续由 Cloud 处理以兼容已安装客户端，但新版 UI 始终使用 HTTP。

### D2：Cloud 以共享应用服务收口人设业务规则

新增账号人设应用服务，承接：读取真实详情与结构化摘要、平台/输入校验、按 `(accountId,idempotencyKey)` 的生成去重、调用 `PersonaGenerator`、调用既有 `PersonaFacade.setPersona`、以及首次绑定引导。WebSocket handler 与 customer-auth 路由都调用同一实例。

这样 HTTP 不会复制 handler 私有的幂等 Map，也不会绕过既有单写通道。失败生成从幂等缓存逐出以允许重试，成功结果保留；只有保存成功才改变绑定态。

### D3：环境级 HTTP 契约严格且不泄露账号键

- `GET /environments/:envKey/persona`：返回 `configured | missing`、当前 `soulYaml`（仅 configured）、Cloud 解析出的精简摘要与更新时间。
- `POST /environments/:envKey/persona/draft`：只接受关键词、可选 Facebook 发言语言和 `Idempotency-Key`，返回未落库草稿与摘要。
- `PUT /environments/:envKey/persona`：只接受非空 `soulYaml`，经既有 soul 校验与持久化单写后返回写后真态和 `firstPostOnboarding`。

每条路由先调用同一个 `resolveBoundAccountForEnv(userId, envKey)`；`environment_not_owned`、`binding_unknown`、`binding_conflict`、`binding_unavailable` 原样保留为可区分失败。响应必须回显 `envKey` 供 Electron 防范围错配，但不得回 `accountId` / `updatedBy`。`source=none` 时不得把 `getDetail()` 提供给后台编辑器的打包起点模板放进“当前人设”。

### D4：结构化摘要由 Cloud 解析，Edge 不复制 soul 解析器

Cloud 用既有 `loadSoulFromYaml` 解析真实 soul，返回有界字段：人设名、定位、背景、语气、发言语言、主/次兴趣、搜索种子与点赞倾向。Edge 只渲染 DTO；“查看完整定义”折叠展示 Cloud 返回的原文，不在客户端解析或校验 YAML。

“调整人设”复用现有选择器，并对语气、语言、点赞倾向和能精确匹配的内容标签做 best-effort 预填；无法反向映射的生成字段仍在当前摘要中可见，不猜测分类。

### D5：手动打开的人设浮层以按需 HTTP 真态为准

用户点击某环境的人设图标后，浮层先显示“正在读取云端人设”，随后按该 `envId` 的请求结果渲染：

- configured：精简摘要卡 + “查看完整定义” + “调整人设”。
- missing：直接显示现有设置向导，生成按钮可用且不依赖 core 状态。
- binding_unknown：说明“首次启动并登录一次”，保留去启动动作。
- 网络/服务失败：显示真实失败与重试，不把失败当成未设置。

自动提醒仍只由在线 `personaBound === false` 触发，未知不自动弹。手动读取结果只更新该环境的会话内投影；环境切换、请求晚回和草稿归属继续按 env 隔离，客户退出时清除。

### D6：仅草稿生成使用长 HTTP 超时

现有 customer-auth fetch 默认 12 秒，无法覆盖 PersonaGenerator 的 180 秒模型天花板。具名草稿请求传 `timeoutMs=200000`；读取、保存和其他 customer-auth 请求继续保持 12 秒。renderer 在 await 前展示骨架/禁用动作，超时或失败恢复原人设与可重试状态。

### D7：首次绑定保持既有持久引导，但不伪造引擎已启动

HTTP 保存首次人设时与 WS 相同地建立一次性 first-post onboarding 状态并返回真值。Edge 可以继续展示既有“开始找灵感”引导；用户点击后才启动/恢复环境。保存成功只表示人设已持久化并热加载，不表示浏览器已经启动或首篇内容已经生成。

## Risks / Trade-offs

- [持久绑定反映上一次成功握手，环境后来在浏览器外换号但尚未再次握手] → 这是现有绑定模型的已知边界；客户端显示环境级绑定真态，不从本地页面猜新账号，下一次握手后自愈。
- [HTTP 与旧 WS 同时生成相同账号草稿] → 共享应用服务按账号+幂等键去重；不同幂等键是用户主动的不同草稿，不自动落库。
- [大模型请求超过普通 HTTP 超时] → 仅具名草稿请求使用 200 秒超时，其他客户 API 继续有界 12 秒。
- [账号在操作期间被改归属或发生跨客户争用] → GET/POST/PUT 每次现读归属与绑定，不信任打开浮层时的旧结果；失败不改本地成功态。
- [返回 soul YAML 增大客户响应] → 单份仍受既有 32 KiB 人设上限和 bounded JSON 解析保护；无批量列表返回全文。
- [UI 状态推送覆盖手动读取结果] → 人设读取/草稿/保存状态按 envId 单独存放，打开浮层时优先当前 env 的请求态；在线 status 仅继续驱动自动提醒与运行状态。

## Migration Plan

1. 在隔离 worktree 完成 Cloud 共享服务与 customer-auth 路由，保持旧 WS 行为和测试兼容。
2. 先集成、推送并从 Cloud `master` 部署到 `dev`，验证新路由鉴权、归属、绑定和健康状态。
3. 再集成、推送 Edge `master` 源码；不构建安装包。新版开发客户端开始使用 HTTP，旧客户端继续走 WS。
4. 在停止环境上验证读取、草稿和保存；再启动同一环境确认新人设热加载生效。不得用真实账号写动作作为本变更验收。
5. 回滚 Edge 只会恢复“需启动后管理”；Cloud 新路由无人调用时无副作用。若回滚 Cloud，应先确保没有新版 Edge 依赖该 dev 版本；旧 WS 路径始终保留。

## Open Questions

- 无。产品边界采用“已持久绑定即可离线管理；从未绑定需首次启动一次”，本期不扩展账号导入或预绑定能力。
