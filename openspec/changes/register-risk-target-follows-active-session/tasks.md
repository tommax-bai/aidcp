# ⏸ 本轮不做（2026-07-30，用户裁定）

> **剩余任务已划出本轮范围，但本 change 未被废弃。** 立论仍然成立，缺陷仍然存在，只是不在这一轮做。
>
> 用户口径：**这些是此前 JS 侧没做完的功能，与「迁移到 Rust 引擎」这批工作没有关系**，
> 不应该混在这一轮里排期。
>
> **进度快照（划出时）：已做 0/11，剩余 11 项本轮不做。**
>
> **与「废弃」的区别**：本节不否定立论。下面每条未勾项都标了「本轮不做」，
> `- [ ]` 在这里表示「没做，本轮也不打算做」，**不表示这条已经不成立**。
> 重新排期时把本节与各条标注删掉即可，任务原文未改动。
>
> **MUST NOT 把本节读成「问题已解决」或「立论已作废」。** 该 change 描述的缺陷在生产上依然存在。

# Tasks

> **本 change 是纯补登**：所述行为 2026-07-23 起已在线（cloud `6b6b542`）。除第 2 节的三条补测外
> **不改任何 sub-repo 代码**；核对出入一律**以代码为准改 spec**，不为凑 spec 改代码。
> tasks 回写时引用的 sha 一律标注为「补登、非本 change 产出」。

## 1. aidcp（中控）— 逐条核对 spec 与 origin/master 代码

- [ ] **【本轮不做 2026-07-30】** 1.1 逐条核对 `specs/same-account-parallel-safety/spec.md` 的 8 条需求与代码：R1↔`src/orchestrator/connection-runtime.ts` 的 `resolveOwnership` + `emitOwnership`；R2↔`src/server.ts` 的 `ownership.onClaimed` → `riskRegistry.evict`；R3↔`src/risk/pg-risk-store.ts` 的条件写 + `src/risk/risk-controller.ts` 的 `persistState`；R4↔`src/risk/risk-controller-registry.ts` 的 `handleNotOwned`；R5↔`risk_counters` 无 target 列 + 记账口无归属闸；R6↔`src/panel/panel-server.ts` 的风控写口；R7↔`src/panel/panel-store.ts` + `src/panel/version.ts` + console `RiskControls.tsx`；R8↔`src/server.ts` 的 `ownershipMode` 解析 + `src/risk/ownership.ts` 的 `OwnershipMode`。
- [ ] **【本轮不做 2026-07-30】** 1.2 核对现有测试与各条需求的对应关系，在本文件标注「已覆盖 / 无覆盖」：cloud `test/risk-ownership.test.ts`、`test/panel-risk-ownership.test.ts`、`test/panel-server.test.ts`；console `src/components/RiskControls.ownership.test.tsx`；edge `test/client/cloud-handshake-rejection.test.ts`（注意：edge 侧那条测的是**旧拒绝码**的呈现，云端该路径已删，需判定是否已成死代码）。
- [ ] **【本轮不做 2026-07-30】** 1.3 `openspec validate register-risk-target-follows-active-session --strict` 通过；并在 scratchpad 拷贝上跑一次 `openspec archive` 干净合入（`interaction-risk-gating` 是 MODIFIED，标题必须逐字命中，本仓已因此中止过两次）。

## 2. aidcp-cloud — 补测（已实装、无覆盖；不改行为）

- [ ] **【本轮不做 2026-07-30】** 2.1 条件写被拒 → 驱逐告警**真的落 alerts 表**。现只有注入 stub 回调的用例，生产接线（`raiseRiskAlert` → `PgAlertStore.raise`，type=`risk_controller_evicted_not_owned`）无任何用例。一条用例即可，不追求全链。
- [ ] **【本轮不做 2026-07-30】** 2.2 归属切换后驱逐/重放回调抛错时**握手仍放行**（`connection-runtime.ts` 的 catch 分支）。现有握手用例覆盖了 null→target / 跨 target / 未变 / 账号不存在，唯独不覆盖回调失败。
- [ ] **【本轮不做 2026-07-30】** 2.3 落败方反复被拒仍诚实：同一账号连续两次状态写都被拒时，MUST 各自驱逐、各自产生告警，且 MUST NOT 返回成功。对应 R4 第二个 Scenario。
- [ ] **【本轮不做 2026-07-30】** 2.4 `npm test` + `npm run typecheck` 全绿。

## 3. aidcp（中控）— 登记，不在本 change 处理

- [ ] **【本轮不做 2026-07-30】** 3.1 真机验收项登记进 `docs/real-machine-acceptance-backlog.md`（归入簇 110）：① 真 PostgreSQL 上「另一连接接管后先写方条件写影响 0 行」——桩测不到，现有测试自述「用桩断言它只是在断言我自己写的桩」；② 归属切换瞬间在途回执仍记入同一本当日账（跨进程时序，桩不可复现）。
- [ ] **【本轮不做 2026-07-30】** 3.2 登记两处已核实的落差，**本 change 不改代码**，判定为缺陷则另开 change：① 面板首页汇总调的是注册表上标 `@deprecated` 的可写口，而同类已提供不物化的只读投影，注释自称「只为读」与实际调用不符；② 告警 sink 后绑定窗口——注册表构造早于 `riskAlertSink` 赋值，该窗口内触发的驱逐告警只走 `console.warn` 不落库。
- [ ] **【本轮不做 2026-07-30】** 3.3 登记拆库待裁决项：条件写谓词在 automation 池上读 api 属主的 `accounts` 表（一条 SQL 跨属主读），`boundaries/` 与 `scripts/db-split/` 下未找到该查询的例外登记。物理拆库后该谓词如何改写，代码里没有答案——**本补登不替它定死**。

## 4. 归档

- [ ] **【本轮不做 2026-07-30】** 4.1 全部核对完成 → `openspec validate --strict` → 归档（无 sub-repo 行为改动，无需部署闸）。

---

## 已知的 spec 与代码之间的强弱差（作者自陈，供复核者对照）

**写得比代码强的地方**（spec 说 MUST，代码是 best-effort 或无测试覆盖）：

1. R1「归属读写失败 MUST 留下可观测记录」——代码是可选 logger 的可选调用，未注入 logger 时不会有任何记录。
2. R8「当前模式 MUST 在进程启动时可观测」——代码是一行启动日志，无测试覆盖。
3. R1 的 P3/P2 与 R4 的 P1 三个严重度取自代码常量，均属「实装、无测试」；写进 spec 后从实现细节升格成契约。
4. R4「每一次被拒 MUST 各自触发驱逐并产生可观测告警」——代码确实无去重、无退避、无抑制窗口，陈述属实；
   已用括号放宽为「是否按窗口聚合不在本要求约束内」，以免将来加告警抑制要先改 spec。
5. R3「结构性阻止为不存在的账号造风控状态行」——代码里这是条件写的**顺带效果**而非设计目的，且在停用
   模式下这层保护完全消失（退回无谓词写），spec 未复述这个损失。

**有意留白的地方**：

6. 「作废先写方」在代码注释里本身 ambiguous——一处写「本次状态写作废」（窄义），另一处只写「作废先写方」
   （读起来像写者被停）。代码只支持窄义，故 R4 单列一条把它钉死为窄义。
7. **停用模式下驱动目标字段的展示语义，代码未定义，spec 有意不写**：停用时归属接线整段不启用，该字段会
   停在上一次由启用态进程写入的旧值。写任何一种读法都是替代码做决定。
8. `claimExecutionTarget` 仍在接口上（自称「保留供运维/兼容口」）但 src 中零生产调用方，spec 不提它——
   将来有人接上它时无约束可依，属已知缺口。
9. R6 用功能性描述绕开了具体路由字面量（代码里的真实路径与部分文档记载不一致），代价是 spec 不能用来核对
   具体路由。

**元风险**：本补登把一份 2026-07-23 上线、至今无 spec 保护的行为一次性固化。核对基线是 `origin/master`
当前 HEAD，未逐 commit 回放 07-23 至今的改动；第 1 节的逐条核对就是为压住这个风险，但它靠人核、不是机械校验。
