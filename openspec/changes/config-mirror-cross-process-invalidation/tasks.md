## 1. aidcp-cloud — 现状盘点与归属划线

- [ ] 1.1 在 `src/config/index.ts` 旁新增 `src/config/mirror-registry.ts`，用 `Record<ConfigMirrorKey, ConfigMirrorDescriptor>` 穷举登记 design.md 表中的 15 处镜像；每条描述符至少含 `mirrorKey`、`owner`（`api` / `automation` / `content`）、`tier`（`gate` / `parameter`）、`staleMs`（参数镜像为 `null`）。新增镜像未登记必须 typecheck 失败。
- [ ] 1.2 在 `src/config/quota-config-store.ts`、`pacing-config-store.ts`、`session-config-store.ts`、`resume-config-store.ts` 的文件头注释里写明「本 store 归 aidcp-automation」，并补一行依据：`src/risk/` 对 `src/config/` 的 import 为 0，反向 13 处。
- [ ] 1.3 补一条模块边界断言测试：`src/risk/**` MUST NOT import `src/config/**`（读源文件做静态断言即可，不引入 lint 依赖）。
- [ ] 1.4 在 `src/config/content-schedule-store.ts` 的 `globalActiveWeekMask` 注入点（`:287`、`:404`）补注释：`session_config_global` 归 automation 之后，`listCatalog()`（`:836`）必须改为向权威侧取生效掩码，MUST NOT 在 api 侧另建副本。

## 2. aidcp-cloud — 镜像版本表与写方推进

- [ ] 2.1 新增迁移 `migrations/00NN_config_mirror_version.sql`（编号取当前最大值 +1，避免与 `0056` 之后的并行 change 碰撞），建 `config_mirror_version(mirror_key TEXT PRIMARY KEY, version BIGINT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now())`；纯 additive DDL，MUST NOT 含 DROP/RENAME/类型收窄。表 MUST NOT 有 `execution_target` 列。
- [ ] 2.2 新增 `src/config/mirror-version-store.ts`：`bumpInTx(client, mirrorKey)` 用 `INSERT ... ON CONFLICT DO UPDATE SET version = config_mirror_version.version + 1, updated_at = now()`；`readAll()` 一次 `SELECT mirror_key, version`。版本自增由库侧完成，MUST NOT 用任何主机时钟当版本。
- [ ] 2.3 让 15 处镜像的写入路径在**持久化成功的同一事务内**调用 `bumpInTx`。写库失败 MUST NOT 推进版本，也 MUST NOT 刷新本进程镜像（保持 `account-persona-config` 既有的「写库成功才刷镜像」不变量）。
- [ ] 2.4 `src/config/persona-store.ts` 的写入路径（含空人设解绑）接 `bumpInTx`；`src/account-state.ts` 的 `pause` / `resume` 与 `src/client-auth/client-user-store.ts:810`、`:840`、`:965`、`:1582` 的慢启动/出口闸写入路径同样接入。
- [ ] 2.5 可选加速器：写方事务提交后额外 `pg_notify('aidcp_config_mirror', mirrorKey)`。实现 MUST 把它标注为非承重通道，MUST NOT 因接了通知而放宽轮询周期。

## 3. aidcp-cloud — 消费侧刷新器与有界陈旧度

- [ ] 3.1 新增 `src/config/mirror-refresher.ts`：一个进程一个实例，周期 `T_poll`（env `AIDCP_CONFIG_MIRROR_POLL_MS`，默认 5000，硬上界 30000，超界 MUST 拒绝启动并打诚实错误而非静默截断）。每轮一次 `readAll()`，只对版本变化的 key 触发对应 store 的重载。
- [ ] 3.2 给每个 store 暴露一个 `refreshFromAuthority()` 公开方法（内部复用现有 `private reload()`），MUST NOT 把 `reload()` 直接改公开、MUST NOT 在重载中途出现半填镜像（沿用 `pacing-config-store.ts:12` 已有的「构建新 Map → 原子替换引用」写法）。
- [ ] 3.3 刷新器维护每个 mirrorKey 的 `lastComparedAt`：**每次成功完成版本比对即更新**，无论是否发生重载。`lastReloadedAt` 单独记录、只用于日志。
- [ ] 3.4 刷新器 MUST 复用组合根已有的 Pool，MUST NOT 另开连接池；单轮查询失败 MUST 记 warn 并保留上次已知版本，MUST NOT 清空镜像。
- [ ] 3.5 整体开关 `AIDCP_CONFIG_MIRROR_REFRESH`（默认开），关闭后行为退回今日现状（启动 + 本进程写入刷新），供秒级回滚。

## 4. aidcp-cloud — 闸门镜像三态与陈旧停手

- [ ] 4.1 定义 `MirrorReadState = 'fresh' | 'stale'` 与统一查询口 `mirrorStateOf(mirrorKey): MirrorReadState`，判据为 `now - lastComparedAt > staleMs`（默认 60000）。进入 `stale` 前先在 `staleMs / 2` 处打一次预警。
- [ ] 4.2 `isPersonaBound` 改签名为返回 `'bound' | 'unbound' | 'unknown'`，改掉 `src/server.ts:2618`、`:3154`、`:3479`、`:3661` 四个注入点。MUST 用具名字符串联合类型，MUST NOT 用 `boolean | undefined`。
- [ ] 4.3 `src/comm/ui-snapshot.ts:171-184` 的 `pushPersonaBound`：`'unknown'` 时 MUST NOT 下发 `personaBound` 字段（保持 `src/comm/protocol.ts:695-701` 的「云端还没说」语义，边缘零改动）；仅 `'bound'` / `'unbound'` 下发 `true` / `false`。
- [ ] 4.4 会话启动闸与 `src/comment-agent/comment-scheduler.ts:425`、`:622`、`src/publish-agent/publish-scheduler.ts:285`、`:324`、`:350`、`:403` 的人设闸：`'unbound'` 保持现有 `needs_persona_setup` 拒绝；`'unknown'` 改走新的 `persona_unavailable` 分支，MUST NOT 复用 `needs_persona_setup`。
- [ ] 4.5 `src/delegated-task/worker.ts:361-366`：`persona_unavailable` 与任何 `config_mirror_stale` 类原因 MUST 走可重试的 `releaseClaim(..., 'deferred', ...)` 路径，MUST NOT 落 `non_retryable_failure`。同步在 `src/delegated-task/reason-humanize.ts` 补这两个码的人话翻译。
- [ ] 4.6 `src/account-state.ts` 的 `isPaused` / `getStatus` 改为三值（`'paused' | 'active' | 'unknown'`）。副本 `stale` 时返回 `'unknown'`，MUST NOT 沿用「miss = active」；`src/comm/handler.ts:442` 的调用点按 `'unknown'` 停手处理。
- [ ] 4.7 `src/client-auth/client-user-store.ts:445` 的环境出口闸与 `:447-448` 的慢启动锚点同样三态化。`src/risk/risk-controller.ts:325-334` 的 `resolveNurtureAnchor` 在锚点副本 `unknown` 时 MUST NOT 返回 `null`（那等于「未开启慢启动」= 满配额），MUST 让上层闸停手。
- [ ] 4.8 停手行为统一实现：不放行新的真实平台动作（新会话不启动、命令泵不下发新的互动/发布/评论命令）；**已在跑的会话走既有自然结束路径收敛**，MUST NOT 就地 kill。
- [ ] 4.9 `src/agents/base-role.ts:48-54` 的取值口在副本 `stale` 时 MUST NOT 靠抛 `no_persona` 兜底——闸门必须在入口收敛；保留该抛出仅作会话中途被真实解绑的防御性路径。
- [ ] 4.10 参数镜像（模型 / 角色 / 类目 / 引流阈值 / FB 配置的非启用位）陈旧时 MUST 继续使用最后已知良值 + 告警，MUST NOT 停手。

## 5. aidcp-cloud — 归属重排与面板透传

- [ ] 5.1 把 `quota-config-store.ts` / `pacing-config-store.ts` / `session-config-store.ts` / `resume-config-store.ts` 及其四个 facade 归入 automation 模块边界（阶段 1 只划线、不拆进程），组合根 `src/server.ts:241-250`、`:538-576`、`:4191-4199` 的装配顺序保持不变。
- [ ] 5.2 面板四类安全配置的读回值改为透传权威侧同一次求值结果，MUST NOT 由另一处副本回答；补一条断言：面板回显的限额数字与同一时刻 `effectiveQuotas()` 采用的数字逐格相等。
- [ ] 5.3 `src/config/content-schedule-store.ts:836` 的 `listCatalog()` 改为向权威侧取生效活跃掩码；`:515` 的 `effectiveActiveWeekMaskFor` 保持在 automation 侧现读不变。
- [ ] 5.4 在四个 facade 的写入路径补 `bumpInTx`，使 dev 面板的写入能被 ol 进程在 `T_poll` 内看到（这是本变更对现存生产缺陷的直接修复）。

## 6. aidcp-cloud — 可观测与告警

- [ ] 6.1 新增具名告警 `config_mirror_stale`，载荷含 `mirrorKey`、陈旧秒数、最后已知版本、`executionTarget`；接入现有 `src/alerts/alert-store.ts` 通道。
- [ ] 6.2 因 `stale` 停手的每一次拒绝 MUST 计数并持久化（按 mirrorKey、按小时可查），与设计内克制（配额耗尽、模型 pass）分别计数，MUST NOT 混计。
- [ ] 6.3 刷新器每轮记录一行 debug 级日志（比对耗时、变化的 key 数），版本发生变化时记 info 级并写明 key 与新旧版本。
- [ ] 6.4 面板/接口暴露一个只读镜像健康投影：每个 mirrorKey 的 `lastComparedAt`、当前版本、`fresh`/`stale`。投影 MUST 标注数据时刻，MUST NOT 只回响应时刻。

## 7. aidcp-cloud — 测试与验收

- [ ] 7.1 写侧改配置 → 读侧有界可见：`T_poll=5s` 下断言写入后 ≤ 10s 内消费侧读到新值（用注入时钟 + 桩 Pool，不打真实 PG）。
- [ ] 7.2 陈旧停手：冻结版本查询使 `lastComparedAt` 超过 `staleMs` → 断言新会话不启动、命令泵不下发新的平台动作命令、落 `config_mirror_stale` 告警，且**已在跑的会话未被 kill**。
- [ ] 7.3 未知不得压成否：副本无某账号人设行且镜像 `stale` → 断言不下发 `personaBound` 字段、不触发人设向导路径、委托任务落 `deferred` 而非 `non_retryable_failure`。
- [ ] 7.4 暂停态方向性：副本 `stale` 且库内该账号已被暂停 → 断言不再下发新命令，MUST NOT 因「miss = active」继续放行。
- [ ] 7.5 never-brick 边界：权威已答但 `quota_config` 缺行 → 断言仍回落 `quotas.ts` 写死默认（零回归）；副本 `stale` → 断言走停手而非回落默认。
- [ ] 7.6 归属重排零回归：`quota_config` / `session_config_global` 改值后，`canDo` 下一次调用即按新值（`interaction-risk-gating` 的「改完即热生效、不需重启」逐字成立）。
- [ ] 7.7 半填竞态：重载进行中并发读镜像 → 断言读到的要么是旧全量要么是新全量，绝不是半填。
- [ ] 7.8 穷举防漂移：新增一个未登记的 mirrorKey → 断言 typecheck 失败。
- [ ] 7.9 跑 `npm run test:acceptance`、`npm test`、`npm run typecheck`，记录确切命令与结果。安全红线 `AC-RISK-*`、`AC-PUB-*`、`AC-PROTO-*` MUST 全过。

## 8. aidcp — 控制仓文档与契约

- [ ] 8.1 更新 `docs/cloud-service-decomposition-proposal.md` §5.1：把 `quota_config` / `pacing_floor_config` / `session_config_global` / `resume_config_global` 从「人设和运营配置 → aidcp-api」显式剥离，改判 `aidcp-automation`；并补一条限定——被 automation 同步闸门消费的 api 权威事实 MUST 以本地只读副本 + 版本 + 失效通知消费，MUST NOT 用构造期快照、MUST NOT 每次调用做跨服务同步请求。
- [ ] 8.2 更新 §6.1 通信表：新增一行「跨进程配置镜像失效 | 共享 PostgreSQL 版本表 + 有界轮询（`pg_notify` 仅作加速器）| 无消息队列、陈旧上限可证明」。
- [ ] 8.3 更新 §11 故障表第 2 行：把「按合同安全收敛」替换为可验收三态——已在跑会话按有界陈旧度收敛到自然终点；已领取未开始的持久任务保持 claim 并按 `deferred` 延后；新会话被拒并回 `persona_unavailable` / `config_mirror_stale` 而非静默。
- [ ] 8.4 更新 §14 红线：新增一条——权威不可达时 automation MUST NOT 以缺省人设或缺省配额继续执行平台动作；副本超过声明陈旧上限后的行为 MUST 是文档中声明的停手，且 MUST 有具名告警与可计量记录。
- [ ] 8.5 更新 §12 阶段 1 交付物：加入「为闸门类跨服务事实建立本地副本 + 版本 + 失效通知适配器，并补一条『写方更新后读方在 T 内可见』的测试」。
- [ ] 8.6 在 `docs/deployment-environments.md` 的共库状态块补一句现存缺陷与本变更的关系：8 张全局配置表在 dev/ol 双进程间不互相刷新，重启前不可见。
- [ ] 8.7 在 `openspec/changes/config-mirror-cross-process-invalidation/tasks.md` 回写各 sub-repo 的 commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`。
- [ ] 8.8 跑 `openspec validate config-mirror-cross-process-invalidation --strict` 并贴出输出。
