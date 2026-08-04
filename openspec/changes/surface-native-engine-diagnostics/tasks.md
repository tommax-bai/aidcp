# Tasks

> 全部工作落 `aidcp-edge` 一个仓。云端 / console / 协议均不涉及。
> 真机验收项**不进本文件**（2026-08-01 裁定）：一律登记到 `docs/real-machine-acceptance-backlog.md`，见 §6。

## 1. aidcp-edge — 宿主转发通路（宿主 TypeScript）

- [x] 1.1 在 `src/native-page-engine/client.ts` 的 `NativePageEngineClientOptions` 上新增可选诊断出口选项；类型只依赖字符串与数字，**不引入 `node:fs` / `console`**，保持纯协议客户端（design D1 / 约束 1）
- [x] 1.2 `NativeProcessTransport` 的 stderr 处理由「拼尾缓冲」改为「行缓冲 → 成行后 tee」：尾缓冲**逐字保留原行为**，新增的是并行出口（spec: 成功路径可达 / 进程级失败归因保持）
- [x] 1.3 实现行成帧：遇 `\n` 才成行；跨 chunk 的半行拼成一行（spec: 行成帧）
- [x] 1.4 实现超长行处理：单行超过每行上限 → 截断 + **显式截断标记**，不静默截断（spec: 超长行）
- [x] 1.5 实现退出冲刷：进程退出时缓冲里残留的半行**冲出并标记不完整**，不丢弃（spec: 退出时的半行）
- [x] 1.6 实现分类：命中引擎具名诊断族的标 `known`，其余标 `other`；**全部转发**，不按族过滤（spec: 全量转发并分类；design D7）
- [x] 1.7 实现每命令量上限：保留**最早**的 N 行（N=50），超出计数；命令结束时补一行显式 `suppressed=<n>`；**不得静默闭嘴**（spec: 量的上限必须响亮；design D6）

## 2. aidcp-edge — 归因与注入（宿主 TypeScript）

- [x] 2.1 `src/native-page-engine/runtime.ts` 注入诊断出口，写到**核心进程 stderr**（非 stdout，避让已被占用的两条 stdout 前缀桥；design D3）
- [x] 2.2 行格式定为 `[engine-diagnostic] cmd=<label> seq=<n> class=<known|other> <line>`：人类可读、可 grep、可落盘；**不用裸 JSON**，避免将来有人照 `[command-diagnostic]` 的先例给它加一个「原始内容不进日志」的分支（design D2 末段）
- [x] 2.3 归因由 `runtime.ts` 盖章（它知道当前在执行什么）；**MUST NOT 在传输层按 pending 条数推断**（控制记录会与命令并存，`client.ts:806-816`）（spec: 归因 / design D4）
- [x] 2.4 无在飞命令时（建会话 / 重连 / 关闭期）如实标 `cmd=none`，**不挂到相邻命令上**（spec: 命令之间到达的行）
- [x] 2.5 确认 Electron 侧零改动即可到达：未命中已知前缀的行经 `main.cjs:5836-5841` 原样进 `edge.log` 与 UI 活动流——**读代码坐实，不改代码**；若发现有分支会吞掉本前缀，则本任务转为需要改动并在此注明

## 3. aidcp-edge — 指针轨迹降级两态可分与留痕（引擎 Rust）

- [x] 3.1 `native/page-engine/src/input.rs`：`PointerPath` 增降级三态字段（无 / 低于拟人下限 / 塌成单帧）
- [x] 3.2 拆开 `generate_pointer_path:1228` 那个 `if`：`distance <= POINTER_DEGENERATE_DISTANCE_PX` 判**无降级**（目标已在脚下是正确行为），`budget == 1` 判**塌成单帧**（spec: 两态可分）
- [x] 3.3 补中间态：`count.min(budget)`（`:1240`）把帧数压到 `POINTER_FRAME_COUNT_MIN` 以下时判**低于拟人下限**，记录实际帧数与下限值
- [x] 3.4 新增纯函数 `pointer_degradation_note(&PointerPath) -> Option<String>`，形态对齐既有的 `typing_degradation_note`（`:499-506`）；**纯函数、可脱机断言**（spec: 诊断内容可脱机断言）
- [x] 3.5 在 `dispatch_pointer_click` 这**一个**分发入口打点；**不改 12 个调用点**、不改函数返回类型（design D8）
- [x] 3.6 确认不改成败：降级路径仍走原有的按下/抬起配对与不可打断窗口，回执仍如实成功；预算真不够时仍走既有的诚实死线拒绝（spec: 降级不改变回执业务真相）

## 4. aidcp-edge — 验证

- [x] 4.1 宿主用例：桩子进程在**命令成功**期间写 stderr → 断言出口收到整行（这是本 change 的中心断言：今天它必然收不到）
- [x] 4.2 宿主用例：chunk 切在行中间 → 断言出去的是一行而非两行
- [x] 4.3 宿主用例：超长行 → 断言带显式截断标记；退出时半行 → 断言被冲出且标记不完整
- [x] 4.4 宿主用例：超过每命令上限 → 断言保留最早 N 行 **且**有显式 `suppressed` 计数（只断言前半条会漏掉「静默闭嘴」这个正是要防的形态）
- [x] 4.5 宿主用例：panic 形状的非诊断族输出 → 断言被转发且标 `class=other`，不被丢弃
- [x] 4.6 宿主回归：进程崩溃 / 超时 / 协议非法三条路径上，尾缓冲仍原样挂进失败 detail（防「改通路顺手把既有归因改坏」）
- [x] 4.7 **接线断言（按引用）**：断言生产运行时构造客户端时**确实传了**出口，而不只是断言选项可被接受（spec: MUST be wired；design 风险「加了但没接上」）
- [x] 4.8 Rust 用例：距离 ≤ 阈值 → 无降级；budget==1 且距离大 → 塌成单帧；budget ∈ [2,14] → 低于拟人下限且带实际帧数；note 函数三态对应 None/Some
- [x] 4.9 变异检验：至少对 3.2 的判据与 4.4 的 `suppressed` 断言各做一次变异，确认**有用例红**并记下**是哪一条**抓住的（承重的常不是端到端那条）。Rust 侧须确认输出里出现 `Compiling`，否则测的是编辑不是新二进制
- [x] 4.10 全量闸：`cargo test --locked` / `cargo fmt --check` / `clippy -D warnings` / `npm run gate:native` / `npm run typecheck` / `npm run test:acceptance` / `npm test`

<!-- 证据（aidcp-edge 8381fea，分支上原 sha 890fec9）：
     §1–§2 宿主通路：`src/native-page-engine/diagnostic-forwarder.ts`（新增）+ `client.ts` tee + `runtime.ts` 注入。
     §3 指针降级：`native/page-engine/src/input.rs` 的 `PointerDegradation` 三态
     （None / BelowHumaneFloor{frames,floor} / CollapsedToSingleFrame），距离判据先于预算判据求值。
     §4 验证：宿主 10 条新用例 + Rust 1 条；四道闸全过（见 5.1）。
     变异四次、每次都点名了抓住它的用例：静默闭嘴 → 「保留最早若干行并报出丢弃条数」+「每命令各自预算」；
     保留最新而非最早 → 仅「保留最早若干行」；**生产忘了传出口 → 仅按引用的接线断言**（六条行为用例全绿，
     正是规格点名要防的那个形态）；Rust 两态压回一态 → 新增的两态用例，而既有那条旧用例**保持绿**
     ——直接证明旧用例原理上看不见这个区分。Rust 变异运行输出中出现 `Compiling`，非陈旧二进制。

     ⚠️ **两处刻意偏离 tasks 原文，评审须知情**：
     ① 1.7 的每命令上限落在 `diagnostic-forwarder.ts`（由 `runtime.ts` 接线）而非 `client.ts`。
        任务原文把它放在客户端小节下，但设计明禁传输层认识「命令」——放在传输层会正好需要
        规格禁止的「按在飞数量推断归属」。
     ② 3.4 的降级两态与其 note 为模块私有而非 `pub(crate)`：`PointerPath` 本身模块私有，
        提成 `pub(crate)` 会触发私有接口 lint（`-D warnings`）。测试同模块，可脱机断言性不受影响。

     ⚠️ **2.5 的结论被实装订正**（原文写「进 edge.log 与 UI 活动流」）：实读坐实转发行进 `edge.log`（无条件）
     与环境的「最后一条消息」，但**到不了按句子渲染的活动流**——那条流只对带 sentence 的结构化 UI 事件触发。
     Electron 侧仍是零改动即可到达，结论成立，只是落点少一个。已在 §6.1 与 backlog 簇 128.1 按订正后登记。 -->

## 5. aidcp-edge — 收口

- [x] 5.1 提交 + 推送 `aidcp-edge` master；本仓 tasks.md 回写
      <!-- aidcp-edge 8381fea 经 scripts/land-change rebase 后 ff 合入 master 并推送；
           分支上原 sha 890fec9。四道验证在 rebase 后复跑：test:acceptance 39/39；npm test 3086 pass /
           0 fail / 1 skip（既有 GOST staging）；typecheck exit 0；gate:native fmt+clippy+test exit 0，
           cargo 388 条全过。 -->
- [x] 5.2 更新 `docs/edge-honesty-gap-inventory.md` 的 **E12**：由「已判：转出」改为本 change 承接并落地，写清承接后的实际形态
- [x] 5.3 更新 `docs/edge-honesty-gap-inventory.md` 里逐字输入降级记账那一条：其记账早已存在，**本 change 让它第一次可达**——如实写明「此前写了但结构上无人可见」
- [x] 5.4 归档前对读 delta 与实装。
      <!-- 2026-08-04 归档前**需求级**对读：两份 delta 共 12 条 Requirement / 30 条 Scenario，
           逐条对着已合并进 master 的代码核（aidcp-edge 8381fea）。全部成立：
           成功路径可达（client.ts 的可选出口 + runtime 注入）/ 行成帧与不完整标记 / 归因盖章且无在飞时 cmd=none /
           量的上限响亮（forward_bound_reached + 结账行 suppressed，且宿主自生行标 class=host 与引擎行可分）/
           全量转发并分类（client.ts:805 按族前缀判 known|other，**不过滤**）/ 生产接线（runtime.ts:127 传出口）/
           只留本机（转发器内零网络调用）/ 指针降级四条（三态枚举、距离判据先于预算判据、单点打点、不改回执真相）。
           **诚实边界**：这是需求级对读，**不是** handoff §12.1 那份 91 项的完整两遍流程；
           MUST NOT 把本行读成「已按 §12.1 全流程复核」。 -->

## 6. 真机验收（不在本文件勾选）

- [x] 6.1 登记到 backlog **簇 128.1**。
      <!-- ⚠️ 本条原文的落点说法**被实装订正**：转发行到达 `edge.log`（无条件）与环境的「最后一条消息」，
           但**到不了按句子渲染的 UI 活动流**——那条流只对带 sentence 的结构化 UI 事件触发。
           簇 128.1 已按订正后的落点登记；本行原文保留以便追溯。 -->
- [x] 6.2 登记到 backlog **簇 128.3**：指针降级在真机上的**实际发生频次**——设计里承认「可达面窄」是推断，只有真机能给出真实分布；若频次高于预期，需回头看是不是预算分配本身偏紧
- [x] 6.3 登记到 backlog **簇 128.2**：`class=other` 行的真实形态与量（panic / backtrace 长什么样、有多长），据此复核每行上限与每命令上限是否需要调整（design Open Questions）

## 7. 实装中发现、登记不改（归档前须确认已另有去处）

- [x] 7.1 **内容安全违规一条，已在同批修掉**（发现于本 change、修在并行流的文件里）：群根决策诊断原本挟带
      两个原始 URL 路径，`bounded_log_value` 只截长度、**截断不是脱敏**。此前无后果（那些行没有收件人），
      **本通路一打通就会持续写进运营机日志**。
      <!-- 修于 aidcp-edge restore-facebook-first-post-recovery 57d5a07：改为只报结论布尔量，
           且该布尔量直接复用落地等待的同一个判据，杜绝两处对「群根」各有一份实现而漂移。 -->
- [ ] 7.2 **其余 `eprintln!` 载荷本批未逐条审**。已抽查：小红书诊断（有限词表）与 Facebook 同意闸干净。
      通路打开后这项从「反正没人看」变成真正承重 ⇒ 登记为 backlog **簇 128.4**。
- [ ] 7.3 **宿主侧失败归因的误报暴露面**：有一处按关键词匹配日志行来记「最后一条失败行」，
      转发进来的引擎诊断或 panic 若含那些词，会被当成失败原因显示给运营。今天无命中
      （诊断信封用的字段名不撞），但**每新增一条引擎诊断这个面就大一点** ⇒ backlog **簇 128.5**。
- [ ] 7.4 **两处刻意偏离 tasks 原文，需评审知情**：① 每命令转发上限落在转发器（由 runtime 接线）而非
      传输层——设计明禁传输层认识「命令」，放在传输层会正好需要规格禁止的「按在飞数量推断归属」；
      ② 降级两态与其 note 保持模块私有——`PointerPath` 本身模块私有，提成 `pub(crate)` 会触发
      私有接口 lint（`-D warnings`）；测试同模块，可断言性不受影响。
