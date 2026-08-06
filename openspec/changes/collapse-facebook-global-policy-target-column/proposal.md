## Why

`unify-facebook-global-policy-across-targets` 把 Facebook 全局运营策略与冷启动完成事实收成了跨运行目标唯一一份，但它是 **expand 段**：做法是把 CHECK 放宽、写入一行作用域为 `all` 的合并行、代码切读该行，而 `dev` / `ol` 两行与 `execution_target` 这个分行列**原样留着**。收缩（删行删列）按本目录纪律必须是独立 change、独立部署、可单独回滚，因此当时刻意没做。

留着的代价现在是具体的，不是洁癖：

- **没人读的写入口仍然敞开。** 三张表里 `dev` / `ol` 两行谁都能写，代码一行都不读。往那儿写一笔会成功、不报错、不生效——写的人以为改了。这正是本条链路一开始要根治的那个毛病（「两边各自如实汇报自己那份配置算出来的结果，所以没有任何一处报错」），换了个位置又长出来一遍。
- **回滚故事在逐日腐烂。** 那两行自 2026-08-05 迁移那一刻起就是冻结的：真回滚到旧代码，读到的是合并当时的旧值，不含之后任何编辑。它看起来像一条退路，实际上每过一天越不像。留着它反而让人以为退路还在。
- **一个还留着的分行维度迟早会被重新用起来。** 迁移文件与 `unify-…` 的 §9.2 都已具名写下这条，并明确要求「MUST NOT 因为现在能跑而无限期挂起」。

## What Changes

- **BREAKING（contract 段）**：删除 `facebook_operation_global_policy`、`facebook_group_comment_policy`、`facebook_environment_slow_start_completion` 三张表的 `execution_target` 列与其上的 CHECK；先删掉这三张表里作用域不是 `all` 的历史行。执行后，**任何仍按运行目标过滤的构建都不能再启动或读写这三张表**。
- 两张策略表由「按 target 一行」改为**真正的单行**：删列后主键消失，须以显式的单行约束替代，使「同时存在两份全局策略」在库层面不可表示。
- 冷启动完成表主键由 `(env_key, execution_target)` 改为 `(env_key)`。
- 存储侧去掉作用域哨兵参数：切读时用来选行的那个常量在删列后不再有对应列，读写路径改为直取单行 / 按 `env_key` 直取。
- **审计表刻意不动**（`*_audit` 的 `execution_target` 列、CHECK 与唯一约束全部保留）：`unify-…` 已定「审计表保留历史行上的运行目标字段**仅供追溯**，不再作为分行键」。实测也不允许收紧——`facebook_operation_global_policy_audit` 现有 9 行只有 6 个不同 `new_revision`（1/2/3 各出现两次，dev 与 ol 各一），把唯一约束改成只按 `new_revision` 会**在现有数据上直接失败**；而新行作用域一律 `all`，既有的 `(execution_target, new_revision)` 唯一性对它们照旧成立。
- 回滚语义**改变且必须写明**：删列之后，回滚不再是「把代码换回去」，而是「从备份恢复」。本 change 的迁移前备份因此不是流程装饰，是唯一的退路。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `facebook-global-policy-single-scope`: 把「唯一一份」的落法由**作用域哨兵行**改为**库层面的单行**——去掉分行维度本身，使「存在第二份全局策略」不可表示；同时把回滚语义由「代码回滚，旧行仍在」改写为「从迁移前备份恢复」，并把审计表保留运行目标字段（仅供追溯、不参与分行、不得收紧唯一约束）写成显式要求。

## Impact

- **归档顺序是硬约束**：`facebook-global-policy-single-scope` 由 `unify-facebook-global-policy-across-targets` 引入，**本 change MUST 在它归档之后归档**，否则 MODIFIED 匹配不到标题会 `Aborted. No files were changed.`
- **上线顺序是硬前置**：本 change 的迁移只有在**全部**运行中的接口进程都已切读合并行之后才可执行。2026-08-06 实测 dev 与 OL 的 `aidcp-api` 均已跑合并后的代码（作用域常量在、5 处引用），故前置已成立；执行前 MUST 重新实测一次，不得引用本段。
- **aidcp-cloud / aidcp-api（属主域 api）**：一条 contract 迁移；`facebook-operation-policy-store` 与 `facebook-group-comment-policy-store` 的读写路径、`client-user-store` 的完成事实读写；作用域常量文件在切换完成后失去用途。
- **aidcp-automation**：经同步读镜像消费该策略，载荷本就是「一份」，预期零改动，但 MUST 验证不因属主侧去掉分行列而漂移。
- **aidcp-console**：无预期改动；面板对 `executionTarget` 字段的 `['dev','ol']` 硬闸仍靠视图回传「当前连接的目标」满足，本 change MUST NOT 改那格的语义。
- **数据**：迁移前实测已确认三条前置全部干净——`all` 覆盖了 dev/ol 的全部 `env_key`（未覆盖 0 个）、`all` 行内 `env_key` 无重复（0 个）、且每个环境的 `all` 完成时刻都不晚于任一旧行（0 个反例）。执行前 MUST 重跑这三条，任一不为 0 即停手。
