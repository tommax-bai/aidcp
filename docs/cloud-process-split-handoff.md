# Cloud 拆进程 · Session 交接（Block ② 2d 进行中）

> 2026-07-24 写。给下一个 session 冷启动接手用。上位设计见 `docs/cloud-process-split-design.md`，接缝地图见 `docs/cloud-decoupling-seam-inventory.md`，路线图见 `docs/cloud-decomposition-roadmap.md`，执行记忆见 memory `cloud-decoupling-execution-progress`。**本文件只记「当前 checkpoint + 下一步怎么接」**，不重复设计。

## 一句话现状

Block① 代码解耦已到地板（跨边界 import `frozenTotal` 266→**101**，全 land+dev、行为零变更）。Block② 拆进程：2a 传输原语 + 2b 数据网关已 land+dev。**2d 拆 content 进程的第一刀 impl 刚做完（在 worktree，未 land）**，暴露一个关键真实约束（见下）。Block③ 物理拆库仍 gated，不碰 ol 生产。

## 当前代码位置（务必先对齐）

- cloud `origin/master` = **87b3429**（`block2-content-process-split: add multi-process run modes via AIDCP_SERVICE`）。frozenTotal = **101**。
- **2d 第一刀已 land + dev 部署 + 冒烟绿（2026-07-24）**：worktree 已清、分支已删。dev `/opt/aidcp/cloud/.deploy-sha` = 87b3429，启动路径 main() 改后进程照常开机（active + 8787 监听 + 飞书长连接 onReady + config-mirror 变化=0）。verify verdict = **clean、零缺陷**（命门 monolith 逐字节等价独立复跑坐实：`env -u AIDCP_SERVICE npm test` 3155/3155 绿）。
- impl/verify 全量结果留存：工作流 journal `.../subagents/workflows/wf_d80fd710-677/`（journal.jsonl + agent-*.jsonl）+ 任务输出 `.../tasks/wwpc9jc10.output`。docpatch 在 `scratchpad/docpatch-content-split.md`。

## 2d 这一刀做了什么（87b3429）

给 `server.ts` 的 `main()` 加了环境变量 `AIDCP_SERVICE` 三模式（一套代码、多入口，不是三仓）：

- **monolith（默认 / 未设 / 未识别值）**：四段全跑（segA→segB→segC→segD），无新监听，网关默认 local。**逐字节等价**——这是唯一不可破的不变量。
- **content（`AIDCP_SERVICE=content`）**：跑 segA+segB、跳 segC/segD；起 InternalHttpServer 在 `127.0.0.1:(AIDCP_CONTENT_PORT ?? 8092)`，只服务它拥有的 curated-content 读端点。
- **core（`AIDCP_SERVICE=core`）**：跑 segA+segC+segD、跳 segB；配 `AIDCP_GATEWAY_MODE=http` + `AIDCP_GATEWAY_BASE_URL` 指向 content 进程时，curated 读走 DataGateway 的 HTTP client。

**新增文件**：`src/gateway/service-mode.ts`（零 import 的纯模式选择器，被 server.ts 单独 import，好让单测不触发 main() 启动整进程）+ `test/gateway/service-mode.test.ts`。**改动文件**：`src/server.ts`、`boundaries/module-ownership.json`（service-mode.ts 按 src/gateway/ 的 inherit=api 自动归属，frozenTotal 不变）。

**绿灯证据（impl 亲跑）**：`npm run typecheck` EXIT=0；`npm test`（默认 monolith）3155/3155 pass、10 skip（历史环境门）、58.5s；service-mode + module-boundary 单测 22/22；frozenTotal 101→101。热文件零改动，无新 npm 依赖。

## ⚠️ 关键真实发现（决定下一步）

**core 进程现在起不来，是开机崩、不是运行路径坏。** 原设计假设「segB = content only」是错的：实测 **segB 还构造了 ~34 个共享地基对象**，segC/segD 在**构造期**就硬依赖它们。跳过 segB 起 core = 启动即崩。

这 ~34 个共享地基对象（都在 segB 里，但本质是「共享地基」不是 content 私有）：
`eventBus, accountStore, accountState, accountDisplayName, accountDisplayNameCandidates, personaStore, personaPanel, personaAutoFillStore, resolvePersona, getSoul, imageProvider, anyImageKeyPresent, conceptStore, curatedContentStore, delegatedTaskService, delegatedTaskStore, postProcessor, publishOrchestrator, approvalPolicyStore, groupRouteStore, interactionFeedStore, likedNoteStore, lastObservedNoteByAccount, firstPostOnboardingStore, facebookPublishMediaStore, notificationContactStore, manualCommentAccounts, valuableCommentStore, onCommentTakeoverStart, onCommentTakeoverEnd, resolveAccountChatId, resolveCardChatId, resolveEffectiveCommentApprovalMode, resolveReviewCardDelivery`。

impl 特意**没硬拆**这块（大改、会威胁 monolith 等价），只铺骨架 + 把后果如实列进 brokenPaths。**这是正确的克制。**

其余 brokenPaths（同样如实留后补）：① content 进程里 segB 对象惰性读 segC/segD 实例（publishScheduler / uiSnapshot / runtimes / postProcessor / publishOrchestrator…）→ undefined，content 的生成/发布运行路径坏，只有它自己的 curated 读端点能用；② core 里未经 gateway 的 content 直依赖消费者仍 undefined（2b 只收口了 curated 读一侧，写/生成侧跨进程传输未建）。

## 下一步（给新 session 的明确剧本）

**第 0 步 ✅ 已完成（2026-07-24 land + dev 部署 + 冒烟绿）**：monolith 安全骨架已在 master（87b3429），dev 已部署、进程照常开机。新 session 无需再做，直接从第 1 步接。

**第 1 步（真正的下一大刀，值得新鲜上下文）：把共享地基从 segB 抽到 segA。** 把上面 ~34 个对象的构造从 segB 移到 segA（segA = 基础段，content 和 core 都跑它）。移完 segB 只剩「真 content 私有」的构造（发布管线、洗稿、精选、配图）。这一步**必须守 monolith 逐字节等价**（移动构造顺序时零重排、`ctx.X` 惰性读那套已经把构造环断了，照它做）→ 全量 npm test（monolith 路径）应全绿。做完 core 才能开机，两进程 dev 才跑得起来。**建议用 impl→对抗verify→repair 工作流编排**（命门就是 monolith 等价），参考 `scratchpad/wf-content-split.js` 的结构。

**第 2 步**：dev 上真起两进程验证——一个 core（`AIDCP_SERVICE=core` + gateway http 指向 content）、一个 content（`AIDCP_SERVICE=content`）。验证 core 经 HTTP 网关读 content 的 curated 数据通。坏的路径（content 生成/发布侧跨进程传输）如实记、后补。

**第 3 步（2e）**：三仓 + kernel 抽共享包 + deploy-target 多服务化。

## 一直有效的红线 / 约束（务必带走）

- **速度第一、可承担风险、过程中 dev 受影响可接受**（用户 2026-07-24 反复强调）。批量收口测试:每刀只 typecheck + 模块单测,整批末尾跑一次全量。
- **monolith 默认逐字节等价 = 唯一不可破不变量**（改 main() 的命门）。
- 提交/推送/dev 部署长期授权,不用逐次问;**ol 部署只在用户明确要求、从发布分支走**。commit 末尾 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
- **canonical checkout 永远停默认分支**（aidcp=main, cloud=master）;分支隔离一律用 worktree。**绝不 git add -A**。部署只从干净 `git archive HEAD` 快照 + 先备份。**dev 同机 isales 绝不碰。**
- **热文件单写、绝不并行碰**:两份 protocol.ts、command-bridge、event-bus/types RoleName、role-catalog、risk-state-machine、src/risk 内部。
- **kernel 准入门禁**（AC-BOUND-03,比机械纯净严）:kernel 文件禁 SQL 字面量 / HTTP-fetch / LLM 供应商标识符（含 `LlmClient`/`ChatLlmClient` 名字）/ 模块级 `new Set`·`new Map`（活状态）/ `setTimeout`（定时器）。
- **Block③ 拆物理库 gated**:碰 ol 生产,只做逻辑准备、不动物理库,等用户拍板从发布分支走。
- 已登记真机 backlog（本轮别顺手做）:① dev 迁移账本整个未 baseline;② 建议把 `scripts/` 纳入 typecheck（现只 src/+test/,曾漏掉搬 pg-config 后的脚本崩）。

## 说人话总结

- 拆进程第一刀写完了:给云端加了个「开机模式开关」,默认那档跟现在**一模一样**(全量测试全绿),另外两档是拆开后的 content 和 core 进程。
- 但试出一个真问题:**core 那档现在开不了机**——因为原本以为「只管内容」的那段,其实还顺手搭了 34 个大家都要用的地基,把它跳过,core 就塌了。
- 所以下一刀很明确:**先把这 34 个地基挪到公共段**,content 和 core 才都能拿到、core 才开得了机。这一刀值得新 session 用新鲜脑子做。
- 交接文档已写好(就是本文件),记忆也会更新。新 session 照「下一步剧本」接着走即可,不用回头问。
