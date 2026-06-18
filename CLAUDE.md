# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 本仓 `aidcp`（仓库根 `.`）是 **aidcp\* 家族的中控 / 总览仓**：契约（架构 / 协议 / 产品设计）在这里定义，后续开发、测试、部署在这里**触发与编排**，走 **openspec** spec-driven 流程。本文件约定 OVERRIDE 默认行为。
>
> **本仓只承载文档与契约（`docs/` + `openspec/` + `README.md`），不含业务代码、无构建链**。root `package.json` 只有一个占位 `npm run docs`（echo），本仓根目录跑 `npm test` / `build` / `lint` 会失败——这些都在 sub-repo 里跑。与本仓相关的唯一可执行校验是 `openspec validate <change> --strict` 与 `openspec list`。

## 0. 路径与环境前置检查（务必先做）

三仓为**同级目录**：本仓即 `.`（cwd = 仓库根），sub-repo 用相对写法 `../aidcp-edge`、`../aidcp-cloud`（文档里历史遗留的 `ai-dcp`、`/Users/bears/codes/…` 均为换机前旧值，正文已统一，勿再产出）。

- **edge / cloud 两个 sub-repo 可能未在当前机器 clone**（中控仓只承载文档与契约）。涉及 edge/cloud 代码、测试或 ECS 部署前，**先 `ls -d ../aidcp-edge ../aidcp-cloud` 确认是否存在**；缺失则停手，向用户确认实际位置或先 clone，**绝不盲目照搬路径执行命令**。
- **部署私钥 `~/codes/isales-4.pem` 可能未在当前机器**。执行任何 `ssh` / `rsync` 到 ECS 前，**先确认私钥存在且 `chmod 600`**；缺失则停手告知用户。

## 1. 三仓关系

| 仓 | 路径 | 默认分支 | 角色 |
| --- | --- | --- | --- |
| **aidcp**（本仓，中控） | `.` | `main` | 契约 / 文档 / openspec changes / 测试与部署编排 |
| **aidcp-edge** | `../aidcp-edge` | `master` | 边缘端：CDP / 定位 / 浏览 / 拟人化 / 反检测 / 发布 / Electron |
| **aidcp-cloud** | `../aidcp-cloud` | `master` | 云端：协议 / 事件驱动编排 / 风控 / 发布 / 概念池 / 飞书 Bot |

中控仓定义契约与变更；代码改动落到对应 sub-repo，进度回写本仓 openspec change。edge 与 cloud 经 `docs/protocol.md` 定义的 **WebSocket 协议 v2** 通信。

## 2. 架构大局（需跨文件才能拼出的上位约束）

改动前先判断「落 edge 还是 cloud」，依据这几条铁律（权威文档：`docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md`）：

- **边轻云重 + 状态单写**：原子操作（click / input / scroll）**永远只在边缘**；规划 / 选元素 / 编排 / 风控 / 持久化全在云端。账号风控最终状态**只由云端 `RiskController` 单写**（状态机 `normal→warned→restricted→frozen`，类在 `src/risk/risk-state-machine.ts`），其他系统只提交事件 / 读投影、不得改写最终状态。
- **红线反模式：MUST NOT「静默假成功」**（贯穿全部 5 个 spec 的核心不变量，自愈不自残）。找不到目标报 `no_target` 而非 `ok`；按实测位移 / 真实数量如实回报（不再 `count||1`）；坏页 / 404 不静默吞；数据缺失不得误判为低质量。新写 edge 动作或 cloud 决策默认遵守。
- **DOM-first 定位三道闸**（`aidcp-edge/src/locating/engine.ts`，靠 `DomProvider` / `ActionExecutor` 接口让 jsdom 桩 ↔ CDP 实现可换、脱离浏览器单测）：① **后置校验**——操作后必须验证业务结果真发生；② **重试上限 + 升级**——连续失败到顶判系统性改版、停手 `escalated`、绝不静默成功；③ **反污染回写**——LLM 新锚点先 stage 暂存、连续确认成功才晋升主缓存、任一次校验失败即 drop。改动勿破坏这三闸与那两个接口。
- **协议 v2（`PROTOCOL_VERSION=2`）改动须三处同步**：edge / cloud 两份 `src/comm/protocol.ts`（逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts` 的动作↔消息映射（如 `scroll→page.scroll`、`open_note→note.open`、`like→interaction.like`、`back→navigation.back`、`profile_open→profile.open`）+ `docs/protocol.md`。漂移由 `npm run typecheck` 暴露（两份 protocol.ts 用 `Record<MessageType,true>` 穷举，不一致即失败）。**消息类型数以两份 protocol.ts 的 `MessageType` 为准**，`docs/protocol.md` 头部计数可能滞后（如加入 `profile.open` 后头部仍写「41 个」）。**协议表里列出 ≠ 已接线生效**：`anchor.get` / `anchor.report`（云端 PG 主缓存同步）、`risk.canDo` / `risk.record`（风控对浏览闭环实时拦截）等为保留通道、边缘尚未接线——浏览侧约束当前靠云端浏览预算，而非 `RiskController` 实时拦截。
- **云端是事件驱动多 Agent**（已非旧单体 `Planner`）：`RoleDispatcher`（`src/orchestrator/role-dispatcher.ts`）注册 **15 角色** + 进程内 `EventBus` + `SessionContext`，浏览闭环由 `feed.entered` 启动、互动 / 返回后再次 `feed.entered` 往复，直到 `SessionMonitor` 判结束。现役主路径 = v2 事件驱动浏览闭环（`page.cards` / `note.detail` 结构化上报 → 逐动作下发）；`plan` / `anchor` / `select` 每步循环为 v1 兼容路径仍在；边缘 `card-filter` 与协议 `browse.next` / `browse.scroll` 已 `@deprecated` / 被角色驱动的 `page.scroll` 取代，**勿在遗留路径上改代码**。已删除的旧文件别再找：`session-orchestrator.ts` / `state-machine.ts` / `engagement-decider.ts` / `concept-extractor.ts` / `src/blackboard/` / `src/publish/`。
- **节奏系数收口云端**（Command Pacing）：内容 / 状态相关的时长系数由云端一处算出**中心值**，随决策指令以 `thinkMs`（动作前犹豫）/ `dwellMs`（离页前总停留，治「秒退」）下发；**边缘只叠 lognormal 抖动 + 保证停留达标 + 断连兜底**；`session.budget.pacing` 只带极薄兜底（`tempo` / `dwellFloorMs`），不含 read/pause/fatigue 系数。改节奏前先确认改的是云端中心值还是边缘抖动层。**实装边界**：限频配额 `effectiveQuotas()`（保守 / 正常 / 激进三档）已实装；`tempo` 降速旋钮（1.0 / 1.3 / 1.6 放大停顿）与「状态迁移接真实平台封号 / 限流信号」尚未实装，当前迁移靠配额阈值触发（已知缺口）。

## 3. openspec 工作流（spec-driven）

- 全局 CLI 可用（`/opt/homebrew/bin/openspec`，1.2.0，不在 package.json）。常用：`openspec list`（看 change 状态）、`openspec list --specs`、`openspec validate <change> --strict`、`openspec status --change <name>`、`openspec show <item>`。
- 所有跨 spec 的功能改动都走 **openspec change 流程**，不要绕过 openspec 直接改 `openspec/specs/` 下的 spec 文件。
- 新 change：`/opsx:propose "<想做什么>"`（探索 / 实装 / 归档用 `/opsx:explore` `/opsx:apply` `/opsx:archive`）。
- **实装前**：先 `openspec list` 看状态，再读 `openspec/changes/<active-change>/tasks.md` 定位当前 task；不凭空起 task。apply 流程靠 CLI 取上下文（`openspec status` / `openspec instructions apply --change <name> --json` 拿 contextFiles 与进度），不要硬编码文件名。
- **实装中**：代码改动落对应 sub-repo（edge / cloud）；`tasks.md` 进度回写本仓，按 sub-repo 分节（如 `## 1. aidcp-cloud — …`）。
- **实装后**：用 HTML 注释把 task 标 `[x]`，写清 commit-sha / 偏离说明，格式 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。
- **完成全部 task → `openspec validate <change> --strict` → archive**（archive 时 `changes/<change>/specs/` 的 delta 合并进 `openspec/specs/`，归档目录按 `<YYYY-MM-DD>-<change-name>/` 命名）。
- **现状指针**（接手时先核对）：当前唯一活跃 change = **`implement-deepread-lineage`**（详情页深读链路：`profile.open` 协议、`DeepReader` 真实看图、`comment_reviewer` 实体化、修 `FollowAgent` 假 0 粉丝数据）。它已 `✓ Complete`（task 全勾、cloud 已 deployed）但**仍躺在 `changes/` 未归档**——下一步 `openspec validate implement-deepread-lineage --strict` 后 archive；**但 archive 前先确认 edge 真机核对已闭合**（`tasks.md` 8.4 标注「待用户重启本机 edge」，edge 侧实机核对存悬挂，勿过早归档）。已合并 5 个 spec：`browse-loop-resilience`（返回 feed 续刷不死锁、看门狗有界 idle、坏页兜底）、`command-pacing`（节奏系数收口云端 + dwellMs/thinkMs）、`deep-read-fidelity`（评论按实测位移回报、上溯找可滚容器）、`follow-decision`（follow 只用平台真实信号、不用作品数）、`note-extraction-fidelity`（正文跨布局抽取、渲染门与抽取器共用选择器）。

## 4. 测试（中控触发，落 sub-repo 执行）

> sub-repo 须先存在于本机（见 §0）。

- edge：`cd ../aidcp-edge && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- cloud：`cd ../aidcp-cloud && npm test`（+ `npm run test:acceptance`、`npm run typecheck`）
- **回归纪律**：任何协议 / 风控 / 发布改动后，**先 `npm run test:acceptance` 再全量 `npm test`，再 `npm run typecheck`**。安全红线必须全过：`AC-PROTO-*`（两份 protocol.ts 不漂移）、`AC-PUB-*`（未授权绝不静默发布）、`AC-RISK-*`（绝不自残、被禁 `record` 返 false）；`AC-E-*` 为端到端。发布审批信号文件两端契约路径 `/tmp/aidcp-publish-approve-<requestId>.json` 必须一致（edge `buildPublishApprovalSignalPath` ↔ cloud `getApprovalSignalPath`），改发布链时勿漂移。真机层 gated：`AIDCP_E2E=1 AIDCP_CLOUD_URL=ws://121.89.85.150:8787 npm test`。
- 本地只做**代码级验证**；cloud 正式运行只在 ECS，本地**不要起 cloud**。

## 5. 部署（云端 ECS，带安全闸）

> **部署铁律**：cloud 只跑在 ECS `121.89.85.150`，本地永不起 cloud；edge 本地跑、连 `ws://121.89.85.150:8787`。
> **同机另有 `isales` 独立运行 —— 任何 ECS 操作绝不能碰它**（不同 systemd 服务 / 目录 / 端口）。
> 执行前先做 §0 私钥与 sub-repo 检查。

- ECS 上 cloud：`/opt/aidcp/cloud`，由 systemd `aidcp-cloud.service` 托管，对外监听 `8787`，PostgreSQL 同机 `127.0.0.1:5432` 库 `aidcp`。
- 部署是**显式发布动作**（不在每次 commit 自动触发），按安全序列：① sub-repo 测试通过 → ② ECS **先备份**（`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ ③ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ ④ `systemctl restart aidcp-cloud.service` → ⑤ healthcheck（`active (running)` + 8787 监听 + 飞书长连接已建立 + PG `select 1`）→ ⑥ 失败即回滚。
- SSH：`ssh -i ~/codes/isales-4.pem root@121.89.85.150`（私钥须 `chmod 600`）。逐条命令、版本台账详见 `docs/handoff-2026-06-05.md`（顶部最新注记块为唯一可信的现役版本来源）与 `aidcp-cloud/docs/deployment-ecs.md`。

## 6. git / 沟通 / 安全边界

- **默认主动 `git commit` + `git push` 到 origin**（本仓 + sub-repo 都适用），推各仓默认分支（本仓 `main`、edge/cloud `master`），不需每次问。commit message 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。**仍需先确认**：force-push、非 fast-forward、推到非默认 protected branch。
- **语言**：正文默认中文；代码 / 注释 / commit / PR / 命令 / 文件名保持英文。
- **不记敏感值**：文档 / 提交 / tasks.md 里不写任何 PostgreSQL 密码 / token / 私钥内容，只记路径、服务位置、命令用法、配置读取方式。
- **每次对话收尾给一段「说人话」的总结**：用非技术语言讲清楚——这次做了什么、对系统有什么影响、下一步是什么。技术细节照常给，但总结那段要让非工程视角也看得懂。
