# Tasks

> **跨仓：`aidcp-edge` + `aidcp-cloud`（事实源）+ 派生四仓/两包的传导（`aidcp-kernel` / `aidcp-transport` / `aidcp-automation` / `aidcp-api`）。**
> ⚠️ **热点文件、须串行**：本 change 动 `protocol.ts`，属 CLAUDE.md §7 单写者文件。
> **开工前 MUST 重核协议热点是否空闲**（fleet 高度活跃，立项时的结论会过期）。

## 0. 开工前复核

- [x] 0.1 重核协议热点空闲：edge / cloud 两侧**在开分支**（worktree 对应分支，按三点比较 `origin/master...HEAD`）无人改 `protocol.ts` 或动作映射表。**MUST NOT 用 `master..branch` 两点比较**——那会把大量早已合并的旧分支算成占用。
  <!-- 2026-08-06 实扫：edge 43 条在开分支 0 命中；cloud 24 条命中 1 条 = `codex/add-managed-automation-runtime`（2026-07-30 已撤出计划，非活跃占用）；automation 3 条 0 命中。判定空闲。 -->
- [x] 0.2 确认协议副本份数与对账门覆盖范围（当前为三份：edge / cloud / automation；`scripts/land-change` 逐字比对）。份数变了以门禁实跑为准，别抄本文件。
  <!-- `scripts/protocol-parity --list` 实跑：edge / cloud / automation 三份参与；api / content 无自己的副本（SKIP，非漂移）。 -->
- [x] 0.3 复核既有待机提示载荷的字段集合，作为「只增不减」的基线快照写进本文件备注。
  <!-- 基线见本文件 §5.2 备注 A。 -->

## 1. 协议（三处同步 + 文档）

- [x] 1.1 在 **三份** `protocol.ts` 中逐字一致地新增该 edge → cloud 消息类型与载荷类型。
  <!-- aidcp-edge 000f970 / aidcp-cloud 322472a；automation 那份走 scripts/sync-split-repos（派生物，绝不手改）。消息类型总数 95 → 96，两仓 AC-PROTO-02 断言同步。 -->
- [x] 1.2 新增握手能力位常量（**注意带版本后缀**，本仓有过手抄漏掉后缀导致能力静默不生效的前科）。
  <!-- `HOST_STANDBY_DECISION_TELEMETRY_CAPABILITY = 'host_standby_decision_telemetry_v1'`，后缀已带。 -->
- [x] 1.3 更新 `docs/protocol.md`：§2 表新增一行 + **同步头部消息计数**（人工维护、易滞后）。
  <!-- §2 表已加行 + §2.1 后补完整载荷说明。**头部没有消息计数可同步**：该文档 §0 明写「本文不复制易漂移的消息总数」，计数只活在两份 protocol.ts 的 MessageType 与 AC-PROTO-02。 -->
- [x] 1.4 确认**不需要**改动作↔消息映射表与边缘 onMessage 主动命令白名单（本消息是 edge → cloud 单向上报，两者都只对 cloud → edge 生效）；把这条判断写进备注，避免下一个人重新纠结。
  <!-- 结论见本文件 §5.2 备注 B。`scripts/operation-registry-parity` 实跑：三份登记表各 46 条、未变。 -->

## 2. 边缘：外壳判决 → 核心 → 云端（三跳）

- [x] 2.1 外壳侧：在准入判决落定处产出回执事实（判决结果、具名原因、连续拒绝次数、首次拒绝时刻、对应提示标识）。**复用既有的连续拒绝记账**，MUST NOT 另起一套计数。
  <!-- aidcp-edge 000f970 `browser-cold-standby.cjs` 的 `standbyDecisionFact()`，连续拒绝记账仍是既有的 `noteStandbyRefusal`，未另起计数。提示标识取该提示的 `generatedAt`（不新增提示字段）。 -->
- [x] 2.2 外壳侧节流：与本地日志留痕**同一套规则**（首次 / 原因变化 / 此后每 N 次）；**判决迁移（拒→让、让→拒）立即发、不受节流约束**。两处节流 MUST NOT 各写一份常量。
  <!-- `shouldReportStandbyDecision()` 内部直接调 `shouldLogStandbyRefusal()`，共用同一个 `STANDBY_REFUSAL_LOG_EVERY`；有一条源码断言钉住这层复用。 -->
- [x] 2.3 外壳 → 核心：新增一条本地消息并发送。
  <!-- `lifecycle.standby_decision`。**信封形状与类型常量只定义一次**（`standbyDecisionRelayMessage` / `STANDBY_DECISION_RELAY_TYPE`），核心侧那份常量与它有相等断言。 -->
- [x] 2.4 核心侧：新增**具名解析分支**并转发到云端。⚠️ 该处是逐类具名解析、非通配转发，**漏加分支的表现是静默不转发**（本仓同形状前科：命令到不了处理器、日志只显示已发送）。
  <!-- 解析器析出到 `src/client/core-lifecycle.ts` 的 `parseStandbyDecisionRelay()`（可单测），`src/main.ts` 的 `process.on('message')` 挂分支并转发。**析出的理由**：留在 main.ts 的闭包里就没法对它做「漏配即红」的定向反例。 -->
- [x] 2.5 能力位：边缘握手时声明；**未声明 ⇒ 不上报**，且该路径 MUST NOT 产生错误。
  <!-- 进 `EDGE_BUILD_CAPABILITIES`（构建能力，不进任一平台 driver 常量——判决在外壳作出、与平台无关，进 driver 会漏掉别的装配路径）。核心侧转发前查 `supportsCapability()`，未协商即静默返回。 -->
- [x] 2.6 **回执失败 MUST NOT 影响准入**：上报异常、云端不可达、对端不支持——三种情形下让位判决与执行**逐字不变**。
  <!-- `reportStandbyDecision()` 绝不抛（未连接回 false）；外壳侧 `reportColdStandbyDecision()` 整段 try/catch，且送不出去时把节流状态还原、什么都不改。三条结构断言钉住它不碰任何准入/待机状态。 -->

## 3. 云端：接收、留存、呈现

- [x] 3.1 新增消息处理，按环境 / 账号留存最近一次判决与连续拒绝态。
  <!-- aidcp-cloud 322472a：`src/comm/handler.ts` 的 `case 'standby.decision'` + `src/comm/host-standby-decision-store.ts`（进程内当前态，不落库——Non-Goal 明写不做历史留档）。键 = edgeId + accountId；身份（机器标签 / 账号）由握手事实补齐，边缘不重复发一遍。 -->
- [x] 3.2 面板侧可读：**在运营所在的另一处能看出「某台机器上某个环境卡住了」**。这是本 change 的验收判据，不是「消息发出去了」。
  <!-- `GET /api/host-standby-decisions`：机器标签 / 环境标识 / 具名原因 / 连续次数 / 已持续时长 / 陈旧度 / `stuck` 标记。读不到回 503（「读不到」MUST NOT 被呈现成「没有环境卡住」）。跨进程读经 kernel 只读端口 + `aidcp-transport` 内部 HTTP。 -->
- [x] 3.3 **只读边界**：消费方 MUST NOT 出现在任何下发决策路径上（待机提示产出、命令下发、风控）。
  <!-- 见 4.5 的结构断言。 -->
- [x] 3.4 未收到回执 MUST NOT 被云端当作异常或据以改变行为（旧客户端不声明能力是正常态）。
  <!-- 能力位**双向**协商：边缘声明 + 云端真接了消费方才回显；任一侧缺席即不协商、边缘不上报、云端不报错。未接消费方却收到回执也只静默丢弃（灰度中途换端是正常态）。 -->

## 4. 回归

- [x] 4.1 **端到端三跳断言**：外壳判决 → 核心转发 → 云端收到并可读。**MUST NOT** 只断言外壳发出——那正好放过链路唯一的静默失败点（核心侧漏配解析分支）。
  <!-- aidcp-edge `test/electron/standby-decision-telemetry.test.ts`：三跳串真实现（外壳事实+信封 → 核心具名解析 → EdgeClient 对假 WS 发真信封），逐字段断言连续次数 / 首次时刻 / 提示标识不在途中丢。 -->
- [x] 4.2 中间跳漏配的定向反例：移除核心侧解析分支 ⇒ 端到端断言必须红。
  <!-- 两条：运行期「不调解析器 ⇒ 云端零帧」+ 源码断言「本地消息路由确实挂了这条分支」（解析器存在 ≠ 被调用，两者同形都表现为静默不转发）。 -->
- [x] 4.3 节流断言：同因连续拒绝按节流上报（非逐跳）；**判决迁移立即上报**（定向回归，防节流吃掉状态变化）。
  <!-- 迁移那条**用同因合成取值**（previous.reason 与本次相同）——真实取值里让位恒 `ok`、与任何拒绝原因都不同，「换因立即发」会把迁移规则整个代劳掉，那道闸就成了恒不生效的闸。 -->
- [x] 4.4 **结构断言：准入输入集合不因本 change 增加任何一项**；回执相关状态出现在准入里即红。
  <!-- 逐字钉住 `shouldEnterColdStandby` 的入参解构签名 + 函数体不得出现任何回执标识符。 -->
- [x] 4.5 **结构断言：云端消费方不在任何下发决策路径上**（对应规格「可见性 MUST NOT 转化为否决权」）。
  <!-- aidcp-cloud `test/comm/host-standby-decision.test.ts`：五个下发路径文件（待机提示产出 / 角色调度 / 风控控制器 / 风控状态机 / 提示推送）全文不得出现该消费方；处理分支不得 emit、不得改会话状态、不得触碰下发口；只读端口不得有第二条路由。 -->
- [x] 4.6 兼容断言：云端待机提示载荷字段集合**未减少任一项**（对 0.3 的基线快照）；缺字段时边缘判整条无效 —— 该行为本身也要有断言，证明这条红线不是空话。
  <!-- 云端：对真实产出的提示逐项断言九个基线字段都在。边缘：缺 `eligible` / 缺 `enabled` / 缺门槛值 / 门槛值 < 1s ⇒ `normalizeBrowserStandbyHint` 返回 null，且准入当场判 `invalid_hint`。 -->
- [x] 4.7 能力位缺席路径：未声明能力的边缘不上报、云端不报错、让位照常。
  <!-- 边缘侧「welcome 不回该能力位 ⇒ 云端零帧」+ 云端侧三种协商组合的 welcome 断言。 -->
- [x] 4.8 变异自查：把 4.2、4.3（迁移立即发）、4.4 三条各破坏一次，确认对应断言真的会红（防恒真断言）。
  <!-- 三次变异实跑，逐条确认对应断言变红、还原后全绿。**4.3 第一次变异没红**——原因即 4.3 备注里那条「迁移规则被换因规则代劳」，据此把断言改成同因迁移后才真正抓住。这条变异不是形式，它当场发现了一道假闸。 -->
- [x] 4.9 两仓分别 `npm run test:acceptance && npm test && npm run typecheck` 全绿。安全红线必须全过：协议不漂移、未授权绝不静默发布、风控绝不自残。
  <!-- edge：acceptance 39/39、全量 3194（0 fail）、typecheck、`gate:native` 全过。cloud：acceptance 189/189、全量 4282（0 fail）、typecheck 全过。跨仓 `protocol-parity` 三份逐字一致、`operation-registry-parity` 三份各 46 条一致。 -->

## 5. 控制仓收尾

- [x] 5.1 本文件按 sub-repo 分节回写 commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`；sha 必须取自**已推送**的提交。
  <!-- 见 §7 的落地清单，全部取自已 push 的提交。 -->
- [x] 5.2 把 0.3 的字段基线、1.4 的判断结论写进备注。
  <!--
  备注 A（0.3 待机提示字段基线，`UiBrowserStandbyPayload`，九项、只增不减）：
    enabled / eligible / reason / waitMs / wakeAt / generatedAt / source / minWaitMs / warmupMs。
    边缘对它做格式先验：`enabled`/`eligible` 不是布尔、或 `minWaitMs` < 1000ms ⇒ **整条提示当场判无效并丢弃**。
    因此任何一项删减都不是降级，而是让**全部在跑的客户端一起停止让位**；且不能靠版本号灰度
    （客户端会被从源码重新编译装机而不抬版本号），唯一安全的开关是握手能力位。
  备注 B（1.4 判断结论）：本消息是 **edge → cloud 单向上报**，因此三处都不需要动——
    ① 动作↔消息映射表（`command-bridge.ts`）只对 cloud → edge 命令生效；
    ② 边缘 `edge-client.ts` 的 onMessage 主动命令白名单只对「云端独立下发、非应答」的命令生效；
    ③ Cloud→Edge 操作登记表（`operation-registry.ts`）同理，实跑仍是三份各 46 条、未变。
    本消息也**不进** `action.completed.action` 那两张动作名映射表——它不是动作回执，不参与角色关联。
  -->
- [x] 5.3 `openspec validate report-host-standby-decisions --strict` 通过。
  <!-- 实跑：Change 'report-host-standby-decisions' is valid -->

## 6. 集成与部署

- [x] 6.1 **上线顺序不可反：云端先上，边缘后到。** 边缘先发而云端不认，消息会被当未知类型丢弃。
  <!-- cloud 先 land（322472a）再 edge（000f970）；派生服务先部署 dev，边缘要到客户端重新编译装机后才开始上报，顺序天然满足。 -->
- [x] 6.2 云端部署走 §5 安全序列（先 `scripts/deploy-target dev --check` → 备份 → rsync → 重启 → 健康检查 → 失败即回滚）；**绝不碰同机 isales**。
  <!-- 2026-08-06 deployed dev。部署的是**派生两服务**（automation + api），不是单体——`aidcp-cloud` 已定为永不部署。
       序列：deploy-target dev --check → 备份 api/automation.bak.20260806-151721.tar.gz + .env.bak → `git archive HEAD` 干净快照 rsync（不从工作区推）
       → ECS 两槽 typecheck 全 CLEAN → restart automation → restart api → 健康检查。isales 未碰（仍 inactive）。
       部署 sha：aidcp-api 7a4c6f3 / aidcp-automation 7791de9。本批无迁移文件新增。 -->
  <!-- ⚠️ **ECS 装不了私有 git 依赖**：机器上没有 GitHub deploy key，`npm install` 直接「无法读取远程仓库」。
       共享包（kernel / transport）的既有装机方式是**把本机 node_modules 里那两个目录 rsync 过去**（dist + package.json）。
       本次照办；`npm ls` 复核两条 pin 与本地一致。这一条不写下来，下一个人会在 ECS 上白等一次 npm。 -->
  <!-- 验收（可当场核的部分）：三服务 active、NRestarts=0、六端口全在（8787/8090/8091/8092/8093/8094）、
       单体仍 inactive+disabled、同步读就绪 ready blockers=[]、两服务近 6 分钟日志 error/fatal 计数 0。
       **新通道两端实证**：automation 内部只读路由 `POST /host-standby-decision/list` → `{"ok":true,"result":[]}`（非 404）；
       面板 `GET /api/host-standby-decisions` → 200 `{"decisions":[],"asOf":…}`，同 token 打一个不存在的路径回 404 ⇒ 那个 200 是真路由、不是兜底。
       空列表是正确的当前事实：还没有装了新构建的边缘客户端连上来。 -->
  <!-- 本批顺带带上了并行 change `restore-derived-migration-executability` 已合入 master 的提交（api 943882c / automation 39502c8 等）——
       dev 部署的是默认分支目标提交，那些提交本就已 land 且各仓全量绿；此处如实记一笔，不是本 change 的改动。 -->
- [x] 6.3 本 change **不含**桌面安装包出包（默认不打包）。收尾说明写清：**边缘侧要到客户端重新编译装机后才开始上报**，且**不得用版本号判断装的是哪份代码**。
- [x] 6.4 回滚口径：云端停止消费即可；协议消息保留无害（边缘发、云端忽略）。**MUST NOT 靠删字段回滚**——删字段会让全部在跑客户端停止让位。
  <!-- 具体做法：把自动化进程那条只读路由注册摘掉即可——消费方一缺席，握手就不再协商该能力位，边缘随之静默停发，全链零报错。MUST NOT 动 `UiBrowserStandbyPayload` 的任何字段。 -->

## 7. 落地清单（已推送的提交）

## 1. aidcp-edge

- 外壳判决 → 核心具名解析 → 云端三跳、能力位、节流与迁移规则、三跳回归与三次变异自查
  <!-- aidcp-edge 000f970 已推 master -->

## 2. aidcp-cloud（事实源）

- 协议消息 + 能力位、消息处理与当前态持有、kernel 只读端口、transport 只读通道、面板端点、边界登记与结构断言
  <!-- aidcp-cloud 322472a 已推 master -->

## 3. aidcp-kernel / aidcp-transport（共享包）

- kernel：只读投影端口
  <!-- aidcp-kernel 2fcbfdd 已推 master -->
- transport：只读跨进程通道（服务端注册 + 类型化客户端 + 路径常量三件套）+ 跟随 kernel pin
  <!-- aidcp-transport 891214e（通道）、761b9bd（kernel pin → 2fcbfdd）已推 master；另有并行 change 的 416db19 把 spec 串统一回 git+ssh 写法，api 侧 pin 取它 -->
- 控制仓：把该通道登记进 `scripts/sync-split-repos` 的 `TRANSPORT_MEMBERS`
  <!-- aidcp 见本 change 的控制仓提交 -->

## 4. aidcp-automation（派生仓，组装根手写）

- 派生源同步（协议 / 处理器 / 持有方 / 传输）走 `scripts/sync-split-repos`；组装根手写：边-云网关构造持有方并喂给消息处理器，内部 API 挂只读路由
- 导出面判据清单同步：`hostStandbyDecisions` 逐条裁定（41 → 42 条）；服务路由清单登记该族（漏登记比漏注册更危险，两向都锁）
  <!-- aidcp-automation 7791de9 已推 master；typecheck 0 / acceptance 296 pass / npm test 2300（0 fail） -->
  <!-- 偏离：boundaries/module-ownership.json 手工补两条。本仓 boundaries:refresh 对 17 个派生私有组装根 fail-closed（既有状态、与本 change 无关），生成器跑不动；沿用同仓 39502c8 的同一做法。 -->

## 5. aidcp-api（派生仓，组装根手写）

- 面板侧注入只读 HTTP 客户端 + `GET /api/host-standby-decisions`；面板能力名册新增一项（未装即启动失败，不会静默少一条端点）
  <!-- aidcp-api 7a4c6f3 已推 master；typecheck 0 / acceptance 26 pass / npm test 578（0 fail） -->
  <!-- 依赖 pin：kernel 2fcbfdd + transport 416db19，两条 spec 串统一 git+ssh 写法——`npm install <pkg>` 会改写成 github: 简写，而本仓「kernel 只能有一份、两处 spec 串逐字相同」那道守卫认字符串，简写即当场红。**别用 `npm install <pkg>` 升 pin**：它按默认分支头重解析、顺手改写 package.json；要改 pin 就手改 package.json 再跑裸 `npm install`。 -->

## 7b. 真机验收（解耦，已登记 backlog）

云端两端已在部署当天实证（内部只读路由与面板端点都回真值、非 404、非兜底），
**缺的是「真有边缘在发」那一段**——它要到客户端从源码重新编译装机之后才发生。
登记为 `docs/real-machine-acceptance-backlog.md` **簇 146**，五条（含两条负向：
上报失败不影响让位、旧客户端静默共存）。

**MUST NOT 把「已归档」读成「已在真机上验过」**；也 MUST NOT 用客户端版本号判断装的是哪份代码。

## 8. 为什么范围比 tasks.md 原写的大

原文只写了「edge + cloud（+ automation 仅协议副本）」。实际必须做到派生链路的末端，理由是**部署事实**：
`aidcp-cloud` 已于 2026-08-05 定为**永不部署**（只作事实源），dev / OL 上真正在跑的是
api / automation 两个派生服务。只改 cloud 的话，本 change 在生产上**一行都不会执行**，
而 3.2 的验收判据（「运营在另一处能看出来」）在真机上是假的。

因此额外落了四处：`aidcp-kernel`（只读端口）、`aidcp-transport`（只读通道）、
`aidcp-automation`（持有方 + 只读路由）、`aidcp-api`（面板注入 + 端点）。
这四处都不是新设计，是同一份设计在拆仓后的必然落点。
