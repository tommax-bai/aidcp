# Tasks: restricted-policy-global-config

## 1. aidcp-automation — 配置存储与镜像

- [x] 1.1 新迁移建 `restricted_policy_config` 单行表(id=1 CHECK;`mode` TEXT CHECK IN ('browse_only','full_pause') NULL、`recovery_hours` INTEGER NULL、updated_at/updated_by);编号按三仓 `migrations/` 并集取下一号,幂等建表 SQL 与 store 同源
  <!-- aidcp-automation 990dec9 migrations/0116_restricted_policy_config.sql;并集最高 0115 → 取 0116。偏离:store 不再携带同源 DDL 常量——AC-SCHEMA-DDL-OWNER 棘轮(只减不增)禁止 src/ 新增运行时 DDL,init 改按 requiredObjects 探测(照 0115 blocking-overlay 先例);另登记 boundaries/table-ownership.json(迁移属主判据)与 KNOWN_MAX_SCHEMA_VERSION 抬到 0116(只抬 KNOWN_MAX 不抬 REQUIRED,纯扩张) -->
- [x] 1.2 新建 `src/config/restricted-policy-store.ts`(复刻 resume-config-store:落库 + 内存镜像 + `writeWithMirrorBump`;缺行/非法值逐项回落默认 `browse_only`/72,绝不 brick;写库成功才刷镜像)与配套 facade
  <!-- aidcp-automation 990dec9 store+facade+单测;AUTOMATION_OWNED_MIRROR_KEYS 收编第五键;顺带修一处既有缺口:resumeConfigStore.init() 从未被调用(重启后库内续场配置静默回默认),现与其余三个配置存储对齐在启动期显式 init -->
- [x] 1.3 在 `src/risk/` 定义 `RestrictedPolicyProvider` 接口(`mode()` / `recoveryHours()`,含写死默认的 fallback 实现);config store 实现该接口,依赖方向保持 config→risk 单向
  <!-- aidcp-automation 990dec9 src/risk/restricted-policy.ts;模式枚举单一事实源在 kernel config-panel-ports(risk/ 已有 kernel import 先例,不构成 config→risk 反向依赖) -->
- [x] 1.4 新 `ConfigMirrorKey` 登记进配置镜像穷举注册表(闸门镜像档位、声明陈旧上限;漏登应由 typecheck 拦截,验证一次故意漏登确实编译失败)
  <!-- aidcp-kernel 1622a0c(ConfigMirrorKey 加第 16 键,出 tag v0.1.1);aidcp-api 50f514f(CONFIG_MIRRORS 登记)。漏登编译失败已双重坐实:kernel 自身 sync-read-facts 的 Record<ConfigMirrorKey,true> 与 api CONFIG_MIRRORS 在补登前都如期 TS2741。偏离(档位):登记为 parameter 而非闸门档——判据从注册表头注:automation 属主、写入方=消费方同进程、本地写透镜像、无跨服务副本,与四类限频配置完全同形;且 automation 侧闸门键表(AUTOMATION_GATE_MIRROR_KEYS)自陈「本进程没有的键放进来会被一条根本不持有的副本永久停手」——本键不经同步读消费流,登记 gate 要么空转要么误停手 -->



## 2. aidcp-automation — 状态机与恢复时刻同源

- [x] 2.1 `risk-state-machine.ts`:恢复窗口注入化(restricted 窗口来自 provider 现读、warned 维持 7d 常量、frozen ∞);恢复基点改 `max(statusSince, lastSignalAt ?? 0)`;恢复基点改 max 取两者;导出单一「恢复时刻」推导函数供三处消费
  <!-- aidcp-automation 990dec9 recoveryBaseAt/recoveryAtMs;微偏离:lastSignalAt 缺失回落 statusSince 而非 0(语义等价于任务式且不依赖「时间恒为正 epoch」的巧合,被合成时间轴单测当场抓出) -->
- [x] 2.2 单测:手动受限(无 lastSignalAt)满窗前不恢复、满窗恢复;窗口内新信号顺延;recoveryHours 改值即刻影响判窗;frozen 永不满窗
  <!-- aidcp-automation 990dec9 test/risk/restricted-policy-recovery.test.ts(15 例全绿,含三处同源断言) -->

## 3. aidcp-automation — view 闸与自动恢复扫描器

- [x] 3.1 `risk-controller.ts` explain():restricted + `full_pause` 时对 `view` 拒绝(reason `state:restricted`,携带 `retryAfterMs` = 恢复时刻 − now);`browse_only` 保持豁免;互动拒绝与配额归零不变;策略每次现读
  <!-- aidcp-automation 990dec9;另导出 controller.recoveryAt()(同源函数 + 注入策略),续场闸接线与扫描器复判都取它 -->
- [x] 3.2 `pg-risk-store.ts` 增只读 `listByStatus(...)`(返回 account_id/status/last_signal_at/status_since/属主),含索引评估
  <!-- aidcp-automation 990dec9;偏离:不回属主列——accounts.execution_target 是 api 域表,automation 库 join 不到(saveState 曾因此整条炸),属主由扫描器经归属端口逐账号问;索引评估结论=不加(risk_state 行数=账号量级、5min 一次顺序扫可忽略,登记在方法头注) -->
- [x] 3.3 新建 `src/risk/risk-recovery-sweeper.ts`:周期(约 5min 抖动)扫 warned/restricted → 属主过滤(execution_target)→ 同源函数判满窗 → `registry.resolveController().applySignal({kind:'recovered'})`;逐账号串行;条件写被拒记驱逐告警并放弃;打带账号数的恢复日志;组合根接线 + 优雅停机
  <!-- aidcp-automation 990dec9;automation-main 就绪闸放行后 start()、stop() 逆序停;驱逐告警走既有 onStateWriteRejected→registry 链,扫描器只如实计数放弃、绝不重试;materialize 后按 controller 内存态二次复判(防库行陈旧发无效信号) -->
- [x] 3.4 单测:恢复到 warned 而非 normal;warned 满 7d 回 normal;frozen 跳过;非属主跳过;写拒不形成第二写者;部署首扫存量成批恢复路径(多账号串行)
  <!-- aidcp-automation 990dec9 同上测试文件;frozen 跳过=不进 listByStatus 查询(断言查询入参)+ controller 态复判双闸 -->

## 4. aidcp-automation — 续场闸与待机提示

- [x] 4.1 `role-dispatcher.ts` resumeGate:restricted 裁决携带 `resumeAt`(同源函数);frozen 维持缺省
  <!-- aidcp-automation 990dec9;新 RoleDispatcher 选项 riskRecoveryAt,connection-dispatcher 接线为 () => ctx.controller.recoveryAt() -->
- [x] 4.2 `browser-standby.ts`:`state:restricted` 拒绝分支产出定时让位(用 retryAfterMs,≥minWaitMs 即 eligible),不再落 hard_blocker;`risk_state` 分支有 resumeAt 用定时、无(frozen)维持 revisit;`needsBrowserToUnblock` 一票否决顺序不动
  <!-- aidcp-automation 990dec9;防御分支:restricted 而 retryAfterMs 缺失(理论不可达)→ 让位+回访,绝不硬阻塞 -->
- [x] 4.3 单测:full_pause 受限定时让位;browse_only 会话结束后按 resumeAt 让位;frozen 回访;受限+验证码暂停不让位;ui.snapshot 待机载荷字段零增减断言
  <!-- aidcp-automation 990dec9 test/comm/browser-standby.test.ts 追加 7 例(含载荷字段集与既有配额路径逐字一致断言) -->

## 5. aidcp-automation — 面板端点与回归

- [x] 5.1 `createRestrictedPolicyPanel`(读/写;写走 mirror bump、回显写后真态;拒非法值:未知模式、非正整数小时)并在组合根挂载
  <!-- aidcp-automation 990dec9;路由对/客户端在共享 transport 包(aidcp-transport 3fd748f,tag v0.1.4,PanelConfigOwnerPorts.restrictedPolicy 必填=漏接线即 typecheck 红);本仓 src/transport/panel-config-http.ts 同名拷贝已逐字节同步;上限 720h 防「事实上永不恢复」 -->
- [x] 5.2 `npm run test:acceptance`(AC-RISK-* 全绿)+ 全量 `npm test` + `npm run typecheck`
  <!-- aidcp-automation 990dec9 acceptance 300/300、全量 2351 pass/0 fail、typecheck 干净;kernel pin v0.1.1 / transport pin v0.1.4 -->

## 6. aidcp-api — 面板透传

- [x] 6.1 面板路由透传受限策略读写端点(沿既有 automation 面板透传通道),含路由测试
  <!-- aidcp-api 50f514f GET/PUT /api/restricted-policy + PanelRestrictedPolicyHttpClient 接线 + capability 名册登记;test/panel-restricted-policy.test.ts 3 例(真态透传/非法值 400/未注入 503 具名) -->
- [x] 6.2 `npm test` + `npm run typecheck`
  <!-- aidcp-api 50f514f 全量 583/583、typecheck 干净(含 lock 里 pin 写法回 git+ssh 的 4b 断言) -->

## 7. aidcp-console — 全局设置界面

- [x] 7.1 全局设置加「受限处置策略」卡片:模式下拉(只浏览/浏览也暂停)+ 恢复小时数输入;枚举值与云端逐字对齐;保存回显写后真态与失败可区分
  <!-- aidcp-console 76c299a 安全页新卡(续场卡之后)+ 编辑弹窗;标签经 labelOf(枚举漂移兜底显示原值,enumTagSafety lint 强制);invalid_value / no_valid_fields 文案可区分 -->
- [x] 7.2 console 测试 + typecheck + build
  <!-- aidcp-console 76c299a 全量 46 文件 359 pass、typecheck 干净、vite build 过;新增 QuotasPage.restricted.test.tsx 4 例(渲染/覆盖态/本地闸/写非乐观逐字枚举 body) -->

## 8. 集成与部署

- [x] 8.1 各仓合回默认分支(rebase + acceptance + typecheck),控制仓 tasks.md 回写 sha
  <!-- 五仓落点:aidcp-kernel 1622a0c(tag v0.1.1)/ aidcp-transport 3fd748f(tag v0.1.4)/ aidcp-automation 990dec9+d298762 / aidcp-api 50f514f / aidcp-console 76c299a(撞 non-ff 一次,rebase 后重验重推);热点文件 risk-state-machine.ts 开工前已确认无并发 session 触碰 -->
- [x] 8.2 部署 dev(automation/api 服务 + console 静态;按逐服务部署流程,先探 ECS 现状);healthcheck + 扫描器日志观察(默认 browse_only/72h,注意首扫对存量受限账号的成批恢复日志)
  <!-- 2026-08-06 deployed(dev):先探 ECS(三服务 active、近 1h 无写入、关键文件 md5 与改动前 master 逐字节一致)→ 备份 automation/api/console → rsync(kernel v0.1.1 / transport v0.1.4 随包送,ECS 拉不动私有 git 依赖)→ stop-then-start → healthcheck 全过(契约门通过、写者锁重获、8787/8090/8091 监听、飞书长连接、面板 /api/restricted-policy 登录态端到端 200 回默认真态、console 新 bundle 上 8088、双服务 0 error)。⚠️ 迁移 0116 刻意未执行(惰性态):共库账本上执行会武装 OL 停机(0115/簇150 同根因),已加「探测失败→响亮降级到写死默认」的启动守卫(d298762);缺表期间判定按 browse_only/72h 跑、面板写响亮失败,执行迁移后重启即满血。扫描器首扫实录:扫 38 账号,restricted→warned 11、warned→normal 14、非属主跳过 8、放弃 0——存量成批恢复如设计预告发生并有带数日志 -->
- [x] 8.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`:full_pause 下受限账号让出槽位→到点唤醒→回警告档恢复浏览的端到端一趟
  <!-- 登记为簇 151(共享前置=迁移 0116 惰性态,与簇 150 同根因;含 full_pause 端到端/验证码一票否决/手动通道即时性/热改窗口/手动受限不秒恢复六项) -->

<!-- 2026-08-07 deployed(ol)+迁移执行(用户明确授权「OL也可以部署了」):
发布分支 release/20260807-ol-restricted-policy(三仓,精确切自本 change 验证过的 sha:
automation d298762 / api 50f514f / console 76c299a——刻意不带 master 上并发新落的
platformize-browse-vocabulary 与 transport v0.1.5,那些不在本次授权与验证范围)。
切前对账:上批发布分支(automation/api release/20260806-ol-derived-services、
console release/20260805-fb-global-policy-unify)对 master `git cherry` 零 + 提交,无待回流。
序列:探 OL(三服务 active、无并发写入、树=改前 master)→ 备份三目录 → 从发布 worktree
rsync(kernel v0.1.1/transport v0.1.4 按发布 lock 现装随包送)→ stop-then-start →
惰性态 healthcheck 过(契约门 0113/认识 0116、写者锁 target=ol、OL 首扫:24 账号
restricted→warned 1 / warned→normal 2 / 非属主跳过 6 / 放弃 0)→
执行迁移 up --owner=automation(status 先核:账本 60 行校验和全一致,待应用恰 0115+0116
均 kind=expand;applied 70ms/42ms;⚠️ 注意 migrate CLI 旗标是 --owner=xxx 带等号,
空格分写会被静默忽略、探全部属主组)→ 两环境 automation 再重启 →
满血 healthcheck:两侧账本 0116、探测警告消失、0 error、OL 面板端到端 200、
OL console 新 bundle 200。0115 同批落地,簇 150 的前置①随之解除。
发布分支保留(remote+local),发布 worktree 已清;分支内容=master 快照,无需回流。 -->
