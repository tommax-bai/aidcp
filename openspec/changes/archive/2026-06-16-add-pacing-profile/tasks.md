# Tasks — add-pacing-profile（指令级节奏 Command Pacing）

> 进度回写在本中控仓。代码改动落对应 sub-repo，标 `[x]` 时附 `<!-- <repo> <commit-sha> 备注 -->`。

## 1. aidcp（中控：契约 / 文档）

- [x] 1.1 `docs/protocol.md §3.7`：角色指令 payload 增可选时间字段——`navigation.back`/`note.close` 加 `dwellMs?`，`interaction.*`/`note.open` 加 `thinkMs?`，给出语义与示例 <!-- aidcp 本次提交 §3.7 增时间指令说明块 -->
- [x] 1.2 `docs/protocol.md §3.9`：`session.budget` 增可选极薄 `pacing` 默认块（`tempo?`/`dwellFloorMs?`，仅兜底用） <!-- aidcp 本次提交 -->
- [x] 1.3 `docs/risk-control.md §3`：标注 read/pause/fatigue 系数**收口云端**、经决策指令的 `dwellMs`/`thinkMs` 下发，`tempo` 为状态联动旋钮 <!-- aidcp 本次提交 §3 顶部加节奏归属说明 -->
- [x] 1.4 校验 change：`openspec validate add-pacing-profile --strict` <!-- aidcp valid ✓ -->

## 2. aidcp-cloud（云端：算时长 + 随指令下发）

- [x] 2.1 `src/comm/protocol.ts`：角色指令类型增可选 `dwellMs`/`thinkMs`；`SessionBudget` 增可选极薄 `pacing` <!-- aidcp-cloud 873ec05 -->
- [x] 2.2 `src/risk/` + 评估角色：实现 `computeDwellMs(content, state, progress)` / `computeThinkMs(...)`——`(base+k_text·len+k_img·img)×tempo×fatigue`，系数取 §3 既定值；无价值路径取较小值但 ≥ 感知下限 <!-- aidcp-cloud 873ec05 src/risk/pacing.ts；glance 模式=0.35×read 作为无价值路径 -->
- [x] 2.3 在 `command-bridge` / 指令装配处把算出的中心值挂到 `navigation.back`/`interaction.*`/`note.open` 等指令上 <!-- aidcp-cloud 873ec05 RoleDispatcher 决策点挂 params；command-bridge 已透传 params 无需改 -->
- [x] 2.4 单测：长内容 dwell > 短内容；`normal/warned/restricted` 三态中心值单调放大；指令序列化含时间字段 <!-- aidcp-cloud 873ec05 test/risk-pacing.test.ts（9 用例）-->
- [x] 2.5 `npm test` + `npm run typecheck` 通过 <!-- aidcp-cloud 873ec05 158 tests pass / typecheck clean --> <!-- 2026-06-16 deployed ECS cloud=873ec05；备份 cloud.bak.20260616-180059.tar.gz；healthcheck 全过；edge 5278eb7 已 push 待本地重启生效 -->

## 3. aidcp-edge（边缘：消费指令 + 抖动 + 返回兜底）

- [x] 3.1 `src/comm/protocol.ts`：同名投影补 `dwellMs`/`thinkMs` 与 `session.budget.pacing` <!-- aidcp-edge 5278eb7 -->
- [x] 3.2 拟人化模块：实现 `jitter()`（lognormal）；`onCommand` 中 `thinkMs`→执行前等待、`dwellMs`→保证页面实际停留达标（未达标补足） <!-- aidcp-edge 5278eb7 humanize/timing.jitterAround + browse-session.thinkBefore/ensureDetailDwell -->
- [x] 3.3 `navigation.back` 前强制 `dwell ≥ jitter(dwellMs ?? builtinFloor)`；有价值阅读已超则不叠加 <!-- aidcp-edge 5278eb7 noteOpenedAt 记录实际停留，elapsed 已达标则不补 -->
- [x] 3.4 缺时间字段（旧云端 / 断连 / 自主动作）→ 内置默认下限兜底，**非零延迟**；子动作运动时序不受时间字段影响 <!-- aidcp-edge 5278eb7 DEFAULT_DWELL_FLOOR_MS{1200,2600} -->
- [x] 3.5 验收：带 `dwellMs` 无价值详情页不秒退、缺字段也不秒退、长文 dwell > 短文、同一中心值两次时序不同 <!-- aidcp-edge 5278eb7 test/browse/browse-session.test.ts 增 4 pacing 用例 -->
- [x] 3.6 `npm test` + `npm run test:acceptance` + `npm run typecheck` 通过 <!-- aidcp-edge 5278eb7 208 tests / acceptance 11 / typecheck clean -->

## 4. 收尾

- [x] 4.1 两侧 `protocol.ts` 与 `docs/protocol.md` 三方一致性自检（字段名 / 可选性 / 默认） <!-- 一致：dwellMs/thinkMs/pacing 字段两侧投影相同，doc §3.7/§3.9 对齐 -->
- [x] 4.2 `openspec validate add-pacing-profile --strict` 通过 → 准备 archive <!-- valid ✓ -->
