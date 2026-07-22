## 1. aidcp-cloud — 现状盘点与归属划线

- [x] 1.1 在 `src/config/index.ts` 旁新增 `src/config/mirror-registry.ts`，用 `Record<ConfigMirrorKey, ConfigMirrorDescriptor>` 穷举登记 design.md 表中的 15 处镜像；每条描述符至少含 `mirrorKey`、`owner`（`api` / `automation` / `content`）、`tier`（`gate` / `parameter`）、`staleMs`（参数镜像为 `null`）。新增镜像未登记必须 typecheck 失败。
  <!-- aidcp-cloud 4495050 描述符用判别联合：gate 必须给 staleMs 数值、parameter 必须写 null，「无上限的闸门镜像」在类型上构造不出来。**偏离**：`ConfigMirrorKey` 联合类型放在中立模块 `src/config-mirror-freshness.ts`（src 根），registry 只 import 它——否则 `src/risk/risk-controller.ts`（task 4.7）为读新鲜度就得第一次 import `src/config/`，当场推翻 task 1.3 的静态断言与定稿 §11.4 要求一的归属依据。 -->
- [x] 1.2 在 `src/config/quota-config-store.ts`、`pacing-config-store.ts`、`session-config-store.ts`、`resume-config-store.ts` 的文件头注释里写明「本 store 归 aidcp-automation」，并补一行依据：`src/risk/` 对 `src/config/` 的 import 为 0，反向 13 处。
  <!-- aidcp-cloud 4495050 四个文件头注均已写明归属 + 依据 + 「归属对齐 MUST NOT 被读作跨进程可见性已消失」 -->
- [x] 1.3 补一条模块边界断言测试：`src/risk/**` MUST NOT import `src/config/**`（读源文件做静态断言即可，不引入 lint 依赖）。
  <!-- aidcp-cloud 259706d test/config/module-boundary.test.ts：正向断言 0 命中 + 反向断言 ≥10 处（归属论证的另一半也一并守住） -->
- [x] 1.4 在 `src/config/content-schedule-store.ts` 的 `globalActiveWeekMask` 注入点（`:287`、`:404`）补注释：`session_config_global` 归 automation 之后，`listCatalog()`（`:836`）必须改为向权威侧取生效掩码，MUST NOT 在 api 侧另建副本。
  <!-- aidcp-cloud 4495050 注入点注释已补；另把 listCatalog 里那段与 effectiveActiveWeekMaskFor 重复的内联 IIFE 收敛到唯一解析点 resolveGlobalActiveWeekMask()（见 5.3） -->

## 2. aidcp-cloud — 镜像版本表与写方推进

- [x] 2.1 新增迁移 `migrations/00NN_config_mirror_version.sql`（编号取当前最大值 +1，避免与 `0056` 之后的并行 change 碰撞），建 `config_mirror_version(mirror_key TEXT PRIMARY KEY, version BIGINT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now())`；纯 additive DDL，MUST NOT 含 DROP/RENAME/类型收窄。表 MUST NOT 有 `execution_target` 列。
  <!-- aidcp-cloud 4495050 编号取 0062（按 fleet 编排指定的编号区间，非 max+1=0058，避让并行 change）；同批建 config_mirror_stale_refusal（task 6.2 的按小时计量表）。两张表都无 execution_target 列 -->
- [x] 2.2 新增 `src/config/mirror-version-store.ts`：`bumpInTx(client, mirrorKey)` 用 `INSERT ... ON CONFLICT DO UPDATE SET version = config_mirror_version.version + 1, updated_at = now()`；`readAll()` 一次 `SELECT mirror_key, version`。版本自增由库侧完成，MUST NOT 用任何主机时钟当版本。
  <!-- aidcp-cloud 4495050 -->
- [x] 2.3 让 15 处镜像的写入路径在**持久化成功的同一事务内**调用 `bumpInTx`。写库失败 MUST NOT 推进版本，也 MUST NOT 刷新本进程镜像（保持 `account-persona-config` 既有的「写库成功才刷镜像」不变量）。
  <!-- aidcp-cloud 4495050 统一走 writeWithMirrorBump(pool, bumper, key, run)：BEGIN → 写 → bumpInTx → COMMIT，任一步抛错即 ROLLBACK 并原样抛出。bumper 缺省时退回单条 pool.query（行为逐位等同本 change 之前，既有假 pool 单测无需实现 connect()）。**一处如实说明**：15 处里 `client_environment_automation_gate`（环境删除生命周期）在本仓**没有任何运行时写入者**——环境删除权已反转为「桌面客户端单写、云端只读」，故它只有刷新入口、没有推进入口；这不是遗漏，是该镜像今天的真实形态 -->
- [x] 2.4 `src/config/persona-store.ts` 的写入路径（含空人设解绑）接 `bumpInTx`；`src/account-state.ts` 的 `pause` / `resume` 与 `src/client-auth/client-user-store.ts:810`、`:840`、`:965`、`:1582` 的慢启动/出口闸写入路径同样接入。
  <!-- aidcp-cloud 4495050 persona set/setIfMissing/clear 三条都接（解绑不推版本＝「客户清空人设」在别的进程永远不可见）；暂停态经 PgAccountStore.setPaused 接入 -->
  <!-- aidcp-cloud cedb586 慢启动锚点补齐两处原稿未点名的写路径：自助建号写入新环境 slow_start_since（既有事务内 bumpInTx）、握手/后台注册导致账号↔环境绑定变化（绑定变化会改变锚点按账号的解析结果）。行号已漂，按语义定位 -->
- [x] 2.5 可选加速器：写方事务提交后额外 `pg_notify('aidcp_config_mirror', mirrorKey)`。实现 MUST 把它标注为非承重通道，MUST NOT 因接了通知而放宽轮询周期。
  <!-- aidcp-cloud 4495050 notifyAfterCommit 只在 COMMIT 之后 fire-and-forget + 吞错；轮询周期与它无关（陈旧上限只由轮询给出）。**边缘侧 LISTEN 消费者未实现**：加速器只发不收，收侧留给后续（不影响任何契约，轮询是唯一承重通道） -->

## 3. aidcp-cloud — 消费侧刷新器与有界陈旧度

- [x] 3.1 新增 `src/config/mirror-refresher.ts`：一个进程一个实例，周期 `T_poll`（env `AIDCP_CONFIG_MIRROR_POLL_MS`，默认 5000，硬上界 30000，超界 MUST 拒绝启动并打诚实错误而非静默截断）。每轮一次 `readAll()`，只对版本变化的 key 触发对应 store 的重载。
  <!-- aidcp-cloud 4495050 resolveMirrorPollMs 超界/非法一律 throw；组合根 catch 后**不启动刷新器**并打 error，退回今日现状而非让整个云端起不来 -->
- [x] 3.2 给每个 store 暴露一个 `refreshFromAuthority()` 公开方法（内部复用现有 `private reload()`），MUST NOT 把 `reload()` 直接改公开、MUST NOT 在重载中途出现半填镜像（沿用 `pacing-config-store.ts:12` 已有的「构建新 Map → 原子替换引用」写法）。
  <!-- aidcp-cloud 4495050 12 个 config store + AccountStateManager + ClientUserStore 两个镜像各一个入口；reload() 全部保持 private。**顺带修两处原有半填隐患**：content-schedule 的 accountCache 与 account-state 的 states 此前是原地 clear+fill，接上跨进程刷新后会变成真实竞态，已改为构建新集合→原子替换 -->
- [x] 3.3 刷新器维护每个 mirrorKey 的 `lastComparedAt`：**每次成功完成版本比对即更新**，无论是否发生重载。`lastReloadedAt` 单独记录、只用于日志。
  <!-- aidcp-cloud 4495050 有专测：120 轮无任何写入但每轮比对成功 → 始终 fresh -->
  <!-- aidcp-cloud 78b8958 **审计修复（这条判据当时被写过头了）**：只看 `lastComparedAt` 会把「我知道权威变了、我拉不动」折叠成「新鲜」——版本表读得动、reload 每次抛错时，实测 20 轮后仍是 `state=fresh / staleGates=0`，一个**已知落后**的闸门副本照常放行平台动作，健康投影还对运营显示 fresh。现每个 mirrorKey 另记 `reloadFailingSince`（连续重载失败起点，任一次成功即复位），副本年龄取「距上次成功比对」与「距失败起点」的**较大值**；`version` 也改为回退到上一个**成功装载**的版本（原代码写 null、与注释「退回上一版本号」不符）。有专测：比对每轮成功 + reload 每次失败 → 转 stale、停手、告警带 `reloadFailing` -->
- [x] 3.4 刷新器 MUST 复用组合根已有的 Pool，MUST NOT 另开连接池；单轮查询失败 MUST 记 warn 并保留上次已知版本，MUST NOT 清空镜像。
  <!-- aidcp-cloud 860a951 组合根此前**没有任何共享池**（每个 store 各 new 一个）。故建一个 configMirrorPool（max=30）并交给全部 12 个配置 store 与版本表共用：镜像子系统零新增连接池，配置层池数反而从 12 收敛到 1（与定稿 §11.5「把散池收敛为每服务一个共享池」同向）。PgAccountStore / ClientUserStore 保持各自的池——bump 走的是**它们自己**的事务客户端，不需要共享池 -->
- [x] 3.5 整体开关 `AIDCP_CONFIG_MIRROR_REFRESH`（默认开），关闭后行为退回今日现状（启动 + 本进程写入刷新），供秒级回滚。
  <!-- aidcp-cloud 4495050 关闭时**不安装新鲜度事实源** → mirrorStateOf 恒 fresh → 全部闸门按今日现状运行，行为逐位等同本 change 之前 -->

## 4. aidcp-cloud — 闸门镜像三态与陈旧停手

- [x] 4.1 定义 `MirrorReadState = 'fresh' | 'stale'` 与统一查询口 `mirrorStateOf(mirrorKey): MirrorReadState`，判据为 `now - lastComparedAt > staleMs`（默认 60000）。进入 `stale` 前先在 `staleMs / 2` 处打一次预警。
  <!-- aidcp-cloud 4495050 查询口在 src/config-mirror-freshness.ts（中立模块，见 1.1 偏离说明）；事实源本身异常时按 stale 收敛（停手侧安全），绝不假装新鲜 -->
- [x] 4.2 `isPersonaBound` 改签名为返回 `'bound' | 'unbound' | 'unknown'`，改掉 `src/server.ts:2618`、`:3154`、`:3479`、`:3661` 四个注入点。MUST 用具名字符串联合类型，MUST NOT 用 `boolean | undefined`。
  <!-- aidcp-cloud 860a951 **一并改名 isPersonaBound → personaBinding**：只换返回类型而留旧名，`!isPersonaBound(id)` 会变成 `!'unbound'`——合法 TS、静默反转语义、typecheck 抓不到。改名让 8 处调用点全部编译报错，每处都必须被重新想一遍 -->
- [x] 4.3 `src/comm/ui-snapshot.ts:171-184` 的 `pushPersonaBound`：`'unknown'` 时 MUST NOT 下发 `personaBound` 字段（保持 `src/comm/protocol.ts:695-701` 的「云端还没说」语义，边缘零改动）；仅 `'bound'` / `'unbound'` 下发 `true` / `false`。
  <!-- aidcp-cloud 860a951 未动 protocol.ts，边缘零改动 -->
  <!-- aidcp-cloud 78b8958 **审计修复（原实装漏了真正的落地面）**：ui-snapshot 对拉取型客户端直接 return（既有测试锁着），当代客户端的绑定态只经 `GET /my-environments` 下发，那条 HTTP 面仍在回权威的 `personaBound:false`。现 `AccountPersonaService.get()` 接上同一判据：副本陈旧且副本里无该行 → 回契约里既有的 `unavailable`，回包不带 `personaBound` 字段（edge `main.cjs` 把缺省读成 null，`renderer.js` 只在 `=== false` 时弹向导，已对着边缘代码核过）。副本里**有**人设时照常返回——读一份稍旧的人设文本不构成「未知压成否」，503 掉一个答得出来的读只会无谓打断人设编辑器 -->
- [x] 4.4 会话启动闸与 `src/comment-agent/comment-scheduler.ts:425`、`:622`、`src/publish-agent/publish-scheduler.ts:285`、`:324`、`:350`、`:403` 的人设闸：`'unbound'` 保持现有 `needs_persona_setup` 拒绝；`'unknown'` 改走新的 `persona_unavailable` 分支，MUST NOT 复用 `needs_persona_setup`。
  <!-- aidcp-cloud 860a951 publish 侧四处收敛为一个 personaGate() 私有闸（四份等价 if 分叉是「以后只改其中三处」的现成陷阱）；comment 侧两处各自给出与「未绑」不同的人话 -->
- [x] 4.5 `src/delegated-task/worker.ts:361-366`：`persona_unavailable` 与任何 `config_mirror_stale` 类原因 MUST 走可重试的 `releaseClaim(..., 'deferred', ...)` 路径，MUST NOT 落 `non_retryable_failure`。同步在 `src/delegated-task/reason-humanize.ts` 补这两个码的人话翻译。
  <!-- aidcp-cloud 860a951 判据按码精确匹配（绝不用「含 persona 就算」这类前缀——needs_persona_setup 必须保持既有非重试终态）；两条测试锁住 deferred + nextEligibleAt 退避 -->
  <!-- aidcp-cloud 78b8958 **审计修复（原实装只做了一半）**：`markAttemptDispatched` 已把 attempt_count +1，deferred 分支既不撤回也不回退，于是每轮基础设施故障都在啃尝试预算，几轮后 runOne 在预算闸上判 `max_attempts`——换了个码仍然是被「云端读不到配置」判死（实测 maxAttempts=2 时第 3 轮终结）。现于 `handleAttemptResult` 入口把这两个码归一成 `deferred + attemptStarted:false`，走 `discardAttemptBeforeStart` 撤回计数；补两条测试：持续 6 轮任务仍在队列且 attemptCount 恒 0，以及普通可重试失败照常按预算终结（预算闸没被顺手关掉） -->
- [x] 4.6 `src/account-state.ts` 的 `isPaused` / `getStatus` 改为三值（`'paused' | 'active' | 'unknown'`）。副本 `stale` 时返回 `'unknown'`，MUST NOT 沿用「miss = active」；`src/comm/handler.ts:442` 的调用点按 `'unknown'` 停手处理。
  <!-- aidcp-cloud 4495050 isPaused → pauseStateOf（同 4.2 的改名理由）；飞书 /status 也如实显示「暂时读不到」而非 active -->
- [x] 4.7 `src/client-auth/client-user-store.ts:445` 的环境出口闸与 `:447-448` 的慢启动锚点同样三态化。`src/risk/risk-controller.ts:325-334` 的 `resolveNurtureAnchor` 在锚点副本 `unknown` 时 MUST NOT 返回 `null`（那等于「未开启慢启动」= 满配额），MUST 让上层闸停手。
  <!-- aidcp-cloud 4495050 出口闸 isAutomationAllowedForEdgeId → automationGateForEdgeId 三态，server.ts 只放行 'allowed'。resolveNurtureAnchor **只改了这一个函数**（尊重 risk-state-cross-process-integrity 的独占）：副本陈旧时退到**最保守锚点（第 1 天）**并记账，绝不返回 null。**如实说明**：真正的停手在上层闸（4.8 的统一实现），本处只是不让配额层在停手生效前把闸放到最松——它是纵深防御，不是「回落最严档代替停手」 -->
  <!-- aidcp-cloud 78b8958 **审计修复两处**：① 慢启动锚点的「最保守回落」同时喂了 `slowStartView()`，于是一个**从未开启**慢启动的账号在投影上变成「已入组、第 1 天」——把「读不到」编成一个确定的「是」。现拆出三态内核 `nurtureAnchorState()`：clamp 侧 unknown 仍取最严（收紧配额，方向安全），投影侧回 `eligible:false` + 既有 `binding_unknown`（**绝不新增枚举值**——边缘对 ineligibleReason 做白名单校验，未知值会让整段慢启动投影被丢弃）。② 出口闸 `unknown` 原本一律拦死，连 `edge.task.release`（浏览器槽位归还）、`ui.snapshot`、`captcha.assist.*` 都扣住，调用方还被误告知 `edge_offline`；现 `unknown` 只拦新的真实平台动作，控制面 / 浏览器生命周期 / 收尾类放行（判据 `allowsTransportWhenGateUnknown`，有正反两组断言）。`blocked` 是确定态、行为逐位不变 -->
- [x] 4.8 停手行为统一实现：不放行新的真实平台动作（新会话不启动、命令泵不下发新的互动/发布/评论命令）；**已在跑的会话走既有自然结束路径收敛**，MUST NOT 就地 kill。
  <!-- aidcp-cloud 860a951 src/config/mirror-stop-work.ts 单点判据；接在 RoleDispatcher.sessionStartVerdict（新会话）与 sendCommand（命令泵）两处。sendCommand 里放在 isQuotaSleepBypass 之后，session.end / excursion 收尾照常穿透 → 在跑的会话自然收敛 -->
  <!-- aidcp-cloud 78b8958 **审计修复**：那条「命令数不增」原是**空断言**——命令本就异步产生，同步比较在新鲜态下同样成立（实测新鲜态 SYNC 0→0、400ms 后才出 1 条 scroll）。现改为 await 后断言，并新增一条**新鲜态对照组**断言同一输入必须产出 ≥1 条命令；否则这条测试将来任何回归都抓不到 -->
- [x] 4.9 `src/agents/base-role.ts:48-54` 的取值口在副本 `stale` 时 MUST NOT 靠抛 `no_persona` 兜底——闸门必须在入口收敛；保留该抛出仅作会话中途被真实解绑的防御性路径。
  <!-- aidcp-cloud 860a951 入口已在 4.4 收敛，此处只补注释锁住意图（改代码反而会削掉「真实解绑」这条防御） -->
- [x] 4.10 参数镜像（模型 / 角色 / 类目 / 引流阈值 / FB 配置的非启用位）陈旧时 MUST 继续使用最后已知良值 + 告警，MUST NOT 停手。
  <!-- aidcp-cloud 4495050 参数镜像 staleMs=null → mirrorStateOf 恒 fresh、不入 staleGateMirrors；刷新器仍打 warn 日志。**口径差异（design 优先，已在 docpatch 登记）**：四类限频配置按 design 决策 3 的分档清单登记为 parameter（消费方与写入方同进程、不存在跨服务副本），而非按 spec 的语义判据登记为 gate -->
  <!-- aidcp-cloud 78b8958 **审计修复（原实装只兑现了「不停手」，没兑现「告警」）**：参数镜像此前被 evaluateStaleness 直接 continue，投影恒 fresh，只剩一条与镜像无关的通用轮询失败 warn。现新增**观测阈值** `PARAMETER_MIRROR_OBSERVE_STALE_MS=300s`：超时发 `config_mirror_stale` 具名告警（P3，文案明说「继续使用最后已知良值」、绝不谎称已停手），健康投影如实回 stale；取值口 `stateOf` **仍恒 fresh**，绝不停手。投影新增 `haltsOnStale` / `observeStaleMs` 两字段自解释 -->
  <!-- **仍未兑现（如实登记）**：spec 场景里的「在相关产出上标注副本时刻」未实装——那要求把镜像副本时刻传播到 LLM 产出的记账里，超出本 change 的改动面。task 4.10 正文本身不含这一句，故不改勾选状态；此项留给主控决定是收进 backlog 还是另起 change -->

## 5. aidcp-cloud — 归属重排与面板透传

- [x] 5.1 把 `quota-config-store.ts` / `pacing-config-store.ts` / `session-config-store.ts` / `resume-config-store.ts` 及其四个 facade 归入 automation 模块边界（阶段 1 只划线、不拆进程），组合根 `src/server.ts:241-250`、`:538-576`、`:4191-4199` 的装配顺序保持不变。
  <!-- aidcp-cloud 4495050 纯划线（文件头注 + 边界断言测试），装配顺序未动 -->
- [x] 5.2 面板四类安全配置的读回值改为透传权威侧同一次求值结果，MUST NOT 由另一处副本回答；补一条断言：面板回显的限额数字与同一时刻 `effectiveQuotas()` 采用的数字逐格相等。
  <!-- aidcp-cloud 259706d **代码零改动**：facade 与 QuotaProvider 本就是同一个 store 实例，展示与生效天然同源。补测锁住它（三档 × 全动作 × 三窗口逐格相等），防以后有人为面板另建投影 -->
- [x] 5.3 `src/config/content-schedule-store.ts:836` 的 `listCatalog()` 改为向权威侧取生效活跃掩码；`:515` 的 `effectiveActiveWeekMaskFor` 保持在 automation 侧现读不变。
  <!-- aidcp-cloud 4495050 listCatalog 本就走注入的 globalActiveWeekMask()（= sessionConfigStore.weekActiveMask()），未另建副本；本次把它与 effectiveActiveWeekMaskFor 里重复的那段逻辑收敛成唯一解析函数 resolveGlobalActiveWeekMask() -->
- [x] 5.4 在四个 facade 的写入路径补 `bumpInTx`，使 dev 面板的写入能被 ol 进程在 `T_poll` 内看到（这是本变更对现存生产缺陷的直接修复）。
  <!-- aidcp-cloud 4495050 bump 落在 store.set()（facade 唯一的落库出口），比落在 facade 更靠内、绕不过去 -->

## 6. aidcp-cloud — 可观测与告警

- [x] 6.1 新增具名告警 `config_mirror_stale`，载荷含 `mirrorKey`、陈旧秒数、最后已知版本、`executionTarget`；接入现有 `src/alerts/alert-store.ts` 通道。
  <!-- aidcp-cloud 860a951 预警（staleMs/2）P2、已陈旧 P1；alertStore 缺失时降级为只打日志、不阻塞启动（与既有告警接线同款） -->
- [x] 6.2 因 `stale` 停手的每一次拒绝 MUST 计数并持久化（按 mirrorKey、按小时可查），与设计内克制（配额耗尽、模型 pass）分别计数，MUST NOT 混计。
  <!-- aidcp-cloud 4495050 独立表 config_mirror_stale_refusal(mirror_key, hour_bucket, execution_target) 累加 upsert；与配额/模型/冷却的既有计数物理分离 -->
  <!-- aidcp-cloud 78b8958 **审计修复两处**：① 记账原挂在**纯读热路径**上且无节流——每条出站信封、每次 effectiveQuotas 求值、每条 note.arrived 各一条 PG 写，且写的正是刷新器自我恢复所依赖的同一个池（陈旧的成因通常就是 PG 不可达）。现按 mirrorKey 做时间窗聚合：窗口内第一次立刻写（可观测性不迟到），其余内存累加、每窗口最多再写一次，`stop()` 强制 flush 尾巴；专测：连打 1000 次 ≤2 条写且累加值一次不少。② 记账从纯取值口（`automationGateForEdgeId` / `resolveNurtureAnchor` / `pauseStateOf`）移到**真正的拒绝点**（传输层拦下时、handler 的 note.arrived 停手分支、会话启动闸），指标不再被「什么都没拒绝的读」污染；`sessionStartVerdict` 因同时服务只读裁决（~60s 每跳）改用不记账的 `hasStaleGateMirror()`，记账落在 `canStartSession` --> 
  <!-- aidcp-cloud 78b8958 补齐人设那一路：`persona_unavailable` 拒绝新会话此前**完全不计数**（binding 判定先于统一停手闸返回，且会话没起来就没有后续命令泵去补记），而它正是停手最常见的一条路径。现显式记在 `persona_config` 名下，有专测 -->
- [x] 6.3 刷新器每轮记录一行 debug 级日志（比对耗时、变化的 key 数），版本发生变化时记 info 级并写明 key 与新旧版本。
  <!-- aidcp-cloud 4495050 -->
- [x] 6.4 面板/接口暴露一个只读镜像健康投影：每个 mirrorKey 的 `lastComparedAt`、当前版本、`fresh`/`stale`。投影 MUST 标注数据时刻，MUST NOT 只回响应时刻。
  <!-- aidcp-cloud 259706d GET /api/config-mirrors，回包带 asOf；刷新器未接线时 503 诚实不可用，绝不回一个「全都新鲜」的空投影。console 前端未接（后端契约已就绪，前端展示不在本 change 范围） -->
  <!-- aidcp-cloud 78b8958 回包补三字段：`reloadFailingSince`（从何时起已知落后）、`observeStaleMs`（`state` 按哪个阈值算）、`haltsOnStale`（该镜像陈旧是否真的停手）。另：整体开关关掉时全部回 fresh + `enabled:false`（那时不存在跨进程副本语义，与 `mirrorStateOf` 同口径），绝不让一次秒级回滚在运营面前显示成 15 条全红 -->

## 7. aidcp-cloud — 测试与验收

- [x] 7.1 写侧改配置 → 读侧有界可见：`T_poll=5s` 下断言写入后 ≤ 10s 内消费侧读到新值（用注入时钟 + 桩 Pool，不打真实 PG）。
  <!-- aidcp-cloud 259706d test/config/mirror-invalidation.test.ts：两个 store 实例模拟 dev/ol 共库，断言比对前读侧仍是旧值（这正是今天的缺陷）、一轮比对后即新值 -->
- [x] 7.2 陈旧停手：冻结版本查询使 `lastComparedAt` 超过 `staleMs` → 断言新会话不启动、命令泵不下发新的平台动作命令、落 `config_mirror_stale` 告警，且**已在跑的会话未被 kill**。
  <!-- aidcp-cloud 259706d 拆成两组：mirror-invalidation.test.ts 验告警 + 预警先于陈旧 + 拒绝记账带 target；mirror-stale-stop-work.test.ts 验新会话被拒（reason=config_mirror_stale）与「在跑会话仍 active、命令数不增」 -->
  <!-- aidcp-cloud 78b8958 「命令数不增」原为空断言，已修（见 4.8 的修复注） -->
- [x] 7.3 未知不得压成否：副本无某账号人设行且镜像 `stale` → 断言不下发 `personaBound` 字段、不触发人设向导路径、委托任务落 `deferred` 而非 `non_retryable_failure`。
  <!-- aidcp-cloud 259706d 三处分别落测：persona-store.bindingFor 返回 unknown、ui-snapshot 一个包都不发、delegated worker 落 deferred -->
  <!-- aidcp-cloud 78b8958 补第四处（真正的落地面）：`AccountPersonaService.get()` 陈旧回 unavailable、`/my-environments` 组装分支不含 personaBound；并补新鲜态对照（权威的「未绑」必须照旧下发，否则人设向导永远不弹）。委托任务侧补多轮断言（见 4.5） -->
- [x] 7.4 暂停态方向性：副本 `stale` 且库内该账号已被暂停 → 断言不再下发新命令，MUST NOT 因「miss = active」继续放行。
  <!-- aidcp-cloud 259706d 关键方向单独断言：副本新鲜时 miss=active（同进程全量镜像下正确），副本陈旧时 miss=unknown -->
- [x] 7.5 never-brick 边界：权威已答但 `quota_config` 缺行 → 断言仍回落 `quotas.ts` 写死默认（零回归）；副本 `stale` → 断言走停手而非回落默认。
  <!-- aidcp-cloud 259706d -->
- [x] 7.6 归属重排零回归：`quota_config` / `session_config_global` 改值后，`canDo` 下一次调用即按新值（`interaction-risk-gating` 的「改完即热生效、不需重启」逐字成立）。
  <!-- aidcp-cloud 259706d 只测了 quota_config 取值口现读（session_config_global 的既有热加载测试原样通过，未重复堆用例） -->
- [x] 7.7 半填竞态：重载进行中并发读镜像 → 断言读到的要么是旧全量要么是新全量，绝不是半填。
  <!-- aidcp-cloud 259706d -->
- [x] 7.8 穷举防漂移：新增一个未登记的 mirrorKey → 断言 typecheck 失败。
  <!-- aidcp-cloud 259706d 用 @ts-expect-error 落成**编译期**断言（随 npm run typecheck 执行）：这行哪天不再报错，就说明闭集合被打开了 -->
- [x] 7.9 跑 `npm run test:acceptance`、`npm test`、`npm run typecheck`，记录确切命令与结果。安全红线 `AC-RISK-*`、`AC-PUB-*`、`AC-PROTO-*` MUST 全过。
  <!-- aidcp-cloud cedb586 test:acceptance 68 passing / 0 failing；test 2932 tests, 2924 pass, 0 fail, 8 skipped（skipped 为既有真机 gated 用例）；typecheck 零错误。三条红线族在 acceptance 全绿内 -->
  <!-- aidcp-cloud 78b8958 审计修复后重跑：`npm run test:acceptance` → 68 tests / 68 pass / 0 fail；`npm test` → 2942 tests / 2934 pass / 0 fail / 8 skipped（skipped 仍为既有真机 gated 用例）；`npm run typecheck` → 零输出零错误 -->

## 8. aidcp — 控制仓文档与契约

- [ ] 8.1 更新 `docs/cloud-service-decomposition-proposal.md` §5.1：把 `quota_config` / `pacing_floor_config` / `session_config_global` / `resume_config_global` 从「人设和运营配置 → aidcp-api」显式剥离，改判 `aidcp-automation`；并补一条限定——被 automation 同步闸门消费的 api 权威事实 MUST 以本地只读副本 + 版本 + 失效通知消费，MUST NOT 用构造期快照、MUST NOT 每次调用做跨服务同步请求。
  <!-- BLOCKED: 该文件由 5 个并行 change 共同修改，本 session 按 fleet 编排约定不直接改，精确编辑已写入 scratchpad/docpatch-config-mirror-cross-process-invalidation.md 由主控串行套用。**核对结果**：四类限频配置在现文档 §5.1 已单列成行并判给 aidcp-automation（`:506`），「显式剥离」已兑现；docpatch 只保留一处必要微改——把人设那一行的「任务创建时引用版本或快照」改掉，它与 §11.4 要求二自相矛盾且在形态上不成立 -->
- [ ] 8.2 更新 §6.1 通信表：新增一行「跨进程配置镜像失效 | 共享 PostgreSQL 版本表 + 有界轮询（`pg_notify` 仅作加速器）| 无消息队列、陈旧上限可证明」。
  <!-- BLOCKED: 同 8.1，精确编辑在 docpatch（含表下一句「MUST NOT 套用 §6.2 Outbox/Inbox」的理由） -->
- [ ] 8.3 更新 §11 故障表第 2 行：把「按合同安全收敛」替换为可验收三态——已在跑会话按有界陈旧度收敛到自然终点；已领取未开始的持久任务保持 claim 并按 `deferred` 延后；新会话被拒并回 `persona_unavailable` / `config_mirror_stale` 而非静默。
  <!-- BLOCKED: 同 8.1，精确编辑在 docpatch（§11.2 表第 2 行、实测 `:1394`） -->
- [ ] 8.4 更新 §14 红线：新增一条——权威不可达时 automation MUST NOT 以缺省人设或缺省配额继续执行平台动作；副本超过声明陈旧上限后的行为 MUST 是文档中声明的停手，且 MUST 有具名告警与可计量记录。
  <!-- BLOCKED: 同 8.1，精确编辑在 docpatch（按 §14.1「新增只在尾部追加」的编号纪律，拟为 31 / AC-DECOMP-31） -->
- [ ] 8.5 更新 §12 阶段 1 交付物：加入「为闸门类跨服务事实建立本地副本 + 版本 + 失效通知适配器，并补一条『写方更新后读方在 T 内可见』的测试」。
  <!-- BLOCKED: 同 8.1，精确编辑在 docpatch（含一条对应的退出判据） -->
- [ ] 8.6 在 `docs/deployment-environments.md` 的共库状态块补一句现存缺陷与本变更的关系：8 张全局配置表在 dev/ol 双进程间不互相刷新，重启前不可见。
  <!-- BLOCKED: 控制仓除本 change 的 tasks.md 外一律只读（fleet 编排约束），精确编辑在 docpatch §8.6；该段同时兑现定稿 §11.4「陈旧上限 T MUST 是部署文档中写死的一个具体值」= 60s -->
- [x] 8.7 在 `openspec/changes/config-mirror-cross-process-invalidation/tasks.md` 回写各 sub-repo 的 commit-sha，格式 `<!-- <repo> <commit-sha> 备注 -->`。
  <!-- aidcp-cloud 4495050 / 860a951 / 259706d / cedb586 / f05f1b0 / 78b8958（审计修复）—— **均为分支本地未推送 sha**（本 session 按 fleet 约定不 push）；集成时若发生 rebase，主控需按新 sha 修订 -->
- [x] 8.8 跑 `openspec validate config-mirror-cross-process-invalidation --strict` 并贴出输出。
  <!-- aidcp 只读校验，输出：Change 'config-mirror-cross-process-invalidation' is valid -->
