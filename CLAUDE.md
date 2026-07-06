# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 本仓 `aidcp`（仓库根 `.`）是 **aidcp\* 家族的中控 / 总览仓**：契约（架构 / 协议 / 产品设计）在这里定义，后续开发、测试、部署在这里**触发与编排**，走 **openspec** spec-driven 流程。本文件约定 OVERRIDE 默认行为。
>
> **本仓只承载文档与契约（`docs/` + `openspec/` + `README.md`），不含业务代码、无构建链**。root `package.json` 只有一个占位 `npm run docs`（echo），本仓根目录跑 `npm test` / `build` / `lint` 会失败——这些都在 sub-repo 里跑。与本仓相关的唯一可执行校验是 `openspec validate <change> --strict` 与 `openspec list`。

## 0. 路径与环境前置检查（务必先做）

三仓为**同级目录**：本仓即 `.`（cwd = 仓库根），sub-repo 用相对写法 `../aidcp-edge`、`../aidcp-cloud`（文档里历史遗留的 `ai-dcp`、`/Users/bears/codes/…` 均为换机前旧值，正文已统一，勿再产出）。

- **edge / cloud 两个 sub-repo 可能未在当前机器 clone**（中控仓只承载文档与契约）。涉及 edge/cloud 代码、测试或 ECS 部署前，**先 `ls -d ../aidcp-edge ../aidcp-cloud` 确认是否存在**；缺失则停手，向用户确认实际位置或先 clone，**绝不盲目照搬路径执行命令**。
- **ECS 操作必须先命名 target**。执行任何 `ssh` / `rsync` 到 ECS 前，先在中控仓运行 `scripts/deploy-target <dev|ol> --check`：`dev=121.89.85.150`（key `~/codes/isales-4.pem`），`ol=123.56.253.183`（key `/Users/baitianxing/Downloads/ol.pem`）。未指定部署目标时，开发完成后的默认部署目标是 `dev`；`ol` 只有用户明确要求线上/OL部署时才执行。target 不清或 key 检查失败则停手告知用户。

## 1. 四仓关系（原三仓 + 管理后台前端 aidcp-console）

| 仓 | 路径 | 默认分支 | 角色 |
| --- | --- | --- | --- |
| **aidcp**（本仓，中控） | `.` | `main` | 契约 / 文档 / openspec changes / 测试与部署编排 |
| **aidcp-edge** | `../aidcp-edge` | `master` | 边缘端：CDP / 定位 / 浏览 / 拟人化 / 反检测 / 发布 / Electron |
| **aidcp-cloud** | `../aidcp-cloud` | `master` | 云端：协议 / 事件驱动编排 / 风控 / 发布 / 概念池 / 飞书 Bot / **面板 API 层（管理后台后端 `src/panel/`）** |
| **aidcp-console** | `../aidcp-console` | `master` | 管理后台前端（统一 Web 控制台）：React+Vite+TS+AntD；**只读云端面板 API + 经 `/api` 下发指令，绝不直连边缘**。remote `git@github.com:tommax-bai/aidcp-console.git`（private）；本机可能尚未 clone |

中控仓定义契约与变更；代码改动落到对应 sub-repo，进度回写本仓 openspec change。edge 与 cloud 经 `docs/protocol.md` 定义的 **WebSocket 协议 v2** 通信；console 经 cloud **进程内面板 API 层**（HTTP `/api` + 浏览器 WS `/ws`，独立端口、与 8787 边-云 ws 物理隔离）取数与下发，见 change `aidcp-console-panel-mvp`。**部署形态**（2026-06-20 首次上线）：ECS 上 cloud 面板层监听 `127.0.0.1:8090`、Nginx `aidcp-console.conf` 在 `8088` serve console 静态 + 反代 `/api`/`/ws`，与同机 isales（80/8000/四服务）隔离。

## 2. 架构大局（需跨文件才能拼出的上位约束）

改动前先判断「落 edge 还是 cloud」，依据这几条铁律（权威文档：`docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md`）：

- **边轻云重 + 状态单写**：原子操作（click / input / scroll）**永远只在边缘**；规划 / 选元素 / 编排 / 风控 / 持久化全在云端。账号风控最终状态**只由云端 `RiskController` 单写**（状态机 `normal→warned→restricted→frozen`，类在 `src/risk/risk-state-machine.ts`），其他系统只提交事件 / 读投影、不得改写最终状态。
- **红线反模式：MUST NOT「静默假成功」**（贯穿全部 5 个 spec 的核心不变量，自愈不自残）。找不到目标报 `no_target` 而非 `ok`；按实测位移 / 真实数量如实回报（不再 `count||1`）；坏页 / 404 不静默吞；数据缺失不得误判为低质量。新写 edge 动作或 cloud 决策默认遵守。
- **DOM-first 定位三道闸**（`aidcp-edge/src/locating/engine.ts`，靠 `DomProvider` / `ActionExecutor` 接口让 jsdom 桩 ↔ CDP 实现可换、脱离浏览器单测）：① **后置校验**——操作后必须验证业务结果真发生；② **重试上限 + 升级**——连续失败到顶判系统性改版、停手 `escalated`、绝不静默成功；③ **反污染回写**——LLM 新锚点先 stage 暂存、连续确认成功才晋升主缓存、任一次校验失败即 drop。改动勿破坏这三闸与那两个接口。
- **协议 v2（`PROTOCOL_VERSION=2`）改动须四处同步**：edge / cloud 两份 `src/comm/protocol.ts`（逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts` 的动作↔消息映射（如 `scroll→page.scroll`、`open_note→note.open`、`like→interaction.like`、`back→navigation.back`、`profile_open→profile.open`）+ `docs/protocol.md` + **新增 cloud→edge 主动控制命令时，`aidcp-edge/src/client/edge-client.ts` 的 onMessage 主动命令路由白名单**（独立下发、非 `plan.response` 步骤的那类命令必须在此放行到 `browseHandler`，否则落到「其他主动消息暂忽略」被**静默丢弃**、命令到不了处理器——`browse-session.ts` 写了处理分支也没用）。前三处漂移由 `npm run typecheck` 暴露（两份 protocol.ts 用 `Record<MessageType,true>` 穷举，不一致即失败）；**第 4 处白名单遗漏 typecheck 抓不到**（实例：notification-monitor 6.5.1，云端 `sendCommand sent=2` 已发但边缘无动作无回执→巡视恢复链卡死→看门狗 idle≈240s 杀整会话；修于 edge `0c28e32`，已补路由回归断言）。**消息类型数以两份 protocol.ts 的 `MessageType` 穷举为准**；`docs/protocol.md` 头部计数与 §2 表为人工维护、可能滞后于代码，新增 / 删除消息后务必同步头部计数与表。**协议表里列出 ≠ 已接线生效**：`anchor.get` / `anchor.report`（云端 PG 主缓存同步）、`risk.canDo` / `risk.record`（风控对浏览闭环实时拦截）等为保留通道、边缘尚未接线——浏览侧约束当前靠云端浏览预算，而非 `RiskController` 实时拦截。
- **云端是事件驱动多 Agent**（已非旧单体 `Planner`）：`RoleDispatcher`（`src/orchestrator/role-dispatcher.ts`）注册 **37 角色**（浏览闭环 25 + 通知巡视 12；其中「评论点赞」两角色 + `curated_comment_evaluator` 仅 `AIDCP_COMMENT_LIKE=true` 时注册、`concept_extractor` 仅概念池可用时注册、两精选准入评估角色 `curated_note_evaluator`/`curated_comment_evaluator` 仅精选库可用时注册）+ 进程内 `EventBus`。注：change `comment-search-command` 的 `comment_search_term_generator`/`comment_target_picker` 在 `RoleName` 穷举内但**不计入此 37 注册数**——它们是**命令式**角色（飞书 `/comment` 触发，由 `CommentScheduler` 按账号构造、不进 dispatcher 运行时注册表，类比 publish-agent 管线角色），仅登记 `role-catalog` 供后台配模型 + `SessionContext`，浏览闭环由 `feed.entered` 启动、互动 / 返回后再次 `feed.entered` 往复，直到 `SessionMonitor` 判结束。**角色数以 `event-bus/types.ts` 的 `RoleName` 穷举 + `setup()` 注册为准**（本计数为人工维护、可能滞后）。角色间纯靠 `EventBus` 接力（无中央状态机）；调度器是唯一命令式接线点，做两层翻译：角色事件→边缘命令（`setupCommandTranslation`，含风控/配额/软暂停统一闸）、边缘上报→角色事件（`setupEdgeEventSubscriptions`）。现役主路径 = v2 事件驱动浏览闭环（`page.cards` / `note.detail` 结构化上报 → 逐动作下发）；`plan` / `anchor` / `select` 每步循环为 v1 兼容路径仍在；边缘 `card-filter` 与协议 `browse.next` / `browse.scroll` 已 `@deprecated` / 被角色驱动的 `page.scroll` 取代，**勿在遗留路径上改代码**。已删除的旧文件别再找：`session-orchestrator.ts` / `state-machine.ts` / `engagement-decider.ts` / `concept-extractor.ts` / `src/blackboard/` / `src/publish/`。
- **节奏系数收口云端**（Command Pacing）：内容 / 状态相关的时长系数由云端一处算出**中心值**，随决策指令以 `thinkMs`（动作前犹豫）/ `dwellMs`（离页前总停留，治「秒退」）下发；**边缘只叠 lognormal 抖动 + 保证停留达标 + 断连兜底**；`session.budget.pacing` 只带极薄兜底（`tempo` / `dwellFloorMs`），不含 read/pause/fatigue 系数。改节奏前先确认改的是云端中心值还是边缘抖动层。**实装边界**：限频配额 `effectiveQuotas()`（保守 / 正常 / 激进三档）已实装；`tempo` 降速旋钮（1.0 / 1.3 / 1.6 放大停顿）**也已实装并接线**（`pacing.ts` 的 `tempoForStatus` → `computeThinkMs` / `computeDwellMs` → `role-dispatcher` 的 `thinkNow` / `dwellForCurrentNote`，按实时风控状态取值）。真正**尚未实装**的是「状态迁移接真实平台封号 / 限流信号」——状态平时停在 `normal`、tempo 多停在 1.0，当前状态迁移仅靠配额阈值（`quota_exceeded`）与验证码 / 风控浮层信号触发（已知缺口）。

## 3. openspec 工作流（spec-driven）

- 全局 CLI 可用（`/opt/homebrew/bin/openspec`，1.2.0，不在 package.json）。常用：`openspec list`（看 change 状态）、`openspec list --specs`、`openspec validate <change> --strict`、`openspec status --change <name>`、`openspec show <item>`。
- 所有跨 spec 的功能改动都走 **openspec change 流程**，不要绕过 openspec 直接改 `openspec/specs/` 下的 spec 文件。
- 新 change：`/opsx:propose "<想做什么>"`（探索 / 实装 / 归档用 `/opsx:explore` `/opsx:apply` `/opsx:archive`）。
- **引入有复杂度 / 可扩展性诉求的新功能：先做「业界方案」设计，再 propose**。方法四步：① 在代码里坐实现状（现有实现 / 约束 / 痛点，带 `文件:行`）→ ② 多角度梳理业界成熟设计模式并映射到本系统 → ③ 综合出一套健壮 + 可扩展的设计 → ④ 一道对抗性评审（防过度设计、查约束违背与失败模式）。这一步可用多 agent workflow 编排（范例：2026-06-19 watcher / 通知监控设计）。产出设计后再落成 openspec change；务实优先、按 YAGNI 砍超前抽象、留干净扩展缝。
- **实装前**：先 `openspec list` 看状态，再读 `openspec/changes/<active-change>/tasks.md` 定位当前 task；不凭空起 task。apply 流程靠 CLI 取上下文（`openspec status` / `openspec instructions apply --change <name> --json` 拿 contextFiles 与进度），不要硬编码文件名。
- **实装中**：代码改动落对应 sub-repo（edge / cloud）；`tasks.md` 进度回写本仓，按 sub-repo 分节（如 `## 1. aidcp-cloud — …`）。
- **实装后**：用 HTML 注释把 task 标 `[x]`，写清 commit-sha / 偏离说明，格式 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。
- **完成全部 task → `openspec validate <change> --strict` → archive**（archive 时 `changes/<change>/specs/` 的 delta 合并进 `openspec/specs/`，归档目录按 `<YYYY-MM-DD>-<change-name>/` 命名）。
- **现状指针**（接手时先核对，截至 2026-06-18）：**当前无活跃 change**（`openspec list` 返回 "No active changes found"）；上一个 change `implement-deepread-lineage` 已于 2026-06-18 归档（详情页深读链路：`profile.open` 协议、`DeepReader` 真实看图、`comment_reviewer` 实体化、修 `FollowAgent` 假 0 粉丝数据）。已合并 **7 个 spec**（`openspec list --specs` 为准，勿手改 `openspec/specs/`，新功能走 change 流程）：`author-profile-visit`（作者主页访问）、`browse-loop-resilience`（返回 feed 续刷不死锁、看门狗有界 idle、坏页兜底）、`command-pacing`（节奏系数收口云端 + dwellMs/thinkMs）、`deep-read-fidelity`（评论按实测位移回报、上溯找可滚容器）、`detail-deep-read`（详情页深读）、`follow-decision`（follow 只用平台真实信号、不用作品数）、`note-extraction-fidelity`（正文跨布局抽取、渲染门与抽取器共用选择器）。最近归档目录见 `openspec/changes/archive/`（如 `2026-06-18-implement-deepread-lineage`）。

## 4. 测试（中控触发，落 sub-repo 执行）

> sub-repo 须先存在于本机（见 §0）。

- edge：`cd ../aidcp-edge && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- cloud：`cd ../aidcp-cloud && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- **回归纪律**：任何协议 / 风控 / 发布改动后，**先 `npm run test:acceptance` 再全量 `npm test`，再 `npm run typecheck`**。安全红线必须全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、`AC-RISK-*`（绝不自残、被禁 `record` 返 false）；`AC-E-*` 为端到端。发布审批信号文件两端契约路径 `/tmp/aidcp-publish-approve-<requestId>.json` 必须一致（edge `buildPublishApprovalSignalPath` ↔ cloud `getApprovalSignalPath`），改发布链时勿漂移。真机层 gated：dev 用 `AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test`，ol 用 `AIDCP_CLOUD_URL=ws://123.56.253.183:8787`。
- 本地只做**代码级验证**；cloud 正式运行只在 ECS，本地**不要起 cloud**。

## 5. 部署（云端 ECS，带安全闸）

> **部署铁律**：cloud 只跑在命名 ECS target，本地永不起 cloud；edge 本地跑并显式连接 dev 或 ol。dev=`ws://121.89.85.150:8787`，ol=`ws://123.56.253.183:8787`。当前权威口径见 `docs/deployment-environments.md`。
> **同机另有 `isales` 独立运行 —— 任何 ECS 操作绝不能碰它**（不同 systemd 服务 / 目录 / 端口）。
> 执行前先做 §0 私钥与 sub-repo 检查。

- ECS 上 cloud：`/opt/aidcp/cloud`，由 systemd `aidcp-cloud.service` 托管，对外监听 `8787`；panel API 默认 `127.0.0.1:8090`。数据库边界按 target 配置，ol 正式上线应使用独立 ol PostgreSQL/RDS，不把 dev 共库当最终架构。
- 部署**默认直接做、不用逐次问**（用户长期授权，2026-06-27）；开发完成后默认 target=`dev`，代码/产物验证、提交、推送完成后自动部署 `dev`。`ol` **不参与默认部署**，只有用户明确提出线上/OL部署时才执行；执行前必须建立或选定 `release/<日期>-<范围>` 这类发布分支，并按该发布分支部署。无论目标是 `dev` 还是 `ol`，都必须严格走安全序列：① 明确 target 并 `scripts/deploy-target <dev|ol> --check` → ② sub-repo 测试通过 → ③ ECS **先备份**（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ ④ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ ⑤ `systemctl restart aidcp-cloud.service` → ⑥ healthcheck（`active (running)` + 8787 监听 + 飞书长连接已建立/或明确禁用 + PG `select 1`）→ ⑦ 失败即回滚。**红线不变**：绝不碰 dev 同机 isales。
- SSH：先用 `scripts/deploy-target <dev|ol> --check` 取目标信息。逐条命令、版本台账详见 `docs/deployment-environments.md`、`docs/handoff-2026-06-05.md`（历史台账）与 `aidcp-cloud/docs/deployment-ecs.md`。

## 6. git / 沟通 / 安全边界

- **默认主动 `git commit` + `git push` 到 origin，并自动部署 `dev`**（本仓 + sub-repo 都适用），推各仓默认分支（本仓 `main`、edge/cloud/console `master`）。**提交 / 推送 / dev 部署都不需每次问**（用户长期授权，2026-06-27；部署安全序列与红线见 §5）。`ol` 部署必须等用户明确要求，并从发布分支执行。commit message 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。**仍需先确认**：force-push、非 fast-forward、推到非默认 protected branch。
- **提交 / 推送 / 部署必须用干净 worktree 做最终确认**：代码改动提交推送后，若当前工作区存在任何无关改动，或处于多任务并行场景，必须从目标提交新建 clean worktree（或等价 `git archive HEAD` 快照）运行部署闸与打包；严禁从脏共享工作区直接 `rsync` / 打包上线，避免把未提交 / 他人改动混入生产。部署仍只从默认分支目标提交的快照走，worktree 用于验证与产物生成，不作为长期开发主干。
- **语言**：正文默认中文；代码 / 注释 / commit / PR / 命令 / 文件名保持英文。
- **问题 / 方案的说明方式（默认模式，用户偏好）**：讲逻辑、不用比喻；不点代码内部标识符（变量 / 类 / 函数 / 消息类型名），改用**功能性正文**描述组件与机制（如「执行端 / 决策端 / 监测体」「发命令给执行端的统一出口」「阻塞式 vs 临时离开式打断」）；分点、句子短、让非工程视角也能跟上；确需落到代码时再补具体 `文件:行`。
- **不记敏感值**：文档 / 提交 / tasks.md 里不写任何 PostgreSQL 密码 / token / 私钥内容，只记路径、服务位置、命令用法、配置读取方式。
- **每次对话收尾给一段「说人话」的总结**：用非技术语言讲清楚——这次做了什么、对系统有什么影响、下一步是什么。技术细节照常给，但总结那段要让非工程视角也看得懂。

## 7. 并行开发规范（多 Claude session / git worktree）

以多个并行 session 同时开发时（用户编排 5–8 个）按下列铁律，防版本错落。这是从「多 session 共用同一子仓工作树」（现状：push 撞 non-ff、脏文件成常态）向「每 change 一个 worktree」的迁移；迁移期两态并存，共享工作树处仍守末条 rebase 纪律。**单个 session 只需守自己这一段；「5–8 条流串行集成」是用户在 fleet 层协调的性质，单 session 强制不了。**

- **一个 session = 一个 openspec change = 一条分支 = 一个 worktree，四者同名**；worktree 放 `../<repo>.wt/<change-name>`。控制仓 aidcp 的 change 是 additive 目录、近零冲突，可不开 worktree、在主 checkout 各写各的 change 目录。
- **用手动 `git worktree add` 到子仓（`scripts/new-change`），不用内置 `EnterWorktree`/`ExitWorktree`**：内置只作用于当前（中控）仓、会切走 session cwd、且不纳管手动建的 worktree——不合本项目「中控仓驱动、代码落子仓」的多仓模型（详见手册 §1）。
- **被指派 change 即为 fleet 成员**：session 若经 `scripts/spawn-change` 启动、或用户直接说「实装 change X」，即独占该 change，按本节自主走全流程（读 change 文档 → worktree 开发 → `land-change` 集成 → tasks.md 回写 → 真机项登记 backlog → 部署前探 ECS → archive），无需逐步征询。
- **极简启动（用户多终端并行的标准入口）**：新终端在本仓起 claude 后，`/impl <change名>` = 指派实装；`/claim` = 自主认领一个无人在做的活跃 change（**worktree = 认领锁**：建 worktree 失败即被并发抢先、换下一个；先报出所选再开工，不等确认）。命令定义在 `.claude/commands/`，指令自包含，用户无需再输入任何交代。
- **先判定自己在哪**：`git worktree list` / `git rev-parse` 认清是「主 checkout」还是某 change 的 worktree。worktree 内 = 只在本分支开发 + 提交 + 跑 `test` / `typecheck`；主 checkout = 集成与部署位。
- **部署只从主 checkout 的 eligible ref 走，绝不从任何 worktree 部署**（dev 用验证后的默认分支；ol 只用用户要求的发布分支，tag / clean SHA 只能作为创建发布分支的来源，不能直接替代分支部署）。
- **热点文件单写者，并行时绝不同时碰**：两份 `protocol.ts` + `aidcp-cloud/src/comm/command-bridge.ts` 动作映射（§2 协议四处同步）、角色注册（`event-bus/types.ts` 的 `RoleName` + `src/config/role-catalog.ts`）、风控状态机 `src/risk/risk-state-machine.ts`。任务若必须动这些，标记为需串行、不与他人并行。
- **开发并行、集成串行**：合回默认分支前先 `fetch` + rebase 到最新默认分支、解冲突、跑 `test:acceptance` + `typecheck` 再 ff 合并。**push 遇 non-ff 一律 rebase 后重来、绝不 force**（force / 非 ff 仍按 §6 需先确认）；空 diff = 已在远端、可弃（见 memory `concurrent-session-shares-subrepo-worktree`）。
- **完成即收口**：部署 + 验证通过 → archive 该 change → 删 worktree / 分支。有 worktree 却无对应活跃 change = 孤儿，清掉。
- 操作手册（开流 / 集成 / fleet 状态命令、helper 脚本）见 `docs/parallel-dev-worktrees.md`。**该手册的命令序列 / 脚本经实战跑通验证后方视为定稿**；未验证前只把本节不变量当 OVERRIDE 法条。
