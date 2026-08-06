# 迁移记录 — `0110_facebook_global_policy_single_scope`

> change `unify-facebook-global-policy-across-targets` 第一段（expand 切读）的执行记录。
> 覆盖 tasks 2.6（备份导出时刻与文件位置）、7.5（受影响对象 / 阈值前后值 / 回滚窗口）、
> 7.6（两批对象分开成两份清单、交集单独标出）。
>
> **所有数值取自 2026-08-06 对 dev/OL 共用库的实读，不是从设计文档抄的预估。**
> 设计里预估「OL 上 10 个环境立即毕业」，**实测是 22 个** —— 预估值 MUST NOT 被当成记录。

## 1. 执行事实

| 项 | 值 |
| --- | --- |
| 迁移 | `0110_facebook_global_policy_single_scope`（kind=expand） |
| 应用时刻 | 2026-08-05 16:28:40+08（合并行 `updated_by=migration:0110_…` 的 `updated_at`） |
| 切换方式 | **一次全量切换，未分阶段**（7.6 前半） |
| 首次尝试 | 失败并整体回滚 —— 完成事实表的约束自动名 65 字节、超 PG 63 字节标识符上限，按拼写全名 `DROP IF EXISTS` 不命中**且不报错**，老约束原样留着拒绝哨兵值。修法与 sha 见 tasks 7.1 |
| 库形态 | dev 与 OL 共用同一个接口属主库（已实测：从 OL 连过去看到同一批行），故迁移只跑一次 |

## 2. 迁移前备份（2.6）

**导出时刻 2026-08-05 16:23（三份 CSV，dev ECS 上）**：

| 文件 | 内容 | 行数 |
| --- | --- | --- |
| `/opt/aidcp/backup-0110-global-policy.csv` | `facebook_operation_global_policy` 全量 | 2 |
| `/opt/aidcp/backup-0110-group-comment.csv` | `facebook_group_comment_policy` 全量 | 1 |
| `/opt/aidcp/backup-0110-completion.csv` | `facebook_environment_slow_start_completion` 全量 | 73 |

**目录与配置备份**：`api` 目录 tar —— dev 16:23 / OL 16:31；两侧 `.env` 各备份一份。

**下一次同类迁移的操作步骤**（已写进 tasks §7.2，此处为展开）：

1. 先确认属主库连接来自本机 `.env` 的 `AIDCP_PG_API_URL`，**不要**用记忆里的连接串。
2. 对本迁移 `aidcp:objects=` 头里声明的**每一张表**各导一份 CSV，文件名带迁移号，落 `/opt/aidcp/`。
3. 记下导出时刻与行数 —— 行数是事后核对合并结果的唯一基准
   （本次 46 + 27 − 24 重叠 = 49，与合并后 `all` 行数一致，这一步当场就能发现取值方向错了）。
4. 打一份服务目录 tar 与 `.env` 副本；**tar 一律排除 `node_modules`**（见记忆 `derived-repo-npm-ci-wipes-node-modules`）。
5. 以上四条完成前 MUST NOT 执行 `migrate up`。

## 3. 合并取值：逐格前后对照（7.5）

**基准说明**：合并那一刻的合并行 = revision 5。它**没有自己的审计行**（迁移直接写主表），
其内容从 `facebook_operation_global_policy_audit` 里 `all` 分支 5→6 那行的 `before_policy` 复原。
**当前值（revision 7）已不等于合并值** —— 2026-08-06 09:46 与 09:47 有两次面板编辑，见 §5。

| 格 | dev 旧行 (rev 4) | ol 旧行 (rev 3) | 合并行 (rev 5) | 对 OL 的实际变化 |
| --- | --- | --- | --- | --- |
| `rule.viewsPerLike` | 5 | 5 | 5 | — |
| `rule.joinEveryNRounds` | 2 | 2 | 2 | — |
| `consumption.viewsPerLike` | 5 | 7 | 5 | 7 → 5 |
| **`consumption.confirmedLikesPerJoin`** | **2** | **5** | **2** | **5 → 2（加群阈值）** |
| `consumption.confirmedJoinsPerComment` | 2 | 2 | 2 | — |
| `slowStart.totalDays` | 5 | 7 | 5 | 7 → 5 |
| `reels.slowStart.viewsPerLike` | 8 | 7 | 8 | 7 → 8 |
| `reels.persona.viewsPerLike` / `viewsPerFollow` | 4 / 10 | 4 / 10 | 4 / 10 | — |
| `reels.slowStart.viewsPerFollow` | 15 | 15 | 15 | — |
| `reels.rule.viewsPerFollow` / `reels.consumption.viewsPerFollow` | 15 / 15 | 15 / 15 | 15 / 15 | — |
| `slowStart.dailyCaps`（5 天曲线） | dev 那份 | ol 那份 | dev 那份 | 换成 dev 的 5 天曲线 |
| 群评论 `join_to_first_comment_hours` | **无行** | 72 | 72 | — |

### 3.1 单列的那一格：加群阈值 5 → 2

设计里就点名要单列（design §90-91）：这是"整套取 dev"的顺带结果，不是本变更的目的。
**一旦观察到加群过频，可只回滚这一格，不必回滚整次合并。**

**实测已生效**：`facebook_consumption_progress` 里 25 条 active 进度行的
`policy_snapshot.confirmedLikesPerJoin` **全部为 2**（含 OL 侧 21 条）。合并前 OL 侧该值为 5。

### 3.2 dev 侧缺席**没有**被当成"配置了默认值"

群评论策略 dev 侧本来就没有行。合并只从**存在的行**里挑，因此 72 小时窗口原样保留。
若把缺席当成"配了默认 24"参与竞争，这里会静默变成 24 —— 这是本次最易出事、且最不会报错的一格。

### 3.3 完成事实取值方向自检

合并规则是同一环境多侧都有记录时取**更早**的完成时刻。
实测 `select count(*) … where merged.completed_at > source.completed_at` = **0**，
即不存在"合并行比任一来源行更晚"的情况，方向没反。

> 这条自检必须在删旧行之前做完 —— 收尾 change 删掉旧行后，这个反证据就没有落点了。

## 4. 受影响对象：两份清单 + 交集（7.6）

> 两批 MUST 分开看：毕业那批看当日各动作总量是否顶到安全限额；消费那批只看加群次数。
> **交集那几个是唯一无法靠观察面归因的样本** —— 它们同时被两种变化命中。

### 清单一 · 立即毕业（合并前该侧无完成记录，合并后有）

**OL 视角 — 22 个环境**（这是本次放宽的主体；当日上限从冷启动曲线跳到安全限额）

| env_key | account_id | 昵称 |
| --- | --- | --- |
| k1es032k | 61591684722505 | Vi Ho |
| k1es0338 | 61591782547397 | Lo Du |
| k1es034j | 61591968120367 | Ve Te |
| k1es035u | 61591641343830 | Mi Xu ★ |
| k1es5kxl | 61591782937395 | Du Co ★ |
| k1etgm0e | 61591824155856 | Gi Vo ★ |
| k1f0s3q8 | 61576869627873 | Đỗ Khánh Mai |
| k1f44fsj | 61591934100810 | Hi He |
| k1f44g0k | 61591899123669 | Vi Le |
| k1f5m5tp | 61589889116544 | Vân Salli ★ |
| k1f5m5v1 | 61589865629337 | Facebook import 2 |
| k1f5m5vv | 61589672287247 | Facebook import 3 |
| k1f5m5wx | 61589550401526 | Facebook import 4 |
| k1f5m5yb | 61589980042592 | Krystel Yutiva |
| k1f5ushb | 61576666357732 | Trần Tuấn Trung ★ |
| k1f5wx73 | 61592522395910 | Daniel Golden ★ |
| k1f5wx7o | 61592340124255 | Facebook import 4 |
| k1f5wx8a | 61592581432786 | Facebook import 5 |
| k1f6n506 | 61572796576250 | Shaila Charu Bide ★ |
| k1f6n50l | 61573588991769 | Aandaleeb Ravee Arya |
| k1f6n516 | 61574017133470 | Vu Bide |
| k1f6n57t | 61575064838299 | Ravi Yadav Yellepeddi |

（★ = 同时在清单二，见交集）

**dev 视角 — 3 个环境**

| env_key | account_id | 昵称 |
| --- | --- | --- |
| k1enonmg | 61591803599213 | Nancy Terry ★ |
| k1f43l0k | 61592087636065 | Ce Di ★ |
| k1f44fit | 61591983719249 | Vo Tu |

**另有 24 个环境两侧都已完成**，合并取了更早时刻；其中 6 个的完成时刻实际前移
（OL 侧原记录晚于 dev 侧 —— 最大一例前移约 1 天 5 小时）。**它们的完成状态没有变化**，
不进"立即毕业"清单，因为两侧原本都已是已完成。

### 清单二 · 处于消费模式的账号（active 进度行）

**OL 侧 21 个 / dev 侧 4 个**（同一账号在两侧各有一份运行态进度，是设计如此：
消费进度是运行态，不在本次合并范围内，其 `execution_target` 仍只接受 `dev`/`ol`）。

OL 侧：k1f6n506 / k1f6n51m / k1f6n52w / k1f6n53y / k1f6n54n / k1f6n4yp / k1f5ushb /
k1etlag0 / k1f5m5tp / k1es035u / k1f4kcw4 / k1f4kcp0 / k1ei3dbi / k1es5kxl / k1enonmg /
k1etgm0e / k1f44fit / k1f43l0k / k1f5wx61 / k1f5wx73 / k1f5wx58

dev 侧：k1enonmg / k1f5wx61 / k1ei3dbi / k1f43l0k

### 交集 · 同时被两种变化命中（归因盲区）

**OL 侧 7 个**：k1es035u（Mi Xu）、k1es5kxl（Du Co）、k1etgm0e（Gi Vo）、
k1f5m5tp（Vân Salli）、k1f5ushb（Trần Tuấn Trung）、k1f5wx73（Daniel Golden）、
k1f6n506（Shaila Charu Bide）

**dev 侧 2 个**：k1enonmg（Nancy Terry）、k1f43l0k（Ce Di）

> 这 9 个对象当天的加群次数上升，**既可能来自毕业（限额放宽）、也可能来自阈值 5→2**，
> 观察面区分不了。若要归因，只能挑非交集样本比对。

## 5. 回滚窗口（7.5 第三项）

**机制**：本迁移只放宽约束 + 写入合并行，旧的 `dev` / `ol` 两行原样保留。
回滚 = 代码回滚 + 恢复分行键读取，旧两行仍在。**但它们从 2026-08-05 16:28 那一刻起就是冻结的** ——
合并之后的任何编辑只写进合并行，不会回流到旧行。

**窗口的当前状态（2026-08-06 实读）：已经开始丢东西了。**

- 合并后合并行被**运营**编辑过两次：revision 5 → 6（2026-08-06 09:46:49）、6 → 7（09:47:43），
  均为 `panel:admin`。
- 净变化：`reels.slowStart.viewsPerLike` **8 → 6**。其余标量格与 5 天曲线一字未动。
- **因此现在回滚会丢掉这一格的人工编辑**，回到 8。丢失面目前很小（一格），
  但它只会随时间单调变大。
- 另有 revision **7 → 12** 共五笔来自 8.3 / 8.4 验收（2026-08-06 14:2x–14:29），
  **净变化为零** —— 改动的两格（`reels.slowStart.viewsPerFollow` / `reels.persona.viewsPerFollow`）
  已改回 15 / 10，与 revision 7 时逐字相同。**它们推高了版本号但不构成回滚损失**；
  之所以写在这里，是因为只看版本号会误以为合并后被改了七次。

**硬截止时刻**：收尾 change `collapse-facebook-global-policy-target-column` 删除旧行之时。
那之后旧行不复存在，**只能向前修**。

**给要动这条线的人的判据**：回滚前先比一次合并行当前值与旧行冻结值的差；
差里若有运营真正在意的格，回滚就不是"恢复原状"，而是"用一份旧快照覆盖运营的编辑"。

## 6. 数据来源

全部为 2026-08-06 对 dev ECS 上两个属主库的只读查询：

- 接口属主库（`AIDCP_PG_API_URL`）：三张策略 / 完成事实表 + 两张审计表 + `client_environments`
- 自动化属主库（`AIDCP_PG_AUTOMATION_URL`）：`facebook_consumption_progress`

**两张表不在同一个库**（从接口库查 `facebook_consumption_progress` 报 relation does not exist）——
这正是拆库不变量在生效，交集只能在库外算，不能靠一条 SQL join。
