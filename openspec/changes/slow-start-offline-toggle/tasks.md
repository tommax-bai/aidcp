## 0. 前置闸（不满足即停手）

- [ ] 0.1 确认依赖 change `curated-envkey-account-binding` **已 land 并已部署 dev**；未落地即停手——本 change 读它建的绑定列，且两者同改 `aidcp-cloud/src/client-auth/client-user-store.ts`（CLAUDE.md §7 热点文件，**必须串行**）。
- [ ] 0.2 确认该依赖的 **D5 跨客户冲突闸**（accountId 已绑到别的客户的环境上即拒写 + 告警）确实在其中实装；没有它，本 change 就是在用一份持久化的自报身份授权写入，**不该上线**。
- [ ] 0.3 `ls -d ../aidcp-edge ../aidcp-cloud` 确认两个 sub-repo 存在（CLAUDE.md §0）。

## 1. aidcp-cloud — 慢启动写路由改用持久绑定

- [ ] 1.1 把 `src/server.ts:4192` 的 `server.resolveAccountIdForEdge(\`ads-${envKey}\`)` 换成经 `clientUserStore` 读持久绑定解析 accountId；读时与 `accounts` 关联（同构参考 `src/client-auth/client-user-store.ts:789-791`），悬空绑定 fail-closed。
- [ ] 1.2 删掉 `src/server.ts:4193-4194` 的 `reason:'edge_offline'` 分支；无绑定 → `binding_unknown`（路由层落 `409`），绑定查询抛错 → `binding_lookup_unavailable`（路由层落 `503`）。**两者绝不合并**（design D2：把查询失败说成「没绑定」= 用无法证实的事实断言盖住「我没查成」，与 `curated-content-store.ts:1038` 的 42P01→`200 {items:[],total:0}` 是同一个毛病）。
- [ ] 1.3 保持 `slowStartView()` + `dayQuotas` 仍取自**同一个** `riskRegistry.getController(accountId)`（`src/server.ts:4199-4207`），绝不从 store 另读一次。
- [ ] 1.4 改写 `src/client-auth/client-auth-server.ts:278-285` 的注释：保留「绝不走 WS 写 / accountId 客户端永不提交」两条（**仍然成立**），删除并替换「**「边缘不在线就改不了」不是缺陷**」那一段，写明用户已推翻及推翻的理由（真态在云端算、只有用量计数才来自边缘）。

## 2. aidcp-cloud — 新增不依赖边缘的 env-scoped 读

- [ ] 2.1 在 `src/client-auth/client-auth-server.ts` 加 `GET /environments/:envKey/slow-start`：同一份持久绑定解析、ownership fail-closed、复用同一 controller 产出。
- [ ] 2.2 回包 **MUST NOT 含 accountId**（既有 scenario「非所有者请求 fail-closed」明令不得泄露账号身份，读路由不得开侧门）。
- [ ] 2.3 无绑定 → `{ eligible:false, ineligibleReason:'binding_unknown' }`，**不带** `state` / `day` / `since` / `totalDays`（design D6：没账号即不知平台，任何默认值都是伪造）。
- [ ] 2.4 **不要动 `src/comm/protocol.ts:331` 与 `src/risk/risk-controller.ts:82` 的联合类型**：`binding_unknown` 在 `ui.snapshot` 路径上结构性不可达（快照产于 `server.ts:2241` 的按 account 取的 controller ⇒ 有快照必有 account），塞进去 = 加死值 + 平白把本 change 拖进 §2 的两份 protocol.ts 四处同步与热点串行。

## 3. aidcp-cloud — 删除 resolveAccountIdForEdge

- [ ] 3.1 确认 `grep -rn "resolveAccountIdForEdge" src/` 在 1.1 之后**生产调用点归零**。
- [ ] 3.2 删实现 `src/comm/ws-server.ts:316-333` 与接口声明 `src/comm/ws-server.ts:85`。
- [ ] 3.3 **保留 `resolveEdgeIdForAccount`（`src/comm/ws-server.ts:290-306`）不动**——把命令发给没连上的边缘是结构上真的做不到，那道在线判据是本质的（design D4）。
- [ ] 3.4 迁移 `test/comm/ws-server-resolve-account.test.ts:57-65` 的「多账号即拒绝猜测」断言：改成 **PK 单值**测试——`client_environments.env_key` 是 PK ⇒ 一个环境至多一行 ⇒ 绑定读只能返回「恰好一个账号」或「null」，「多候选任取其一」的路径结构上不存在。**该文件整文件都是被删函数的测试**，其余用例随函数一并删除。
  <!-- 注：任务书给的路径 test/ws-server-resolve-account.test.ts 有误，实际为 test/comm/ws-server-resolve-account.test.ts -->

## 4. aidcp-cloud — 测试

- [ ] 4.1 写路由：边缘离线 + 有绑定 → 写入成功并回写后真态；无绑定 → `409 binding_unknown` 且不写入；绑定读抛错 → `503` 且**不是** `binding_unknown`。
- [ ] 4.2 写路由回归：请求体夹带 `accountId` / `since` / `quotaLevel` 仍整块拒；非所有者仍 fail-closed 且不泄露账号身份；`{enabled:false}` 只清 `slow_start_since`、风控档位 / 终态 / 写总闸逐位不动。
- [ ] 4.3 回执**不得**出现「已保存 / 待下发边缘」二态（design D5：慢启动执行体在云端，该状态不存在，照抄即造假）。
- [ ] 4.4 读路由：从未连接的环境读到真态且回包无 accountId；未绑定 → `binding_unknown` 且不含 `state`/`day`/`since`/`totalDays`；非所有者 fail-closed；查询失败 → `503`。
- [ ] 4.5 按 CLAUDE.md §4 回归纪律执行：先 `npm run test:acceptance`，再全量 `npm test`，再 `npm run typecheck`。

## 5. aidcp-edge — 拆掉客户端的内核在线闸

- [ ] 5.1 拆掉 `src/electron/renderer/ui-logic.js:762` 的 `out.disabled = stale`。**保留 `:763` 的 reason 但改口径**——它从此描述**用量计数陈旧**，不再是禁用理由。
- [ ] 5.2 **不要**在 `main.cjs:3831` 的 `'slow-start:set'` IPC 或 `interactionCustomerRequest`（`main.cjs:550`）上新增任何浏览器 / 环境在线闸（两处现在都没有；为「一致」加一个正是 DEFECT 3 的病灶形状）。
- [ ] 5.3 改写 `src/electron/main.cjs:3828-3830` 与 `src/electron/renderer/ui-logic.js:760-761` 两份「离线改不了不是缺陷」注释副本，与云端 1.4 口径一致。

## 6. aidcp-edge — binding_unknown 可见态 + 云端读接线

- [ ] 6.1 `src/electron/renderer/ui-logic.js:734-738` 的文案表补 `binding_unknown` 专属文案（说明尚未识别到账号 + 启动一次该环境完成登录即可绑定）。**只补这个不够**——见 6.2。
- [ ] 6.2 接 `GET /environments/:envKey/slow-start`：没有活快照时用它填这一行。**这是 `binding_unknown` 可见性的前置**——真正让它「什么都不显示」的是 `ui-logic.js:749`（无 payload ⇒ `visible:false` ⇒ 整行不渲染），不是文案表缺键；停止的环境 `dailyUsage` 默认 null（`main.cjs:1038`）⇒ 云端改得再对也无人可点。
- [ ] 6.3 实装 design D3 的来源优先级：**有活快照 → 快照治理；无活快照 → HTTP 读；PUT 回执 → 对发起环境在写入瞬间权威**。三者同源于 `controller.slowStartView()`，但**MUST NOT 逐字段合并**（拼出一个哪个源都没说过的混合态 = 自己造事实）。
- [ ] 6.4 卡上分别标注两条轴：慢启动真态（云端、新鲜）vs 用量计数（本机、离线时陈旧）。文案受 `ui-logic.js:726-733` 既有红线约束且**有测试守着**：`#daily-summary` 全域不得出现「已达 / 上限 / 额度 / 释放 / 已满」，不得出现「新账号」，不得暗示「动作更慢 / 更像真人」。

## 7. aidcp-edge — 测试

- [ ] 7.1 jsdom：**已停止**的环境（`dailyUsage: null` + `status.cloud !== 'connected'`）→ 慢启动行可见且开关可点。**验收必须用已停止的环境**——冷待机（浏览器关、内核在）今天走的是 `status.cloud === 'connected'`，本来就能点，用它测会显示「一切正常」并错误地暗示 6.2 的 HTTP 读多余（与 DEFECT 3 的验收陷阱同形）。
- [ ] 7.2 jsdom：`binding_unknown` → 整行可见、开关禁用、显示专属文案（**不是**落到 `:757` 的 `|| '当前无法启用慢启动'` 泛化兜底）。
- [ ] 7.3 jsdom：离线 + 有真态 → 徽章照常呈现 + 用量标注可能过期；离线写入成功 → 呈现为已生效，**不得**出现「已保存 / 等待本机应用」。
- [ ] 7.4 jsdom：来源优先级与「不得逐字段合并」；env-scoped 失败反馈在够不到云端时如实展示（复用 `slow-start-optimistic-feedback` 已建通路）。
- [ ] 7.5 按 §4 回归纪律：`npm run test:acceptance` → `npm test` → `npm run typecheck`。

## 8. 验证与收口

- [ ] 8.1 `openspec validate slow-start-offline-toggle --strict`。
- [ ] 8.2 复核 diff 无越界：**不得**触碰 `protocol.ts`（两份）、`command-bridge.ts`、`RoleName` 注册、`risk-state-machine.ts`（CLAUDE.md §7 热点文件）。
- [ ] 8.3 部署 dev（CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 测试通过 → ECS 备份 → rsync → restart → healthcheck → 失败即回滚；**绝不碰同机 isales**）。
- [ ] 8.4 客户端改动**默认不出安装包**（CLAUDE.md §6 长期授权）；真机验收项按共享环境登记进 `docs/real-machine-acceptance-backlog.md`。
- [ ] 8.5 真机验收登记：用一个**已停止**（非冷待机）的环境，验证开关可点、写入生效、以及一个未绑定环境显示 `binding_unknown` 专属文案。
- [ ] 8.6 回写本 change tasks.md，格式 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
