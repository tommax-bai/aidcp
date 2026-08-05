# 设计：拆进程后面板能力的补齐与对账

## 1. 现状坐实（2026-08-05 dev 实测）

- nginx `aidcp-console.conf` 把 `/api/` 反代到 `127.0.0.1:8090`；8090 由 `aidcp-api.service` 持有（同进程另持 8091 客户登录门、8093 内部口）。链路本身正确，没有指错进程。
- `aidcp-api/src/server.ts:2108` 的 `panelDeps` 挂 29 个键；`aidcp-cloud/src/server.ts:9552` 的同一对象挂 49 个。差集 21 项（其中 `botChats` / `configMirrorHealth` 经其他字段兜住，实测 200，不计入缺口）。
- 面板对缺失可选依赖的处理是逐路由 503（`panel-server.ts` 各分支的 `if (!deps.X) sendJson(res, 503, ...)`）。**这是诚实回执，不是 bug**；bug 是没装。

## 2. 分类判据：这一项到底缺什么

对每一项问同一个问题——**它的构造依赖是否全在接口域**：

| 类别 | 判据 | 处置 |
| --- | --- | --- |
| A · 纯搬运遗漏 | 依赖全是接口域属主表 / 本进程已构造的对象 | 直接在手写组装根里构造并装上 |
| B · 单体已有 api 分支 | 单体组装根里已写 `mode === 'api'` 的实现 | 把那条分支照搬进手写组装根 |
| C · 跨属主 | 事实源在内容 / 自动化域 | 开「服务端注册 + 类型化客户端 + 路径常量」三件套 |
| D · 跨多域拼装 | 依赖同时落在两个以上域 | 分域取用后在接口侧拼，不搬实现 |

落到具体项：

- **A**：`modelConfig` 的读与凭据写、`roleConfig`、`categoryConfig`、`hotLeadConfig`、`facebookGroupCommentPolicy`、`interactionPermissions`。
  - `interactionPermissions` 值得单独说：单体里它建在自动化段（`server.ts:6284`），于是被当成跨段依赖。但它是 `buildInteractionPermissionOverview(panelUsers, grants)` 的纯函数结果，两个入参都是本进程可得的配置。**它落在自动化段是历史位置，不是归属。**
  - `modelConfig.getView` 同理：单体把 `buildModelConfigView` 定义在自动化段里并用跨段取用闸包着，但它读的是接口域的模型配置表 + 凭据表 + kernel 的厂商登记表，零跨域。
- **B**：`publishDraft`（`server.ts:9680` 已有 api 分支，用接口域的发布台账 + 审批读客户端）、`notifyPublishPreviewChanged`（`:9706` 同）。
- **C**：内容域 —— 模型探活、`tokenUsage` + `billingPriceRefresh`、`curatedContent` + `curatedActions`、`facebookPublishMedia`；自动化域 —— `captchaAssist`、`preflightApprovePublish`、`publishDispatcher`（在途 id）。
- **D**：`rolePromptPreview`。它要三样东西：预览用的角色清单（自动化域的调度器）、人设（接口域）、发布 / 配图的渲染闭包表（内容域）。**MUST NOT 把渲染闭包复制进接口仓**——那是第二份实现，行为测试原理上看不见它与正本的漂移。做法是各域各出一段，接口侧只做拼装。

## 3. 探活不得被绕过

模型 / 角色 / 分类的写路径都以「先对目标厂商探活、失败即拒、绝不落库」为既有保证。探活真调用模型，客户端归内容域。

- 内容侧新增窄口 `POST /internal/llm/probe`，入参 `{provider, model}`，出参判别式结果（`ok` / `provider_key_missing` / `model_invalid`），与单体 `probeModelResult` 的分类逐字同源。
- 接口侧客户端超时取该调用的实际量级（探活单次 8s，跨进程留 15s 默认即可），**失败一律映射成拒写**。
- **MUST NOT** 在探活通道不可用时「跳过探活直接写」。那会让一个打错的模型名静默落库，直到下一次真实调用才炸——正是「静默假成功」。
- 探活消耗真实 token，仍按既有口径记在 `system:model_probe` 角色下，不静默丢。

## 4. 跨进程三件套的形态

沿用既有范式（`src/transport/*-http.ts`，如 `panel-config-http.ts` 的四个面板配置客户端）：同一文件里放路径常量、服务端注册函数、类型化客户端；文件进 `aidcp-transport` 共享包点名清单，三家共用。**不复制两份**——两份的路径常量会各自编译通过、各自测试通过，只有真跑起来才 404（本仓已为此付过代价）。

两条纪律：

- 新增的 transport 文件必须同时登记进 `scripts/sync-split-repos` 的 `TRANSPORT_MEMBERS`，否则派生仓拿不到、下次对账才发现。
- 跨进程后 `instanceof` 恒 false：探活与精选库动作的失败识别一律按结构化字段判，MUST NOT 依赖错误类身份。

## 5. 装配对账门（防复发）

本次缺口的根因不是判断错，是**没有任何机械手段会提醒「少装了」**。TypeScript 帮不上忙：这些字段全是可选的，少写一个照样编译通过。

做法：

1. 面板契约里新增一份**运行时可读的能力名册** `PANEL_CAPABILITY_KEYS`，并用类型层穷举把它钉死在 `PanelDeps` 上（`Exclude<keyof PanelDeps, 名册项>` 必须是 `never`）。名册漏一项 ⇒ 编译红。手抄名单的老问题（`satisfies` 不查写全）由这个 `Exclude` 判据堵住。
2. 各进程组装根在装配后调用一次覆盖断言：名册里的每一项，**要么在 deps 里、要么在本进程的具名缺席表里并带理由字符串**，两者皆无即启动失败。
3. 具名缺席表就是账本：它让「本进程不打算提供这项能力」成为一个**写下来的决定**，而不是一次静默的遗漏。缺席表只准缩短；新增一项要写清用户可见后果。

这道门刻意做成**启动期硬失败**而非测试期告警：面板层是运营唯一的操作面，少一项就是一页打不开，值得让进程起不来。

## 6. 不做的事

- 不动 console 前端：它的调用面本来就对，后端从 503 变成真答即可。
- 不动协议 v2、不动数据库形状。
- 不把单体那份 `server.ts` 当作可以直接 rsync 的替代品——组装根永远各写各的，这是拆仓的既定纪律。
- 不为 `botChats` / `configMirrorHealth` 补装：实测 200，已被其他字段兜住，补装反而多一份路径。
