# 迁移记录 — 0114_facebook_global_policy_collapse_target

> change `collapse-facebook-global-policy-target-column`（收缩段）。
> 本文件是任务 7.4 的产出。**回滚方式在 §5，它与 `0110` 那次完全不同，MUST NOT 照抄那次的说明。**

## 1. 执行时刻与执行者

| 项 | 值 |
| --- | --- |
| 迁移 | `0114_facebook_global_policy_collapse_target`（`kind=contract`，属主 api） |
| 库 | `aidcp_api` @ `121.89.85.150:5432` —— **dev 与 OL 共用这一个实例**（见 §6） |
| 应用时刻 | 2026-08-06 16:40 CST，耗时 35ms |
| 命令 | 在 `/opt/aidcp/api` 执行 `npm run migrate up -- --owner=api --allow-contract --by=claude-code:collapse-facebook-global-policy-target-column` |
| 账本 `applied_by` | `claude-code:collapse-facebook-global-policy-target-column` |
| 代码落点 | `aidcp-cloud@2d34e06`（事实源）→ `aidcp-api@90dfb6e` / `aidcp-automation@ccc41b0` / `aidcp-content@7d312ba` / `aidcp-transport@2b54cc2`（tag `v0.1.1`） |
| 发布分支（OL） | `release/20260806-fb-policy-collapse`（api / automation / content 三仓同名） |

## 2. 数据前置的当次实测值

四条断言全部写在迁移本体的 `DO $$ … $$` 块里，整体排在任何 `DELETE` 之前，任一不成立即整条失败回滚。
执行时的实测值（**不是引用文档快照**）：

| 前置 | 当次值 | 要求 |
| --- | --- | --- |
| ① 合并行未覆盖的 `env_key` 数 | 0 | 必须为 0，否则删旧行会丢掉毕业事实 |
| ② 合并行内 `env_key` 重复数 | 0 | 必须为 0，否则主键收敛到 `(env_key)` 会失败 |
| ③ 合并完成时刻晚于任一旧行的环境数 | 0 | 必须为 0，这是对 `0110`「取更早」的事后复核 |
| ④ 两张策略表「有旧行却无合并行」 | 无 | design 未列，本次补上；不成立会静默丢掉运营写下的值 |

同一组值在动手前（16:26）也单独查过一次，结果相同。

## 3. 删除的行数（按表）

| 表 | 收缩前 | 删除 | 收缩后 |
| --- | --- | --- | --- |
| `facebook_operation_global_policy` | 3（`all`/`dev`/`ol` 各 1） | 2 | 1 |
| `facebook_group_comment_policy` | 2（`all`/`ol`；dev 侧本就无行） | 1 | 1 |
| `facebook_environment_slow_start_completion` | 122（`all` 49 / `dev` 46 / `ol` 27） | 73 | 49 |
| `facebook_operation_global_policy_audit` | 14 | **0（不动）** | 14 |
| `facebook_group_comment_policy_audit` | 1 | **0（不动）** | 1 |

结构变化：两张策略表加 `singleton` 列、主键换成 `PRIMARY KEY (singleton)` + `CHECK (singleton)`；
完成事实表主键收敛到 `(env_key)`；三处 `execution_target` 列连同其列级 CHECK 一并消失；
索引 `idx_facebook_environment_slow_start_completion_target` 随列消失且**不补建替代**。

## 4. 迁移前备份（唯一退路）

导出于库所在机 `121.89.85.150`，时刻 **2026-08-06 16:31:51**：

| 内容 | 文件 |
| --- | --- |
| 数据（五张表，142 条 `INSERT`） | `/opt/aidcp/backup/facebook-global-policy-precollapse.20260806-163151.sql` |
| 结构（五张表） | `/opt/aidcp/backup/facebook-global-policy-precollapse-schema.20260806-163151.sql` |

服务目录与 `.env` 另有备份：dev `/opt/aidcp/*.bak.20260806-163404.tar.gz`、
OL `/opt/aidcp/*.bak.20260806-165729.tar.gz`（`api` / `automation` / `content` 各一）。

## 5. 回滚方式 = 从备份恢复（**不是换代码**）

`0110` 那次的退路是「代码回滚，旧行仍在」。**本次那条退路已经不存在**：
分行列被删之后，任何仍按运行目标过滤的构建都读不到这三张表，且**不会报错退出**——
它只是读不到策略。所以：

1. 回滚 MUST 从 §4 的两份导出恢复（先恢复结构、再恢复数据），
2. 然后才谈把代码换回收缩前的版本，
3. 且 **dev 与 OL 必须同批**（§6）。

## 6. 必须写下来的事实：dev 与 OL 共用这一个接口库

OL 的 `AIDCP_PG_API_URL` 指向 `121.89.85.150:5432/aidcp_api`，即 dev 本机那个库。因此：

- 这条 contract 迁移对**两个环境是同一个动作**，MUST NOT 按「先 dev 观察几天再 OL」排期。
- 实测代价：16:40 迁移落地后，OL 上仍跑旧构建的 `aidcp-api` 立刻开始报
  `column c.execution_target does not exist`（16:41–16:52 共 124 条），
  `client_environment_slow_start` 镜像停在 `version=1768` 不再前进。
  这是**响亮失败**（日志逐条说明缺哪一列、副本落后多少秒），不是静默错值。
- 16:59 OL 部署完成后当场恢复：`execution_target` 报错归零，镜像重载到 `version=1789` 并继续推进。
- 新旧代码**没有共存窗口**：迁移前跑新代码那条不带过滤的子查询会直接报
  `more than one row returned by a subquery`（同一 `env_key` 在 `all` 与 `dev`/`ol` 上各有一行）；
  迁移后跑旧代码则缺列。所以部署次序只能是：**备份 → 送代码（不重启）→ 跑迁移 → 立刻重启**。

## 7. 上线后核对

- `migrate verify --owner=api`：**缺失对象 0**，声明 557 个对象（收缩前 554；+7 新声明 −4 退役声明）。
- 两侧接口进程各重启一次后仍能起来，schema 契约门（`enforce`）判通过：
  api 认 `0114`，automation / content 按各自属主版本集合收窄后认 `0113`。
- 两侧后台读到的策略与收缩前逐格相同（含 `revision`）；
  自动化侧镜像载荷 md5 与行数与收缩前逐格相同（`01591ba4cf97afcf4948ea4641c5231c` / 149）。
- 真库上试插第二行全局策略、以及给同一 `env_key` 插第二条完成事实，都被主键拒绝。
