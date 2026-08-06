# Tasks

> 蓝图批 2。行为变更批（身份闸机制换血、结果对七条不变——对照表见 design 决策一）。
> 不动 protocol.ts，与批 3（`add-state-observation-command`，动协议）并行安全；登记表会撞，集成串行后到者 rebase。
> 批 3 将按本批新增的 `page_observation` 类别登记其观察命令（已协调）。

## 1. aidcp-edge

- [ ] 1.1 `operation-registry.ts`：类别联合加 `page_observation` / `environment_assist`（注释写清编址判据与「不为将来预留」）；七条改类按 design 决策一/二（browser 维一律不动；acquire 保持 `page_account`）。
- [ ] 1.2 `identity-command-gate.ts`：删 `IDENTITY_RESCUE_OPERATIONS`，判据收敛为纯身份维；模块注释重写（判例四根治实录 + acquire 裁定）。
- [ ] 1.3 测试改写：救援清单断言退役 → 新断言「被拦集合＝身份维推导，含全部留痕命令 + acquire」（按引用零手抄）；七条行为对照表逐条用例（身份未落定时的放行/拒绝，新旧结果一致）。
- [ ] 1.4 入口平台段闸（`edge-client.ts` onMessage，位于未登记闸之后）：首段 ∈ 平台枚举 ⇒ 与本会话账号平台比对，不符拒收 + 如实回执。休眠态注释 + 变异测试（假 `facebook.x.y` 命令发往 xhs 会话 ⇒ 拒）。
- [ ] 1.5 变异验证：①摘掉新断言里 acquire 的特判来源（把其身份维改非 page_account）⇒ 断言红；②把 `interaction.comment` 身份维改掉 ⇒ 断言红；③平台段闸注释掉 ⇒ 变异测试红。
- [ ] 1.6 `typecheck` + `test:acceptance` + 全量 + `gate:native`（未动引擎应全绿）。

## 2. aidcp-automation

- [ ] 2.1 `operation-registry.ts` 同扩容同改类，与 edge 逐字段一致（对表闸验）。
- [ ] 2.2 出口平台段闸（下发路径，`operation_unclassified` 同层）：不符拒发 + 响亮日志；变异测试同 1.4。
- [ ] 2.3 `typecheck` + `test:acceptance` + 全量。

## 3. 集成与部署

- [ ] 3.1 锁步成对落地（同批 1 偏离三的流程：rebase → 全量 → 成对 ff push → 闸复验）；与批 3 的先后按完成顺序，后到者解登记表冲突。
- [ ] 3.2 部署 dev（安全序列 + healthcheck）。
- [ ] 3.3 真机注意：**行为变更但七条结果不变**（对照表）；dev 车队观察一轮身份未落定场景的日志（有账号进入身份终局时，读身份/验证码协助照常放行、acquire 照常被拒）。登记 backlog 若无法当场观察。

## 4. 归档

- [ ] 4.1 tasks 回写（master sha）→ `openspec validate --strict` → archive。
