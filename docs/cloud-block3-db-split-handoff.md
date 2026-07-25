# Block③ 物理拆库 交接文档（aidcp-cloud）

> 目的：让新 session 无缝接手 **Block③ 物理拆库（L2 → L3）**。Block② 进程拆分已代码完成 + land + 部署 dev。
> 本文档给出**操作要求（务必先读第 1 节）** + 现状 + L2/L3 逐步剧本 + 红线 + 验证清单。
> 生成于 2026-07-24，作者上一 session 刚完成 Block②。执行关键处标注了「先核实」。

---

## 0. 状态更新（2026-07-24 夜，本 session 续做 L2）

**L2 已全做完 + 部署 dev + 真机验证。cloud `origin/master` = `653e910`（在 Block² 的 90319eb 之上 +L2）。**

已核实并坐实的关键事实（原文多处「先核实」的结论）：
- **dev 与 ol 的 `.env` 都只设 `PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD`，均未设 `DATABASE_URL`，三个 `AIDCP_PG_*_URL` 也都没设。** ⇒ 交接文档 §4.2 风险①判为安全：resolver 回落链 `DATABASE_URL(未设)→PGHOST/...` 与今天 HOST-param / ENVCFG 三条路径全部塌成同一份 PGHOST 配置，**L2 接线在 dev+ol 都字节等价**。
- **master 早已有 0071–0074**（tasks.md 里「3e75332 未合入 master」的注释已过时）；`schema-contract` `KNOWN_MAX=0074_event_outbox`、`REQUIRED=0070`，与迁移目录顶端一致。

本 session 已完成：
1. **baseline 共享库（执行器 11.4 / 3.4）**——dev 上 `migrate verify` 缺失 0/多余 0（先定向补了 `migrations/0073 publish_execution_state`，属另一 change publish-log-split-prep 的自建缺表、幂等纯 expand）；`migrate baseline` 写账本 **73 行 / 最高 0074**。**dev/ol 共用物理库 → 一次覆盖两端**。部署后启动日志契约门（warn）**通过**：账本 0074 ≥ REQUIRED 0070。
2. **L2 池接线（Track A）**——组合根建 `apiPool/automationPool/contentPool`（max 30）+ `tokenUsagePool`（content 专用 max 4）；`configMirrorPool = apiPool`（现有引用零改）。**39 store 全按属主接线：api 20 / automation 14 / content 5**。⚠️ **quota/pacing/session/resume 四个 automation 配置 store 钉在 api 池**（它们在自己写事务里同连接 bump api 属主 `config_mirror_version`，跨库不可分 → L3 前必须先把该 bump 移出事务，见 §4.2 风险②，代码里已留 inline 注释）。测试：tsc 0 / acceptance 105/0 / 全量 3194/0（monolith 字节等价）。
3. **resolver 落 kernel** + 边界裁定（`boundaries/ownership-rules.json` fileOverrides + `kernel-non-members.json` roster + 重生成 `module-ownership.json`）。
4. **0075/0076 以 staged ops 脚本入库**（`scripts/db-split/`，**未执行**）。

**L2 未做/推迟（交给 L3 或需 admin）：**
- **`account-delete-cascade.ts` 推迟到 L3**（未接线的跨 owner purge；它在 `src/transport/`（自动继承 automation），但 purge 写 content 表 → 静态跨层 DML，需要写豁免，而豁免只有在真接线后才有正当性。L2 为死代码登记豁免不划算）。
- **0075 建三空库 BLOCKED**：dev 上 app 角色 `aidcp` **无 CREATEDB 权限**（`rolcreatedb=f`），需 admin（postgres 角色）或 `GRANT aidcp CREATEDB` 才能建。三个 owner 库现**尚不存在**。非关键路径（L3 数据迁移前才需要）。
- **OL 代码未部署 L2**：OL 是**稳定生产、从 `release/*` 分支部署**（非 master）。L2 代码→OL 是独立的发布分支决策；baseline（DB）已覆盖 OL；L2 字节等价 ⇒ dev 跑 L2、OL 跑旧码、共库无 skew。
- **enforce（6.5）暂不切**：活跃 schema 重构期 `warn` 更安全（漂移只记不砖）；账本 0074==KNOWN_MAX、enforce 会通过，但等拆库稳定 + 覆盖一次 ol 部署后再切。

**L3 进展（2026-07-25，策略已定=owner-URL 整体翻转）：**
- **完整跨 owner 依赖地图已测绘**（3 agent 并行扫三 owner + 综合，逐处 file:line 核实）：**58 依赖 / 55 raw**，**没有一个 owner 现在能干净翻转**。权威计划 + 逐 owner 修法 + 排序见新文档 **`docs/cloud-block3-l3-cutover-plan.md`**。核心：owner-URL 翻转机械上简单，但拆库前必须先把 55 处 raw 跨库访问路由过传输层（Block² 端口模式），其中 **9 处跨库事务**（4 config-mirror bump + 5 offboard 联合提交）+ 1 处跨库写（interaction_audit_events 双写）**需架构级最终一致重设计**，不是 HTTP 化能解。这是把 Block² 未完的数据层解耦补齐的大工程、多变更、须每步测+部署。
- **step0 已做（纯字节等价）**：outbox 传输 helper 池改绑——`startRiskCommandConsumer`/`bridgeEventBusToOutbox`/`PanelEventReplay`/`emitRiskCommand` 从 api 的 configMirrorPool 改绑 **automation 池**（event_outbox / 风控命令 outbox 属 automation；ConfigMirrorRefresher 读 api 的 config_mirror_version、保持 api 池）。monolith 下这 4 个 helper 不实例化 → dev/ol 零影响；修掉拆库后读写错库的接线 bug。**cloud master `f8651f0`，测试 tsc0/acc0/全量3194·0，部署 dev 验证通过。**
- **架构铁律（2026-07-25 定，此前一版取巧被撤）**：最终目标是三个**真正独立的服务**（各自进程、各自库、只走接口）。**一个域绝不直连另一个域的数据库**。跨域读一律走「属主域的接口」（kernel 定义、属主域用自己的连接实现、消费方只依赖接口）；同进程期接口=进程内直调，拆进程后换 HTTP。**曾有一版把别的域的池注入 content 让它「在对的池上跑查询」——那仍是 content 直连别人的库、知道别人的表，反模式，已撤销重做为接口。** 唯二不因接口化解决:跨库**事务**（不能跨库，须最终一致）+ 跨库**写**（须收口单写者）。
- **content 三处运行时跨库读全解——经接口、零跨库直连**（半连接改写 `e0d353c` → 接口重做 `5cbb6b1`，部署 dev）：curated listForClient 经 kernel 接口 `TriggeredPublishRefsReader` 向 automation 域要触发集（属主 `PgDelegatedTaskStore.triggeredPublishRefs` 跑在 automation 池），本地 `id=ANY` 半连接、排序/分页 SQL 不变（**dev 真实数据等价 31==31 双向差 0**）；media 经 kernel 接口 `AccountPlatformReader` 向 api 域要平台（属主 `PgAccountStore.getPlatformOrNull` 跑在 api 池，缺账号返 null）；draft claimNext 移除 vestigial `EXISTS(publish_log)`（publish_log 从不删）。组合根惰性 thunk 接线。**还减一条耦合边**（media→platform/index，frozenTotal 101→100）。⇒ **content 零跨库直连**，只剩 4 条跨 owner DDL FK（翻转时降）。tsc0/acc0/全量3194·0。
- **未做（须监督，同样一律走接口）**：api↔automation 双 HUB 的读（属主加读端口、消费方依赖 kernel 接口、拆跨库 JOIN）、**9 处跨库事务 + 1 处跨库写**（架构级最终一致）、DDL FK 降级、任何实际翻转（含建库+拷数据+翻 URL）——用户不在时不对生产数据路径盲改。详见 `docs/cloud-block3-l3-cutover-plan.md`。

**L3 剩余工作（破坏性 / 需决策；详见 `docs/cloud-block3-l3-cutover-plan.md`）：**
- **① cascade 单库验收形态（设计任务，先解再接线）**：naive 单库接线会死循环——relay 读 api outbox 又 emit 到 content/automation，而单库单 `event_outbox` 表 = relay 再读到自己的投递 → 无限重放。需独立 outbox 流（拆库后天然成立）或给 relay 加「带 sourceEventId 的不再 relay」守卫。cascade 单测用的是**每 owner 一个独立内存 outbox 桩**，即假设拆库后拓扑。
- **② 切换策略分叉（用户拍板）**：**owner-URL 整体翻转**（粗粒度、每 owner 一次短停机切换）vs **逐表五阶双写**（细粒度、零停机，但 §8.5 团队自订模板强制每阶段 ≥3 自然日观察、覆盖 dev+ol 各一完整业务日）。resolver+owner-URL 设计暗示前者；§5.3 / `docs/table-ownership-migration.md` 模板是后者。**两者对共享生产库数据的风险与时长完全不同，动数据前必须先定**。
- **③ 0076 降 12 条跨域外键**：危险窗口——**只在 ① cascade 接线并验证跑通之后**才 drop；共库期可逆（附了重建语句）；drop 前**共享库先整库 `pg_dump`**。
- **④ 数据切换**：建 owner 库（0075，需 admin）→ 各 owner 表+数据搬进各自库 → 配 `AIDCP_PG_<OWNER>_URL`（dev/ol 同值、共享三库）→ 切换。含不可逆 DROP、跨多日、共享生产库。
- **⑤ 四个钉 api 的配置 store**：automation 库拆出去前，必须先把它们的 `config_mirror_version` bump 移出跨库事务。
- **⑥ segC/segD outbox 地雷**：`bridgeEventBusToOutbox` / `PanelEventReplay` / `startRiskCommandConsumer` / `emitRiskCommand` 都跑在 api 池，但 `event_outbox` 属 automation——单库字节等价，automation 库拆出后就读/写错库。

---

## 1. 操作要求（OVERRIDE 默认工作方式，务必遵守）

用户对本重构的长期铁律（速度第一）：

1. **速度第一**：重构完成速度是第一目标。过程中**可接受 dev 有损**、可快速改、靠测试兜底。不纠结、不过度设计、YAGNI。
2. **尽量并行**：能并的独立轨全部并起来。**判据 = 是否碰同一个热点文件**。
   - `src/server.ts`（组合根）是**单写热点**——任何改它的活**串行独占**，一次只能一个写者。
   - 不碰 server.ts 的活（新迁移 SQL、新独立模块、新测试、建库脚本、文档）**可并行**，各开独立 worktree。
   - 每条并行轨 = 一个独立 git worktree，**各自 `npm ci`，绝不软链 node_modules**（软链会顺链改写 canonical，破坏并发 + 本机 Edge 运行环境；见 memory `worktree-symlink-gitadd-trap`）。
3. **测试统一进行一次**：**减少中间过程测试**。开发期各轨只跑 `typecheck` + 自己那点新单测收敛；把 `npm run test:acceptance` + 全量 `npm test` **攒到批次末、集成后统一跑一次**再 land。
4. **worktree 纪律**（见 memory `canonical-checkout-stays-on-main`、`parallel-fleet-dev-conventions`）：
   - 四个 canonical checkout（aidcp=main，edge/cloud/console=master）**永远停默认分支**，绝不在其中 `git checkout <feature>`。要分支隔离就另开 worktree（`../aidcp-cloud.wt/<name>`）。
   - 提交一律**显式列文件**（`git add <paths>`），**绝不 `git add -A`**。
   - commit message 末尾带 `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`。
5. **部署红线**（见 CLAUDE.md §5、memory `verify-ecs-state-before-deploy`）：
   - 部署只从 canonical master 的 eligible ref 走，**绝不从 worktree 部署**。
   - dev 部署默认直接做（用户长期授权），安全序列：`scripts/deploy-target dev --check` → 测试过 → **ECS 先备份** → rsync（不带 `--delete`，exclude `.env`/`node_modules`）→ 写 `.deploy-sha` → restart → 健康检查 → 失败即回滚。
   - **绝不碰同机 isales**（不同 systemd 服务/目录/端口）。
   - OL 部署**必须等用户明确要求**，从发布分支走，OL **先备份**。
6. **L3 破坏性专属红线**：
   - ⚠️ **dev 与 ol 共用同一物理库 `aidcp`**（隔离只靠异步任务的 `execution_target` 列，不靠连接）。**在「dev」跑破坏性 schema 迁移 = 改的是 ol 也在读的同一批行/约束**。所以「dev 先」不是隔离测试，而是**在共享库低峰期跑 + 就地验证**——这正是用户「周末无 OL 用户才冲 L3」的真意义。**执行前 OL/共享库先整库备份**。
   - **每表非批量**：逐表 backup → dual-write → 切读 → 停旧写 → drop，不要一把梭。
   - **「危险窗口」铁律**：跨域外键（0076）**只能在 account-delete-cascade 的 relay + per-owner purge 消费者已接线并验证之后**才 drop——先 drop 后接 = 删账号时子表变孤儿。
   - **绝不 DROP 未确认无引用的表/列**；drop 前先确认读写都切走。
   - 用户已拍板「周末无 OL 用户 → 冲到 L3」，但共享库备份 + 危险窗口顺序不能省。

---

## 2. 现状：Block② 进程拆分已 DONE（land + 部署 dev）

**cloud `origin/master` = `90319eb`**（本 session ff-merge 上去，dev 已部署到此 sha，跑 monolith，健康）。

Block② 让**一套 `src/` 代码**按环境变量 `AIDCP_SERVICE` 当 1 个或多个进程跑（纯选择器 `src/gateway/service-mode.ts`）：
- `monolith`（默认/未设）：四段全跑 = 拆分前逐字节等价（**dev 安全底线**）。
- `content`(A+B)、`automation`(A+C)、`api`(A+D)、`core`(A+C+D)。

已落提交链（都在 master）：
| sha | 内容 |
|---|---|
| `d645cc3` | batch1 生成/状态传输接缝（发布状态读端口 + 生成触发端口，同步 kick + 分段长轮询绕 180s HTTP 天花板） |
| `cb84f84`(merge `e65df56`) | api-split 三件传输原语（RiskReadPort / risk-command outbox / eventbus→outbox 桥），已建已测 |
| `79311c3` | 5 服务模式 + 纯选择器 service-mode.ts |
| `e73fb4e` | **de-fat**：内容生成管线（postProcessor/wanxiang/seedream/imageProvider/publishOrchestrator + 视觉块 + 31 发布角色）从 segA尾/segC 整体搬进 segB；content 拥有生成，automation 瘦身开机 |
| `a780255` | 边界裁 3 个 kernel 契约文件（AC-BOUND 12/12） |
| `90319eb` | **api-split 接线**：三件接进 segC/segD，全 mode-gated 默认 local |

**三红线（已亲验守住，接 L2/L3 时勿破坏）**：
- monolith 逐字节等价：全量测试改前改后逐字相同（3198 tests / 3188 pass / 0 fail）。
- 风控单写：segD 唯一风控写 `recoverRestrictedForAccount`（server.ts:6037）在 `mode==='api'` 分支**每条路径都 return**（restricted → `emitRiskCommand` 命令落 outbox、返 `changed:false` 不伪造迁移；无 target → fail-closed 返 null），**绝不落穿**到 6073 的直调；单写者只在 segC 的 `startRiskCommandConsumer` apply。
- monolith 启动零新传输组件（consumer/bridge/replay/read-API 全 `mode!=='monolith'` 门控）。

**已知 follow-up（诚实崩、非假成功，非阻塞）**：api 模式下 panel 的 `risk/status`+`risk/quota`、command-dispatch、edge 端点请求时 500（用 undefined 的 riskRegistry）。属跨进程读/命令未接线，L2/L3 之外的独立小活。

---

## 3. 已 park 的 Block③ 脚手架（两个分支，未 land）

均由本 session 的 workflow/agent 产出，各自绿、独立 worktree、无软链。

### 分支 `db-l2-resolver`（tip `d90e7c5`）
- `src/kernel/pg-owner-connection-resolver.ts` + `test/kernel/pg-owner-connection-resolver.test.ts`（6/6 绿）。
- `resolveOwnerPgConfig(owner, env)`：owner ∈ content/automation/api → per-owner `pg.PoolConfig`；**任一 owner 的 `AIDCP_PG_<OWNER>_URL` 未设时逐字回落今天的共享单库配置**（`DATABASE_URL` → `PGHOST/...` → `DEFAULT_PG_CONFIG`）。三 owner URL 都不设（今天）→ 三者与现网 `resolveEnvPgConfig()` 逐字节一致 = 单库、三别名。
- **纯函数、未接线**（dead-but-safe）。

### 分支 `db-l3-authoring`（tip `eb874e6`）
- `scripts/db-split/0075_create_per_service_databases.sql`：幂等非破坏建 `aidcp_content/aidcp_automation/aidcp_api` 三空库（`SELECT … WHERE NOT EXISTS … \gexec`）。**是 ops 脚本非迁移**（CREATE DATABASE 不能进事务/不在目标库内）。
- `src/transport/account-delete-cascade.ts` + 测试（14/14 绿）：`account.deleted` 跨库 outbox 级联，复用 `event-outbox.ts`（`emitOutboxEvent`+`OutboxConsumer`，事务型、至少一次、execution_target 隔离）。per-owner 幂等 purge。**未接线。**
- `migrations/0076_downgrade_cross_owner_account_fk.sql`：降 **12 条跨域外键**（11 `ON DELETE CASCADE` + 1 plain；`accounts` 属 api，跨域 = content/automation）。**已写未 apply。**
- ⚠️ **caveat + 合并前必做**：0076 放 `migrations/` 但未 bump `KNOWN_MAX_SCHEMA_VERSION` → 该分支 `schema-contract.test` 预期内红。**合并/land 前先把 0076 从 `migrations/` 挪到 `scripts/db-split/`（标 staged 未激活）让分支全绿**；等真做 L3 时再移回 `migrations/` + bump 常量 + apply。

**关键架构事实**：账号删除今天靠跨 content/automation/api 三域的 `ON DELETE CASCADE` 外键级联，**物理拆库打断它**（跨库外键不可能）。所以「跨域外键降级 + account-delete outbox 级联」是 **L3 硬前置**——必须先落，才能切任何表的读写。

---

## 4. L2 剧本（非破坏、byte-equivalent、可安全 land + 部署 dev）

L2 = 「代码就绪 + 建空库」，默认仍单库、零行为变更。可高度并行。

### 4.1 池接线（已核实的真实结构）

server.ts 的 segA = **lines 791–1872**（恒跑段）。**整个 server.ts 只有一处字面 `pg.Pool`**：`configMirrorPool`（`server.ts:811`，`new pg.Pool({...resolveEnvPgConfig(), max:30})`）。其余全是 store 内部 `this.pool = options.pool ?? new Pool(...)`——server 要么把 `pool: configMirrorPool` 传给它复用，要么让它自建。三种自建配置路径：**SHARED**（用 configMirrorPool）/ **HOST-param**（`{host:PGHOST??DEFAULT,...}`，**不读 DATABASE_URL**）/ **ENVCFG**（`resolveEnvPgConfig()`，读 DATABASE_URL）。

**最小接线（store 内部零改，只在组合根分派池）**：
1. 在 L811 同槽建三 owner 池：`contentPool/automationPool/apiPool = new pg.Pool({...resolveOwnerPgConfig('<owner>'), max:30})`；`configMirrorPool` 即 `apiPool`（config_mirror_version 属 api）。
2. 经每个 store 已有的 `options.pool` 缝，按 owner 分派对应池（owner 映射见 `boundaries/table-ownership.json`：segA 里 api 20 store / automation 14 / content 5，均单 owner 表集）。
3. `TokenUsageStore`（content，专用 max:4 小池）改 `resolveOwnerPgConfig('content')`。
4. segC 的风控/告警/interaction 池、segD 的 panel 池在 segA 之外构造，可 follow-up 接线。

### 4.2 两个逐字节风险（接线前必确认，否则破 monolith 等价）

1. **HOST-param store 今天无视 `DATABASE_URL`**（15 个：publish-log/account/credential/content-schedule/facebook-*/liked-notes/valuable-comments/interaction-feed/delegated-task/notification-contact/publish-approval/first-post 等），只读 PG* 环境或 `DEFAULT_PG_CONFIG`。而 resolver 默认路径**优先 DATABASE_URL**。**⇒ 搬 HOST store 到 owner 池，仅当部署 `.env` 里 `DATABASE_URL` 未设时才 byte-equiv**；若 ECS 设了 DATABASE_URL，这些 store 的目标会从 PG*/DEFAULT 切到 DATABASE_URL。**接线前先 SSH 确认 dev `.env` 用的是 `DATABASE_URL` 还是 `PGHOST/...`。**
2. **跨域事务 = 真拆库硬阻（非 L2 阻，标记留给物理拆库 change 裁决）**：`writeWithMirrorBump`（`config/mirror-version-store.ts:164`）在 **store 自己的连接**上 `BEGIN` → 写本 store → 同连接 `bumpInTx` 写 **api 的 config_mirror_version** → `COMMIT`。4 个 automation 配置 store（quota/pacing/session/resume）都在一个事务里原子 bump 一张 api 表。单库默认下透明；**真给 per-owner URL 后跨库事务做不到**。L2 默认（单库）不触发，**别在 L2 解它**，但接线时留注释、物理拆库 change 必须裁决（config-mirror 簇归 api 内聚 / 或把 bump 移出 store 事务）。

### 4.3 并行轨 + 统一测试 + land

**并行轨（独立 worktree，各自 npm ci 无软链）**：
- **轨 A（server.ts，串行独占）**：4.1 的池接线。
- **轨 B（新文件，可与 A 并）**：把 `db-l3-authoring` 的 `account-delete-cascade.ts` + `0075` 整理到主干（**0076 先挪 `scripts/db-split/` staged**）。
- **轨 C（ops，可并）**：dev 上 `npm run migrate baseline`（**dev 未 baseline，见 5.1**）→ apply `0075` 建三空库（幂等非破坏，不动 `aidcp`）。

**集成 → 统一测试一次 → land**：
1. 集成 worktree（off master）合 `db-l2-resolver` + `db-l3-authoring` 绿件（0076 挪 staged）+ 轨 A 接线。
2. **统一测试一次**：`npx tsc --noEmit` → `npm run test:acceptance` → 全量 `npm test`，要求 monolith 全量零新失败（逐字节等价）。
3. ff-merge → master → push → 部署 dev（安全序列，仍 monolith）。

---

## 5. L3 剧本（破坏性，共享库低峰期，逐表，红线见第 1.6 节）

### 5.1 迁移机制（已核实）——先懂再动

- **迁移经 CLI 触发，非启动时**：`npm run migrate <status|up|verify|baseline>`（`scripts/migrate.ts`）。`up` 取批级 advisory lock、按序 apply、**每条迁移各自 BEGIN/COMMIT**、写账本表 `schema_migrations`；任一条失败 → ROLLBACK 停整批。（旧 `scripts/run-migration.ts` 无账本无序，task 5.11 待删，别用。）
- **schema 契约门（`src/schema/schema-contract.ts`）**：`REQUIRED_SCHEMA_VERSION='0070_baseline_self_heal_columns'`、`KNOWN_MAX_SCHEMA_VERSION='0074_event_outbox'`。启动时 `server.ts:801`（segA 最前、所有 store.init 之前）读账本比对，verdict = unreadable/behind/ahead/ok。**模式由 `AIDCP_SCHEMA_GATE` 定，缺省 `warn`（只记不砖）**，`enforce` 才 fail-closed（task 6.5 待翻）。关键：账本 **低于 KNOWN_MAX 但 ≥ REQUIRED 也算 ok**——所以可先部署 bump 了 KNOWN_MAX 的代码、再 apply SQL。
- ⚠️ **dev 从未 baseline（task 11.3/11.4，阻塞前置）**：dev 的 `schema_migrations` 账本表**尚不存在**，`migrate status` 报 70 版全 pending。**任何 `migrate up` 之前，必须先在 dev 跑 `npm run migrate baseline`**（把已存在的 schema 登记进账本），否则 up 会试图重建已存在的表。
- **共享库**：`migrate` 经 `.env`（`DATABASE_URL`/`PG*`）连的就是 dev+ol 共用的 `aidcp` 库。**apply=改共享库**（见 1.6）。
- 0075/0076/scripts/db-split 现在**只在 parked 分支**，master 上没有（master 迁移顶到 0074）。
- 关联 change `cloud-schema-migration-executor`（59/68 done）：开项 5.7/5.8（batch5-6 含 `client_environments.account_id→accounts` FK 回填）、5.9-5.11（空库上拉 + 删 knob/run-migration.ts）、**6.5（翻 enforce）**、**11.4（baseline dev）**。

### 5.2 硬前置（切任何表读之前，按序）

1. `npm run migrate baseline`（dev，若未做）。
2. **先接线并验证** `account-delete-cascade.ts`（api 删账号发 `account.deleted` → 各 owner 消费者幂等清本域账号行）——**危险窗口铁律：cascade 证明可用后**才降外键。
3. 把 `0076` 移回 `migrations/` → `npm run migrate up` 降 12 条跨域外键 → bump `KNOWN_MAX_SCHEMA_VERSION` 到 `0076...` → 重启 → `migrate verify`。（`REQUIRED` 不动。0076 是 `kind=expand`，DROP CONSTRAINT 属放松、无需 `--allow-contract`。）

### 5.3 逐表五阶（每表独立走完再下一张，`accounts` 作级联源**排最后**）

1. **备份 + 建**：目标 owner 库建同结构表（+ 现有数据快照）。
2. **dual-write**：双写新旧库一段时间。
3. **切读**：读切到新库（配 `AIDCP_PG_<OWNER>_URL` → per-owner 池）。
4. **停旧写**：确认无旧库写入。
5. **DROP**：确认读写都切走后再 drop 旧表。

**OL**：dev 全程验证通过 → 用户拍板 → **共享库/OL 先整库备份** → 周末低峰期同法逐表 → **绝不碰 isales**。

---

## 6. 关键 sha / 分支 / 命令

```
cloud origin/master     = 90319eb   （Block② landed，dev 已部署到此）
parked  db-l2-resolver  = d90e7c5   （连接解析器 + 测试）
parked  db-l3-authoring = eb874e6   （account-delete-cascade + 0075 + 0076；0076 需挪 staged）
canonical cloud         = /Users/baitianxing/codes/aidcp-cloud （停 master）
DB 前置设计草稿          = <prior-session scratchpad>/db-split/  （*.md + table-ownership-manifest.json）
权威表归属               = boundaries/table-ownership.json
dev 部署脚本            = <prior-session scratchpad>/deploy-cloud-dev.sh （安全序列，可复用）
dev 目标               = 121.89.85.150  key ~/codes/dev-0722.pem  svc aidcp-cloud.service  dir /opt/aidcp/cloud
```

常用：
```bash
# 开并行 worktree（各自 npm ci，绝不软链）
git -C /Users/baitianxing/codes/aidcp-cloud worktree add -b <name> ../aidcp-cloud.wt/<name> master
cd ../aidcp-cloud.wt/<name> && npm ci --prefer-offline

# 统一测试（批次末一次）
npx tsc -p tsconfig.json --noEmit
npm run test:acceptance      # AC-* 红线（含 AC-BOUND / AC-OWN / AC-PROTO / AC-PUB / AC-RISK）
npm test                     # 全量 node:test（tsx --test 'test/**/*.test.ts'）

# 边界棘轮：改 kernel 归属后必跑
npm run boundaries:refresh   # 重生成 module-ownership.json
```

---

## 7. 多服务部署拓扑（已核实）与激活

`deploy/multi-service/`（master）：一套代码 `/opt/aidcp/cloud`、一份共享 `.env`，`AIDCP_SERVICE` 选段。激活矩阵：

| service（unit） | `AIDCP_SERVICE` | 段 | 监听 | 跨服务 env |
|---|---|---|---|---|
| **content** | `content` | A+B | `127.0.0.1:8092`（`AIDCP_CONTENT_PORT`，内部 curated 读 API） | 无 |
| **automation** | `automation` | A+C | `0.0.0.0:8787`（`AIDCP_PORT`，边缘 WS） | 无（不建数据网关） |
| **api** | `api` | A+D | panel `AIDCP_PANEL_PORT`(默认 8090) + client-auth（均从 `.env`） | `AIDCP_GATEWAY_MODE=http`、`AIDCP_GATEWAY_BASE_URL=http://127.0.0.1:8092`（curated 读远程 content）、`AIDCP_AUTOMATION_URL`（风控读远程 automation） |
| **core** | `core` | A+C+D | 8787 + panel + client-auth | 同 api（网关 http） |

两种拓扑：**3-service**（content+automation+api，目标）/ **2-service**（content+core，过渡）。`deploy-multi.sh <target> [check|up]` 切换前会 grep 同步的 `service-mode.ts` 做能力探测，不满足则拒绝、保 monolith 活着。

**⚠️ README/unit 头里「serviceModeFromEnv 只认 content/core/monolith、api/automation 回落 monolith」与「segD 引 segC 字段不能独立开机」两条 hard blocker 已被 Block²（`90319eb`）解阻**——api/automation 模式（`79311c3`）+ segD 接线（`90319eb`）都已 land 到 master、三模式实测开机不崩。**该 README 是 Block² 前写的、陈旧**；接手时把它更新为「已解阻」。dev 当前连单库经 `.env` 的 `DATABASE_URL`（主）或 `PGHOST/...`；三 owner URL 均未设 ⇒ resolver 接线后仍塌成同一池。

---

## 8. 验证清单（统一测试一次，接手照跑）

```bash
npx tsc -p tsconfig.json --noEmit          # 期望 EXIT 0
npm run test:acceptance                    # 期望 105/0（AC-BOUND/AC-OWN/AC-PROTO/AC-PUB/AC-RISK 红线）
npm test                                   # 期望全量 3188 pass / 0 fail（monolith 逐字节等价）
# 改了 kernel 归属：npm run boundaries:refresh 后再跑 test:acceptance
# 改了迁移：npm run migrate status / verify（dev 需先 baseline）
```

三条红线不可破：monolith 全量零新失败；风控终态只 automation 单写；monolith 不启动新传输组件。

> 记忆锚点：`cloud-decoupling-execution-progress`（全链进度 + sha）、`worktree-symlink-gitadd-trap`、`canonical-checkout-stays-on-main`、`verify-ecs-state-before-deploy`、`delegated-task-cloud-target-and-stale-recovery`（DEV/OL 共库 target 隔离）、`openspec-triage-and-realmachine-backlog`。
