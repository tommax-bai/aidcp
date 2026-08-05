# Tasks

> **实装中发现堵点是两道不是一道**：云端补齐登记表后实测 `sent=1`（云端这侧通了），
> 但边缘仍静默 20s —— 第二道在边缘 `EdgeClient` 的主动命令路由白名单（§2 第 4 处同步点）。
> 第 6 节即为此追加，proposal 的 Impact 已相应扩大到边缘一个文件。

## 1. aidcp-cloud — 补齐云端登记表

- [x] 1.1 在 `src/comm/operation-registry.ts` 的 `AUTOMATION_OPERATION_REGISTRY` 中，紧随 `'profile.open'` 之后补 `'identity.read_current'` / `'identity.read_self_profile'` 两条 `pageAutomation()`，位置与边缘 `CLOUD_OPERATION_REGISTRY` 一致（便于逐行比对）。 <!-- aidcp-cloud b89b8d4 -->
- [x] 1.2 补验收用例：期望值按引用取自本表里同类命令（`profile.open`）的描述符，不另抄字面量。 <!-- aidcp-cloud b89b8d4 -->
- [x] 1.3 `npm run test:acceptance`（189/189）→ `npm test`（4223 pass / 0 fail）→ `npm run typecheck` 全过。 <!-- aidcp-cloud b89b8d4 -->
- [x] 1.4 变异验证：摘掉这两条登记 → 只有新用例变红，其余三条照绿，归因干净。 <!-- 2026-08-05 -->

## 2. aidcp（控制仓）— 跨仓对表闸

- [x] 2.1 新增 `scripts/operation-registry-parity`：解析三方 Cloud→Edge 登记表，比对键集合与描述符四字段；解析不了的条目判失败绝不跳过；参与方 < 2 判失败。docstring 写清「为什么必须在控制仓」。
- [x] 2.2 变异验证（键集合向）：首次运行即**独立复现真实缺陷**——在未被告知找什么的前提下报出 `aidcp-cloud / aidcp-automation 缺少 identity.read_current, identity.read_self_profile`。
- [x] 2.3 变异验证（字段向）：把派生仓 `pageAutomation` 的 `browser` 由 `required` 改成 `forbidden` → 逐键报 browser 字段差异，证明它不只比键集合。用 `git checkout --` 还原（不用 mv/cp）。
- [x] 2.4 登记入 `scripts/README.md`（与 `protocol-parity` 并列，顺带补上后者当时缺的一行）。
- [x] 2.5 **接进 `scripts/land-change`**（关键：没人跑的闸不是闸）。已在 edge 本次集成中实跑通过：`OK: 3 份 Cloud→Edge 登记表一致，各 46 条`。

## 3. 派生仓同步

- [x] 3.1 `scripts/sync-split-repos --repo aidcp-automation` dry-run 确认**唯一内容差异**是 `src/comm/operation-registry.ts`（两个组装根永不同步、pin 已对齐）→ `--apply`。 <!-- aidcp-automation 0e15132 -->
- [x] 3.2 `aidcp-automation` 侧 `npm run typecheck` 通过。 <!-- aidcp-automation 0e15132 -->
- [x] 3.3 `scripts/operation-registry-parity` 三方一致（各 46 条）。

## 4. 集成与部署（云端侧）

- [x] 4.1 `scripts/land-change aidcp-cloud …--yes`：rebase → 全量测试 → ff 推 master。 <!-- aidcp-cloud b89b8d4 -->
- [x] 4.2 部署 `dev`：§5 安全序列全走（`deploy-target dev --check` → rsync 空跑确认**唯一内容差异是该文件、零删除**、不踩并发会话 16:52 的部署 → 备份 `automation.bak.20260805-190339.pre-opreg.tar.gz` + `.env` → rsync → restart → healthcheck）。部署的是 `aidcp-automation` 派生服务；**未部署 `aidcp-cloud`**（§8.0）。 <!-- 2026-08-05 deployed dev -->
- [x] 4.3 dev healthcheck：schema 门通过 / 写者锁 target=dev / **同步读就绪=ready、业务入口=已放行** / 8787 监听 / NRestarts=0。
- [x] 4.4 dev 实测云端侧已通：`operation_unclassified（type=identity.read_current）` 消失；`sendCommand … action=identity_read_current sent=1`（19:04:24、19:04:25 两账号各一次）。
- [ ] 4.5 **待验**：边缘侧修复部署后，`本人昵称采集超时（edge 静默 ~20s）` MUST 消失、MUST 出现 `identity.observed` 回报。当前仍全数超时——因为运营机 / 本机跑的客户端还是旧构建（见第 6 节）。

## 5. OL

- [ ] 5.1 **不默认部署**。OL 仍会持续报 `operation_unclassified`，直到用户明确要求走发布分支上线（§5 / §6）。

## 6. aidcp-edge — 边缘入口路由（实装中新发现的第二道堵点）

- [x] 6.1 `src/client/edge-client.ts` 的 onMessage 主动命令白名单补 `identity.read_current` / `identity.read_self_profile`；注释写明漏放行=静默丢弃、与「没装到 / 页面读不出来」三者同形。 <!-- aidcp-edge c4ec8bc -->
- [x] 6.2 补**反向结构断言**（`test/client/operation-registry.test.ts`）：以登记表为事实源，逐条去 `edge-client.ts` 源码找分派点；带防空转下限（≥25 条），避免解析失配后「零条全过」与真全覆盖同形。不设例外清单——判据取「出现在任一 `env.type === '<x>'` 比较里」，publish / edge.task / captcha.assist / plan.response 各自的独立分支天然满足。 <!-- aidcp-edge c4ec8bc -->
- [x] 6.3 变异验证：摘掉两条放行 → 新断言变红并点名两条命令；**而原有那张手抄清单的用例依旧绿**，坐实手抄清单对「漏抄」这一失败模式结构上是瞎的。 <!-- 2026-08-05 -->
- [x] 6.4 `npm run test:acceptance`（39/39）+ `npm run typecheck` 通过；`land-change` 全量 + native gate + 两道跨仓对表闸全绿。 <!-- aidcp-edge c4ec8bc -->
- [ ] 6.5 **未做（按 §6 长期授权，出安装包属用户显式触发）**：桌面客户端未重新打包。运营机与本机跑的客户端仍是旧构建，第 6.1 的修复对它们尚未生效——4.5 因此仍待验。

## 7. 真机验收登记

- [x] 7.1 登记 `docs/real-machine-acceptance-backlog.md` **簇 141**（5 项）：身份终局自救链路端到端。本次两处修复只恢复了通道的可达性，**终局自救本身仍未在真机上验过**；簇内含「先确认运营机客户端版本包含 edge `c4ec8bc`」一项，否则验的是旧构建、结论无效。 <!-- 2026-08-05 -->
- [ ] 7.2 归档前置：待 4.5 / 6.5 落地（桌面出包 + 边缘侧实测通）后方可 `openspec archive`。**当前 MUST NOT 归档**——云端半边已生效、边缘半边未到达运营机。
