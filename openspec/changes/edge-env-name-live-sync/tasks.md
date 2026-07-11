# Tasks: edge-env-name-live-sync

## 1. aidcp-edge — 源头修（创建路径带回环境名）

- [ ] 1.1 `ads-create-flow.cjs` `createEnvironment` 返回体增加 `name`（= 实际写入 AdsPower 的 `name || templateKey`）；`ads-create-env-service.cjs` 已 verbatim 透传、无需改。
- [ ] 1.2 `main.cjs` `ads:createEnv`：单建路径（返回 `createEnvironmentWithGroupRecovery` 结果，随 1.1 自动带 `name`）；FB 导入批量路径 `created.push({…, name: result.name })` 且单账号返回体带回 `name`。
- [ ] 1.3 `renderer.js:2085` 创建成功自动选中改为传真名：`selectProfile(r.userId, null, r.name || '', r.platform || platform)`。

## 2. aidcp-edge — 兜底修（拉列表时回填花名册名）

- [ ] 2.1 `renderer.js` 新增 `reconcileRosterNames(profiles)`：仅覆盖列表中在场、且实时名非空且与花名册名不同的成员，返回改动数；不内部落盘。
- [ ] 2.2 `refreshEnvs`：在 `!r.truncated` 守卫下先 `reconcileRosterNames` 再 `pruneOrphanRoster`（次序保证 prune 的落盘已含回填名）；prune 未落盘但有回填时单次 `persistRoster`，全程仅一次落盘、无竞态。

## 3. aidcp-edge — 回归测试

- [ ] 3.1 `renderer-smoke.test.ts`：创建返回带 `name` + `user/list` 含该环境 → 断言左栏/花名册显示真名而非「环境 …末4位」。
- [ ] 3.2 `renderer-smoke.test.ts`：花名册成员名为空、`user/list` 返回非空名 → 刷新后断言回填为真名（并触发一次落盘）。
- [ ] 3.3 `renderer-smoke.test.ts`：截断/失败拉取 → 断言绝不回填（不因缺数据误改）。
- [ ] 3.4 `ads-create-flow.test.ts`：断言 `createEnvironment` 成功返回体含 `name`。

## 4. 验证与集成

- [ ] 4.1 `npm run test:acceptance` + `npm test` + `npm run typecheck` 全绿。
- [ ] 4.2 land 到 edge `master`，更新主 checkout；edge-only 无 ECS 部署（运营机 pull + 重建安装包后生效，登记真机验收 backlog）。
- [ ] 4.3 `openspec validate edge-env-name-live-sync --strict` → archive。
