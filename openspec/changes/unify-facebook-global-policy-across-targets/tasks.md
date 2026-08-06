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

## 2. aidcp-cloud — 数据模型与迁移（**只做 expand 段**，删列见第 9 组）

- [x] 2.1 写 expand 迁移 `0110_facebook_global_policy_single_scope.sql`：五处 `CHECK` 放宽到接受哨兵值 `'all'`（三张主表 + 两张审计表）
  <!-- 原计划是「删 execution_target 改单行约束」，与 migrations/README.md「收缩 MUST 独立 change、
       独立部署、MUST NOT 与 expand 同批交付」冲突。改为两段：本段 expand 切读，删列另立 change。
       见 design D1 修订。 -->
- [x] 2.2 审计表放宽后新行写 `'all'`，唯一约束 `(execution_target, new_revision)` 原样保留；历史行一行不改
- [x] 2.3 主策略与群评论策略按"两行都在取 dev、只有一行取那一行"写入合并行；**只从存在的行里挑**，故 dev 侧的缺席不会把 72 小时改回默认 24
- [x] 2.4 完成事实按 `env_key` 分组取 `min(completed_at)` 写入合并行
- [x] 2.5 新 revision 起点取全表最大值 +1，写进迁移
- [ ] 2.6 迁移前备份的操作步骤写进部署任务（第 7 组），并在迁移记录里留导出时刻与文件位置
- [ ] 2.7 `npm run migrate status` / `verify` 在 dev 上确认本迁移声明的对象与实际一致

## 3. aidcp-cloud — 存储与路由

- [x] 3.1 `FacebookOperationPolicyStore`：全局策略读写改按作用域键选行；审计写入把目标降级为追溯字段
  <!-- aidcp-cloud 7fd4137（分支 unify-facebook-global-policy-across-targets）。
       新增 src/config/facebook-global-policy-scope.ts 作唯一定义；7 处行选择器切读。
       视图上的 executionTarget 改为「你正在通过哪个目标的接口读」——MUST NOT 回传作用域键，
       管理后台对该字段有 ['dev','ol'] 硬闸，回它不认识的值不是报错、是整页打不开。 -->
- [x] 3.2 `FacebookGroupCommentPolicyStore`：同上；legacy env 回落语义不变
  <!-- aidcp-cloud 7fd4137。**入参 executionTarget 直接删掉**而不是留着不用：留着会让下一个人
       以为还能按目标分，唯一拦着他的只是约定；删掉则仍在传它的组装根当场编译失败——本次
       正是靠它把 3 个构造点全点出来的。派生 api 仓的手写组装根同样要改，见 5.2。 -->
- [x] 3.3 冷启动完成事实的读写（含镜像重建子查询）切读作用域键
  <!-- aidcp-cloud 7fd4137。client-user-store 6 处 + policy-store 6 处 + api-sync-read-source 1 处。
       **client_env_revocation_holds 那 3 处保持按目标隔离**——它是运行态，不在本次合并清单里。 -->
- [x] 3.4 客户鉴权侧冷启动进度写：新增 / 删除完成事实不再按目标
  <!-- aidcp-cloud 7fd4137 -->
- [x] 3.5 面板全局策略读写路由不再接受也不再推导目标选择器
  <!-- aidcp-cloud 7fd4137：路由本就没有目标入参，目标推导全在存储层，已随 3.1 收掉。 -->
- [x] 3.6 依 1.2 的结论落跨目标可见性通道 → **补消费者名册**
  <!-- aidcp-api 2219134（该组装根不参与自动同步，必须手改；单体侧已有同名刷新器且已挂这几个存储，无需改动）。
       窄装：只挂 facebook_operation_policy / content_schedule / client_environment_slow_start 三个键的重载器，
       **不**注册成新鲜度事实源、**不**接停手闸、**不**发陈旧告警——那些是自动化进程侧的既有职责，
       在接口进程一并打开等于顺手改了它的停手语义。
       三个键按「谁被推了就重载谁」登记：**群评论策略的写只推 content_schedule**，只挂
       facebook_operation_policy 一个键会漏掉它（写入侧的 bumpInTx 是唯一判据，别按名字猜）。
       刷新器挂到组装根上只为关停时能停掉；它不是取值口。启动失败不致命但打 error——
       不启动 = 退回合并前的可见性，那是降级不是正确。typecheck 0；本仓 567 通过 0 失败。 -->

## 4. aidcp-cloud — 测试

- [x] 4.1 单测：同一份配置从两个不同 `AIDCP_DEPLOY_ENV` 的进程读出逐格相同（含 revision） <!-- aidcp-cloud 0da148e / aidcp-api 9651873。承重点是**同一份数据、两个部署目标的 store**（夹具新增 storeOnSameData）：各起一套夹具各播一份同样种子的写法证不出东西，实现仍按目标分行也会全绿。视图的 executionTarget 是唯一允许不同的一格，用例把它的语义钉住——它表示「通过哪个目标的接口读」，不是「配置属于谁」（实现刻意不回作用域键：后台对该字段有 dev/ol 硬闸，回它不认识的值是整页打不开）。变异：把选行键改回部署目标 → 本例连同既有 5 例一起红 -->
- [x] 4.2 单测：合并取值规则 —— 一侧无行时取另一侧人工值，MUST NOT 取回落默认 <!-- aidcp-cloud 0da148e test/facebook-global-policy-merge-migration.test.ts；断言合并只从**存在的行**里挑（源为表本身 + 排除合并行 + 无 COALESCE/DEFAULT）。变异：给缺席的 dev 侧合成一行默认 24 小时再同权竞争 → **只有**群评论那条红，正是会把运营手写的 72 悄悄改回 24 的那条路 -->
- [x] 4.3 单测：完成事实合并取更早时刻；取更晚的实现必须让该用例红 <!-- aidcp-cloud 0da148e；断言 min(completed_at) + GROUP BY env_key，且显式 doesNotMatch max(...)。变异：改成 max → 该例精确变红、其余不动 -->
- [x] 4.4 单测：基于过期 revision 的并发写被具名拒绝并返回最新投影，MUST NOT 覆盖 <!-- 既有用例本已断「具名拒绝 revision_conflict + 回最新投影 + 不写审计」；本批补上缺的另一半：**那一行确实没被动过**（revision/取值/updated_by 四格）。合并后这条更要紧——过期写落地覆盖的是两个目标共用的那一行，而审计表照样只有一条，正是静默覆盖的形状。aidcp-cloud 0da148e -->
- [x] 4.5 单测：冷启动完成写入后，另一目标视角读到同样为已完成 <!-- aidcp-cloud 0da148e；同一份数据上 dev 侧写毕业、ol 侧读，写前断未完成、写后断已完成。这正是事故形态：dev 标了毕业而 ol 仍显示未完成、配额继续被冷启动曲线夹住，两边各自都在如实汇报自己那份事实 ⇒ 零报错 -->
- [x] 4.6 迁移用例：喂"dev 有行 / ol 无行""两侧都有且时刻不同""两侧 revision 不同"三种输入，断言合并结果 <!-- aidcp-cloud 0da148e；六条按仓内既有迁移测试写法（读 SQL 断形状），文件头写明它能证什么、不能证什么：不执行 SQL 故证不了「跑一遍得到某结果」，它守的是**取值方向**——而这条迁移里所有会造成损失的错法恰好都是方向反了，方向反了在真库上同样不报错、只是数值不同。含 dev 优先、revision 取全表 max+1（合并后必须是一条序列，否则两侧各自 CAS 拦不住）、ON CONFLICT DO NOTHING 幂等、以及「本迁移只放宽不删除」（收缩须独立 change，删了回滚就没有落点）。三次变异各自只红对应用例 -->
- [x] 4.7 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`
  <!-- 2026-08-05 acceptance 189/0、全量 4204 中 4193 通过 0 失败、typecheck 0。
       期间修掉两处机械闸：KNOWN_MAX_SCHEMA_VERSION 抬到 0110；迁移头补表声明
       （约束名反推不出表 → 归属推断落「残留」→ 该迁移被计入全部属主库，拆库后会被派去自动化库跑）。 -->

## 5. aidcp-api — 派生仓同步与组装根

- [x] 5.1 从控制仓跑 `scripts/sync-split-repos --repo aidcp-api`（先 dry-run 对账再 `--apply`）
  <!-- 源 aidcp-cloud@e2d0e6d，写入 5 文件。六仓全量对账：api/automation/content 三仓 0 差异，
       故本 change 只需部署 api。**迁移文件不派生**，须手工 cp 进该仓 migrations/。 -->
  <!-- **必须等 cloud 分支合回 master 之后再做**：同步脚本从 canonical aidcp-cloud 的 master 取源、
       写 canonical aidcp-api，现在跑只会把不含本 change 的旧源同步过去。 -->
- [x] 5.2 派生仓手写组装根按需调整
  <!-- aidcp-api 6f3e02a。删掉群评论策略存储的 executionTarget 实参；
       该仓 test/ 不派生，属主那边改过的两个测试文件在这里是独立副本，同样三处照搬。 -->
  <!-- 已知必改一处、且**顺序不能反**：cloud 侧删掉了群评论策略存储的 executionTarget 入参，
       该仓组装根现在仍在传它。同步（5.1）之前删会因为入参仍必填而编译失败，
       同步之后不删会因为多余属性编译失败——只有「先同步、后删参」这一个顺序是通的。
       3.6 的刷新器接线已先行落在 2219134，与本条无依赖。 -->
- [x] 5.3 派生仓 `npm run typecheck` 通过
  <!-- aidcp-api 6f3e02a：typecheck 0、567 通过 0 失败。 -->

## 6. aidcp-console — 明示"对全部运行目标同时生效"

- [x] 6.1 Facebook 全局策略页顶部加明示标注（含入群后评论延迟那一块）
  <!-- aidcp-console 2ea50b7。卡片体顶部 + 编辑弹窗顶部各一条；子卡片独立一条（运营可能只看到它）。
       文案集中在新文件 facebookGlobalPolicyScopeNotice.ts，两处引用同一份、不各自漂移。 -->
- [x] 6.2 写入确认环节携带同样告知
  <!-- aidcp-console 2ea50b7。两处保存各包一层确认，正文点明「没有只回滚一侧的办法」。 -->
- [x] 6.3 组件测试断言标注与确认告知都存在
  <!-- aidcp-console 2ea50b7。做过变异归属验证：删卡片标注 → 两条标注用例红；
       把子卡片确认文案换成普通文案 → 只有子卡片那条红，全局那条仍绿（不是端到端顺带过的）。 -->
- [x] 6.4 `npm run typecheck` 与既有测试通过
  <!-- aidcp-console 2ea50b7。typecheck 0；vitest 全量 44 文件 348 通过 1 跳过 0 失败。
       多一道确认后 EnvironmentsPage 3 条既有用例补了确认点击，并因并行负载各加 20s 显式超时。 -->
  <!-- 该 agent 报出的跨组风险（面板卡片对 executionTarget 有 ['dev','ol'] 硬闸、类型必填）
       已在 3.1 就地解决：属主继续下发该字段，但语义改为「你连的是哪台后台」；
       console 侧文案也已就地点破这一点，两边口径一致，不需要再开 console 后续 change。 -->

## 7. 部署与迁移执行

- [x] 7.1 dev 部署 + 迁移
  <!-- 2026-08-05 dev：api rsync + migrate up + 重启，healthcheck 通过；console 也已部署。
       **迁移第一次失败并整体回滚**：完成事实表的约束自动名 65 字节、超过 PG 63 字节标识符上限，
       实际落库的是被截断的名字；按拼写全名 DROP IF EXISTS 不命中、**且不报错**，老约束原样留着，
       写哨兵值时被它拒绝。修法：两个名字都 drop + 新约束用短名（aidcp-cloud 7246bcf / aidcp-api 749dbfe）。 -->
- [x] 7.2 迁移前备份
  <!-- dev 上 /opt/aidcp/backup-0110-{global-policy,group-comment,completion}.csv（2026-08-05 16:23，
       2 / 1 / 73 行）；api 目录 tar 备份 dev 16:23、ol 16:31；两侧 .env 各备份一份。
       dev 与 ol 共用同一个 api 库（已实测：从 ol 连过去看到同一批行），故迁移只需跑一次。 -->
- [x] 7.3 在一个事务里执行 DDL + 数据合并
  <!-- 执行器逐条单事务；第一次失败时整条回滚、账本未动，这一点被实测确认。 -->
- [x] 7.4 两个接口进程重启
  <!-- dev 16:29 起来干净。**ol 起了一次事故**：OL 上 npm install 拉不到 git 依赖（无 GitHub 访问），
       其 node_modules 的 aidcp-transport 仍是旧 pin，缺 model-probe-http，新代码启动即崩；
       回滚到备份又被 schema 闸拦住（账本已 0110、旧构建只认 0109）——**回滚路径被自己堵死**，
       OL 接口面短时中断。向前修：把 dev 上已装好的 aidcp-transport / aidcp-kernel 打包搬到 OL，
       再上新代码，16:35 恢复。**教训见 backlog：OL 无法装 git 依赖，任何抬 pin 的部署都必须
       先解决包分发，否则 OL 的回滚窗口会在迁移应用后立即消失。** -->
- [ ] 7.5 迁移记录里逐个列出：受影响的"立即毕业"环境键、消费模式加群阈值那一格的前后值、回滚窗口截止时刻
- [ ] 7.6 一次迁移全量切换（不分阶段）；迁移记录 MUST 把"立即毕业"与"处于消费模式"两批对象分开成两份清单，交集单独标出——它们是当天唯一无法靠观察面归因的样本
- [x] 7.7 **撤回 OL 接口服务为本 change 的迁移临时追加的 schema 放行位。** 本 change 上线（构建认识
  `0110_facebook_global_policy_single_scope`）后 MUST 从 OL 的 `/opt/aidcp/api/.env` 删掉那行
  `AIDCP_ALLOW_SCHEMA_AHEAD=…`，并重启接口服务确认它靠自己就能过契约门。
  **本条未完成前 MUST NOT 归档本 change** —— 放行位留着等于这台机器的契约门对这一段版本永久失效。
  <!-- 缘由：2026-08-05 面板上线时撞出，OL 接口服务从 0110 应用那一刻起就「一重启即死」且零告警
       （DEV/OL 共库 + 本 change 当时尚未完成 ⇒ 所有不含 0110 的构建当场失去启动能力，回滚同样救不了）。
       完整现场见 `openspec/changes/restore-panel-capability-wiring/tasks.md` 9.4b。
       该行在 .env 里已就地注明「本 change 上线后 MUST 撤回」，但那是机器上的注释、不是任务；
       此前唯一的登记点是一条**已勾选**任务的注释，随该 change 归档就会沉进 archive，
       所以在这里补一条它自己的未勾任务——本 change 上线才是撤回时机。 -->
  <!-- 2026-08-06 随 release/20260806-ol-derived-services 完成：api 与 automation 的
       AIDCP_ALLOW_SCHEMA_AHEAD 均已移除；新构建分别认识 0110 / 0111，启动日志由自身通过
       enforce 契约门，放行区间日志计数=0。旧 .env 保存在发布前完整备份与单独的
       *.env.before-schema-allow-removal 中。 -->

## 8. 验收（缺一不可）

- [ ] 8.1 两边后台读到逐格相同的一份配置与相同 revision
  <!-- 2026-08-06 **未完成，不要当作已验**。已坐实的三件：两侧接口进程都跑着合并后的代码（OL 上 scope 常量在、5 个文件引用它，与 dev 一致）；库里三张表的合并行都在；存储按作用域哨兵选行，若仍按部署目标选行会以 policy_missing 报错。**缺的是最后一步**：`/api/facebook/operation-global-policy` 需要面板 token，本次拿不到，所以「两边后台各读一次、逐格比对 + revision 相同」这一步没做。结构证据 ≠ 端到端读数，两者不得互相顶替。 -->
- [x] 8.2 原处于最后一天的环境显示已完成，且其当日上限等于安全限额而非冷启动曲线 <!-- 2026-08-06 用户确认「看起来 ok 了」。**此勾来自用户观察、不是本次实测**——我没有独立复核当日上限是否等于安全限额。 -->
- [ ] 8.3 在一侧改一格，另一侧在 1.1 约定的时限内读到新值，无需重启
- [ ] 8.4 两侧并发写触发 409 而非互相覆盖
- [x] 8.5 入群后首次评论等待仍为 72 小时（未被 dev 的缺席回落成 24） <!-- 2026-08-06 实测：`facebook_group_comment_policy` 的合并行 join_to_first_comment_hours=72（另有一条 ol 旧行同为 72、dev 侧本就无行）。合并基准里最易出事的一格保住了——dev 缺席若被当成「配置了默认值」参与竞争，这里会静默变成 24。 -->
- [x] 8.6 迁移当天分开观察并各自记录结论：毕业那批看当日各动作总量是否顶到安全限额；消费模式那批只看加群次数是否随阈值 5→2 成比例上升 **【按用户裁定划掉 2026-08-06：本条不做，用户明确要求先划掉。此勾表示「按裁定清账」，MUST NOT 读成「已观察」】**
- [ ] 8.7 真机 / 长周期观察项登记进 `docs/real-machine-acceptance-backlog.md`
- [x] 8.8 放行位撤回后（7.7），OL 接口服务**重启一次**并确认它不靠放行位也能过契约门：
      启动日志里 MUST NOT 再出现放行区间那条记录，服务 active、`NRestarts=0`、接口口答得上。
      **MUST NOT 用「服务现在活着」代替这次重启** —— 契约门只在启动时跑，不重启就等于没验。
      <!-- 2026-08-06 10:28 CST 真重启：api schema gate 以账本最高 0110 自身通过，active、
           NRestarts=0，8090/8091 在，local/public health 均 {"ok":true}，schema allow 日志 0。 -->

## 9. 收尾：把中间态收掉（**独立 change，本 change 不做，但必须立项**）

- [x] 9.1 切读稳定后立一个独立的 contract change：删掉 `dev` / `ol` 两行与三张主表的 `execution_target` 列，策略表改单行约束、完成表主键改 `env_key` <!-- 2026-08-06 已立项：`collapse-facebook-global-policy-target-column`（proposal / design / specs / tasks 齐备，strict 通过）。设计上的两点与本条原文有出入，均为实测所致：① 策略表删列后主键会一起消失，故改用取值集合只有一个元素的单例主键，而不是「单行约束」这个说法；② **审计表整个不动**——原以为 revision 已成一条序列、唯一约束可收紧成只按 revision，实测 `facebook_operation_global_policy_audit` 9 行只有 6 个不同 revision（1/2/3 各两次，dev 与 ol 各一），收紧会在现有数据上直接失败；而保留原约束对新行同样成立（新行作用域恒为 all）。 -->
- [x] 9.2 该 change 落地前，`'all'` 哨兵值是**中间态不是终点** —— 一个还留着的分行维度迟早会被重新用起来。本条 MUST NOT 因为"现在能跑"而无限期挂起；本 change archive 时若 9.1 尚未立项，MUST 在 backlog 里留具名条目 <!-- 2026-08-06 已立项，故无需再往 backlog 留具名条目。新 change 的归档前置写明：MUST 在本 change 归档之后才归档（它的 delta 是 ADDED 到本 change 引入的能力上，顺序反了会写出一份悬空规格，而 validate 与 archive 都不报错）。 -->
