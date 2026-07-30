# interaction-risk-gating（delta）

## MODIFIED Requirements

### Requirement: 慢启动状态投影必须与实际 clamp 同源同格

云端对外投影的慢启动状态（下发客户端的 `state` / `day` / `binding` / `eligible` / `ineligibleReason`）与 `applyColdStartClamp` 实际采用的**天数**与**平台准入判定** MUST 由**同一组解析函数**与**同一次时钟读取**得出，MUST NOT 各自独立计算。任何「投影说第 7 天、clamp 已按第 8 天放行」的错位 MUST 不可能出现。

**平台准入闸 MUST 同时约束投影与 clamp。** 慢启动 SHALL 只对白名单内的平台生效；平台不在白名单内时，投影 MUST 标注 `eligible=false` 且原因为「平台不支持」，**同时 `applyColdStartClamp` MUST 原样返回风控缩放配额、MUST NOT 叠加任何平台曲线的 clamp**。「投影说不适用、clamp 照夹」是被禁止的状态：它对运营是一条无法解释的静默限流——界面宣称该账号没在养号，实际配额却被一条从不属于它的曲线压着，且无日志无告警。

**此约束与慢启动锚点的来源无关。** 无论慢启动窗口是由账号级开关开启、还是由全局旁路开关（env）带出，平台准入闸的结论 MUST 一致：白名单外的平台在两种来源下都 MUST NOT 被 clamp。旁路开关 MUST NOT 成为绕过平台准入的后门——那正是「投影说没开、clamp 正在夹」的成因。

平台准入 MUST NOT 靠给个别动作开逐项豁免来近似。给不支持的平台补一个动作豁免，只会把「白名单说不支持」与「clamp 照夹其余动作」的矛盾固化：漏掉的动作（如入站评论回复）仍会被夹成 0，且下一个新增动作会再次默认落入被夹集合。**唯一正确的边界是平台级准入闸；准入不通过即整体不 clamp。**

`binding` SHALL 如实表达「本次 clamp 是否至少收紧了一项配额」：当曲线天花板在所有窗口所有动作上均不严于风控缩放后的档位配额时，`binding` MUST 为 false。投影 MUST NOT 在 `binding` 为 false 时宣称配额已被压低。平台准入不通过时 `binding` MUST 为 false。

平台准入闸只关闭「慢启动 clamp」这一条通路，MUST NOT 影响该账号的风控档位缩放、限频计数或任何其它闸——被排除的平台自第一天起即按其风控档位的安全限额运行，这就是它的常态，不需要额外的恢复动作把它拨回来。反之，把某平台纳入白名单是显式的代码 / 配置变更，纳入后 clamp 与投影 MUST 同时开始生效，不存在只生效一半的中间态。

#### Scenario: 投影天数与 clamp 天数逐格相等

- **WHEN** 某账号开启慢启动、处于第 1 至第 8 天中任一天
- **THEN** 投影的 `day` 与该次 `effectiveQuotas()` 内 clamp 采用的天数 MUST 相等
- **AND** 第 8 天时投影 MUST 为毕业态且 clamp MUST 放行，两者同时发生

#### Scenario: 白名单外平台不被任何曲线 clamp

- **WHEN** 全局旁路开关 `AIDCP_COLDSTART_RAMP=true`，某视频号账号入库 1 天，而视频号不在慢启动平台白名单内
- **THEN** 该账号 `effectiveQuotas()` 逐位等于其风控缩放后的安全限额，MUST NOT 被夹到任何平台曲线的当日天花板
- **AND** 其 `comment` 与 `dm_reply` 配额 MUST NOT 被夹成 0
- **AND** 投影 MUST NOT 出现「宣称未启用 / 不适用、而配额正被夹」的矛盾

#### Scenario: 账号级开关下白名单外平台的投影与 clamp 一致

- **WHEN** 某视频号账号被账号级开关开启慢启动，而视频号不在白名单内
- **THEN** 投影 MUST 为 `eligible=false`、原因「平台不支持」、`binding=false`
- **AND** `applyColdStartClamp` MUST 原样返回风控缩放配额，与该投影一致

#### Scenario: 白名单内平台行为逐位不变

- **WHEN** 同一开关下，某 Facebook 账号与某小红书账号各自处于慢启动窗口内
- **THEN** 二者的 clamp 结果与投影逐位不变（零回归），仍为 `min(当日天花板, 风控缩放安全限额)`

#### Scenario: 曲线不比档位更严时如实标注

- **WHEN** 某小红书账号处于 conservative 档、开启慢启动且处于第 5 至 7 天，此时曲线上界在 view / like / comment / publish 上均不低于该档位配额
- **THEN** `binding` MUST 为 false
- **AND** 投影 MUST NOT 表述为「配额已被压低」
