## 1. aidcp-edge — 判据析出为纯函数

- [x] 1.1 在 `src/electron/fleet.cjs` 新增无副作用判据：输入「是否在权威可见集内 + 云端绑定态」，输出「是否收敛 + 具名原因（撤权 / 跨客户绑定冲突）」；未绑定与绑定不可用一律不收敛。<!-- aidcp-edge e903cf7 automationAuthorizationDecision；认不出的绑定态同样不收敛（不把没认出来的原因折进已有判决） -->
- [x] 1.2 导出该判据并在 `test/electron/` 增加逐输入用例：可见集内 × 每一种绑定态（bound / binding_unknown / binding_unavailable / binding_conflict / 缺省）+ 不在可见集内，断言只有撤权与冲突产出收敛。<!-- aidcp-edge e903cf7 test/electron/automation-authorization-gate.test.ts（5 个用例，含缺参数按最保守解读） -->

## 2. aidcp-edge — 会话维护复核改造

- [x] 2.1 会话维护复核改用 1.1 的判据；删除「必须等于 bound 才算可信」这条判据。<!-- aidcp-edge e903cf7 main.cjs enforceOwnedAutomationEngines -->
- [x] 2.2 增加前置：只有本次权威可见集读取成功才据其收敛；读取失败 / 超时 MUST NOT 停止任何环境（保留上次已知集的既有行为不变）。<!-- aidcp-edge e903cf7 allowedEnvironmentsAuthoritative；登出 / 切部署目标 / 会话失效时复位 -->
- [x] 2.3 收敛分支改走与用户显式关闭同一条路径（推进操作代以取消错峰队列与串行启动队列待执行项、归还启动排队名额、清等槽位资历），并停止在跑引擎。<!-- aidcp-edge e903cf7 advanceLifecycleGeneration + clearSlotWaiting + clearColdStandbyTimer + stopRequested -->
- [x] 2.4 具名原因文案落到环境行：撤权 / 跨客户绑定冲突 / 会话失效各不相同，且保留「数据管理仍可继续使用」的既有表述。<!-- aidcp-edge e903cf7 三张文案表（行内消息 / 在场感 / 核心退出叙述）；旧 binding_untrusted 原因串与已死的 CONTROL_BOOTSTRAP_REASON_ZH 一并删除 -->

## 3. aidcp-edge — 回归与守卫

- [x] 3.1 更新 `test/electron/client-core-bootstrap-contract.test.ts`：把写死的「必须等于 bound」形状断言换成新不变量断言（该复核不得以未绑定为由收敛；仍不得调用任何启动 / 唤醒 / 开浏览器入口）。<!-- aidcp-edge e903cf7 新增 doesNotMatch(binding_unknown|binding_unavailable) + 权威读前置断言 -->
- [x] 3.2 增加回归断言：该复核的收敛分支必须撤销在途启动（推进操作代 + 清等槽位资历），杜绝「已判停止仍会打开浏览器」。<!-- aidcp-edge e903cf7 同文件第二个用例 -->
- [x] 3.3 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过（按 CLAUDE.md §4 顺序）。<!-- aidcp-edge e903cf7 acceptance 39/39；全量 3130 passed / 1 skipped / 0 failed；typecheck exit 0；land 时 rebase 到 b3d9978 后由 land-change 重跑一遍（含 gate:native 全绿） -->

## 4. 集成与交付

- [x] 4.1 rebase 到最新 `master`（与 `cancel-in-flight-environment-launch`、`browser-slot-scheduling` 同区，需解冲突后重跑验收）并 ff 合入，推送。<!-- aidcp-edge e903cf7 rebase 到 b3d9978（cancel-in-flight-environment-launch 已先落）无冲突，ff 推送 master -->
- [x] 4.2 回写本文件的 commit-sha 与偏离说明；`openspec validate stop-automation-only-on-authorization-loss --strict` 退出 0。
- [x] 4.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：撤权环境真被停、未绑定新环境不再被误停、收敛后不再浮出无人认领的浏览器。（桌面客户端改动需出安装包才在运营机生效；出包按 §6 默认不做。）<!-- 簇 131（7 项，含 2 项已知未闭合）；与簇 129/130 共享「必须重新出包才能验」这一前置 -->

### 偏离说明

- **没做自动恢复**（提案里已声明）：授权恢复后不自动拉起引擎，与既有不变量「登录和 roster 刷新 MUST NOT 自动启动普通引擎」保持一致。
- **顺手删掉了一处死代码**：旧的云端绑定原因中文映射表在判据换掉后再无消费者；两处把它当代码块分隔锚点的形状测试改指相邻常量，断言范围未变。
- **未出安装包**：本 change 只到 `master`，运营机上生效需重新打包桌面客户端（按 CLAUDE.md §6 默认不打）。
