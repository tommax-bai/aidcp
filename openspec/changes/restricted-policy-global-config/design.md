# Design: restricted-policy-global-config

## Context

受限(`restricted`)行为的现役事实(2026-08-06 实读代码坐实,与 `docs/risk-control.md` §7 的描述有出入):

1. **会话内浏览放行**:`aidcp-automation/src/risk/risk-controller.ts:200` 对 restricted 豁免 `view` 动作;调度器的浏览前闸(`explainView`,`role-dispatcher.ts:447` 附近接线注释)因此放行,受限账号会把当前会话浏览到自然结束。
2. **新会话早已拦停**:续场闸 `resumeGate`(`role-dispatcher.ts:3745`)对 `restricted` / `frozen` 一律 `blocked, reason='risk_state'`,且**不带恢复时刻**。
3. **自动恢复是死代码**:`risk-state-machine.ts` 有 `RESTRICTED_RECOVERY_MS = 72h` / `WARNED_RECOVERY_MS = 7d` 与 `recoverIfEligible()`,但全仓无人调用、也从不发 `recovered` 信号(`role-dispatcher.ts:3744` 与 `browser-standby.ts:17` 的注释均自陈)。受限唯一出口是人工:客户端「解除受限」(`aidcp-api/src/client-auth/client-auth-server.ts:1667` 起,restricted→normal)或运营改状态。
4. **让位只有回访语义**:`browser-standby.ts` 对 `risk_state` 分支走 `revisit`(默认 6h「回来再问一次」,非恢复承诺);唤醒主路径是 `ui.snapshot` ~60s 周期链,回访是周期链断掉时的死人开关。
5. **手动受限没有信号时间戳**:状态机 `transition()` 只对 `light/confirmed/fatal` 记 `lastSignalAt`;`manual_restrict` 不记。`recoverIfEligible()` 的窗口守卫是 `lastSignalAt && now - lastSignalAt < window`——`lastSignalAt` 为 null 时守卫**直接跳过**,一旦有人调用恢复,手动受限的号会被**秒恢复**。接活死代码前必须先修这个基点。

配置模式的既有模板:`resume_config_global`(`src/config/resume-config-store.ts`)——PG 单行表(id=1 CHECK)+ 内存镜像 + `writeWithMirrorBump` 跨进程失效(dev/ol 两进程共库)+ 缺值逐项回落写死默认绝不 brick + automation 面板端点(`automation-main.ts:1726` `createResumeConfigPanel`)+ api 透传 + console 编辑。配置镜像必须在 `ConfigMirrorKey` 编译期穷举注册表登记(spec `config-mirror-invalidation`)。

风控写路径约束:每账号 controller 单写(`risk-controller-registry.ts`),dev/ol 共库靠 `execution_target` 属主 + 条件写 + advisory writer lock(`writer-lock.ts`、`ownership.ts`);一切状态变更经 `applySignal` / 具名恢复方法 + `persistState()`,绝不直改 `risk_state` 表。

## Goals / Non-Goals

**Goals:**

- 受限处置策略成为全局可配:模式(只浏览 / 浏览也暂停)+ 恢复时长 N 小时(默认 72),后台改完即热生效。
- 接活自动恢复:受限满 N 小时无新信号自动回「警告」,警告满 7 天回「正常」,全程走单写通道。
- 「浏览也暂停」的受限账号让出浏览器槽位,并在恢复时刻或状态翻转时被唤醒;边缘零改动。
- 手动通道(客户端解除受限 / 运营信号)语义与优先级不变。

**Non-Goals:**

- 不改 frozen 语义(仍无自动恢复、让位维持回访)。
- 不做按账号 / 按平台维度的策略(全局单例;要分维度将来再立 change)。
- 不把警告 7 天回迁窗口做成可配(本次只配受限的 N;7 天维持常量,扫描器一并接活即可)。
- 不动协议、不动边缘(`ui.snapshot.browserStandby` 载荷字段只增不减且本次零新增)。
- 不接小红书真实限流信号(已知缺口,另案)。

## Decisions

### D1. 配置落点:新建单行表 `restricted_policy_config`,不并入 `resume_config_global`

复刻 `resume-config-store.ts` 全套(单行 CHECK、镜像、mirror bump、回落默认)。不并入 resume 表:那张表语义是「续场护栏 + 看门狗阈值」,受限策略属风控处置语义,消费方也不同(RiskController / 扫描器 vs 调度器)。新表 + 新 `ConfigMirrorKey`(编译期穷举强制登记,漏登即 typecheck 失败)。迁移编号按三仓并集取下一号(§8.1)。字段:`mode TEXT CHECK (mode IN ('browse_only','full_pause'))`、`recovery_hours INTEGER`,均可 null(回落默认 `browse_only` / 72)。

提供者接口定义在 `src/risk/`(如 `RestrictedPolicyProvider { mode(); recoveryHours(); }`),config 层实现——依赖方向维持「config → risk 单向」的既成事实(两个既有 store 头注均以此为归属依据)。

### D2. 「浏览也暂停」的实现点:关掉 explain('view') 的 restricted 豁免,而非新增命令闸

`risk-controller.ts:200` 改为:`restricted` 时,`full_pause` 模式下 `view` 也拒,reason `state:restricted`,并携带 `retryAfterMs = 恢复时刻 − now`(恢复时刻见 D4 基点)。选这里因为消费面全部现成:

- 会话内:调度器浏览前闸(`explainView`)被拒 → 走既有「浏览休眠」路径,不打开下一篇;
- 会话启动:「浏览会话启动时现问一次 view 配额」的既有 requirement(spec `interaction-risk-gating`)同样吃到拒绝;
- 待机提示:`browser-standby.ts` 的 `source.explain('view')` 同一入口。

`browse_only` 模式保持豁免,零回归。**不**给 `page.scroll` / `navigation.back` 加闸(spec 明文禁止,防浏览循环死锁)——受限休眠靠「不开下一篇 + 不续场 + 冷待机收走浏览器」,不靠拦推进命令。

### D3. 自动恢复扫描器:automation 进程内周期任务,经 registry 逐账号单写

新模块(如 `src/risk/risk-recovery-sweeper.ts`):周期(约 5min,带抖动)执行:

1. `pg-risk-store` 新增只读查询:`listByStatus(['warned','restricted'])`,返回 `account_id/status/last_signal_at/status_since/execution_target 属主`;
2. 过滤:仅本进程 `execution_target` 拥有的账号(属主列与条件写机制已有,复用 `ownership.ts` 判据);
3. 判窗:`now − max(lastSignalAt, statusSince) ≥ 窗口`(restricted 窗口 = `recoveryHours` 现读;warned = 7d 常量);
4. 命中 → `registry.resolveController(accountId)` → `applySignal({ kind: 'recovered' })`(内部 `recoverIfEligible` + `persistState`,mutation queue 串行,条件写撞属主即驱逐告警、诚实放弃)。

**不**绕过 controller 直改库;**不**在 api 进程跑(单写者在 automation)。逐级回迁沿用状态机:restricted→warned→(7d)→normal,不直跳 normal——warned 期保守档浏览本身就是「恢复」的第一阶段。

### D4. 恢复基点:`max(lastSignalAt, statusSince)`,改在状态机层

`recoverIfEligible()` 的窗口守卫改为以 `max(lastSignalAt ?? 0, statusSince)` 为基点,同时恢复窗口改为注入(restricted 窗口来自策略配置,warned 维持常量,frozen 恒 ∞)。这样修掉 Context #5 的秒恢复漏洞:手动受限(无 `lastSignalAt`)从进入受限时刻起算满 N 小时;受限期间再来新信号则顺延。`retryAfterMs` 与续场闸 `resumeAt`(D5)用同一函数推导,三处(view 拒绝、续场闸、扫描器)对「恢复时刻」的口径**必须同源**,禁止各自拼算式。

### D5. 让位链路:续场闸带真实 `resumeAt`,待机提示为受限加定时分支

- `resumeGate`(`role-dispatcher.ts:3745`):restricted 时 `resumeAt = 恢复时刻`(同源函数);frozen 维持缺省(算不出)。
- `browser-standby.ts` 两处:
  - `explain('view')` 拒绝分支:`state:restricted` 现在会落进「非 quota: 前缀 → hard_blocker 不让位」(`:160`)——加专门分支,用 `retryAfterMs` 产出定时让位提示(等待 ≥ `minWaitMs` 即 eligible);
  - `resumeGate.blocked, reason='risk_state'` 分支(`:170`):有 `resumeAt` 用定时提示,没有(frozen)维持 revisit。
- `needsBrowserToUnblock` 一票否决(验证码)保持压在所有来源之前——受限往往正是验证码/阻断弹窗触发的,**绝不能关掉运维正要去解弹窗的浏览器**;弹窗清除、暂停解除后,下一跳周期链才可能产出让位提示。
- 唤醒:冷待机期间 `ui.snapshot` ~60s 周期链不断;扫描器把状态翻回 warned 后,下一跳提示 `eligible=false` → 边缘唤醒;周期链断掉时靠 `wakeAt`(= 恢复时刻)兜底。**边缘零改动**。

### D6. 面板与 console:复刻 resume 配置通路

automation 侧 `createRestrictedPolicyPanel`(读 / 写,写走 `writeWithMirrorBump`,回显写后真态,遵守 `console-write-operations` 非乐观写);api 面板路由透传;console 全局设置加卡片:模式下拉(只浏览 / 浏览也暂停)+ 恢复小时数输入。console 枚举值与云端逐字对齐(有枚举漂移白屏前科)。

## Risks / Trade-offs

- **[秒恢复漏洞]** 接活恢复而不改基点 → 手动受限账号被扫描器立即恢复 → D4 基点修正 + 单测覆盖「manual_restrict 后 N 小时内不恢复、满 N 小时恢复」。
- **[双进程重复恢复]** dev/ol 共库,两进程都跑扫描器 → 属主过滤 + controller 条件写(已有驱逐机制)兜底;非属主命中即放弃并告警,不产生第二个写者。
- **[验证码浏览器被收走]** 受限常由弹窗触发,若让位分支绕过一票否决会关掉待解弹窗的浏览器(该事故路径在 `browser-standby.ts:143-151` 注释里有完整推演)→ 一票否决保持在所有来源之前,新分支不改判定顺序;补一条「受限 + 验证码暂停中 → 不让位」断言。
- **[配置镜像陈旧]** 跨进程失效窗口 ≈ 2s+5s 轮询;`full_pause` 切回 `browse_only` 后另一进程最长晚 ~7s 才放行浏览 → 可接受(方向是「多停一会」,安全侧);登记镜像档位时按闸门镜像声明陈旧上限。
- **[行为变化]** 默认 `browse_only` 下受限账号也从「永久停」变「N 小时回警告」——这是本 change 的目的而非事故,但部署后首次扫描会把**存量**受限账号成批恢复(可能一次好几个)。缓解:扫描器逐账号串行 + 恢复到的是保守档 warned(非 normal),并打一条带账号数的日志便于部署当天观察。
- **[三处口径漂移]** view 拒绝 / 续场闸 / 扫描器各自算恢复时刻 → 同源函数(D4)+ 单测断言三处引用同一实现。

## Migration Plan

1. automation:迁移(新表)→ store/facade/镜像登记 → 状态机基点与窗口注入 → controller view 闸 → 扫描器 → 续场闸/待机提示 → 面板端点;`npm run test:acceptance` + `npm test` + `npm run typecheck`(`AC-RISK-*` 必须全绿)。
2. api:面板透传 + 测试。
3. console:设置卡片 + 测试。
4. 部署 dev(默认配置 = `browse_only`/72h,行为变化仅「存量受限账号开始按 72h 回迁」);观察扫描器日志与待机提示。
5. 回滚:扫描器与 view 闸都以配置缺行回落默认为兜底;整体回滚按逐服务备份(§8.0),配置表 additive、无破坏性迁移。

## Open Questions

- 无阻塞项。恢复目标(回警告而非直跳正常)与警告窗口不配置化,均按本设计默认执行;用户若要「直跳正常」再加模式枚举即可,存储与判定面已留缝。
