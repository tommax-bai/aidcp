# Tasks

> 蓝图批 2。行为变更批（身份闸机制换血、结果对七条不变——对照表见 design 决策一）。
> 不动 protocol.ts，与批 3（`add-state-observation-command`，动协议）并行安全；登记表会撞，集成串行后到者 rebase。
> 批 3 将按本批新增的 `page_observation` 类别登记其观察命令（已协调）。

## 1. aidcp-edge

- [x] 1.1 `operation-registry.ts`：类别联合加 `page_observation` / `environment_assist`（注释写清编址判据与「不为将来预留」）；七条改类按 design 决策一/二（browser 维一律不动；acquire 保持 `page_account`）。
- [x] 1.2 `identity-command-gate.ts`：删 `IDENTITY_RESCUE_OPERATIONS`，判据收敛为纯身份维；模块注释重写（判例四根治实录 + acquire 裁定）。
- [x] 1.3 测试改写：救援清单断言退役 → 新断言「被拦集合＝身份维推导，含全部留痕命令 + acquire」（按引用零手抄）；七条行为对照表逐条用例（身份未落定时的放行/拒绝，新旧结果一致）。
- [x] 1.4 入口平台段闸（`edge-client.ts` onMessage，位于未登记闸之后）：首段 ∈ 平台枚举 ⇒ 与本会话账号平台比对，不符拒收 + 如实回执。休眠态注释 + 变异测试（假 `facebook.x.y` 命令发往 xhs 会话 ⇒ 拒）。
- [x] 1.5 变异验证：①摘掉新断言里 acquire 的特判来源（把其身份维改非 page_account）⇒ 断言红；②把 `interaction.comment` 身份维改掉 ⇒ 断言红；③平台段闸注释掉 ⇒ 变异测试红。
- [x] 1.6 `typecheck` + `test:acceptance` + 全量 + `gate:native`（未动引擎应全绿）。

## 2. aidcp-automation

- [x] 2.1 `operation-registry.ts` 同扩容同改类，与 edge 逐字段一致（对表闸验）。
- [x] 2.2 出口平台段闸（下发路径，`operation_unclassified` 同层）：不符拒发 + 响亮日志；变异测试同 1.4。
- [x] 2.3 `typecheck` + `test:acceptance` + 全量。

## 3. 集成与部署

- [x] 3.1 锁步成对落地（同批 1 偏离三的流程：rebase → 全量 → 成对 ff push → 闸复验）；与批 3 的先后按完成顺序，后到者解登记表冲突。
- [x] 3.2 部署 dev（安全序列 + healthcheck）。
- [x] 3.3 真机注意（已登记 backlog 新簇，见 §5）：**行为变更但七条结果不变**（对照表）；dev 车队观察一轮身份未落定场景的日志（有账号进入身份终局时，读身份/验证码协助照常放行、acquire 照常被拒）。登记 backlog 若无法当场观察。

## 4. 归档

- [x] 4.1 tasks 回写（master sha）→ `openspec validate --strict` → archive。

## 5. 实装实录（2026-08-06）

- **落点**：edge master `25ba858`、automation master `a51b57b`（锁步成对落地，闸复验全绿：登记表 43 条逐字段一致、协议逐字一致）。部署 dev（`automation.bak.*-pre-vocab-batch2` 备份 → rsync → restart → active / NRestarts=0 / 8787 / 零 error）。
- **T18 即行为对照表**：七条命令在身份未落定态的放行/拒绝断言原样保持全绿——「结果不变、机制换血」的回归证明。
- **新断言首跑抓到真缺口并钉成棘轮**：`interaction.reply.send` 留痕却不受页面身份闸约束（API 路径、令牌鉴权，close-account 9.1 已登记）——差集断言写死「恰好等于这一条」，新增任何留痕外漏当场红。
- **变异验证全过**（三条 edge + 一条 automation 出口闸），期间两次踩「checkout 复原冲掉未提交实装」坑，已落记忆 mutation-restore-needs-committed-baseline：**变异前必须先 commit**。
- **kernel 类别联合未扩**（它没有新两类）：调用点映射保持 mirror-unknown 闸对观察/处置逐位不变；session.end / task.release 随真实类别归入控制类 ⇒ 该闸放行——唯一有意行为变化，方向与 kernel 文档自陈的「收尾被扣＝死锁」一致。
- 3.3 真机观察：dev 车队正常运行；身份终局场景可遇不可造，登记 backlog 观察项。
