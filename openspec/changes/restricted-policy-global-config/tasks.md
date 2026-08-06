# Tasks: restricted-policy-global-config

## 1. aidcp-automation — 配置存储与镜像

- [ ] 1.1 新迁移建 `restricted_policy_config` 单行表(id=1 CHECK;`mode` TEXT CHECK IN ('browse_only','full_pause') NULL、`recovery_hours` INTEGER NULL、updated_at/updated_by);编号按三仓 `migrations/` 并集取下一号,幂等建表 SQL 与 store 同源
- [ ] 1.2 新建 `src/config/restricted-policy-store.ts`(复刻 resume-config-store:落库 + 内存镜像 + `writeWithMirrorBump`;缺行/非法值逐项回落默认 `browse_only`/72,绝不 brick;写库成功才刷镜像)与配套 facade
- [ ] 1.3 在 `src/risk/` 定义 `RestrictedPolicyProvider` 接口(`mode()` / `recoveryHours()`,含写死默认的 fallback 实现);config store 实现该接口,依赖方向保持 config→risk 单向
- [ ] 1.4 新 `ConfigMirrorKey` 登记进配置镜像穷举注册表(闸门镜像档位、声明陈旧上限;漏登应由 typecheck 拦截,验证一次故意漏登确实编译失败)

## 2. aidcp-automation — 状态机与恢复时刻同源

- [ ] 2.1 `risk-state-machine.ts`:恢复窗口注入化(restricted 窗口来自 provider 现读、warned 维持 7d 常量、frozen ∞);恢复基点改 `max(statusSince, lastSignalAt ?? 0)`;导出单一「恢复时刻」推导函数供三处消费
- [ ] 2.2 单测:手动受限(无 lastSignalAt)满窗前不恢复、满窗恢复;窗口内新信号顺延;recoveryHours 改值即刻影响判窗;frozen 永不满窗

## 3. aidcp-automation — view 闸与自动恢复扫描器

- [ ] 3.1 `risk-controller.ts` explain():restricted + `full_pause` 时对 `view` 拒绝(reason `state:restricted`,携带 `retryAfterMs` = 恢复时刻 − now);`browse_only` 保持豁免;互动拒绝与配额归零不变;策略每次现读
- [ ] 3.2 `pg-risk-store.ts` 增只读 `listByStatus(...)`(返回 account_id/status/last_signal_at/status_since/属主),含索引评估
- [ ] 3.3 新建 `src/risk/risk-recovery-sweeper.ts`:周期(约 5min 抖动)扫 warned/restricted → 属主过滤(execution_target)→ 同源函数判满窗 → `registry.resolveController().applySignal({kind:'recovered'})`;逐账号串行;条件写被拒记驱逐告警并放弃;打带账号数的恢复日志;组合根接线 + 优雅停机
- [ ] 3.4 单测:恢复到 warned 而非 normal;warned 满 7d 回 normal;frozen 跳过;非属主跳过;写拒不形成第二写者;部署首扫存量成批恢复路径(多账号串行)

## 4. aidcp-automation — 续场闸与待机提示

- [ ] 4.1 `role-dispatcher.ts` resumeGate:restricted 裁决携带 `resumeAt`(同源函数);frozen 维持缺省
- [ ] 4.2 `browser-standby.ts`:`state:restricted` 拒绝分支产出定时让位(用 retryAfterMs,≥minWaitMs 即 eligible),不再落 hard_blocker;`risk_state` 分支有 resumeAt 用定时、无(frozen)维持 revisit;`needsBrowserToUnblock` 一票否决顺序不动
- [ ] 4.3 单测:full_pause 受限定时让位;browse_only 会话结束后按 resumeAt 让位;frozen 回访;受限+验证码暂停不让位;ui.snapshot 待机载荷字段零增减断言

## 5. aidcp-automation — 面板端点与回归

- [ ] 5.1 `createRestrictedPolicyPanel`(读/写;写走 mirror bump、回显写后真态;拒非法值:未知模式、非正整数小时)并在组合根挂载
- [ ] 5.2 `npm run test:acceptance`(AC-RISK-* 全绿)+ 全量 `npm test` + `npm run typecheck`

## 6. aidcp-api — 面板透传

- [ ] 6.1 面板路由透传受限策略读写端点(沿既有 automation 面板透传通道),含路由测试
- [ ] 6.2 `npm test` + `npm run typecheck`

## 7. aidcp-console — 全局设置界面

- [ ] 7.1 全局设置加「受限处置策略」卡片:模式下拉(只浏览/浏览也暂停)+ 恢复小时数输入;枚举值与云端逐字对齐;保存回显写后真态与失败可区分
- [ ] 7.2 console 测试 + typecheck + build

## 8. 集成与部署

- [ ] 8.1 各仓合回默认分支(rebase + acceptance + typecheck),控制仓 tasks.md 回写 sha
- [ ] 8.2 部署 dev(automation/api 服务 + console 静态;按逐服务部署流程,先探 ECS 现状);healthcheck + 扫描器日志观察(默认 browse_only/72h,注意首扫对存量受限账号的成批恢复日志)
- [ ] 8.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`:full_pause 下受限账号让出槽位→到点唤醒→回警告档恢复浏览的端到端一趟
