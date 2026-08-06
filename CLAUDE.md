# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 本仓 `aidcp`（仓库根 `.`）是 **aidcp\* 家族的中控 / 总览仓**：契约（架构 / 协议 / 产品设计）在这里定义，后续开发、测试、部署在这里**触发与编排**，走 **openspec** spec-driven 流程。本文件约定 OVERRIDE 默认行为。
>
> **本仓只承载文档与契约（`docs/` + `openspec/` + `README.md`），不含业务代码、无构建链**。root `package.json` 只有一个占位 `npm run docs`（echo），本仓根目录跑 `npm test` / `build` / `lint` 会失败——这些都在 sub-repo 里跑。与本仓相关的唯一可执行校验是 `openspec validate <change> --strict` 与 `openspec list`。

## 0. 路径与环境前置检查（务必先做）

三仓为**同级目录**：本仓即 `.`（cwd = 仓库根），sub-repo 用相对写法 `../aidcp-edge`、`../aidcp-cloud`（文档里历史遗留的 `ai-dcp`、`/Users/bears/codes/…` 均为换机前旧值，正文已统一，勿再产出）。

- **edge / cloud 两个 sub-repo 可能未在当前机器 clone**（中控仓只承载文档与契约）。涉及 edge/cloud 代码、测试或 ECS 部署前，**先 `ls -d ../aidcp-edge ../aidcp-cloud` 确认是否存在**；缺失则停手，向用户确认实际位置或先 clone，**绝不盲目照搬路径执行命令**。
- **ECS 操作必须先命名 target**。执行任何 `ssh` / `rsync` 到 ECS 前，先在中控仓运行 `scripts/deploy-target <dev|ol> --check`：`dev=121.89.85.150`（key `~/codes/dev-0722.pem`），`ol=123.56.253.183`（key `~/codes/ol-0722.pem`）。未指定部署目标时，开发完成后的默认部署目标是 `dev`；`ol` 只有用户明确要求线上/OL部署时才执行。target 不清或 key 检查失败则停手告知用户。

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
- **DEV/OL 共库异步隔离**：PostgreSQL 长期共用。凡由后台扫描、认领、重试或恢复的持久任务，必须由 Cloud 按本机 `AIDCP_DEPLOY_ENV` 写入 `execution_target=dev|ol`；创建、查询、认领、恢复和更新始终限定当前 target，target 缺失或非法时不启动该 worker。普通共享业务数据和配置不因此强制增加 target。
- **红线反模式：MUST NOT「静默假成功」**（贯穿全部 5 个 spec 的核心不变量，自愈不自残）。找不到目标报 `no_target` 而非 `ok`；按实测位移 / 真实数量如实回报（不再 `count||1`）；坏页 / 404 不静默吞；数据缺失不得误判为低质量。新写 edge 动作或 cloud 决策默认遵守。**这条约束的是「回执内容」**——它**不构成**「不确定就不许动手」或「不确定就终结这一趟」的授权，见下一条。
- **红线的另一半：MUST NOT「静默假失败」；停手必须是结构性的**（完整判据 `docs/stop-or-continue.md`，2026-08-04 立）。**三件事必须分开判、分开写：要不要动手 / 如实回报什么 / 这一趟还继不继续。**
  - **动手与否，只看目标身份**：一条观测若换个结果会导致**被写的是另一个对象**（含「因为我其实还站在另一页上」这条路径），它才是身份条件，确认不了就不动手；只描述目标周边处境的是**姿态条件**（地址带不带参数、渲染完没完、区域划不划得清），只准触发一次有界纠正再复测，MUST NOT 单凭它拒绝动手。**降级姿态代理的前提是下游那道直证同样能抓住它抓住的那一类**；抓不住的，它就是唯一证据。判据是语义不是长相——反例见该文档 §4 Q1（一条长得像 URL 格式检查的判断，实际是唯一能证明跳转真落地的证据）。
  - **终结与否，只看结构性**：判据是「同一步在**重新加载后的页面上**原样重来，有没有可能得到不同结果」。有 ⇒ MUST 留**带上限**的自愈通道、MUST NOT 落终态、MUST NOT 记成「做不到」；没有 ⇒ 才可终结，且回执要写清「为什么重来也不会变」。**恢复预算 MUST 只由失败消费**（准备工作花掉的导航 / 下滚不算重试）。**跨进程 / 兄弟服务暂时读不到，恒非结构性失败。**
  - **提交点是最外层前置**：命令已离开本进程、或页面上的提交已按下的，任何自愈通道 MUST NOT 覆盖它——重投一条可能已上墙的内容是本仓代价最高的错误。
  - **回报永远第一诚实，三态不得压成一态**（「没能确认」/「确认到没有」/「已发出但核不到」端到端须有不同原因值）；**跨层翻译 MUST 保住可恢复性、MUST NOT 有兜底桶**——把没认出来的原因折进已有失败名，跨层传下去就成了终局判决。
  - **加闸准入（防止本条变成新的加闸许可证）**：MUST NOT 以「存在一条通向坏结果的路径」为由加闸——**概率低 × 后果可恢复 = 不加闸，记档即可；只有后果不可逆且对外可见的，才配用低概率当加闸理由**。**排序按「不改的代价」，不按「改起来便不便宜」**（「一行就能修」不是优先级理由，便宜正是那条把防御定价成零的成本函数的伪装形态）。加闸前先排除「这道闸在替上游没做的等待 / 没拆的分类擦屁股」，并给出该与项自身失败率的量级估计——**平台不稳定，连乘是本系统的主要失效模式**。
  - **为什么需要这一条**：档案里最贵的三次**重复对外写入**（重复加群 / 重复发出真评论 / XHS 重复评论风险）根因**全是一次停手**——停手一旦在下游被读成「所以什么都没发生」，就直接制造重复动作。`docs/edge-honesty-gap-inventory.md` 那句「错报失败危害远小于错报成功」**只对回执成立、对控制流不成立**，已就地加限定。
- **定位三道闸（红线本身不变，但落点已换代——2026-08-05 据实修订）**：① **后置校验**——操作后必须**重新读回**业务结果、校验不过一律判失败，绝不静默成功；② **重试上限 + 升级**——连续失败到顶判系统性改版、停手 `escalated`，且须分「一次都没写下去」与「写下去了但结果始终没发生」两种终局，**不可重放的写一经派发即停手报不确定、绝不重放**；③ **反污染回写**——非确定性来源的新锚点先 stage 暂存、连续确认成功才晋升主缓存、任一次校验失败即 drop。
  - **权威落点已不是 `aidcp-edge/src/locating/engine.ts`**：那个文件连同 `locating/cache.ts` 与「每步让模型做选择题」那条路径**已从生产构建剪除**（退役名单事实源＝`aidcp-edge/scripts/native-engine-inventory.cjs` 的 `RETIRED_DIST_MODULES`）。`DomProvider` / `ActionExecutor` 是定义在该文件里的 **TypeScript 接口，编译后零运行时痕迹**，"jsdom 桩 ↔ CDP 实现可换"描述的是退役那一代。
  - **现役落点分两层，且必须分开说**：闸①②的实际行为活在 **Native 引擎各平台分片自己的实现里**（`aidcp-edge/native/page-engine/src/`）；`native/page-engine/src/locating.rs` 是三道闸的**统一新落点，但其模块注释自陈「只造原语、尚未接进任何平台命令」**，且**闸③在当前引擎里必然空转**——固定选择器不产生任何需要暂存确认的新锚点。
  - **因此：MUST NOT 据此把「定位自愈已恢复」当成事实**，也 MUST NOT 在退役的 TypeScript 定位模块上实装（写完全绿、发版成功，运营机上跑的仍是引擎那一套，**零生产效果且无任何警告**）。改动前先确认落点在哪一层。全景见 `docs/architecture.md` §2.2 / §3.2 / §3.3。
- **协议 v2（`PROTOCOL_VERSION=2`）改动须四处同步**：edge / cloud 两份 `src/comm/protocol.ts`（逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts` 的动作↔消息映射（如 `scroll→page.scroll`、`open_note→note.open`、`like→interaction.like`、`back→navigation.back`、`profile_open→profile.open`）+ `docs/protocol.md` + **新增 cloud→edge 主动控制命令时，`aidcp-edge/src/client/edge-client.ts` 的 onMessage 主动命令路由白名单**（独立下发、非 `plan.response` 步骤的那类命令必须在此放行到 `browseHandler`，否则落到「其他主动消息暂忽略」被**静默丢弃**、命令到不了处理器——`browse-session.ts` 写了处理分支也没用）。前三处漂移由 `npm run typecheck` 暴露（两份 protocol.ts 用 `Record<MessageType,true>` 穷举，不一致即失败）；**第 4 处白名单遗漏 typecheck 抓不到**（实例：notification-monitor 6.5.1，云端 `sendCommand sent=2` 已发但边缘无动作无回执→巡视恢复链卡死→看门狗 idle≈240s 杀整会话；修于 edge `0c28e32`，已补路由回归断言）。**第 5 处：`action.completed.action` 的动作名口径**——该字段是云端**角色关联键**（`open_note` / `browse_images` / `scroll_comments`），**不是协议消息名**（`note.open` / `note.browse_images`）。两侧各有一张 21 条映射表（edge `src/facebook/facebook-session.ts` 的 `FB_COMMAND_ACTION_NAMES` 发前归一 / cloud `src/comm/handler.ts` 的 `LEGACY_ACTION_COMPLETION_ALIASES` 入口归一），字段两端都是裸 `string`、**typecheck 同样抓不到**。回传错名的后果不是报错，而是**角色永远等不到回执 + 调度器把它当未知失败动作、在详情页上下发 feed scroll**（实例：Facebook 会话；修于 edge `7b9b37e` / cloud `25379e6`）。新增平台 / 命令时，动作名必须与云端角色期望的规范名一致。**注**：客户端内稿件审批新增的 `publish.approval_action` / `.result`（协议 72→74）**不需要**进第 4 处白名单——`.result` 是按信封 id 关联的应答，由客户端 pending 表直接 resolve，那条白名单只对「云端独立下发、非应答」的命令生效。**消息类型数以两份 protocol.ts 的 `MessageType` 穷举为准**；`docs/protocol.md` 头部计数与 §2 表为人工维护、可能滞后于代码，新增 / 删除消息后务必同步头部计数与表。**协议表里列出 ≠ 已接线生效**：`anchor.get` / `anchor.report`（云端 PG 主缓存同步）、`risk.canDo` / `risk.record`（风控对浏览闭环实时拦截）等为保留通道、边缘尚未接线——浏览侧约束当前靠云端浏览预算，而非 `RiskController` 实时拦截。
- **云端是事件驱动多 Agent**（已非旧单体 `Planner`）：`RoleDispatcher`（`src/orchestrator/role-dispatcher.ts`）注册 **37 角色**（浏览闭环 25 + 通知巡视 12；其中「评论点赞」两角色 + `curated_comment_evaluator` 仅 `AIDCP_COMMENT_LIKE=true` 时注册、`concept_extractor` 仅概念池可用时注册、两精选准入评估角色 `curated_note_evaluator`/`curated_comment_evaluator` 仅精选库可用时注册）+ 进程内 `EventBus`。注：change `comment-search-command` 的 `comment_search_term_generator`/`comment_target_picker` 在 `RoleName` 穷举内但**不计入此 37 注册数**——它们是**命令式**角色（飞书 `/comment` 触发，由 `CommentScheduler` 按账号构造、不进 dispatcher 运行时注册表，类比 publish-agent 管线角色），仅登记 `role-catalog` 供后台配模型 + `SessionContext`，浏览闭环由 `feed.entered` 启动、互动 / 返回后再次 `feed.entered` 往复，直到 `SessionMonitor` 判结束。**角色数以 `event-bus/types.ts` 的 `RoleName` 穷举 + `setup()` 注册为准**（本计数为人工维护、可能滞后）。角色间纯靠 `EventBus` 接力（无中央状态机）；调度器是唯一命令式接线点，做两层翻译：角色事件→边缘命令（`setupCommandTranslation`，含风控/配额/软暂停统一闸）、边缘上报→角色事件（`setupEdgeEventSubscriptions`）。现役主路径 = v2 事件驱动浏览闭环（`page.cards` / `note.detail` 结构化上报 → 逐动作下发）；`plan` / `anchor` / `select` 每步循环为 v1 兼容路径仍在；边缘 `card-filter` 与协议 `browse.next` / `browse.scroll` 已 `@deprecated` / 被角色驱动的 `page.scroll` 取代，**勿在遗留路径上改代码**。已删除的旧文件别再找：`session-orchestrator.ts` / `state-machine.ts` / `engagement-decider.ts` / `concept-extractor.ts` / `src/blackboard/` / `src/publish/`。
- **节奏系数收口云端**（Command Pacing）：内容 / 状态相关的时长系数由云端一处算出**中心值**，随决策指令以 `thinkMs`（动作前犹豫）/ `dwellMs`（离页前总停留，治「秒退」）下发；**边缘只叠 lognormal 抖动 + 保证停留达标 + 断连兜底**；`session.budget.pacing` 只带极薄兜底（`tempo` / `dwellFloorMs`），不含 read/pause/fatigue 系数。改节奏前先确认改的是云端中心值还是边缘抖动层。**实装边界**：限频配额 `effectiveQuotas()`（保守 / 正常 / 激进三档）已实装；`tempo` 降速旋钮（1.0 / 1.3 / 1.6 放大停顿）**也已实装并接线**（`pacing.ts` 的 `tempoForStatus` → `computeThinkMs` / `computeDwellMs` → `role-dispatcher` 的 `thinkNow` / `dwellForCurrentNote`，按实时风控状态取值）。「状态迁移接真实平台限流信号」**Facebook 侧已实装**（2026-07-10 随 FB 集成分支合回主干）：FB 的软阻断 / 限流文案识别（`src/comm/facebook-throttle-signals.ts` → `captcha-coordinator` → `applySignal` → 激进退避到 `restricted`），同批的冷启动配额爬坡也已接线（`risk-controller.ts` 的 `applyColdStartClamp`，env `AIDCP_COLDSTART_RAMP=false` 可秒回滚）。**仍未实装**：小红书侧的真实封号 / 限流信号接入——XHS 账号状态平时仍停在 `normal`、tempo 多停在 1.0，迁移仅靠配额阈值（`quota_exceeded`）与验证码 / 风控浮层信号（已知缺口）。

## 3. openspec 工作流（spec-driven）

- 全局 CLI 可用（`/opt/homebrew/bin/openspec`，1.2.0，不在 package.json）。常用：`openspec list`（看 change 状态）、`openspec list --specs`、`openspec validate <change> --strict`、`openspec status --change <name>`、`openspec show <item>`。
- 所有跨 spec 的功能改动都走 **openspec change 流程**，不要绕过 openspec 直接改 `openspec/specs/` 下的 spec 文件。
- 新 change：`/opsx:propose "<想做什么>"`（探索 / 实装 / 归档用 `/opsx:explore` `/opsx:apply` `/opsx:archive`）。
- **引入有复杂度 / 可扩展性诉求的新功能：先做「业界方案」设计，再 propose**。方法四步：① 在代码里坐实现状（现有实现 / 约束 / 痛点，带 `文件:行`）→ ② 多角度梳理业界成熟设计模式并映射到本系统 → ③ 综合出一套健壮 + 可扩展的设计 → ④ 一道对抗性评审（防过度设计、查约束违背与失败模式）。这一步可用多 agent workflow 编排（范例：2026-06-19 watcher / 通知监控设计）。产出设计后再落成 openspec change；务实优先、按 YAGNI 砍超前抽象、留干净扩展缝。
- **实装前**：先 `openspec list` 看状态，再读 `openspec/changes/<active-change>/tasks.md` 定位当前 task；不凭空起 task。apply 流程靠 CLI 取上下文（`openspec status` / `openspec instructions apply --change <name> --json` 拿 contextFiles 与进度），不要硬编码文件名。
- **实装中**：代码改动落对应 sub-repo（edge / cloud）；`tasks.md` 进度回写本仓，按 sub-repo 分节（如 `## 1. aidcp-cloud — …`）。
- **实装后**：用 HTML 注释把 task 标 `[x]`，写清 commit-sha / 偏离说明，格式 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。
- **完成全部 task → `openspec validate <change> --strict` → archive**（archive 时 `changes/<change>/specs/` 的 delta 合并进 `openspec/specs/`，归档目录按 `<YYYY-MM-DD>-<change-name>/` 命名）。
- **现状指针**（接手时先核对；**fleet 高度活跃，任何硬编码计数都会滞后——一律以 CLI live 为准，不要相信正文里的快照数字**）：活跃 change 跑 `openspec list`，已合并 spec 跑 `openspec list --specs`（2026-07-14 实测 97 个、随归档增长），最近归档目录见 `openspec/changes/archive/`（按 `<YYYY-MM-DD>-<name>/` 命名，最新一批为 `2026-07-13-*`）。**下一批清账清单现成**：`openspec list` 里已 ✓ Complete 但未归档的 change 即候选（2026-07-14 有 8 个）。**勿手改 `openspec/specs/`，新功能一律走 change 流程**（archive 时其 `specs/` delta 自动并入主 spec）。清账节奏：landed+deployed 的 change 攒批「分诊清账」归档，真机验收项解耦收拢在 `docs/real-machine-acceptance-backlog.md`（按共享真机环境聚成「簇」）。历史锚点：`implement-deepread-lineage`（详情页深读：`profile.open` 协议 / `DeepReader` 真实看图 / `comment_reviewer` 实体化 / 修 `FollowAgent` 假 0 粉丝）于 2026-06-18 归档。上一次大规模清账 2026-07-11：归档 31 个 landed+deployed change、真机项归并入 backlog（含新簇 59），另有 5 个因另有门槛（部署待核 / 依赖未落 / spec delta 待理顺）留活跃、1 个（`facebook-scheduled-comment`，target-URL 设计已被取代）已废弃删除，见 backlog 顶部清账清单。
- **统一自动化运行模型已撤出计划（2026-07-30 用户裁定），其「以本方案为准」的授权同时失效。** 原 change `add-managed-automation-runtime`（111 项、零开工）已移到 `docs/design/managed-automation-runtime/`，**不再出现在 `openspec list` 里，不再是任何工作的前置或阻塞**；后续由用户本人重新立项。
  - **随之撤销的旧口径**：2026-07-25 那条「重叠处以本方案为准」**不再有效**；动 publish / comment / browse / 排期 / 风控配额 / 仲裁 / 客户投影 类 spec **不再需要**先去查它的 §24 处置映射表。**已上线规格重新是唯一权威。**
  - **撤出不改变任何生产行为、不丢任何已上线保证**：它零开工、一条 delta 都没落，而它自己的规则本来就写着「取代不得先于对应 delta 生效」。那份设计里所有「取代 / 收编」表述现在都只是设计意图、零约束力。
  - **重新立项时别重做的**：§24 那张约 60 份能力的逐条处置映射表（实读规格得出，成本很高；且早先 72 条取代主张已有 63 条被推翻改判为「收编」，表里是修正后的口径）、§24.2 的四条待裁决冲突、§24.4 两条已具名放弃的保证。索引见该目录 `README.md`。
  - **不随本次撤出取消的**：边缘侧「页面身份复核 / 动作后验证 / 诚实回执」那批缺口，用户已裁定继续做——它们是边缘本该有的行为，与这套运行模型是否立项无关。

## 4. 测试（中控触发，落 sub-repo 执行）

> sub-repo 须先存在于本机（见 §0）。

- edge：`cd ../aidcp-edge && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- cloud：`cd ../aidcp-cloud && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- **回归纪律**：任何协议 / 风控 / 发布改动后，**先 `npm run test:acceptance` 再全量 `npm test`，再 `npm run typecheck`**。安全红线必须全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、`AC-RISK-*`（绝不自残、被禁 `record` 返 false）；`AC-E-*` 为端到端。**发布审批信号文件已不是跨服务契约（2026-08-05 据实修订）**：`/tmp/aidcp-publish-approve-<requestId>.json` 那一套现在是**本机开发夹具**——边侧 `src/publish/approval-gate.ts` 已加显式启用门（同时要求 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 与 `AIDCP_DEV_PUBLISH=1`，否则立即返回未授权，绝不静默通过），且该文件**已从生产 `dist` 剪除**；**生产人审在云端完成**（持久审批记录 + 客户端内审批，见 change `publish-approval-signal-to-database` 的 6.1 / 6.2）。改发布链时按云端审批记录对账，不再按这个文件路径对齐两端。真机层 gated：dev 用 `AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test`，ol 用 `AIDCP_CLOUD_URL=ws://123.56.253.183:8787`。
- 本地只做**代码级验证**；cloud 正式运行只在 ECS，本地**不要起 cloud**。

## 5. 部署（云端 ECS，带安全闸）

> **部署铁律**：cloud 只跑在命名 ECS target，本地永不起 cloud；edge 本地跑并显式连接 dev 或 ol。dev=`ws://121.89.85.150:8787`，ol=`ws://123.56.253.183:8787`。当前权威口径见 `docs/deployment-environments.md`。
> **同机另有 `isales` 独立运行 —— 任何 ECS 操作绝不能碰它**（不同 systemd 服务 / 目录 / 端口）。
> 执行前先做 §0 私钥与 sub-repo 检查。

- ECS 上 cloud：`/opt/aidcp/cloud`，由 systemd `aidcp-cloud.service` 托管，对外监听 `8787`；panel API 默认 `127.0.0.1:8090`。DEV/OL 长期共用数据库，异步任务按 §2 的 target 规则隔离。
- 部署**默认直接做、不用逐次问**（用户长期授权，2026-06-27）；开发完成后默认 target=`dev`，代码/产物验证、提交、推送完成后自动部署 `dev`。`ol` **不参与默认部署**，只有用户明确提出线上/OL部署时才执行；执行前必须建立或选定 `release/<日期>-<范围>` 这类发布分支，并按该发布分支部署。无论目标是 `dev` 还是 `ol`，都必须严格走安全序列：① 明确 target 并 `scripts/deploy-target <dev|ol> --check` → ② sub-repo 测试通过 → ③ ECS **先备份**（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ ④ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ ⑤ `systemctl restart aidcp-cloud.service` → ⑥ healthcheck（`active (running)` + 8787 监听 + 飞书长连接已建立/或明确禁用 + PG `select 1`）→ ⑦ 失败即回滚。**红线不变**：绝不碰 dev 同机 isales。
- SSH：先用 `scripts/deploy-target <dev|ol> --check` 取目标信息。当前流程见 `docs/deployment-environments.md` 与 `aidcp-cloud/docs/deployment-ecs.md`；历史 handoff 只用于追溯，不作为部署指令。

### edge 桌面客户端打包红线（Electron / asar）

> 这类 bug **只在打包版暴露，本地 `electron .`、`npm run typecheck`、单测都抓不到**，最容易一路发到运营机才现形。改 `aidcp-edge/src/electron/**` 的任何进程启动前必看；权威细节在 `aidcp-edge/CLAUDE.md`「打包红线」。

- **spawn 的 `cwd` 与入口路径绝不能落进 `app.asar`**。打包态（electron-builder 默认 `asar:true`）下 `app.getAppPath()` 返回的是 `.../Contents/Resources/app.asar` 一个**文件**、非目录；把它当 `child_process.spawn` 的 `cwd`，macOS 直接抛 `spawn ENOTDIR`，核心子进程根本起不来、指纹浏览器无法启动。本地 dev 因 `appRoot` 是真目录不触发——所以是纯打包态回归。
- **守卫**：核心 spawn 用 `appRoot.endsWith('.asar') ? path.dirname(appRoot) : appRoot`（`dirname` = `Contents/Resources`，历史可跑通值）。新增任何子进程启动点照此守卫；不传 `cwd`（继承主进程 cwd、绝非 asar）的才安全。
- **打包类修复必须 forward-port 到 `master`**：本 bug 曾修于签名分支 `codex/edge-macos-developer-id-signing`（`20d3784`）却没合回 master，`0.3.5` 又把 regression 打包发出（复修 edge master `3f578b9`，版本抬到 `0.3.6`）。只活在 feature 分支的打包 fix，一到 master 发版就复发。
- **发版前先在本机跑一遍打包产物**（起一次编译后的核心、确认能走到云端连接 / AdsPower 调用），别把 cwd / asar 类回归留给运营机。桌面发版流程见 `aidcp-edge/docs/release-desktop.md`。

## 6. git / 沟通 / 安全边界

- **默认主动 `git commit` + `git push` 到 origin，并自动部署 `dev`**（本仓 + sub-repo 都适用），推各仓默认分支（本仓 `main`、edge/cloud/console `master`）。**提交 / 推送 / dev 部署都不需每次问**（用户长期授权，2026-06-27；部署安全序列与红线见 §5）。`ol` 部署必须等用户明确要求，并从发布分支执行。commit message 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。**仍需先确认**：force-push、非 fast-forward、推到非默认 protected branch。
- **提交 / 推送 / 部署必须用干净 worktree 做最终确认**：代码改动提交推送后，若当前工作区存在任何无关改动，或处于多任务并行场景，必须从目标提交新建 clean worktree（或等价 `git archive HEAD` 快照）运行部署闸与打包；严禁从脏共享工作区直接 `rsync` / 打包上线，避免把未提交 / 他人改动混入生产。部署仍只从默认分支目标提交的快照走，worktree 用于验证与产物生成，不作为长期开发主干。
- **发布分支（OL）上的任何改动，落地时必须同时回流主干（铁律，2026-07-14 用户定）**。发布分支是「已上线」的，主干是「将上线」的：修复只落在前者，等于给一个必然到来的未来埋一颗一模一样的雷，而且没有任何机械手段会提醒你（控制仓对这些 sha 全文 grep 零命中）。**代价已付过两次**：`210f386`（人设弹窗竞态）只活在 `release/20260712-ol-recut`，用户跑的 master 客户端从来没拿到它 →「修了几次还复发」（见 §2 的三态修复）；打包 spawn cwd/asar 的 fix 只活在签名分支 → master 发版把同一个 regression 原样打包发出（见 §5「打包红线」）。
  - **验收口径是「主干上有等价行为 + 有测试覆盖」，不是 patch-id 相同**：cherry-pick、冲突解决、在主干新代码上重新实现，都算完成。`git cherry` 的 `+` 只是线索不是判决（本次 `5ee9d2d` 就必须重新实现——它叠在被取代的 `210f386` 上，与主干新的人设三态闸 9 处冲突）。
  - **回流不成必须当场登记**（tasks.md + backlog，写清 sha 与原因），绝不静默留在发布分支上。
  - **唯一例外＝发布态工件指针**（安装包版本号、下载页指向哪个包）：那是「哪台机器上放了哪个包」的部署状态、不是代码，照搬会让主干指向另一台机器上并不存在的产物。必须显式对账，但不得机械照搬。
  - **切下一个 release 分支前**，先 `git cherry -v origin/master origin/release/<上一个>`，凡 `+` 逐条给出「已回流 / 已被取代 / 工件指针」的结论。
- **打 edge 桌面安装包默认不做（用户长期授权，2026-07-08）**：`electron:build` / `electron-builder`（含 `electron:build:mac` / `:win`）要调用远程 GitHub 服务 + 苹果签名 / 公证、耗时长，**默认一律不打包**；只有用户明确要求「打安装包 / 出包 / 发版」时才执行。edge 代码改动的默认收尾只到 `commit` / `push`（+ 必要时 `dev` 部署与 `typecheck` / 测试），**不含出安装包**；打包属用户显式触发的动作，不进自动收尾。
- **语言**：正文默认中文；代码 / 注释 / commit / PR / 命令 / 文件名保持英文。
- **问题 / 方案的说明方式（默认模式，用户偏好）**：讲逻辑、不用比喻；不点代码内部标识符（变量 / 类 / 函数 / 消息类型名），改用**功能性正文**描述组件与机制（如「执行端 / 决策端 / 监测体」「发命令给执行端的统一出口」「阻塞式 vs 临时离开式打断」）；分点、句子短、让非工程视角也能跟上；确需落到代码时再补具体 `文件:行`。
- **不记敏感值**：文档 / 提交 / tasks.md 里不写任何 PostgreSQL 密码 / token / 私钥内容，只记路径、服务位置、命令用法、配置读取方式。
- **每次对话收尾给一段「说人话」的总结**：用非技术语言讲清楚——这次做了什么、对系统有什么影响、下一步是什么。技术细节照常给，但总结那段要让非工程视角也看得懂。

## 7. 并行开发规范（多 Claude session / git worktree）

以多个并行 session 同时开发时（用户编排 5–8 个）按下列铁律，防版本错落。这是从「多 session 共用同一子仓工作树」（现状：push 撞 non-ff、脏文件成常态）向「每 change 一个 worktree」的迁移；迁移期两态并存，共享工作树处仍守末条 rebase 纪律。**单个 session 只需守自己这一段；「5–8 条流串行集成」是用户在 fleet 层协调的性质，单 session 强制不了。**

- **一个 session = 一个 openspec change = 一条分支 = 一个 worktree，四者同名**；worktree 放 `../<repo>.wt/<change-name>`。控制仓 aidcp 的 change 是 additive 目录、近零冲突，可不开 worktree、在主 checkout 各写各的 change 目录——**但这里「共用主 checkout」永远指「在主 checkout 的默认分支（aidcp=`main`）上直接写 additive 目录」，绝不指切分支**。
- **四个 canonical checkout 的分支指针都永远停在各自默认分支（铁律，2026-07-11 加、2026-07-13 扩到 sub-repo）**：`aidcp`=`main`，`aidcp-edge` / `aidcp-cloud` / `aidcp-console`=`master`；**绝不在其中任何一个里 `git checkout <feature>` / `git checkout -b`**（含**切 OL 发布分支**——2026-07-12 的事故正是 canonical `aidcp-edge` 被切到 release 分支停了 24h，导致本机跑桌面客户端时执行的是 OL 发布树），要分支隔离就另开 worktree。`main` 只能活在主 checkout，**绝不许被任何 `.wt/<change>` worktree 蹲占**。**起手自检**：每个 session 第一步 `git -C /Users/baitianxing/codes/aidcp branch --show-current`，不等于 `main` 即红灯——先还原（安全时）或另开 worktree，别在错位的主目录里开工。**事故实例**：本次接手时主 checkout 被前一 session 切到 `codex/remote-captcha-assist`（其使命早已在 origin/main 归档）、`main` 反被 `aidcp.wt/publish-queue-stage-overview` worktree 蹲占，主目录悄悄落后 origin/main 163 提交、无人收尾；根因即「在主目录直接 checkout feature 分支」+「把 main checkout 进 worktree」两步错位。**若确需还原错位的主 checkout**：等占用它的并发 session 收工、腾出被蹲占的 `main`（先清孤儿 worktree），再 `git checkout main` + `git merge --ff-only origin/main`；碰共享状态，先与用户 / fleet 协调，**绝不 `-f` 硬切抹掉他人 WIP**。
- **四道守卫防漂移**：① 法条＝本节上面两条；② **git `post-checkout` 守卫**（版本控制在 `scripts/git-hooks/post-checkout`）——主 checkout 一离开 main 就当场告警，工具无关（Claude/Codex/手动 git 都触发）；③ **Claude `SessionStart` 守卫**（`.claude/settings.json` + `.claude/hooks/check-canonical-main.sh`，随 main 自动分发）——起 session 时查主目录分支、漂了就报；④ **任务准入硬门禁 `scripts/task-preflight`（2026-07-13 加，唯一会 exit 1 拦停的一道）**——`scripts/new-change` / `scripts/spawn-change` 在建 / 复用 worktree **之前**强制先跑，检查**四个 canonical checkout 是否都停在各自默认分支**（aidcp=`main`，edge / cloud / console=`master`），发现非默认分支 / detached / canonical 目录被 linked worktree 蹲占即 exit 1。它**只读、不自愈、无绕过参数**（不切分支、不 stash、不删 worktree），只能由人先把发布 / feature 工作挪进 linked worktree 或还原默认分支。**三条必须知道的性质**：(a) 它是 **fleet 全局**的——任一仓漂移会拦下**全部四仓**的新任务，所以切 `release/<日期>-<范围>` 发布分支（OL 上线 / 签名出包）**必须在 linked worktree 里做，绝不在 canonical checkout 上 checkout 发布分支**；(b) 它只挂在 `new-change` / `spawn-change` 两个入口——`/impl` 的「worktree 已存在则直接复用」路径、手动 `git worktree add`、`land-change` / `deploy-target` / `release-desktop-macos` 都**绕过**它；(c) 从控制仓 worktree 或拷贝里跑它，四仓会全部 SKIP 并报 `no canonical repositories are available`（看着像工作区坏了，其实是 cwd 不对）。**它的诱因是真事故**：canonical **aidcp-edge** checkout 被切到 OL 发布分支停留约 24h，本机跑 Edge 桌面客户端时执行的是 OL 发布树而非带 Facebook 的默认分支——② ③ 两道守卫**只看控制仓、且只告警**，对 sub-repo 漂移完全无感。**git 钩子需一次性激活**：新 clone 跑一次 `scripts/install-git-hooks`（additive 拷进 `.git/hooks/`、**绝不碰公司 pre-commit 扫描器**；git 安全设计下 clone 不自动装钩子）；worktree 共享 hooks 目录，装一次覆盖全部。SessionStart 守卫首次加入后需开一次 `/hooks` 或重启 Claude 才生效。
- **用手动 `git worktree add` 到子仓（`scripts/new-change`），不用内置 `EnterWorktree`/`ExitWorktree`**：内置只作用于当前（中控）仓、会切走 session cwd、且不纳管手动建的 worktree——不合本项目「中控仓驱动、代码落子仓」的多仓模型（详见手册 §1）。
- **被指派 change 即为 fleet 成员**：session 若经 `scripts/spawn-change` 启动、或用户直接说「实装 change X」，即独占该 change，按本节自主走全流程（读 change 文档 → worktree 开发 → `land-change` 集成 → tasks.md 回写 → 真机项登记 backlog → 部署前探 ECS → archive），无需逐步征询。
- **极简启动（用户多终端并行的标准入口）**：新终端在本仓起 claude 后，`/impl <change名>` = 指派实装；`/claim` = 自主认领一个无人在做的活跃 change（**worktree = 认领锁**：建 worktree 失败即被并发抢先、换下一个；先报出所选再开工，不等确认）。命令定义在 `.claude/commands/`，指令自包含，用户无需再输入任何交代。
- **先判定自己在哪**：`git worktree list` / `git rev-parse` 认清是「主 checkout」还是某 change 的 worktree。worktree 内 = 只在本分支开发 + 提交 + 跑 `test` / `typecheck`；主 checkout = 集成与部署位。
- **部署只从主 checkout 的 eligible ref 走，绝不从任何 worktree 部署**（dev 用验证后的默认分支；ol 只用用户要求的发布分支，tag / clean SHA 只能作为创建发布分支的来源，不能直接替代分支部署）。
- **热点文件单写者，并行时绝不同时碰**：两份 `protocol.ts` + `aidcp-cloud/src/comm/command-bridge.ts` 动作映射（§2 协议四处同步）、角色注册（`event-bus/types.ts` 的 `RoleName` + `src/config/role-catalog.ts`）、风控状态机 `src/risk/risk-state-machine.ts`。任务若必须动这些，标记为需串行、不与他人并行。
- **开发并行、集成串行**：合回默认分支前先 `fetch` + rebase 到最新默认分支、解冲突、跑 `test:acceptance` + `typecheck` 再 ff 合并。**push 遇 non-ff 一律 rebase 后重来、绝不 force**（force / 非 ff 仍按 §6 需先确认）；空 diff = 已在远端、可弃（见 memory `concurrent-session-shares-subrepo-worktree`）。
- **完成即收口**：部署 + 验证通过 → archive 该 change → 删 worktree / 分支。有 worktree 却无对应活跃 change = 孤儿，清掉。
- 操作手册（开流 / 集成 / fleet 状态命令、helper 脚本）见 `docs/parallel-dev-worktrees.md`。**该手册的命令序列 / 脚本经实战跑通验证后方视为定稿**；未验证前只把本节不变量当 OVERRIDE 法条。

## 8. 云端多仓事实源（2026-08-06 翻转后模式 · OVERRIDE）

> **事实源已翻转**（change `invert-split-fact-source`，用户点火，冻结点 cloud@`2d34e06`）：
> `aidcp-api` / `aidcp-automation` / `aidcp-content` / `aidcp-kernel` / `aidcp-transport`
> **各自是自己代码的唯一事实源**；`aidcp-cloud` 已删除全部 `src/` 与 `migrations/`，
> 身份＝**整图集成测试仓**。重放（`sync-split-repos --apply`）已双重封死
> （翻转标记 `scripts/fact-source.json` + 「cloud 无 src 即拒绝」的硬封），
> `task-preflight` 拦任何 cloud 侧源码回潮。

### 8.0 身份与部署

- **cloud MUST NOT 部署到任何环境**（它已无可运行代码；两环境 systemd 单体 unit 均 disabled）。
  回滚走**逐服务备份**（`docs/deployment-environments.md` 的 Rollback 节），MUST NOT 以单体为回滚路。
- **cloud 仓 MUST NOT 再进任何业务源码**。它只收：跨属主 / 整图测试（`test/`）、测试基础设施、冻结史料。
- `boundaries/` 是**冻结史料**（见其 `FROZEN.md`）：测试仍按原路径读它做属主查表，但它不再驱动任何同步。

### 8.1 日常改动怎么落

- **业务代码 → 属主派生仓**。逐文件属主查 cloud `boundaries/module-ownership.json`（冻结快照）或
  控制仓 `docs/cloud-service-decomposition-proposal.md` §4.7；常见：`comm/ orchestrator/ agents/` →
  automation，`panel/ client-auth/ feishu/` → api，生成 / 发布管线 → content。
- **新迁移 → 属主仓 `migrations/`，编号取三仓并集的下一号**（集成仓的并集编号测试兜底撞号；
  同名副本必须逐字节一致——校验和断言会拦分叉）。已应用迁移字节不可改，规则不变。
- **跨属主 / 整图测试 → cloud `test/`**。编译期用别名 `@api/* @automation/* @content/* @kernel/*`；
  运行时数据读取走 `test/helpers/sibling-repos.ts`（找不到兄弟仓响亮失败）；迁移并集走
  `test/helpers/migration-union.ts`。**硬前置：四个兄弟仓已 clone 且各自 `npm ci`。**
- **协议 v2 两份一致**的边云配对现在是 **edge ↔ automation**（`AC-PROTO-*` 在集成仓跑）。
- 各派生仓的组装根（`src/server.ts` / `src/index.ts` / `src/<svc>-*.ts`）是手写主交付物，无同步、无重放。

### 8.2 共享包版本化（kernel / transport）

- 派生仓钉 **annotated tag**（`git+ssh://…#v<x.y.z>`，自 `v0.1.0` 起）；kernel / transport 一有改动就出新 tag。
- 检查器（`sync-split-repos` 只读模式）认 `git+ssh://` 与 `github:` 两种写法，认不出＝报错；
  落后最新 tag **只报告不拦**——升级是各仓自己的节奏。
- **kernel 准入原则不变**：零副作用（无模块级活状态 / 定时器 / 连接池）、MUST NOT import 业务层、
  不放行为类；**transport 准入＝三家都可能调 + 零属主表 SQL**。
  ⚠ 机器闸换家未完成：原 `KERNEL_ADMISSION_CHECKS`（在已退役的 cloud 整图边界测试里）尚无新家，
  再收 kernel 成员前先在 kernel 仓补准入测试（登记于 change 5.7 递延项）。

### 8.3 红线的多仓形态（防「静默假成功」，全部仍然有效）

- **跨段前向引用走响亮取用闸**（`crossSegment`），MUST NOT 裸 `ctx.X?.…` 把缺席吞成成功。
- **一个域绝不直连另一个域的数据库**；本进程只对本属主库开池，启动期断言两个方向都拦。
- **跨进程 `instanceof` 恒 false**：错误识别用结构化守卫（`name` + 具名字段）。
- **依赖 / 引用审计必须算动态 `import()`**。
- **同一契约类跨仓有两份运行时拷贝是常态**（别名读 src、包依赖读 dist）：测试的身份断言
  MUST 对准被测方真正解析到的那份拷贝（先例见集成仓 5.3 各桶提交）。
- **边界执法在各仓自己的扫描器**（automation 侧实现为准，双仓 parity 闸护漂移至 5.7 结构性收口）；
  跨仓边看控制仓 `scripts/boundary-census`。
