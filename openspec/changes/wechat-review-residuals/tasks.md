# Tasks — wechat-review-residuals

## 0. 前提重验（必须最先做）

> **为什么这一节排第一**：本评审历时约 14 小时，期间主干前进 12 个提交并已修掉 3 条发现（M1 / H12 完全修掉、M10 部分形态作废）。**行号必然已漂移**，判据一律按行为写、不按行号；提交号一律按可达性验证、不按记忆。任一条已被他人修复或已失去前提 → 在本文件如实登记「已失效 + 依据」并跳过，**绝不为了勾选而重复实装**。
>
> **同名不同物**：`openspec/changes/` 下已有 `wechat-send-failure-semantics` / `wechat-env-ownership-revocation` / `wechat-console-enum-and-ledger` / `wechat-sync-timestamp-honesty` 四个**重名但内容不同**的上游 change。核对「是否已被上游覆盖」**必须读内容，不得凭 change 名判断**。

- [x] 0.1 逐条重验下表判据（撰稿基线：`aidcp` `origin/main`=`2cff970`，`aidcp-cloud` `origin/master`=`6122083`，`aidcp-edge` `origin/master`=`0d38116`，`aidcp-console` `origin/master`=`643aad5`）。

| 发现 | 仓 | 行为判据（按此核对，不按行号） |
| --- | --- | --- |
| **H6** | cloud | `src/interactions/send-orchestrator.ts` 的 `dispatchQueued`：`sent === 0` 时是否仍调 `markDispatchFailed` 把 job 置终态？投递前是否**仍无**任何边缘暂停态检查？同函数 `!edgeId` 分支是否仍不建 attempt、留 `queued`（那条不对称是否还在）？ |
| **H9** | cloud | `migrations/0039_interaction_inbox.sql` 的 `idempotency_key` 列是否仍是**无条件** `TEXT NOT NULL UNIQUE`（而非部分索引）？`replyIdempotencyKey()` 是否仍不含 attempt 序号？`src/interactions/interaction-store.ts` 的 `createAttempt` catch 是否仍把 23505 一律映射成「已有发送尝试在进行中」？`interaction_send_attempts.retryable` 是否仍无消费者（**注意**：全仓其余 `retryable` 命中多为 `InteractionError.retryable`，是另一回事，别数错）？ |
| **H1** | cloud | `src/client-auth/client-user-store.ts` 的 `enqueueOffboard` 里，撤销读写开关（`UPDATE interaction_runtime_controls ... comments_read_enabled=false ...`）与撤销登录态（`UPDATE interaction_auth_state SET status='disabled' ...`）两条语句的 WHERE 是否仍带 `env_key=$2`、且是否仍无人检查 `rowCount`？ |
| **H12 遗留缺口** | cloud | `enqueueCleanupHold` 是否仍只写 `client_env_revocation_holds`、**完全不撤销任何能力**？（若 `60acb89` 被 revert，则 H12 本体复活 → 停手登记，重新评估范围。） |
| **M11** | cloud | `src/interactions/runtime-controls-provider.ts` 的 `projectRuntimeControls` 是否仍把缺失环境标识回落成账号 id（`controls.envKey?.trim() || accountId`）、`scopeValid` 是否因此恒真？`hasPendingOffboard` 是否仍只读 `interaction_offboards`、对墓碑无感？ |
| **H7** | edge + cloud | `src/wechat-channels/dm-sync.ts` / `comment-sync.ts` 的 `sync()` 定向分支是否仍用 `request.requestedAt` 合成占位对象的 `updatedAt`？`src/wechat-channels/types.ts` 的两个 `updatedAt` 是否仍是非空 `number`？cloud `interaction-store.ts` 的线程 upsert 是否仍是 `last_message_at=GREATEST(...)`（即假值是否仍不可回退）？`src/comm/protocol.ts` 的 `InteractionSyncThread.updatedAt` 是否仍是非空 `number`（**若已被他人改成可空，登记后可简化为直接传 `null`；但 MUST NOT 由本 change 去改它——那是热点文件**）？ |
| **M12** | cloud + console | 云端 `src/risk/types.ts` 的 `RISK_ACTIONS` 是否仍含 `dm_reply`（9 项）？后台 `src/types/aidcp-enums.ts` 的 `RISK_ACTIONS` / `RISK_ACTION_LABEL` / `RISK_ACTION_COLOR` 是否仍缺它（8 项）？`src/types/api.ts` 的 `QuotaAction` 联合类型是否仍是**另一份**缺 `dm_reply` 的手写副本？`src/pages/QuotasPage.tsx` 的动作列渲染与编辑弹窗标题是否仍为裸取、`ACTION_ORDER` 对未知值是否仍给 `NaN`？ |
| **M10** | cloud | `src/risk/risk-controller.ts` 的 `applyColdStartClamp` 是否**仍不查** `SLOW_START_PLATFORMS`（白名单是否仍只被 `slowStartView()` 引用）？`coldStartDailyCap` 是否仍是「`platform === 'facebook'` 走 FB 曲线、否则小红书曲线」（即视频号仍落 XHS 曲线）？`applyColdStartClamp` 里对 `wechat_channels` 的 `dm_reply` 逐窗口特判是否仍在？先跑 `git log -3 -- src/risk/risk-controller.ts` 看有没有人在飞。 |
| **M9** | aidcp | 逐个 sha 跑 `git merge-base --is-ancestor <sha> origin/<默认分支>`。**MUST NOT 用 `git cat-file` 判可达性——它对悬空提交照样回 `commit`**。冻结 spec `openspec/changes/wechat-channels-interaction-management/specs/wechat-channels-interaction/spec.md` 里写死的 `MessageType` 总数，与两端实测对照：`awk '/export type MessageType/,/pong.;/' src/comm/protocol.ts \| grep -cE "^\s*\|\s*'"` 两仓各跑一次。 |

- [x] 0.2 确认「不改 schema」的前提仍成立（H1 / H12 遗留缺口所需）：`interaction_runtime_controls` 的 `env_key` 仍可空、主键仍是 `(platform, account_id)`；`interaction_auth_state` 的 `env_key` 仍 `NOT NULL`、主键仍是 `(platform, account_id)`。若已有他人加了 migration 改动这两处，停手并在本文件登记，重新评估 proposal 的 schema 判断。

<!-- 2026-07-17 revalidation: aidcp origin/main=3dbe4df, cloud origin/master=293c4e5, edge origin/master=3a70981, console origin/master=4ea8785. H6/H9/H1/H12 residual/M11/H7/M12/M10/M9 all remain reproducible by the behavioral criteria above; 60acb89 was not reverted. interaction_runtime_controls.env_key remains nullable with PK (platform,account_id), interaction_auth_state.env_key remains NOT NULL with the same PK, so the no-schema-change premise for H1/H12 still holds. Both protocol MessageType unions count to 91. -->

## 1. aidcp-cloud — H6：暂时不可投递不得判终态失败

文件：`src/interactions/send-orchestrator.ts`（+ `src/server.ts` 一行注入）

- [x] 1.1 给 `InteractionSendOrchestrator` 的构造 deps 增加可选 `isEdgePaused?: (edgeId: string) => boolean`，语义与注入方式对齐 `src/publish-agent/publish-dispatcher.ts` 的同名 dep（未注入 → 视为从不暂停，行为不变）。在 `server.ts` 装配处注入 `ws-server` 的 `isEdgePaused`（该函数在 `server.ts` 已被另外三处消费，照抄即可）。**`server.ts` 是共享文件：合回前先 rebase 再改，勿做无关重排。**
- [x] 1.2 在 `dispatchQueued` 中，**解析到 edgeId 之后、`createAttempt` 之前**加暂停闸：`isEdgePaused(edgeId)` 为真 → 不建 attempt、不改 job 状态（留 `queued`）、抛可重试错误（`INTERACTION_UPSTREAM_UNAVAILABLE`，503，retryable=true），使 30s 恢复循环的 catch 记 `deferred` 而非烧稿。计量打 `interaction_send_blocked_total{reason:'edge_paused'}`（与既有 `edge_offline` 分支同格）。
- [x] 1.3 `sent === 0` 分支：**不再**调 `markDispatchFailed`、**不再**把 job 置终态。改为把已建的 attempt 作废到不占活跃唯一槽的状态（与 2.1 的部分索引口径一致），job 回 `queued`，抛 503 可重试错误。计量 `interaction_send_attempt_total{status:'deferred',reason:'not_delivered'}`。
- [x] 1.4 保留 `sent > 1` 与 `pushToEdges` 抛异常两条既有分支的 `ambiguous` 语义**不变**——那两条是「无法证明命令未离开进程」，保守留 ambiguous 是对的，**勿一并放开**。
- [x] 1.5 确认 job 回 `queued` 后能被 `pendingQueuedJobs()` 捞到：该查询要求「不存在 status IN ('created','dispatched','ambiguous') 的 attempt」。1.3 作废 attempt 的目标状态必须不落在这三个里，否则 job 会被永久排除出恢复循环。**这是本条最容易埋的新雷，必须写用例锁住（见 5.2）。**

## 2. aidcp-cloud — H9：幂等键仅在活跃态唯一 + 错误映射拆分

文件：`migrations/`、`src/interactions/interaction-store.ts`

- [x] 2.1 新建 `migrations/0046_interaction_idempotency_active_unique.sql`：`DROP` `interaction_send_attempts.idempotency_key` 上的无条件 UNIQUE 约束，改建部分唯一索引 `uq_interaction_send_attempts_active_idem ON interaction_send_attempts (idempotency_key) WHERE status IN ('created','dispatched','ambiguous')`，写法对齐同表兄弟索引 `uq_interaction_send_attempts_active_job` / `_active_account`。保留列上的 `CHECK (idempotency_key ~ '^[a-f0-9]{64}$')`。
- [x] 2.2 **核实迁移落地方式**：interaction 系列表**不自建 schema**——`interaction-store.ts` 的 `init()` 是 fail-closed 的 schema 预检（缺列即抛 `interaction_schema_missing_run_0042`，只关掉这一个功能而非整个进程）。故 0046 必须**手工在目标库执行**后才能部署新代码。把 0046 的新索引加进 `init()` 预检（如检 `pg_indexes` 中该索引存在），并把 `Error` 文案更到 `interaction_schema_missing_run_0046`。
- [x] 2.3 `createAttempt` 的 23505 映射拆分：先查该 job 是否**真有**活跃 attempt（`status IN ('created','dispatched','ambiguous')`）。真有 → 保留现文案「已有发送尝试在进行中」（409 `INTERACTION_STATE_CONFLICT`）；没有 → 如实报键冲突（新文案，勿冒充「进行中」），且**不得**被静默吞掉后回报「已排队」。
- [x] 2.4 处置 `retryable` 列：接线成恢复循环的真实判据，或删除该列的写入与列本身。**二选一，不得留着当无消费者的谎言标记**。若选接线，`markDispatchFailed`（`retryable=true`）与 `applyReplyResult` 两处赋值口径必须统一。若选删除，同批 migration 处理。**范围克制**：本 change **不**做「云端按 `errorCategory` 给失败结果分流」——那是 M1，已由上游 `wechat-send-failure-semantics` 覆盖，勿重复实装。
<!-- 2.4 implementation choice: removed the unused retryable column and all writes in migration 0046; no errorCategory-based Cloud routing was added. -->
- [ ] 2.5 部署前在目标库手工执行 0046 并记录执行凭据（**只记命令与库位置，不记任何密码 / 连接串**）。
<!-- 2026-07-17 safety gate: read-only target checks passed, but live env inventory confirms dev uses 127.0.0.1:5432/aidcp while ol uses 121.89.85.150:5432/aidcp. Migration 0046 drops a unique constraint and a column, so docs/deployment-environments.md forbids applying it until ol has an independent PostgreSQL boundary. No migration was run. -->

## 3. aidcp-cloud — H1 + H12 遗留缺口 + M11：吊销作用域

文件：`src/client-auth/client-user-store.ts`、`src/interactions/runtime-controls-provider.ts`（+ `src/server.ts` 一行注入）

- [x] 3.1 `enqueueOffboard` 中撤销读写开关的 UPDATE：删除 WHERE 里的 `env_key=$2`，只按 `platform='wechat_channels' AND account_id=$1` 定位（与同文件 / 同库其余写入者一致，也与「授权」侧一致）。
- [x] 3.2 `enqueueOffboard` 中撤销登录态的 UPDATE：同样删除 `env_key=$2`。该表 `env_key` 虽为 `NOT NULL`（不触发空值语义），但环境重绑后传入值可能与库内值不符而静默漏改，且该条件相对主键本就冗余。
- [x] 3.3 两条 UPDATE 均检查 `rowCount`：撤销登录态时命中 0 行 = 结构性异常（调用方是在已读到绑定后才进来的），MUST 抛错让事务回滚，MUST NOT 继续返回成功。撤销读写开关时命中 0 行的判定见 3.4。
- [x] 3.4 明确「读写开关行不存在」的语义：该行由管理员配置或边缘上报惰性创建，可能确实不存在。**不存在 ≠ 撤销失败**（没有能力可撤），但**存在却没改到**必须报错。实现上先 UPDATE 并读 `rowCount`，为 0 时再确认该账号确无控制行；确有行却没改到 → 抛错回滚。**MUST NOT 用「行可能不存在」当借口吞掉所有 0 行情况。**
- [x] 3.5 **H12 遗留缺口**：`enqueueCleanupHold` 在同一事务里撤销该环境对应账号的读写能力与登录态（复用 3.1–3.4 的撤销逻辑，抽一个私有方法，勿复制粘贴两份）。注意墓碑路径的入口条件恰是「无登录绑定」，因此 accountId 可能取不到：**只在能确定账号身份时撤销，取不到时 MUST NOT 伪造 accountId**，此时依赖 3.6 的恢复路径与 3.8–3.10 的投影屏障兜底。
- [x] 3.6 恢复路径写进代码注释并补测：清理墓碑不是终点——`reconcileRevocationHolds` 在**迟到的登录态**出现（`interaction_auth_state` 出现该 `env_key` 的行）时，把墓碑兑现成正式 offboard 并删除墓碑。**任何进入不可用态的转换都必须回答「什么把它拨回来」，这条就是答案，必须有测试钉住**（见 5.5）。
- [x] 3.7 确认数据库级 guard（`client_env_revocation_holds` 存在时 scope 写入 fail closed 的触发器）在本次改动后行为不变，勿误伤。
- [x] 3.8 **M11**：删除 `projectRuntimeControls` 里 `envKey = controls.envKey?.trim() || accountId` 的回落。环境标识缺失时 MUST NOT 用账号 id 顶替；投影出的环境标识只能是库里存的那个。
- [x] 3.9 环境标识缺失（未绑定）时，`commentsReadEnabled` / `commentsReplyEnabled` / `dmReadEnabled` / `dmSendTextEnabled` 一律投影为 false（fail-closed：能力缺失必须全关，不得沿用旧值）。
- [x] 3.10 未了结的清理墓碑与待处理解绑同等对待，构成能力屏障：投影时若该账号所属环境有未了结墓碑 → 全部能力 false。墓碑查询实现在 `ClientUserStore`（该 store 是 `client_env_revocation_holds` 的唯一读写者，保持这一约束），按 accountId 经 `interaction_auth_state` 关联到 `env_key` 再查墓碑；以新增 dep 注入 `projectRuntimeControls`，并在 `server.ts` 接线。**`server.ts` 是共享文件：极小 additive 编辑，先 rebase 再改。**

## 4. aidcp-cloud — M10：冷启动 clamp 尊重慢启动平台白名单

文件：`src/risk/risk-controller.ts`

> 前置：0.1 已确认该缺口仍成立。若 0.1 判定已失效 → 整节登记作废并跳过。

- [x] 4.1 动手前 `git log -3 -- src/risk/risk-controller.ts` 确认无并发改动在飞；有则先与该 change 协调串行。该文件**不是**热点清单成员（热点是 `risk-state-machine.ts`），但改动频率高。
- [x] 4.2 让 `applyColdStartClamp` 与对外投影 `slowStartView` 共用同一道平台准入判定：平台不在 `SLOW_START_PLATFORMS` 内 → **原样返回风控缩放配额、不叠任何 clamp**。判定 MUST 提取为单一函数供两处调用，MUST NOT 各写一份（各写一份正是本缺口的成因）。**结论 MUST 与锚点来源无关**——账号级开关与 env 全局旁路两条路径下都必须一致，旁路不得成为绕过准入的后门。
- [x] 4.3 删除 `applyColdStartClamp` 里针对 `wechat_channels` 的 `dm_reply` 逐窗口特判——4.2 落地后视频号根本不会走到 clamp，该分支成死代码。**MUST NOT** 改为「再补一个 `comment` 豁免」：那会把「白名单说不支持、clamp 照夹」的矛盾固化，且下一个新增动作会再次默认落入被夹集合。

## 5. aidcp-cloud — 测试（克制：关键行为少数用例）

- [x] 5.1 `dispatchQueued`：边缘暂停态下不建 attempt、job 仍为 `queued`、抛 503（H6 主用例）。
- [x] 5.2 `dispatchQueued`：`sent===0` 后 job 仍为 `queued` 且**能被 `pendingQueuedJobs()` 捞到**（锁 1.5 的雷）。
- [x] 5.3 同一 job 前一次 attempt 已 `failed` 后再次 `dispatchQueued`：不撞 23505、能建出第 2 个 attempt（H9 主用例，需部分索引已生效的库或等价桩）。无活跃 attempt 时的键冲突不得回「已有发送尝试在进行中」（H9 假话用例）。
- [x] 5.4 H1 原始失败场景：管理员先配好开关、客户端从未连过（`env_key` 为 NULL）→ 触发解绑 → 断言读写开关全 false、登录态 `disabled`、且返回成功。**修前必红。** 再补一条：模拟撤销登录态命中 0 行 → 断言整笔回滚且**不**返回成功。
- [x] 5.5 墓碑恢复路径：先立墓碑 → 断言能力已撤销（账号身份可确定时）→ 再写入登录态 → 跑 `reconcileRevocationHolds` → 断言产出 offboard、墓碑被删、能力保持关闭。
- [x] 5.6 M11：① 控制行 `env_key` 为 NULL → 投影四项能力全 false 且不出现被顶替的环境标识；② 有未了结墓碑 → 投影全 false。
- [x] 5.7 M10：① 全局旁路开关打开 + 视频号账号 + 入库 1 天 → `effectiveQuotas()` 逐位等于风控缩放配额，`comment` / `dm_reply` MUST NOT 被夹成 0；② 同条件下 Facebook / 小红书账号的 clamp 行为逐位不变（零回归）。
- [x] 5.8 H7 云端侧：`thread.updatedAt` 远超 `observedAt` 的批次 MUST 被 422 拒绝，且 `interaction_threads` MUST 无写入（不得部分落库）。
- [x] 5.9 `cd ../aidcp-cloud && npm run test:acceptance`（安全红线 `AC-RISK-*` / `AC-PUB-*` / `AC-PROTO-*` 必须绿）→ `npm test` → `npm run typecheck` 全绿。
<!-- Final post-rebase validation: acceptance 55/55; full suite 2421 passed, 8 explicitly gated skips; typecheck passed. Disposable PostgreSQL 16 integration passed 8/8 before integration. -->

## 6. aidcp-cloud — H7 云端侧：入口拒绝未来时间戳

文件：`src/interactions/interaction-store.ts`

> **协调**：此文件可能与 `wechat-store-and-circuit` 撞车。改动务必 surgical、只动同步批次入口校验这一处。

- [x] 6.1 同步批次入口：任一 `thread.updatedAt` 超过 `payload.observedAt + 容差`（取 5 分钟时钟偏移容差）即以既有的 `InteractionError('INTERACTION_VALIDATION_FAILED', …, 422)` 拒绝整个批次，错误文案点名违规的 `externalThreadId` 与两个时间值。**MUST NOT 静默 clamp**——clamp 会把「边缘在编值」这个 bug 藏起来，而 `GREATEST` 下未来值一旦落库就永久粘住，必须让它响。
- [x] 6.2 确认拒绝路径不会把同步**永久卡死**：批次被拒 → edge 的 `assertMatchingAck` 不通过 → checkpoint 不提交 → 下次同步重试同一游标。恢复路径是「修边缘的编值 bug 后重试即自动通过」，无需人工改库、无需清墓碑。若核对发现拒绝会写入任何持久化的失败 / 墓碑状态，必须一并给出把它拨回来的机制。

## 7. aidcp-edge — H7：定向同步不得编造时间戳

- [x] 7.1 `src/wechat-channels/types.ts`：`WechatPost.updatedAt` 与 `WechatDmSession.updatedAt` 改为 `number | null`。`api-schemas.ts` 的解析层不动——它已经在用 `epochMs()` 从平台响应取真值并在缺失时抛 schema-changed，`number` 可直接赋给 `number | null`。
<!-- Baseline drift: widening the internal type required null-safe narrowing in two api-schemas.ts dedupe comparisons; epochMs parsing and schema-changed behavior remain unchanged. -->
- [x] 7.2 `src/wechat-channels/comment-sync.ts`：定向分支合成的 `WechatPost` 传 `updatedAt: null`；`buildThreads()` 改为 `post.updatedAt === null ? root.createdAt : Math.max(post.updatedAt, root.createdAt)`。根评论的 `createdAt` 是平台值且恒存在，故评论侧线程时间戳**永远**是平台事实，不需要「不发这一行」。
- [x] 7.3 `src/wechat-channels/dm-sync.ts`：定向分支合成的 `WechatDmSession` 传 `updatedAt: null`；`publishThreadPage()` 计算 `threadUpdatedAt = session.updatedAt ?? max(messages.map(m => m.createdAt))`（本页无消息时为 `null`）。
- [x] 7.4 `src/wechat-channels/dm-sync.ts`：`threadUpdatedAt` 为 `null` 时，本批次 `threads: []`（不发该线程行）。**此路径只在本页消息也为空时可达**——云端要求消息必须引用批次内线程（「消息引用了批次外线程」422），故不会造成孤儿消息。`cursorBefore` / `cursorAfter` / `hasMore` / checkpoint 提交照旧，翻页不受影响。
- [x] 7.5 检查 `src/wechat-channels/protocol-validation.ts` 的线程校验（`updatedAt: timestamp(...)`）无需改动——本方案不引入空值上线。**红线**：`InteractionSyncThread.updatedAt` 保持非空 `number` 是**刻意的设计约束**，为的是避开两份 `protocol.ts`（热点文件）。**MUST NOT** 为了表达「未知」去把协议字段改可空。
- [x] 7.6 补测（`test/wechat-channels/sync.test.ts`，克制，两条即可）：① 定向评论同步：线程 `updatedAt` MUST 等于根评论 `createdAt`，MUST NOT 等于 `request.requestedAt`（用与 `requestedAt` 明显不同的桩时间，断言不含 `requestedAt`）；② 定向私信同步：有消息时线程 `updatedAt` MUST 等于本页消息最大 `createdAt`；本页为空时批次 MUST 不含线程行且 checkpoint 照常推进。
- [x] 7.7 `cd ../aidcp-edge && npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。**不打安装包**（CLAUDE.md §6：打包默认不做）。
<!-- Final validation after the last concurrent master advance and rebase: acceptance 23/23; full suite 1668/1668; typecheck passed. No installer build or publication was performed. -->

## 8. aidcp-console — M12：动作镜像补齐 + 未知值优雅回落

- [x] 8.1 在 `src/types/aidcp-enums.ts` 的 `RISK_ACTIONS` 补入 `dm_reply`，并同步补齐 `RISK_ACTION_LABEL`（中文文案：私信回复）与 `RISK_ACTION_COLOR`（择一未被占用的 AntD preset 色，与既有八色不重复）。三处必须同批改——`RISK_ACTION_LABEL` / `RISK_ACTION_COLOR` 是 `Record<RiskAction, …>`，只补数组会直接 typecheck 红；既有镜像自洽测试也会对「动作集 ⇔ label 键集 ⇔ color 键集」双向断言。
- [x] 8.2 **同批补 `src/types/api.ts` 的 `QuotaAction`**——它是**另一份手写的 8 项联合类型**，与 `aidcp-enums.ts` 的镜像各写一遍。漏它会让 wire 类型继续撒谎（`QuotasPage` 的行类型仍不认 `dm_reply`）。顺带评估能否让它由 `RiskAction` 派生以消灭这份副本；**若派生会牵动大面积消费方则不做**（YAGNI），但必须在本文件登记「为何保留两份」。
<!-- QuotaAction now derives directly from RiskAction; no duplicate union remains. -->
- [x] 8.3 更新 `src/types/aidcp-enums.test.ts` 里的云端真值快照断言，使其期望 9 项动作。**MUST NOT** 只改期望值而不改镜像本体（那会让哨兵恒绿、彻底失去探测能力）。
- [x] 8.4 让按线上值取中文文案的地方对未知值优雅回落：为标量文案映射提供与既有 `tagOf()` 同范式的容错取值入口（未知值返回原值字符串，绝不返回 `undefined`、绝不抛），并把 `src/pages/QuotasPage.tsx` 的动作列渲染与编辑弹窗标题两处裸取改走它。排序用的 `ACTION_ORDER` 对未知值 MUST 回落为确定性的末位序号，MUST NOT 产生 `NaN` 比较（`NaN` 会让整表排序结果不稳定）。
- [x] 8.5 扩 `src/enumTagSafety.test.ts` 的扫描面：现有正则只禁「大写映射按变量索引后再读 `.color/.text/.label`」，标量文案映射（`SOME_LABEL[wireValue]` 直接当子节点渲染）不在禁列（该文件的注释已明说这一豁免——记得同批更新那段注释）。加一条针对 `*_LABEL` 类映射按变量裸取的检查，命中即失败并指向容错入口。**范围克制**：只覆盖会被渲染成可见文案的映射，不要把所有大写映射一律入罪（会误伤纯内部常量表）。
<!-- The scalar guard covers only *_LABEL visible-text maps; existing visible lookups were routed through labelOf, while color/status/internal maps remain outside the rule. -->
- [x] 8.6 补测（克制，两条即可）：① 安全限额页拿到含 `dm_reply` 的行时，动作列渲染出中文文案而非空白，编辑弹窗标题不含 `undefined`；② 拿到一个镜像里不存在的动作值时，该行仍渲染（原值可见）、整页不崩、其余行不受影响。
- [x] 8.7 `cd ../aidcp-console && npm test` + `npm run typecheck` 全绿。（注：本仓 portal 类测试已知 flaky，需要时串行复跑。）
<!-- Final serial single-worker rerun: 174 passed, 1 explicitly gated skip; typecheck passed. A concurrent three-repo run hit existing UI timing flakes, so only the clean serial result is used as the final gate. -->

## 9. aidcp（中控）— M9：台账订正 + 冻结 spec 计数订正

> 改的是 `openspec/changes/wechat-channels-interaction-management/` 下的文件（另一个仍活跃的 change）。只订正可验证性，**MUST NOT** 改动其 task 的完成判定或勾选状态。

- [x] 9.1 用 `git merge-base --is-ancestor` 逐一复核 `tasks.md` 中出现的全部提交号，列出「可达 / 不可达」清单。**不可达 ≠ 工作丢了**——先在目标默认分支上按提交 subject 搜等价提交（`git log --oneline origin/<默认分支> --grep="<subject>"`），确认内容一致后再替换。
<!-- Fresh reachability audit: 20 distinct task SHAs were reachable; a678003, cdc3ffc, 777b30f, c4dcf79 and 1995721 were not. Their same-subject default-branch equivalents are recorded below; all four Edge pairs have identical stable patch IDs, while the control pair has matching subject/file stats and a range-diff limited to rebased surrounding context. -->
- [x] 9.2 将 5 处不可达提交号替换为主干等价提交（下列为 2026-07-17 用 `merge-base --is-ancestor` 实测的结果；**接手时必须自行复核可达性再写入，不要盲抄**）：

  | 位置 | 悬空（不可达） | 主干等价（可达） | subject |
  | --- | --- | --- | --- |
  | 控制仓 `aidcp` | `a678003` | `3aa51de` | `docs: freeze wechat channels interaction contract` |
  | 边缘 `aidcp-edge` | `cdc3ffc` | `723a7fd` | `feat: add WeChat Channels interaction adapter` |
  | 边缘 `aidcp-edge` | `777b30f` | `ccbb2e7` | `fix: declare WeChat Channels delegated actions` |
  | 边缘 `aidcp-edge` | `c4dcf79` | `3649e05` | `fix: make WeChat reply execution atomic` |
  | 边缘 `aidcp-edge` | `1995721` | `1eb5e93` | `fix(electron): harden interaction and customer auth boundaries` |

  已复核为**可达、无需改动**：edge `49028a4` / `dc9dac6` / `6ad092b`，cloud `ae7b4e8` / `f6548504`，console `3a477c1`。
- [x] 9.3 改写被证伪的那句表述（tasks.md 里「the control contract `a678003` … are all integrated on their default branches」）：按事实写明各仓真实集成到默认分支的提交号（即 9.2 订正后的等价提交），去掉对悬空提交的「已集成」断言。
- [x] 9.4 消除两份台账的矛盾：`docs/real-machine-acceptance-backlog.md` 已于 2026-07-17 把 `a678003` 订正为 `3aa51de`（含说明），与本次订正结果对齐；两份对同一事实 MUST 给出同一结论。若另一份记的结论与实测冲突，以 `merge-base` 实测为准并在本文件登记依据。
- [x] 9.5 订正冻结 spec 的消息类型总数：`openspec/changes/wechat-channels-interaction-management/specs/wechat-channels-interaction/spec.md` 里写死的 `89` → 改为实测值（0.1 复测；2026-07-17 两端各为 91）。同时在该句补一条口径注记：以两端 `protocol.ts` 的联合类型穷举为准，数字为人工维护、可能滞后。**只改这一处数字与口径**，MUST NOT 顺手改动该 spec 的其它语义。
- [x] 9.6 `openspec validate wechat-channels-interaction-management --strict` 与 `openspec validate wechat-review-residuals --strict` 均通过。

## 10. 集成与部署

- [x] 10.1 合回各仓默认分支前 rebase 到最新默认分支、解冲突后重跑该仓的 `test:acceptance` + `npm test` + `typecheck` 再 ff 合并；push 遇 non-ff 一律 rebase 重来，**绝不 force**。
<!-- Default-branch integration: cloud 780f104, edge db98d75, console 28776f1. Edge rebased repeatedly as concurrent master advanced; the final ff push followed a fresh 23/23 + 1668/1668 + typecheck run. All three SHAs were verified reachable from origin/master with merge-base --is-ancestor. -->
- [ ] 10.2 部署 dev（按 CLAUDE.md §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck；**绝不碰同机 isales**）。**云端部署前必须先手工执行 0046**（见 2.5）——interaction 表不自建 schema，未跑迁移即部署会让互动功能 fail-closed 关停。
<!-- Deployment intentionally stopped before backup/migration/rsync/restart: 0046 contains destructive DDL while dev and ol still share the aidcp PostgreSQL database. No isales service or directory was touched. -->
- [x] 10.3 edge 侧改动的默认收尾只到 commit / push（+ 测试）；**不打安装包**。

## 11. 真机验收（登记 backlog，不在本 change 内跑）

- [x] 11.1 把下列项登记进 `docs/real-machine-acceptance-backlog.md`。**优先并入视频号既有簇**；若需新建簇，簇号取**当前文件末尾簇号 +1**（跑 `grep -oE '^## 簇 ?[0-9]+' docs/real-machine-acceptance-backlog.md | tail -1` 现取，**不要硬编码**——并行 session 会撞号）。
  - **H6 / H9**：① 真实验证码暂停窗口内，排队积压不被烧成终态、暂停解除后 30s 内自动重投并发出；② 一条 `failed` 的回复 job 重新生成后能真正再次发出（不再 409 空转）。
  - **H1 / H12 遗留**：① 运营在后台为某视频号账号配好互动开关（该账号客户端从未连过）→ 客户在客户端删除该环境 → 后台面板该账号 MUST NOT 再显示「允许读取」，登录态 MUST 显示已停用；② 管理员对一个「已授予、从未扫码」的环境撤销归属 → 能撤下来且能力当场关闭；随后该环境首次扫码登录 → 墓碑被兑现成正式解绑、能力保持关闭。
  - **H7**：① 在 dev 打开视频号读取开关 → 对一个有历史评论的帖子点「重新同步评论」→ 收件箱中该帖下会话 MUST 保持原有时间与排序位置，MUST NOT 跳顶显示「刚刚」；私信同一路径同样验一次。② 存量污染诊断：用诊断查询列出 `last_message_at` 超过该线程 `max(platform_created_at)` 的可疑视频号线程，由运营对照真机判定是否需要人工修库；**注明全局同步路径下该情形可能是合法的**（平台会话更新时间可领先于已翻页到的最新消息），故禁止一刀切回填。
  - **M12**：安全限额页在真实数据下的运营可读性——三行私信回复限额的动作列显示中文、编辑弹窗标题正常。
  - **M10**：视频号账号在开启全局旁路后的真实配额放行（`comment` / `dm_reply` 不为 0）。

## 12. 收尾

- [ ] 12.1 本文件按格式回写实装台账：`<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。**sha 必须取自已推送提交**，写入前用 `git merge-base --is-ancestor <sha> origin/<默认分支>` 自证——本 change 的 §9 存在理由就是台账 sha 不可达。**不得编造或填写悬空提交。**
<!-- aidcp-cloud 780f1049c876ca3fe6d4a32f2647f99399e98335 implementation; pushed and reachable from origin/master -->
<!-- aidcp-edge db98d75ee28ee96c8d4b1f28b16fcbf97b283461 implementation; pushed and reachable from origin/master; no installer built -->
<!-- aidcp-console 28776f14a126a99fe2427b4ae43d07e0838930e9 implementation; pushed and reachable from origin/master -->
- [ ] 12.2 `openspec validate wechat-review-residuals --strict` 通过。
- [ ] 12.3 **归档序**：本 change 必须等 `wechat-channels-interaction-management` **先归档**（`wechat-channels-interaction` 与 `inbound-interaction-management` 两个 capability 目前只活在它的 delta 里，尚未并入 `openspec/specs/`），否则 spec-merge 会找不到基线 capability。
