# Tasks — unblock-facebook-consumption-comment-segment

## 1. aidcp-cloud — 等待中的义务不再占用推进槽位

- [x] 1.1 `facebook-consumption-mode-runtime-store.ts` 的 `applyConfirmedView`：槽位指向的动作若同时满足「非 like + `waiting_target`/`waiting_gate` + `dispatch_phase='not_started'`」，则在同一事务内清空 `active_action_id` 并继续正常浏览流程；其余情形逐字不变（尤其 `dispatched` 一律照旧占槽）。 <!-- aidcp-cloud 93635de 判据收成纯函数 isDeferrableFacebookConsumptionObligation，SQL 侧谓词是它的机械转写；账号级闸与冲突回查两处同步改 -->
- [x] 1.2 浏览结果携带被让位的义务（`deferredObligation`），供调用方决定是否驱动；结果种类本身不变（`counted` / `duplicate` / 动作）。 <!-- aidcp-cloud 93635de 刻意只挂在 counted/duplicate 上：action_created 那轮已经有一个面向边缘的动作 -->
- [x] 1.3 同类义务积压上限：造 join / comment 义务前先查本账号本策略号下是否已有同类未终结义务；有则不造第二份、返回已有那份并**响亮记一行**（合并），MUST NOT 静默跳过。 <!-- aidcp-cloud 93635de 同时由迁移 0111 的唯一索引在库层兜住 -->
- [x] 1.4 `role-dispatcher.ts` 的消费浏览处理：拿到 `deferredObligation` 时驱动它；但**本轮产生了点赞就不驱动**（一次浏览至多一个边缘动作）。 <!-- aidcp-cloud 93635de 驱动失败只 warn，不拖住浏览 -->
- [x] 1.5 库层唯一性换代：`uq_facebook_consumption_active_action` 由「每账号至多一条未终结」改成「每账号每动作类型至多一条」。 <!-- aidcp-cloud 93635de migrations/0111（kind=contract；索引名刻意不变，契约门按名字查，改名会让回滚到旧码起不来）；头声明必须带 table: 否则归属推断落进「残留」被派去每个属主库 -->

## 2. aidcp-cloud — 群评论时序策略接进同步读

- [x] 2.1 `kernel/sync-read-facts.ts`：`ContentScheduleSnapshot` 增加 `facebookGroupCommentPolicy`（`joinToFirstCommentHours` / `sameGroupRecommentCooldownHours` / `revision` / `source`，整体可为 null）+ 校验器穷举同步更新。 <!-- aidcp-cloud 93635de -->
- [x] 2.2 `config/api-sync-read-source.ts`：新增策略取值口（与 `facebookOperationPolicy` 同形的注入），写进 `content_schedule` 快照；游标不动（该策略的写入本就 bump `content_schedule`）。 <!-- aidcp-cloud 93635de；**热修 63507bb**：必须逐字段挑，见 §7.2 -->
- [x] 2.3 `server.ts`：单体装配处把策略存储接到同步读源，保持整图一致。 <!-- aidcp-cloud 93635de 该口不 require：策略缺席只挡评论那一格，与基线缺席（FB 全账号跑不起来）后果不同 -->

## 3. aidcp-cloud — 回归覆盖

- [x] 3.1 单测：等待态评论义务在场时，浏览事实照记、第 N 条照产生点赞机会；已 dispatched 的动作仍然占槽不放行。 <!-- aidcp-cloud 93635de test/orchestrator/facebook-consumption-mode-runtime.test.ts 新增 1 例（内存库的唯一性与让位判据同步改） -->
- [x] 3.2 单测：同类义务至多一份（第二次到点不造第二份且留痕）。 <!-- aidcp-cloud 93635de 同上一例内断言 -->
- [x] 3.3 单测：`content_schedule` 载荷校验器接受带策略段、拒绝形状不合法的策略段；策略缺失时消费方仍报同一个具名 blocker。 <!-- aidcp-cloud 93635de test/kernel/sync-read-facts.test.ts；零小时预热必须被拒（等于「刚加完就能评」） -->
- [x] 3.4 变异验证：把让位判据改成恒 false（恢复旧行为），记录哪些用例精确变红。 <!-- aidcp-cloud 93635de 只有 3.1/3.2 那条精确变红，其余 9 例全绿 ⇒ 承重的是它 -->
- [x] 3.5 `npm run test:acceptance` → `npm test` → `npm run typecheck`，记录结果。 <!-- aidcp-cloud: acceptance 189/189；全量 4225 pass / 0 fail；typecheck CLEAN -->
- [x] 3.6 **补一例守住载荷形状**（事故后补）：属主视图带多余键时，发出去的载荷仍 MUST 过校验器。 <!-- aidcp-cloud 63507bb test/config/api-sync-read-source-group-comment-policy.test.ts；判据是「载荷能过校验器」而不是字段值对不对——这次事故里字段值全对 -->

## 4. aidcp-api — 属主侧发得出

- [x] 4.1 组装根把 `FacebookGroupCommentPolicyStore` 接到 `ApiSyncReadSource` 的新取值口。 <!-- aidcp-api 5b11654 -->
- [x] 4.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`。 <!-- aidcp-api: acceptance 24/24；全量 567/567；typecheck CLEAN。热修后重跑 acceptance 24/24 + typecheck CLEAN（7d5cabb） -->

## 5. aidcp-automation — 两个取用点由 unavailable 改为 wired

- [x] 5.1 取用口：从 `content_schedule` 镜像取出策略；镜像陈旧 / 缺载荷 → 返回 null（fail-closed 不变）。 <!-- aidcp-automation 60f9022 落在 automation-main.ts 组装根（两个取用点共用同一实例，各拿一份会让「预热多久」在同一进程里有两个答案） -->
- [x] 5.2 `automation-main.ts` 的两处 `groupCommentPolicy: { state: 'unavailable' }` 改为 wired，两条缺席告警随之消失。 <!-- aidcp-automation 60f9022；dev 实测 21:09 启动日志中两条告警计数=0 -->
- [x] 5.3 `npm run test:acceptance` → `npm test` → `npm run typecheck`。 <!-- aidcp-automation: acceptance 293/293；全量 2273 pass / 0 fail；typecheck CLEAN -->

## 6. 集成与部署

- [x] 6.1 派生仓落地：`scripts/sync-split-repos`（先 dry-run 对账，再 `--apply`）。 <!-- 迁移文件需手工放进 aidcp-automation/migrations（脚本只报不搬）；kernel 6d8ba99 / transport 7d10d2f 已推，三仓 pin 同批抬 -->
- [x] 6.2 三仓合回默认分支并推送。 <!-- aidcp-cloud 93635de + 63507bb / aidcp-api 5b11654 + 7d5cabb / aidcp-automation 60f9022 / aidcp-content 0cbb648（仅 pin） -->
- [x] 6.3 部署 dev（安全序列：target 检查 → 备份 → rsync → restart → healthcheck）。 <!-- 2026-08-05 deployed；备份 {api,automation,content}.bak.20260805-204610.tar.gz + .env.bak；git archive 快照 rsync（不从工作区推）；ECS 上三槽 typecheck 全 CLEAN；迁移 0111 经 /opt/aidcp/cloud 的执行器 `migrate up --allow-contract` 应用（只进 automation 库）；重启序 content → automation → api -->
- [x] 6.4 部署验收（可当场核的部分）。 <!-- 三服务 active、NRestarts=0、六端口全在（8787/8090/8091/8092/8093/8094）、单体仍 inactive+disabled、isales 未碰；库内索引定义已换代为 (account_id, execution_target, action_type) WHERE state<>'terminal'；**dev 上 blocker 已从 facebook_group_comment_policy_unavailable 变为 comment_edge_offline / no_strict_eligible_historical_group ⇒ 策略确实读到了** -->
- [ ] 6.5 **真机验收（未完成，已登记 backlog）**：需边缘客户端接入并跑一场消费模式浏览，核 ① 槽位指针归零 ② 该账号重新出现 `action=like sent=1` ③ 评论义务仍在、不再挡路。部署时边缘全部离线，无法当场观测。
- [ ] 6.6 OL 处置：OL 上 10 个冻结账号在 OL 部署前不会自动恢复（其 blocker 仍是 `facebook_group_comment_policy_unavailable`）。需用户明确要求才走发布分支上 OL。

## 7. 部署期踩到的两个坑（下次照做）

- [x] 7.1 **同步读载荷加字段，部署时必须给该流的镜像版本推一次**。载荷变了而游标没变 ⇒ 消费方按设计报 `same_cursor_payload_drift` 整条拒收 ⇒ 就绪度永不 ready ⇒ **8787 不监听、边缘一台都连不上**。本次在 dev 上 `update config_mirror_version set version=version+1 where mirror_key='content_schedule'`（193→194）后立刻恢复。 <!-- 2026-08-05 实测；这一步 MUST 进 OL 部署清单 -->
- [x] 7.2 **组装根 MUST NOT 把属主存储的视图原样交给同步读源**。属主视图比载荷契约宽（另带 bounds / 冷却来源 / 更新元数据），而校验器判「键刚好是这几个」。TS 对**变量**不做多余属性检查 ⇒ 两侧类型都对、编译全绿、单测全绿，唯一现形方式是生产上整条拒收。已在源头逐字段挑并补回归用例。 <!-- aidcp-cloud 63507bb / aidcp-api 7d5cabb；本次因此在 dev 上造成约 11 分钟 8787 不可连（21:09–21:20） -->
