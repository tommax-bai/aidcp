# Tasks — add-pacing-profile（指令级节奏 Command Pacing）

> 进度回写在本中控仓。代码改动落对应 sub-repo，标 `[x]` 时附 `<!-- <repo> <commit-sha> 备注 -->`。

## 1. ai-dcp（中控：契约 / 文档）

- [ ] 1.1 `docs/protocol.md §3.7`：角色指令 payload 增可选时间字段——`navigation.back`/`note.close` 加 `dwellMs?`，`interaction.*`/`note.open` 加 `thinkMs?`，给出语义与示例
- [ ] 1.2 `docs/protocol.md §3.9`：`session.budget` 增可选极薄 `pacing` 默认块（`tempo?`/`dwellFloorMs?`，仅兜底用）
- [ ] 1.3 `docs/risk-control.md §3`：标注 read/pause/fatigue 系数**收口云端**、经决策指令的 `dwellMs`/`thinkMs` 下发，`tempo` 为状态联动旋钮
- [ ] 1.4 校验 change：`openspec validate add-pacing-profile --strict`

## 2. aidcp-cloud（云端：算时长 + 随指令下发）

- [ ] 2.1 `src/comm/protocol.ts`：角色指令类型增可选 `dwellMs`/`thinkMs`；`SessionBudget` 增可选极薄 `pacing`
- [ ] 2.2 `src/risk/` + 评估角色：实现 `computeDwellMs(content, state, progress)` / `computeThinkMs(...)`——`(base+k_text·len+k_img·img)×tempo×fatigue`，系数取 §3 既定值；无价值路径取较小值但 ≥ 感知下限
- [ ] 2.3 在 `command-bridge` / 指令装配处把算出的中心值挂到 `navigation.back`/`interaction.*`/`note.open` 等指令上
- [ ] 2.4 单测：长内容 dwell > 短内容；`normal/warned/restricted` 三态中心值单调放大；指令序列化含时间字段
- [ ] 2.5 `npm test` + `npm run typecheck` 通过

## 3. aidcp-edge（边缘：消费指令 + 抖动 + 返回兜底）

- [ ] 3.1 `src/comm/protocol.ts`：同名投影补 `dwellMs`/`thinkMs` 与 `session.budget.pacing`
- [ ] 3.2 拟人化模块：实现 `jitter()`（lognormal）；`onCommand` 中 `thinkMs`→执行前等待、`dwellMs`→保证页面实际停留达标（未达标补足）
- [ ] 3.3 `navigation.back` 前强制 `dwell ≥ jitter(dwellMs ?? builtinFloor)`；有价值阅读已超则不叠加
- [ ] 3.4 缺时间字段（旧云端 / 断连 / 自主动作）→ 内置默认下限兜底，**非零延迟**；子动作运动时序不受时间字段影响
- [ ] 3.5 验收：带 `dwellMs` 无价值详情页不秒退、缺字段也不秒退、长文 dwell > 短文、同一中心值两次时序不同
- [ ] 3.6 `npm test` + `npm run test:acceptance` + `npm run typecheck` 通过

## 4. 收尾

- [ ] 4.1 两侧 `protocol.ts` 与 `docs/protocol.md` 三方一致性自检（字段名 / 可选性 / 默认）
- [ ] 4.2 `openspec validate add-pacing-profile --strict` 通过 → 准备 archive
