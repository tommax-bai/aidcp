## Context

### 现状 1：15 处进程内镜像，刷新入口只有两个

实测清单（`aidcp-cloud`，2026-07-22）：

| # | 镜像 | file:line | 表 | 权威侧 | 消费侧 |
| --- | --- | --- | --- | --- | --- |
| 1 | 安全限额 | `src/config/quota-config-store.ts:99` | `quota_config`（PK `tier,action`，全局） | 面板 → api | risk → automation |
| 2 | 操作兜底 floor | `src/config/pacing-config-store.ts:86` | `pacing_floor_config`（PK `operation`，全局） | 面板 → api | risk → automation |
| 3 | 单场会话上限 | `src/config/session-config-store.ts:136` | `session_config_global`（单行） | 面板 → api | risk → automation |
| 4 | 自动续场护栏 | `src/config/resume-config-store.ts:114` | `resume_config_global`（单行） | 面板 → api | risk → automation |
| 5 | 账号人设 | `src/config/persona-store.ts:71` | `persona_config` | api | automation + content |
| 6 | 内容排期 | `src/config/content-schedule-store.ts:400-401` | `content_schedule*` | api | automation |
| 7 | 全局模型配置 | `src/config/model-config-store.ts:73` | `model_config` | api | content + automation |
| 8 | 角色模型配置 | `src/config/role-config-store.ts:82` | `role_config` | api | content + automation |
| 9 | 类目模型配置 | `src/config/category-config-store.ts:85` | `category_config` | api | content |
| 10 | 引流热度阈值 | `src/config/hot-lead-config-store.ts:78` | `hot_lead_config` | api | automation |
| 11 | FB 评论配置 | `src/config/facebook-comment-config-store.ts:172` | FB 评论配置表 | api | automation |
| 12 | FB 加群自动化配置 | `src/config/facebook-group-join-automation-store.ts:113` | FB 加群配置表 | api | automation |
| 13 | 运营暂停态 | `src/account-state.ts:26` | `accounts.status` | api（面板 / 飞书）+ automation（FB 加群自停） | automation |
| 14 | 环境慢启动锚点 | `src/client-auth/client-user-store.ts:447-448` | `client_environments.slow_start_since` | api | automation（risk） |
| 15 | 环境自动化出口闸 | `src/client-auth/client-user-store.ts:445` | 环境删除生命周期 | api | automation（WS 出口） |

刷新入口只有两个：`init()` 里的一次 `reload()`（`src/config/*-store.ts` 的 `reload()` 全部 `private`，唯一调用点是同文件的 `init()`），以及本进程写入时的就地改缓存。`src/config/` 与 `src/risk/` 下 `setInterval` / `LISTEN` / `NOTIFY` / `pg_notify` 命中数为 0。`src/server.ts` 里那条注释把这条性质写死：「raw SQL 改库**不刷镜像**（全仓无 watch / setInterval）→ 没有此闸就没有秒级止血手段。重启即生效。」（定位用 `grep -n "不刷镜像" src/server.ts`；该文件改动频繁、行号会漂，2026-07-22 实测在 `:1411`，本 change 早期稿写的 `:1430` 是错的。）

### 现状 2：这个缺陷今天就在生产上成立

dev 与 ol 是两个 cloud 进程，读写同一个 `121.89.85.150/aidcp`，只按 `account_id` 隔离（`docs/deployment-environments.md:64-70`）。两台各自跑自己的面板 API（`docs/deployment-environments.md:177`）。上表第 1–4、7–10 共 8 处是**全局表、无 `execution_target` 列**（`quota_config` PK `(tier, action)`；`session_config_global` / `resume_config_global` 是 `CHECK (id = 1)` 单行；`pacing_floor_config` PK `operation`）。因此：在 dev 控制台改一个全局安全限额，ol 进程的镜像到重启才可见，中间零日志、零告警、后台回显写入成功。

第 5、6、11–15 是账号 / 环境作用域的，今天靠「一个账号只在一个 target 跑、且编辑走该 target 的面板」这条**未声明的偶然条件**遮住了同一个缺陷。拆服务会把这条偶然条件彻底移除。

### 现状 3：读取契约写死为「同步、零 IO、永不抛」

`src/risk/types.ts:21-40` 逐字写明这条契约，并给出理由：`effectiveQuotas()` 是同步热路径（`canDo` / `explain` / `dailyRemaining` 全同步调用，`canDo` 在浏览闭环每个动作都调），绝不能 await PG；同处还写明「为什么是现读而非构造期快照」——`RiskControllerRegistry` 的 controller Map 永不驱逐，构造期读入会让勾选「写库成功、HTTP 回 200、行为纹丝不动到重启，且零日志」。

人设侧同理：`src/config/persona-store.ts:107-115` 的 `getForAccount` 是同步读镜像、永不抛；`src/config/persona-store.ts:239-252` 的 `createPersonaResolver` 每次现读；`src/agents/base-role.ts:48-54` 每次访问 `this.soul` 都走这个取值口。

### 现状 4：两处热路径镜像今天是 fail-open

- `src/account-state.ts:58-62`：`isPaused` 缓存 miss 返回 `false`（视为 active）。同进程下正确——镜像是全量持久化投影，miss 只发生在从未注册/从未暂停的账号。
- `openspec/specs/accounts-master-data/spec.md:104-110`：「有人设行 → 已绑，无人设行 → 未绑」。同进程下正确——镜像即库。

跨进程副本下这两条都会翻向：「副本里没有」≠「库里没有」。

### 现状 5：三态今天只活在边云线上，没进服务契约

`src/comm/protocol.ts:695-701` 定义了 `personaBound` 的三态（`true` / `false` / 字段缺省=未知），`openspec/specs/edge-companion-ui/spec.md:752`、`:772`、`:1093` 把它写成 MUST。但云端一侧的判据 `isPersonaBound(accountId): boolean` 是**二值**（`src/server.ts:2618` 等 4 处注入点），`src/comm/ui-snapshot.ts:177-183` 直接把这个 boolean 下发。也就是说：三态的第三态今天只由「云端还没推」这一事件产生，云端自身没有能力表达「我不知道」。副本陈旧会让云端**权威地**下发 `personaBound: false`，边缘按契约弹向导——这正是 `persona-bound-tristate` 修掉的那个 bug 的形状。

同一个二值判据还有更硬的下游：`src/delegated-task/worker.ts:361-366` 把 `needs_persona_setup` 走 `blocked → retryable:false → non_retryable_failure` 终态路径，用户的委托任务会被**永久判死**。

## Goals / Non-Goals

**Goals：**

- 消除「写方改了配置、读方永远看不到」这一类静默失效，先在单进程内可验收，拆进程当天不返工。
- 给每一处跨进程副本一个**可证明的陈旧上限**，以及超限后的**明确停手**行为。
- 把「未知≠否」从边云线上契约延伸到云端服务契约，覆盖人设、暂停态、环境出口闸。
- 不引入新的运行时依赖（现有依赖只有 `pg` / `ws` / `ali-oss` / `satori` / `@resvg`）。

**Non-Goals：**

- 不做通用配置总线、不做配置热更新框架、不做快照引用。
- 不改协议消息类型，不动两份 `protocol.ts`、命令桥动作映射、角色注册、风控状态机。
- 不改变拆仓决策本身，也不改变 dev/ol 拆库这一已被推迟的决定。
- 不为 `persona_config` 新增版本列（用内容哈希 + `updated_at` 推导即可）。

## Decisions

### 1. 四类限频配置随消费方归 `aidcp-automation`（先做，零代码成本）

**核实结论：属实。** `grep "from '.*config/" src/risk/` 命中 0；`grep "from '.*risk/" src/config/*.ts` 命中 13 处（`quota-config-store.ts:18-27`、`pacing-config-store.ts:27`、`session-config-store.ts:30`、`resume-config-store.ts:32`、以及四个 facade）。依赖方向已经单向倒置：配置层依赖风控层的常量与校验，风控层只持接口不依赖配置层实现。这四个 store 在 `src/config/` 之外的引用只出现在组合根 `src/server.ts:241-250`、`:538-576`、`:4191-4199`。

因此把这四个 store 与其四张表判给 `aidcp-automation`，是纯归属划线，不需要改任何一行消费方代码。收益是一次性消除四条跨服务同步读，`interaction-risk-gating` 的「每次现读、改完即热生效、MUST NOT 需要重启进程」（`openspec/specs/interaction-risk-gating/spec.md:97`、`:226`）在 automation 进程内逐字成立。

**后台编辑的落点**：Console → `aidcp-api` → `aidcp-automation` 窄内部 HTTP 写。方案 §4.2 已允许这条方向（另见 §5.1 表内「四类限频配置」行：后台编辑经 `aidcp-console → aidcp-api → aidcp-automation` 窄内部 HTTP 写，`aidcp-api` MUST NOT 直写）。

**必须同时写死的两条约束**（否则归属重排会制造新缺陷）：

- **api MUST NOT 为这四张表保留本地副本用于面板回显。** 面板读回值必须透传 automation。理由与 `openspec/specs/interaction-risk-gating/spec.md:589-593`（慢启动投影与 clamp MUST 同一解析函数、同一次时钟）同源：只要展示值和生效值分两处求值，就一定会出现「后台说 6、闸按 4 拦」。
- **归属重排消除的是「跨服务同步读」，不消除「跨进程可见性」。** dev 与 ol 是两个 automation 进程共库，一次面板写入只到达其中一个进程的镜像。因此这四张表**仍然需要**决策 2 的版本表，只是消费方从「另一个服务」变成「另一个 target 的同一服务」。这一点评审意见没有覆盖，但它决定了版本表是必需项而非可选项。

**一处必须处理的连带影响**：`src/config/content-schedule-store.ts:515`、`:836` 通过注入的 `globalActiveWeekMask()` 读 `session_config_global` 的活跃掩码，其中 `:836` 位于 `listCatalog()`——那是面板目录投影（api 侧）。`session_config_global` 迁走后，api 侧目录 MUST 改为向 automation 的窄内部接口取**生效掩码**，MUST NOT 在 api 侧另建一份 `session_config_global` 副本自行合成。

### 2. 失效通道：版本表 + 有界轮询为承重，`pg_notify` 只做加速器

**选定机制（写死）：** 共享 PostgreSQL 上单张 `config_mirror_version` 表，消费侧一个进程一个刷新器按固定周期整表拉取版本号并比对。

```sql
CREATE TABLE IF NOT EXISTS config_mirror_version (
  mirror_key TEXT PRIMARY KEY,
  version    BIGINT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

写方在**持久化配置的同一个事务里**做 `INSERT ... ON CONFLICT (mirror_key) DO UPDATE SET version = config_mirror_version.version + 1, updated_at = now()`。版本是库侧自增整数，不依赖任何主机时钟——三服务 × 两 target 跨主机部署下时钟不可信。

消费侧每轮一次 `SELECT mirror_key, version FROM config_mirror_version`（行数 = 镜像数，十几行），只对版本变化的那一个 key 触发对应 store 的 `reload()`。

**为什么是这条：**

- **无消息队列可用。** 方案 §15 明确不引入 Kafka；运行时依赖只有 5 个包。任何新通道只能落在已有的 PostgreSQL 上，不得引入新依赖。
- **`LISTEN/NOTIFY` 不能单独承重。** 它是 fire-and-forget：连接断开期间发出的通知永久丢失、无补偿、无痕迹；且 `pg` 的 Pool 不能用于 `LISTEN`（需独占长连 Client）。把它当唯一通道，一次网络抖动就原样复现「写方改了读方永远看不到」，而且比今天更难查——今天至少「重启即生效」是一条稳定规律。
- **陈旧上限可被直接证明。** 轮询下的陈旧度 ≤ 轮询周期 + 一次查询耗时，与通知是否送达无关。这正是本变更验收项所需要的可测量量；`LISTEN/NOTIFY` 给不出这个界。
- **不用 Outbox/Inbox（方案 §6.2）。** 那套是为跨服务**业务命令**设计的，带投递账本、去重、死信与重放。配置失效通知不是业务命令：无副作用、可丢可重、只需最终一致。套用只会新增一个死信运维面（评审 F23 已指出死信只有名词没有运维界面），换不来任何额外保证。
- **`pg_notify` 保留为可选加速器。** 允许在写方事务提交后额外 `NOTIFY`，消费方收到即提前触发一次比对。但陈旧上限的定义**只**由轮询周期给出，实现 MUST NOT 因为接了通知就放宽轮询周期。

**镜像键为闭集合。** `ConfigMirrorKey` 用 `Record<ConfigMirrorKey, true>` 穷举登记，新增镜像不登记即 typecheck 失败。这是本项目已被验证有效的防漂移手法（两份 `protocol.ts` 用 `Record<MessageType, true>` 穷举）。

**版本表 MUST NOT 加 `execution_target` 列。** CLAUDE.md §2 的 target 隔离约束的是「由后台扫描、认领、重试或恢复的持久任务」；版本表不是任务表，没有认领语义。配置本身是 dev/ol 共享的，两个 target 的进程各自独立轮询同一张表、各自维护自己的副本，这是正确行为而非缺陷。

**周期取值：** `T_poll` 默认 5 秒，可经 env 调整，实现 MUST 硬编码一个上界（建议 30 秒）并对超界值拒绝启动而非静默截断。

### 3. 镜像分两档，闸门镜像陈旧即停手

**分档判据（按字段语义，不按 store）：** 一个镜像字段若其取值可以让系统**开始或继续对真实平台下发动作**，即为**闸门镜像**；只改变动作参数、不决定是否动作的，为**参数镜像**。

按此判据划分（决策 1 迁走的 4 张表已成为 automation 本地写透镜像，不在跨服务副本集合内，但仍受决策 2 的跨 target 可见性约束）：

- **闸门镜像**：人设（5）、内容排期（6）、FB 评论配置的启用位（11）、FB 加群自动化配置的启用位（12）、运营暂停态（13）、环境慢启动锚点（14）、环境自动化出口闸（15）。
- **参数镜像**：全局模型配置（7）、角色模型配置（8）、类目模型配置（9）、引流热度阈值（10）、FB 评论/加群配置中的非启用参数位（11、12 的其余字段）。

**闸门镜像的陈旧行为（MUST）：**

- 每个闸门镜像声明 `T_stale`，默认 60 秒（= 12 × `T_poll`，容忍连续 11 次拉取失败）。
- 计时基准是**上一次成功完成版本比对**的时刻，不是上一次成功 `reload()` 的时刻——否则一个长期无变更的镜像会被永远算作陈旧。
- 超过 `T_stale` 即进入 `stale`：不再放行**新的**真实平台动作（新会话不启动、命令泵不下发新的互动/发布/评论命令）；**已在跑的会话走既有的自然结束路径诚实收敛**，MUST NOT 被就地 kill，也 MUST NOT 拿旧副本开启新动作。
- MUST 落一条具名告警 `config_mirror_stale`（带 mirror key、陈旧秒数、最后已知版本），且这次降级 MUST 可计量。
- MUST NOT 用「回落到最严档继续跑」代替停手。理由：最严档仍然是**放行**真实平台动作，且会把一次基础设施故障静默转成全车队降速——运营看到的是「系统在跑、只是慢」，正是评审 F06 描述的「外观健康、产出为零」那一类最难发现的故障。

**参数镜像的陈旧行为：** 继续使用最后已知良值，MUST 打告警并在相关产出上标注副本时刻，MUST NOT 停手。

### 4. never-brick 的适用面必须收窄

现有 never-brick 语义（`openspec/specs/interaction-risk-gating/spec.md:99`：提供者缺失 / 缺行 / 值非法 → 回落 `quotas.ts` 写死默认，绝不抛、绝不让风控闸失效）在拆分前是安全的，因为「提供者缺失」只发生在启动装配失败这一种情形。

拆分后「副本读不到」会变成常态化的运行时状态。若沿用 never-brick，等于「权威一挂，全车队按写死默认满配额继续跑」。因此必须写死这条区分：

- **权威已答但缺行 / 值非法** → 保持 never-brick，回落写死默认。
- **权威未答（副本陈旧或不可达）** → 走决策 3 的闸门镜像停手，MUST NOT 套用 never-brick。

决策 1 把四类限频配置迁进 automation 之后，never-brick 的实际适用面**不变**（provider 与 controller 同进程）；这条规则约束的是任何未来把它们再拆出去的做法。

### 5. 三态贯穿服务契约

**人设：** 判据签名从 `isPersonaBound(accountId): boolean` 改为返回 `'bound' | 'unbound' | 'unknown'`。选具名字符串而非 `boolean | undefined`，理由是 `undefined` 在 TypeScript 里太容易被 `!x` / `?? false` 压成 `false`——那正是历史 bug 的形状，而这类压平 typecheck 抓不到。

- 只有 `'unbound'` 才允许：`ui.snapshot` 下发 `personaBound: false`、置 `needs_persona_setup`、把发布/评论任务判为非重试终态。
- `'unknown'` MUST 映射为独立不可用态 `persona_unavailable`：MUST NOT 下发 `personaBound` 字段（保持 `src/comm/protocol.ts:695-701` 既有的「云端还没说」表达，边缘零改动）、MUST NOT 触发人设向导、MUST NOT 让委托任务落 `non_retryable_failure`（MUST 改为可重试的 `deferred`）。
- `src/agents/base-role.ts:52` 的取值口在会话中途遇到副本陈旧时 MUST NOT 靠抛 `no_persona` 来「兜底」：闸门 MUST 在会话/动作入口就收敛，角色执行中途抛异常是把一次可预期的降级伪装成崩溃。

**运营暂停态：** `isPaused` 从二值改为 `'paused' | 'active' | 'unknown'`。`unknown` 按闸门镜像停手，MUST NOT 沿用 `src/account-state.ts:62` 现有的「miss = active」——那条在同进程全量镜像下正确，在跨进程副本下等于「运营点了暂停、后台回 200、账号继续点赞」。

**环境自动化出口闸：** 同族三态，`unknown` 时 MUST NOT 向该环境下发普通自动化命令。

**慢启动锚点：** 副本 `unknown` 时 MUST NOT 判为「未开启慢启动」——那是把「未知」压成「否」的配额版本，会让一个刚开启慢启动的新号按满配额跑。

### 6. 落点在方案 §12 阶段 1，而不是阶段 2/4

方案阶段 1 的既定要求是「即使暂时使用进程内适配器，也采用未来 HTTP/消息的合同形状」。对本变更这批同步取值口，这条要求当场不成立——除非在阶段 1 就按**副本语义**实现（版本 + 刷新器 + 陈旧上限），而不是直接同步调对方 store。

在阶段 1 建的三条理由：① 单进程内即可跑通全部验收（写方 +1 版本、读方轮询 reload、断版本查询验停手），风险为零；② dev/ol 双进程共库的现存缺陷当场就被修掉，收益不必等拆分兑现；③ 若不在阶段 1 建，阶段 2/4 拆进程当天就会静默失效，而这类失效没有任何既有机制能报出来。

## Risks / Trade-offs

- **[轮询给整库加了一条固定负载]** → 一次 `SELECT` 十几行、无 join、走主键顺序扫，`T_poll=5s` 下每进程 12 QPM。实测稳态 aidcp 库仅约 5 条连接，余量充裕。刷新器 MUST 复用现有 Pool，MUST NOT 另开连接池。
- **[`T_stale` 取太小会误停车队]** → 计时基准是「成功比对」而非「成功 reload」，且 `T_stale` 默认取 12 倍 `T_poll`，允许连续 11 次失败。取值 MUST 可经 env 调整，且 MUST 在进入 `stale` 前先打一次预警告警。
- **[停手语义可能被实现成 kill 在跑会话]** → 规范明确写「已在跑的会话走既有自然结束路径收敛」，并配一条场景断言。
- **[三态改造触及热路径签名，可能被压平回二值]** → 用具名字符串联合类型而非 `boolean | undefined`；`unknown` 分支在每个消费点都必须显式处理，否则 TypeScript 穷举检查失败。
- **[归属重排后面板显示与生效值分家]** → 决策 1 已写死 api MUST NOT 保留本地副本，面板读回值透传权威服务。
- **[版本表本身成为单点]** → 它与配置数据在同一个库、同一个事务里推进，不引入新的故障域。版本表不可读 = 库不可读，这一类已由方案 §11 缺失的「PostgreSQL 不可用」行统一处理，不属本变更范围。

## Migration Plan

1. 先建 `config_mirror_version` 表与迁移（纯 additive DDL，符合 `docs/deployment-environments.md:66` 的破坏性 DDL 冻结约束）。
2. 写方先开始推进版本（读方尚未接线，无行为变化）。
3. 接刷新器 + 参数镜像（陈旧只告警不停手），观察一轮。
4. 接闸门镜像三态与陈旧停手，逐个镜像灰度，每个都带 env 开关可秒回滚到「只告警不停手」。
5. 归属重排（四类限频配置划归 automation 模块边界 + 面板透传）在单仓内以模块边界形式落地，不改部署形态。

回滚：刷新器整体可经 env 关闭，关闭后行为退回今日现状（启动 + 本进程写入刷新），无数据回退步骤。

## Open Questions

- 无。`persona_config` 的版本推导口径已定（内容哈希优先、`updated_at` 兜底），是否新增版本列留给实装决定，不影响本契约。
