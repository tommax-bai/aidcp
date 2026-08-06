# Proposal: restricted-policy-global-config

## Why

受限(`restricted`)状态今天的行为是「半接线」:会话内浏览仍然放行、新会话被续场闸拦停、而 72 小时自动恢复是**死代码**(状态机里恢复常量与恢复函数俱在,全仓无人调用、也从不发恢复信号),槽位让出对受限只有「隔段时间回访」语义。结果是受限账号永远停在原地等人工,且运营无法按业务风险偏好选择受限的处置力度(继续养号式浏览 vs 彻底静默)。

## What Changes

- **新增全局单行配置「受限处置策略」**(复刻 `resume_config_global` 模式:PG 单行表 + 内存镜像热加载 + 跨进程失效信号 + 缺值回落默认绝不 brick):
  - `mode`:`browse_only`(只浏览,默认,现状零回归)/ `full_pause`(浏览也暂停);
  - `recoveryHours`:恢复时长 N 小时,默认 72,两种模式下都生效。
- **浏览也暂停模式**:风控对浏览动作(`view`)在 restricted 时也拒绝,并随拒绝给出剩余等待时长;会话内浏览循环经既有「浏览休眠」路径停下,不新建停摆机制。
- **接活自动恢复死代码**:新增周期扫描器,受限满 N 小时无新信号 → 经每账号控制器单写通道发恢复信号回「警告」;警告 7 天回迁同一扫描器一并接活。恢复基点取 `statusSince` 与 `lastSignalAt` 的较大者(防手动受限账号无信号时间戳被秒恢复);按 `execution_target` 属主只扫本进程拥有的账号(dev/ol 共库)。
- **受限的待机提示从「回访」升级为「定时让位」**:续场闸对受限携带真实恢复时刻;待机提示据此产出带等待时长的让位提示(等待 ≥ 阈值即让出浏览器槽位),冻结维持无时刻回访语义;「正卡在验证码上绝不让位」一票否决保留。
- **手动通道不变**:客户端「解除受限」、运营 `manual_restrict` / `operator_override_recover` 立即生效、不受 N 小时约束。
- **面板与后台界面**:automation 出配置读写面板端点(api 透传),console 加全局设置项(枚举与云端严格对齐)。

行为变化提示(非 BREAKING,但属预期新行为):即使保持默认 `browse_only`,受限账号也将从「永远等人工」变为「N 小时后自动回警告档」。

## Capabilities

### New Capabilities

- `restricted-account-policy`: 受限处置策略全局配置(模式 + 恢复时长)的存储 / 热加载 / 面板编辑,与风控自动恢复扫描器(单写、属主隔离、恢复基点、逐级回迁)。

### Modified Capabilities

- `interaction-risk-gating`: view 闸在 restricted 下的判定改为按策略模式(`full_pause` 时拒绝并携带剩余等待时长);恢复窗口从写死常量改为策略配置现读。
- `browser-cold-standby`: 受限且有真实恢复时刻的账号 SHALL 产出定时让位提示(而非回访 / 硬阻塞);冻结维持回访;验证码一票否决优先级不变。

## Impact

- **aidcp-automation**(主体):`src/risk/risk-controller.ts`(view 豁免按模式关闭 + retryAfterMs)、`src/risk/risk-state-machine.ts`(恢复窗口注入 + 恢复基点)、新扫描器、`src/risk/pg-risk-store.ts`(按状态枚举查询)、`src/orchestrator/role-dispatcher.ts`(续场闸 resumeAt)、`src/comm/browser-standby.ts`(受限定时分支)、新配置 store + facade + 面板、`migrations/`(编号按三仓并集取下一号)、配置镜像注册表登记(编译期穷举强制)。
- **aidcp-api**:面板路由透传新配置读写。
- **aidcp-console**:全局设置界面新增受限策略卡片。
- **边缘零改动、协议零改动**:复用 `ui.snapshot` 的 browserStandby 载荷与双向冷待机机制;唤醒走既有 ~60s 周期链与 wakeAt。
- 不触碰:风控状态单写路径的既有约束(扫描器经控制器 applySignal,不直改库)、`AC-RISK-*` 验收红线、边云协议四处同步面。
