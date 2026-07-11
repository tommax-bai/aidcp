# Tasks: edge-env-name-live-sync

## 1. aidcp-edge — 源头修（创建路径带回环境名）

- [x] 1.1 `ads-create-flow.cjs` `createEnvironment` 返回体增加 `name`（= 实际写入 AdsPower 的 `name || templateKey`）；`ads-create-env-service.cjs` 已 verbatim 透传、无需改。 <!-- aidcp-edge 1d2620a -->
- [x] 1.2 `main.cjs` `ads:createEnv`：单建路径（返回 `createEnvironmentWithGroupRecovery` 结果，随 1.1 自动带 `name`）；FB 导入批量路径 `created.push({…, name: result.name })` 且单账号返回体带回 `name`。 <!-- aidcp-edge 1d2620a -->
- [x] 1.3 `renderer.js` 创建成功自动选中改为传真名：`selectProfile(r.userId, null, r.name || '', r.platform || platform)`。 <!-- aidcp-edge 1d2620a -->

## 2. aidcp-edge — 兜底修（拉列表时回填花名册名）

- [x] 2.1 `renderer.js` 新增 `reconcileRosterNames(profiles)`：仅覆盖列表中在场、且实时名非空且与花名册名不同的成员，返回改动数；不内部落盘。 <!-- aidcp-edge 1d2620a -->
- [x] 2.2 `refreshEnvs`：在 `!r.truncated` 守卫下先 `reconcileRosterNames` 再 `pruneOrphanRoster`（次序保证 prune 的落盘已含回填名）；prune 未落盘但有回填时单次 `persistRoster`，全程仅一次落盘、无竞态。 <!-- aidcp-edge 1d2620a -->

## 3. aidcp-edge — 回归测试

- [x] 3.1 `renderer-smoke.test.ts`：创建返回带 `name` + `user/list` 含该环境 → 断言左栏/花名册显示真名而非「环境 …末4位」。 <!-- aidcp-edge 1d2620a -->
- [x] 3.2 `renderer-smoke.test.ts`：花名册成员名为空、`user/list` 返回非空名 → 刷新后断言回填为真名（并触发一次落盘）。 <!-- aidcp-edge 1d2620a -->
- [x] 3.3 `renderer-smoke.test.ts`：截断/失败拉取 → 断言绝不回填（不因缺数据误改）。 <!-- aidcp-edge 1d2620a -->
- [x] 3.4 `ads-create-flow.test.ts`：断言 `createEnvironment` 成功返回体含 `name`（缺省回落模板名 + 显式 name 原样回执）。 <!-- aidcp-edge 1d2620a -->

## 4. 验证与集成

- [x] 4.1 `npm run test:acceptance`（16 绿）+ `npm test`（968 绿）+ `npm run typecheck`（干净）全过。 <!-- aidcp-edge 1d2620a 于干净 clone(origin/master cdb7115) 上验证 -->
- [x] 4.2 land 到 edge `master`（`cdb7115..1d2620a`，ff）。edge-only 无 ECS 部署；运营机需 pull master + 重建安装包后生效——已登记真机验收 backlog。 <!-- aidcp-edge 1d2620a landed -->
- [x] 4.3 `openspec validate edge-env-name-live-sync --strict` 通过 → archive。 <!-- 控制仓 archive 于收尾提交 -->

> 落地说明（环境事故）：实装期间本机 edge 并行开发区（`~/codes/aidcp-edge` 公共 `.git` + 各 worktree node_modules）被外部进程清空，导致无法从原 worktree 提交。改动经完整备份后，于 session scratchpad 内一份**全新 origin clone**（基线 `cdb7115`）上重新落好并全量验证，再 push `master`。不涉及、也未触碰本地那批坏掉的 worktree。
