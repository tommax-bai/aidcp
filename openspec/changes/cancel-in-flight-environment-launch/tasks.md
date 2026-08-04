## 1. aidcp-edge — 现状坐实与行为基线

- [x] 1.1 逐条读清所有会拉起核心子进程的路径及其真实取消条件（常规启动 / 崩溃重起 / 待机唤醒 / 排期任务 / 无浏览器控制面 bootstrap / 受限离场清理 / 临时浏览器通道），列出每条路径「该按什么判据准入」，作为准入闸分档的事实源 <!-- aidcp-edge b3d9978 结论与 design 预期不同：`spawnEdgeChild` 是唯一的 spawn 入口，三条特殊路径都经它；受限离场清理不是「豁免判据」，而是在 startRestrictedOffboardCleanupCore 里显式复位 stopRequested。故真正按意图分档的只有 allowWhilePaused 一个标志，design D2 已按实读结论改写 -->
- [x] 1.2 确认 `initializeOwnedCoreChild` 是 `handle.child` 赋值的唯一入口（全仓 grep 佐证），若存在第二处赋值先收口到该入口 <!-- aidcp-edge b3d9978 grep 佐证：core-child-startup.cjs:69 是唯一赋值点，main.cjs 另两处均为置 undefined 的清理 -->
- [x] 1.3 为拆分兜底：补齐锁住 `spawnEdgeChild` 现有分支行为的用例（adspower 常规 / 代理权威注入 / 控制面 bootstrap / 离场清理），确保后续搬动语句顺序时有红可依 <!-- aidcp-edge b3d9978 未新增：D1 改为「复核紧贴 spawn + 源码断言钉住区间」后不再搬动分支语句，既有 lifecycle-contract / offboard-cleanup-core-contract / client-core-bootstrap-contract 已覆盖这些分支 -->

## 2. aidcp-edge — 提交点原子化（design D1）

- [x] 2.1 把 `spawnEdgeChild` 拆成「准备段（可 await，产出纯数据启动方案）」与「提交段（同步函数，不带 async）」两部分，所有 await 前移到准备段 <!-- aidcp-edge b3d9978 形式改动见 design D1「实装时改了形式」：观测者闭包捕获 child，抽独立同步函数需连带重构五条分支约 200 行；改为「提交点复核紧贴 spawn + 源码断言禁 await」，语义等价、回归风险小得多。两处 await 本就已在提交点之前 -->
- [x] 2.2 提交段依次做：取消闸复核（当前操作代次 / 停止意图 / 已移出 / 客户端退出中）→ `spawn` → 所有权登记 → 启动态写入，中间不得有任何 await <!-- aidcp-edge b3d9978 复核置于本轮 handle.* 复位之前，避免被取消的一趟抹掉 browserStateUnconfirmed 等既有事实 -->
- [x] 2.3 提交段复核不通过时：归还启动排队名额、settle 串行启动队列的就绪等待、不写失败态，返回可区分的「已取消」结果 <!-- aidcp-edge b3d9978 releaseStartQueue + settleLaunchReady(false) + 原始日志留因，返回 false -->
- [x] 2.4 用例：准备段进行中插入关闭 → 断言未发生 spawn、名额已归还、队列已放行下一个 <!-- aidcp-edge b3d9978 lifecycle-contract「the launch commit point stays synchronous…」以源码区间断言覆盖（Electron 主进程无法在单测里真起子进程）；行为侧由 core-child-startup 的准入闸用例覆盖 -->
- [x] 2.5 用例：断言提交段是同步函数（非 AsyncFunction），防止日后插入 await 静默重开中间地带 <!-- aidcp-edge b3d9978 等价断言：复核→所有权区间内不得出现 await（doesNotMatch /\bawait\b/） -->

## 3. aidcp-edge — 所有权登记准入闸（design D2）

- [x] 3.1 `initializeOwnedCoreChild` 新增**必填**准入判据参数，缺失时抛错（与现有 handle/child 参数校验同款） <!-- aidcp-edge b3d9978 admit + onAdmissionDenied 双必填 -->
- [x] 3.2 准入被拒时：先完成所有权登记与退出观测者安装，再经既有终止路径终止该子进程，使退出走既有收敛（清所有权、归还浏览器执行名额、放行等槽位队列） <!-- aidcp-edge b3d9978 实装取了相反且更安全的次序：**先判后登记**。原方案在「已有活着的兄弟子进程」这一拒因下会覆盖 handle.child、把那个仍在跑的进程变成孤儿，且登记后 hasChild 恒真使判据自废。改为不登记所有权 + 装最小 'error' 安全网（崩溃隔离）+ terminateUnadoptedChild 自走 SIGTERM→有界 SIGKILL；未登记即未计入名额，无需归还 -->
- [x] 3.3 被拒如实写入原始日志（环境、拒收原因），不投影为失败态、不消耗有界重起预算 <!-- aidcp-edge b3d9978 -->
- [x] 3.4 在 `spawnEdgeChild` 按启动意图分档提供判据：常规浏览器核心读停止意图 / 移出 / 退出中；无浏览器控制面 bootstrap 与受限离场清理按各自取消条件（依据 1.1） <!-- aidcp-edge b3d9978 按 1.1 实读结论收敛为一条规则 + allowWhilePaused 一个标志 -->
- [x] 3.5 用例：已被要求停止的环境送来子进程 → 断言被终止、名额归还、无运行态残留 <!-- aidcp-edge b3d9978 core-child-startup「a launch denied at the ownership gate…」 -->
- [x] 3.6 用例：环境已移出但离场清理核心仍被放行 → 断言不被通用停止意图误杀 <!-- aidcp-edge b3d9978 改为按实装形态断言：fleet 判据用例覆盖 allowWhilePaused（暂停态放行、停止意图仍拦得住）；离场清理不走豁免口，其放行由既有 offboard-cleanup-core-contract 覆盖 -->

## 4. aidcp-edge — 原始日志按所有权全量落（design D3）

- [x] 4.1 `handleEdgeOutput` 的操作代次不一致分支改为：逐行落原始日志并标注来自已被取代的代次，然后返回；代次一致时行为逐字不变 <!-- aidcp-edge b3d9978 前缀 [superseded-generation] -->
- [x] 4.2 确认不产生重复行（与 `handleEdgeLogLine` 内既有的 `appendEdgeLog` 调用互斥） <!-- aidcp-edge b3d9978 两条分支互斥（陈旧代次 return，不进 handleEdgeLogLine） -->
- [x] 4.3 明确不动：人设回执 / 发布审批回执 / 浏览器窗口回执 / 引擎命令诊断 / 状态投影仍保持现有代次门（在代码注释里写清为什么只拆日志这一层） <!-- aidcp-edge b3d9978 -->
- [x] 4.4 用例：代次已推进但子进程仍归本环境所有并输出 → 断言逐行进原始日志、界面运行态未被改写 <!-- aidcp-edge b3d9978 lifecycle-contract「output from a still-owned child is never discarded…」 -->

## 5. aidcp-edge — 就绪超时如实呈现（design D5）

- [x] 5.1 就绪预算超时（默认 180s）除既有控制台告警外，同时写入该环境状态：已超预算 / 队列已放行下一个 / 本环境仍在继续启动 <!-- aidcp-edge b3d9978 -->
- [x] 5.2 断言该呈现不写失败态、不写终态、不置放弃标记 <!-- aidcp-edge b3d9978 只写 lastMessage + presence，不碰任何状态轴 -->
- [x] 5.3 用例：超时触发后断言状态文案与非失败语义 <!-- aidcp-edge b3d9978 未新增独立用例：该分支只写两个展示字段、无分支逻辑，用例只会复读字面量（见 memory test-case-restraint）；真机口径落 backlog 130.5 -->

## 6. aidcp-edge — 回归与验收

- [x] 6.1 `npm run test:acceptance` 全过（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 不得回归） <!-- aidcp-edge b3d9978 39/39 pass -->
- [x] 6.2 `npm test` 全量通过 <!-- aidcp-edge b3d9978 3133 pass / 0 fail / 1 skipped -->
- [x] 6.3 `npm run typecheck` 通过 <!-- aidcp-edge b3d9978 -->
- [x] 6.4 变异验证：把提交段的取消复核改成恒真（闸失效）→ 断言 2.4 的用例当场变红；把准入闸判据参数改成可选默认放行 → 断言 3.5 当场变红 <!-- aidcp-edge b3d9978 四条变异全部 RED 且各有具名承重用例：判据恒放行→3 条 launchCancellationReason 用例；删提交点复核→commit-point 用例；准入闸退回可选→「gate is required」用例；陈旧代次日志退回丢弃→superseded-generation 用例 -->

## 7. 收尾

- [x] 7.1 集成回主干（`scripts/land-change aidcp-edge cancel-in-flight-environment-launch`），推送 <!-- aidcp-edge b3d9978 ff 推送到 origin/master，worktree 与分支已清理 -->
- [x] 7.2 本仓 tasks.md 按 `<!-- <repo> <commit-sha> 备注 -->` 回写落地 sha（sha 必须取自已推送提交）
- [x] 7.3 真机验收项登记到 `docs/real-machine-acceptance-backlog.md`：多环境车队下「启动中途关闭」不再产生无人认领的核心、不再滞留「关闭中」、名额如实归还（需重新出安装包后验证，出包按 CLAUDE.md §6 由用户显式触发） <!-- 簇 130，6 条验收 + 2 条已知未闭合 -->
- [x] 7.4 `openspec validate cancel-in-flight-environment-launch --strict` 通过 <!-- valid -->
