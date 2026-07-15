## ADDED Requirements

### Requirement: 配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）

`effectiveQuotas()` 的每日 / 分钟 / 小时窗口配额 MUST 直接采用**安全限额配置**（经注入的配额提供者读 `quota_config` 表，缺值 / 缺行回落 `quotas.ts` 写死默认三档），MUST NOT 按账号年龄（`accounts.created_at` 现算的「入库天数」）压低为逐日爬坡的冷启动天花板。新账号自第一天起即按其风控档位（conservative / normal / aggressive）的安全限额浏览与互动；浏览（`view`）MUST NOT 被封顶在某个低于安全 `view` 配额的冷启动值（例如 Facebook 旧曲线第 7 天的 `view=70`）。

账号年龄冷启动爬坡 MAY 作为 opt-in 机制在代码中保留（曲线数据与 clamp 逻辑不删除），但**仅当运维显式设 `AIDCP_COLDSTART_RAMP=true` 时启用**；缺省（未设或非 `true`）MUST 关闭、MUST NOT 叠加任何冷启动 clamp。生产接线默认与 `RiskController` 的类默认 MUST 一致为「关」，MUST NOT 出现「类默认开、服务默认关」的口径分裂。

本要求 MUST NOT 改变既有不变量：安全限额**数字**不变；`warned` 的缩放、`restricted` / `frozen` 的互动清零 / 归零语义仍照常作用于安全限额基准；账号风控终态（`normal` / `warned` / `restricted` / `frozen`）MUST 仍仅由云端 `RiskController` 单写。与本机制无关的「重启防 burst 静默期」（进程重启后首次成功前的临时抑制）MUST NOT 受本要求影响。

#### Scenario: 新号默认按安全配额浏览、不被冷启动压低

- **WHEN** 某 Facebook 账号建号未满 7 天（历史冷启动窗口内）、`AIDCP_COLDSTART_RAMP` 未设为 `true`，`effectiveQuotas()` 被调用
- **THEN** 其 day 窗口 `view` 配额等于该账号风控档位的安全 `view` 限额（如 aggressive 写死默认 `300`），MUST NOT 被压到冷启动第 7 天的 `70`

#### Scenario: 冷启动仅在显式 opt-in 时生效

- **WHEN** 运维显式设 `AIDCP_COLDSTART_RAMP=true`
- **THEN** 逐日养号爬坡重新生效，`effectiveQuotas() = min(冷启动当日天花板, 风控缩放安全限额)`（原机制供养号需要时回退，行为与开启前一致）

#### Scenario: 关闭冷启动不动风控缩放语义

- **WHEN** 冷启动关闭（默认）且账号为 `warned` 或 `restricted`
- **THEN** `warned` 的缩放与 `restricted` 的互动清零仍照常作用于安全限额基准，账号威胁态单写不变量不受影响；MUST NOT 因关闭冷启动而放宽被限账号的互动闸
