## 1. 前置坐实（动手改代码之前必须先有结论）

- [x] 1.1 坐实"另一目标多久能看到对方的写"
  <!-- 结论比设计里的假设更差：**接口进程根本没有周期性重读这张表**。
       `facebookOperationPolicy.refreshFromAuthority()` 在派生 api 仓只有一个调用点
       （aidcp-api `src/server.ts:1944`），它在**属主快照闭包**里——只有当自动化进程
       过来拉 `facebook_operation_policy` 这条流时才跑。节奏由**对方**决定，不是本进程的定时器。
       单体侧的 `scheduleSyncReadRefresh('api-owner', 30_000, …)`（aidcp-cloud `src/server.ts:1527`）
       是单体自己的推送循环，派生 api 走的是 `snapshotFor` 拉取式（aidcp-api `src/server.ts:3054`），
       两者不是同一条路，30s 这个数**不能**当作派生部署下的时限来引用。 -->
- [x] 1.2 依 1.1 结论二选一并记录理由 → **选"补消费者名册"，不沿用副作用**
  <!-- 接口进程今天持有 MirrorVersionStore 但只用来**写** bump（aidcp-api `src/server.ts:1241`），
       全进程没有任何"按镜像版本重读自己配置"的消费侧通道（grep `refreshFromAuthority` 的调用点可证）。
       今天不需要是因为每张表只有一个进程在写、它自己的缓存永远是对的；合并后有两个 api 进程，
       这条通道从"不需要"变成"必须有"。
       沿用副作用的失效方式：自动化改拉取节奏、或那条流改成"变更才拉"，另一目标就**永远**读旧值且不报错。
       任务落到 3.6。 -->
- [x] 1.3 清点全部按 `execution_target` 过滤这三张表的读写点
  <!-- aidcp-cloud 侧：
       - `src/config/facebook-operation-policy-store.ts`：979/988（全局行读）、1243/1252/1295/1296（写+RETURNING）、
         1327（审计插入）、1789/1791/1798（完成事实写删）、2501 与 2688（完成事实子查询）、
         2670/2676（完成事实插入）、2599（行→视图）、332/413/433/446（行类型与 schema 要求集）
       - `src/config/facebook-group-comment-policy-store.ts`：174、255、274、289、302（读/写/审计）、
         46/53/69-70（schema 要求集与索引名）
       - `src/client-auth/client-user-store.ts`：1260（镜像重建子查询）、1502/1517/1520/1558/1575/1578
         （进度写的完成事实增删）、2129（全局策略读）
       - `src/config/api-sync-read-source.ts`：206（完成事实子查询）
       - `src/panel/panel-server.ts`：1144/1152/1435/1441（只是错误串，无目标过滤，不改）
       - `src/orchestrator/facebook-consumption-mode-coordinator.ts`：231（错误串，不改）
       - migrations：0100 / 0103 / 0104 / 0107
       派生 `aidcp-api` 仓的手写组装根另计（构造这两个存储时传 `executionTarget`）。 -->
- [x] 1.4 确认自动化侧经同步读镜像消费的载荷形状不含目标维度
  <!-- 载荷是 `slowStart: store.slowStartRuntimePolicy()`（`src/config/api-sync-read-source.ts:103`），
       只有 totalDays + dailyCaps，无目标维度；自动化侧取用口
       `AutomationSyncReadMirrors.facebookSlowStartPolicy()` 同样不带目标。预期零改动，
       但 4.x 要有一条断言钉住"属主去掉过滤后载荷逐字不变"。 -->

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
- [ ] 7.6 一次迁移全量切换（不分阶段）；迁移记录 MUST 把"立即毕业"与"处于消费模式"两批对象分开成两份清单，交集单独标出——它们是当天唯一无法靠观察面归因的样本

## 8. 验收（缺一不可）

- [ ] 8.1 两边后台读到逐格相同的一份配置与相同 revision
- [ ] 8.2 原处于最后一天的环境显示已完成，且其当日上限等于安全限额而非冷启动曲线
- [ ] 8.3 在一侧改一格，另一侧在 1.1 约定的时限内读到新值，无需重启
- [ ] 8.4 两侧并发写触发 409 而非互相覆盖
- [ ] 8.5 入群后首次评论等待仍为 72 小时（未被 dev 的缺席回落成 24）
- [ ] 8.6 迁移当天分开观察并各自记录结论：毕业那批看当日各动作总量是否顶到安全限额；消费模式那批只看加群次数是否随阈值 5→2 成比例上升
- [ ] 8.7 真机 / 长周期观察项登记进 `docs/real-machine-acceptance-backlog.md`
