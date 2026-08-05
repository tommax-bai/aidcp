## 1. 前置坐实（动手改代码之前必须先有结论）

- [ ] 1.1 坐实"另一目标多久能看到对方的写"：读接口进程的同步读快照发布周期与 `refreshFromAuthority()` 的实际触发点，给出一个可写进规格的时限上限（带 `文件:行`）
- [ ] 1.2 依 1.1 结论二选一并记录理由：沿用现有周期性重读（则把时限写进规格并补验收），或把接口进程补进 `facebook_operation_policy` 镜像键的消费者名册走既有失效通道
- [ ] 1.3 清点全部按 `execution_target` 过滤这三张表的读写点（含派生 `aidcp-api` 仓自己的组装根），列成清单；**MUST 把动态引用与 SQL 字符串一起 grep**，只匹配符号名会漏
- [ ] 1.4 确认自动化侧经同步读镜像消费的载荷形状不含目标维度（预期零改动，但要验证不因属主侧去掉过滤而漂移）

## 2. aidcp-cloud — 数据模型与迁移

- [ ] 2.1 写迁移：`facebook_operation_global_policy` 删 `execution_target`，改单行约束（固定主键 + CHECK），数据按逐项基准落一行
- [ ] 2.2 写迁移：`facebook_operation_global_policy_audit` 保留 `execution_target` 作历史追溯，放宽 CHECK 允许"全目标"取值，唯一约束 `(execution_target, new_revision)` 保持不变；历史行一行不改
- [ ] 2.3 写迁移：`facebook_group_comment_policy` 删 `execution_target`，收成单行；取值按"缺席不参与"规则落 ol 现值（72 小时）
- [ ] 2.4 写迁移：`facebook_environment_slow_start_completion` 删 `execution_target`，主键改为 `env_key`，同环境多行按 `min(completed_at)` 合并
- [ ] 2.5 新 revision 序列起点取两侧历史最大值 +1，写进迁移
- [ ] 2.6 迁移脚本自带前置备份步骤（三张表全量导出、含时刻），并在缺备份时拒绝执行

## 3. aidcp-cloud — 存储与路由

- [ ] 3.1 `FacebookOperationPolicyStore`：全局策略读写去掉目标过滤与 `executionTarget` 依赖；审计写入把目标降级为追溯字段
- [ ] 3.2 `FacebookGroupCommentPolicyStore`：同上；保留既有 legacy env 回落语义不变
- [ ] 3.3 冷启动完成事实的读写（含 `refreshEnvironmentSlowStartMirror` 的子查询）去掉目标条件
- [ ] 3.4 客户鉴权侧冷启动进度写：新增 / 删除完成事实不再按目标
- [ ] 3.5 面板全局策略读写路由不再接受也不再推导目标选择器
- [ ] 3.6 依 1.2 的结论落跨目标可见性通道（补消费者名册 或 明确沿用并记录时限）

## 4. aidcp-cloud — 测试

- [ ] 4.1 单测：同一份配置从两个不同 `AIDCP_DEPLOY_ENV` 的进程读出逐格相同（含 revision）
- [ ] 4.2 单测：合并取值规则 —— 一侧无行时取另一侧人工值，MUST NOT 取回落默认
- [ ] 4.3 单测：完成事实合并取更早时刻；取更晚的实现必须让该用例红
- [ ] 4.4 单测：基于过期 revision 的并发写被具名拒绝并返回最新投影，MUST NOT 覆盖
- [ ] 4.5 单测：冷启动完成写入后，另一目标视角读到同样为已完成
- [ ] 4.6 迁移用例：喂"dev 有行 / ol 无行""两侧都有且时刻不同""两侧 revision 不同"三种输入，断言合并结果
- [ ] 4.7 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`

## 5. aidcp-api — 派生仓同步与组装根

- [ ] 5.1 从控制仓跑 `scripts/sync-split-repos --repo aidcp-api`（先 dry-run 对账再 `--apply`）
- [ ] 5.2 派生仓手写组装根按需调整（该文件不参与自动同步，必须手改）
- [ ] 5.3 派生仓 `npm run typecheck` 通过

## 6. aidcp-console — 明示"对全部运行目标同时生效"

- [ ] 6.1 Facebook 全局策略页顶部加明示标注（含入群后评论延迟那一块）
- [ ] 6.2 写入确认环节携带同样告知
- [ ] 6.3 组件测试断言标注与确认告知都存在
- [ ] 6.4 `npm run typecheck` 与既有测试通过

## 7. 部署与迁移执行

- [ ] 7.1 dev 部署代码，跑迁移前先在 dev 上做一次演练（备份 → 迁移 → 验收 → 回滚 → 再迁移）
- [ ] 7.2 迁移窗口选低峰；执行前导出三张表全量备份并记录时刻与文件位置
- [ ] 7.3 在一个事务里执行 DDL + 数据合并
- [ ] 7.4 两个接口进程重启，确保缓存重新装载
- [ ] 7.5 迁移记录里逐个列出：受影响的"立即毕业"环境键、消费模式加群阈值那一格的前后值、回滚窗口截止时刻

## 8. 验收（缺一不可）

- [ ] 8.1 两边后台读到逐格相同的一份配置与相同 revision
- [ ] 8.2 原处于最后一天的环境显示已完成，且其当日上限等于安全限额而非冷启动曲线
- [ ] 8.3 在一侧改一格，另一侧在 1.1 约定的时限内读到新值，无需重启
- [ ] 8.4 两侧并发写触发 409 而非互相覆盖
- [ ] 8.5 入群后首次评论等待仍为 72 小时（未被 dev 的缺席回落成 24）
- [ ] 8.6 迁移当天盯"立即毕业"那批账号的实际用量，记录观察结论
- [ ] 8.7 真机 / 长周期观察项登记进 `docs/real-machine-acceptance-backlog.md`
