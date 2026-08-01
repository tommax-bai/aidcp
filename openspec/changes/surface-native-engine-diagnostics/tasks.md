# Tasks

> 全部工作落 `aidcp-edge` 一个仓。云端 / console / 协议均不涉及。
> 真机验收项**不进本文件**（2026-08-01 裁定）：一律登记到 `docs/real-machine-acceptance-backlog.md`，见 §6。

## 1. aidcp-edge — 宿主转发通路（宿主 TypeScript）

- [ ] 1.1 在 `src/native-page-engine/client.ts` 的 `NativePageEngineClientOptions` 上新增可选诊断出口选项；类型只依赖字符串与数字，**不引入 `node:fs` / `console`**，保持纯协议客户端（design D1 / 约束 1）
- [ ] 1.2 `NativeProcessTransport` 的 stderr 处理由「拼尾缓冲」改为「行缓冲 → 成行后 tee」：尾缓冲**逐字保留原行为**，新增的是并行出口（spec: 成功路径可达 / 进程级失败归因保持）
- [ ] 1.3 实现行成帧：遇 `\n` 才成行；跨 chunk 的半行拼成一行（spec: 行成帧）
- [ ] 1.4 实现超长行处理：单行超过每行上限 → 截断 + **显式截断标记**，不静默截断（spec: 超长行）
- [ ] 1.5 实现退出冲刷：进程退出时缓冲里残留的半行**冲出并标记不完整**，不丢弃（spec: 退出时的半行）
- [ ] 1.6 实现分类：命中引擎具名诊断族的标 `known`，其余标 `other`；**全部转发**，不按族过滤（spec: 全量转发并分类；design D7）
- [ ] 1.7 实现每命令量上限：保留**最早**的 N 行（N=50），超出计数；命令结束时补一行显式 `suppressed=<n>`；**不得静默闭嘴**（spec: 量的上限必须响亮；design D6）

## 2. aidcp-edge — 归因与注入（宿主 TypeScript）

- [ ] 2.1 `src/native-page-engine/runtime.ts` 注入诊断出口，写到**核心进程 stderr**（非 stdout，避让已被占用的两条 stdout 前缀桥；design D3）
- [ ] 2.2 行格式定为 `[engine-diagnostic] cmd=<label> seq=<n> class=<known|other> <line>`：人类可读、可 grep、可落盘；**不用裸 JSON**，避免将来有人照 `[command-diagnostic]` 的先例给它加一个「原始内容不进日志」的分支（design D2 末段）
- [ ] 2.3 归因由 `runtime.ts` 盖章（它知道当前在执行什么）；**MUST NOT 在传输层按 pending 条数推断**（控制记录会与命令并存，`client.ts:806-816`）（spec: 归因 / design D4）
- [ ] 2.4 无在飞命令时（建会话 / 重连 / 关闭期）如实标 `cmd=none`，**不挂到相邻命令上**（spec: 命令之间到达的行）
- [ ] 2.5 确认 Electron 侧零改动即可到达：未命中已知前缀的行经 `main.cjs:5836-5841` 原样进 `edge.log` 与 UI 活动流——**读代码坐实，不改代码**；若发现有分支会吞掉本前缀，则本任务转为需要改动并在此注明

## 3. aidcp-edge — 指针轨迹降级两态可分与留痕（引擎 Rust）

- [ ] 3.1 `native/page-engine/src/input.rs`：`PointerPath` 增降级三态字段（无 / 低于拟人下限 / 塌成单帧）
- [ ] 3.2 拆开 `generate_pointer_path:1228` 那个 `if`：`distance <= POINTER_DEGENERATE_DISTANCE_PX` 判**无降级**（目标已在脚下是正确行为），`budget == 1` 判**塌成单帧**（spec: 两态可分）
- [ ] 3.3 补中间态：`count.min(budget)`（`:1240`）把帧数压到 `POINTER_FRAME_COUNT_MIN` 以下时判**低于拟人下限**，记录实际帧数与下限值
- [ ] 3.4 新增纯函数 `pointer_degradation_note(&PointerPath) -> Option<String>`，形态对齐既有的 `typing_degradation_note`（`:499-506`）；**纯函数、可脱机断言**（spec: 诊断内容可脱机断言）
- [ ] 3.5 在 `dispatch_pointer_click` 这**一个**分发入口打点；**不改 12 个调用点**、不改函数返回类型（design D8）
- [ ] 3.6 确认不改成败：降级路径仍走原有的按下/抬起配对与不可打断窗口，回执仍如实成功；预算真不够时仍走既有的诚实死线拒绝（spec: 降级不改变回执业务真相）

## 4. aidcp-edge — 验证

- [ ] 4.1 宿主用例：桩子进程在**命令成功**期间写 stderr → 断言出口收到整行（这是本 change 的中心断言：今天它必然收不到）
- [ ] 4.2 宿主用例：chunk 切在行中间 → 断言出去的是一行而非两行
- [ ] 4.3 宿主用例：超长行 → 断言带显式截断标记；退出时半行 → 断言被冲出且标记不完整
- [ ] 4.4 宿主用例：超过每命令上限 → 断言保留最早 N 行 **且**有显式 `suppressed` 计数（只断言前半条会漏掉「静默闭嘴」这个正是要防的形态）
- [ ] 4.5 宿主用例：panic 形状的非诊断族输出 → 断言被转发且标 `class=other`，不被丢弃
- [ ] 4.6 宿主回归：进程崩溃 / 超时 / 协议非法三条路径上，尾缓冲仍原样挂进失败 detail（防「改通路顺手把既有归因改坏」）
- [ ] 4.7 **接线断言（按引用）**：断言生产运行时构造客户端时**确实传了**出口，而不只是断言选项可被接受（spec: MUST be wired；design 风险「加了但没接上」）
- [ ] 4.8 Rust 用例：距离 ≤ 阈值 → 无降级；budget==1 且距离大 → 塌成单帧；budget ∈ [2,14] → 低于拟人下限且带实际帧数；note 函数三态对应 None/Some
- [ ] 4.9 变异检验：至少对 3.2 的判据与 4.4 的 `suppressed` 断言各做一次变异，确认**有用例红**并记下**是哪一条**抓住的（承重的常不是端到端那条）。Rust 侧须确认输出里出现 `Compiling`，否则测的是编辑不是新二进制
- [ ] 4.10 全量闸：`cargo test --locked` / `cargo fmt --check` / `clippy -D warnings` / `npm run gate:native` / `npm run typecheck` / `npm run test:acceptance` / `npm test`

## 5. aidcp-edge — 收口

- [ ] 5.1 提交 + 推送 `aidcp-edge` master；本仓 tasks.md 按 `<!-- <repo> <sha> 备注 -->` 回写（sha 必须取自**已推送**提交）
- [ ] 5.2 更新 `docs/edge-honesty-gap-inventory.md` 的 **E12**：由「已判：转出」改为本 change 承接并落地，写清承接后的实际形态
- [ ] 5.3 更新 `docs/edge-honesty-gap-inventory.md` 里逐字输入降级记账那一条：其记账早已存在，**本 change 让它第一次可达**——如实写明「此前写了但结构上无人可见」
- [ ] 5.4 归档前按 handoff §12.1 逐条对读 delta 与实装（本轮实测 91 条命中 16 条），**至少读两遍、第二遍在修完之后**

## 6. 真机验收（不在本文件勾选）

- [ ] 6.1 登记到 `docs/real-machine-acceptance-backlog.md`：诊断行确实出现在运营机的 `edge.log` 与 UI 活动流（共同前置＝重打一次客户端安装包，与簇 122/123/125/126 同批）
- [ ] 6.2 登记到 backlog：指针降级在真机上的**实际发生频次**——设计里承认「可达面窄」是推断，只有真机能给出真实分布；若频次高于预期，需回头看是不是预算分配本身偏紧
- [ ] 6.3 登记到 backlog：`class=other` 行的真实形态与量（panic / backtrace 长什么样、有多长），据此复核每行上限与每命令上限是否需要调整（design Open Questions）
