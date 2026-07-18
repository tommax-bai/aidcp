## MODIFIED Requirements

### Requirement: 配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）

云端 SHALL 保留两条显式、互不合成的慢启动路径：

1. 历史 env 全局旁路：仅当 `AIDCP_COLDSTART_RAMP=true` 时，按账号 `created_at` 启用历史冷启动爬坡；默认与 `RiskController` 类默认均为关。
2. 环境级慢启动：仅当账号当前唯一绑定环境的 `client_environments.slow_start_since` 非 NULL 时，对该环境当前账号启用，起点取环境字段自身。

anchor 解析 MUST 严格按「当前环境设置优先，否则才考虑历史旁路」：当前唯一绑定环境起点非 NULL → 用环境 `slow_start_since`；否则 env 全局旁路开且账号 `created_at` 存在 → 用 `created_at`；否则不叠 clamp。两条路径的起点 MUST NOT 以 OR / AND / min 或任何其它方式合成。

环境慢启动的起点 MUST NOT 取 `accounts.created_at` 或 `accounts.slow_start_since`。前者只是账号第一次连上本云端库的时刻；后者是迁移前遗留数据。部署切换后两者均 MUST NOT 成为环境级开关的运行时事实源。

`AIDCP_SLOW_START_DISABLED=true` MUST 作为全局停用闸：置真时无视所有环境级慢启动设置与历史 env 旁路、全体不叠 clamp，且对外投影 MUST 如实标注该原因。

冷启动天花板的平台曲线选择 MUST 建立在已确认的平台之上。账号平台无法确认时 MUST NOT 回落到任一平台曲线，MUST 不叠 clamp 并如实标注不可用原因。

慢启动是 `effectiveQuotas()` 的输入，不是账号风控状态：它 MUST NOT 写入 `risk_state`、MUST NOT 经 `setQuotaLevel` / `applySignal` 或风控终态单写链，MUST NOT 改变账号威胁态。安全限额数字、warned/restricted/frozen 语义和重启防 burst 静默期均 MUST 保持不变。

同一账号若异常映射到多个环境，运行时 MUST NOT 任取某个环境的设置，也 MUST NOT把某个环境设置永久复制到账号。系统 SHALL 报出可诊断的绑定冲突并停止声称某个环境设置已对该账号生效；不得自动删除或重写绑定来掩盖异常。

#### Scenario: 新号默认按安全配额浏览、不被冷启动压低

- **WHEN** 某 Facebook 账号所在环境的 `slow_start_since` 为 NULL、`AIDCP_COLDSTART_RAMP` 未设为 `true`
- **THEN** 其 day 窗口配额等于该账号风控档位的安全限额，MUST NOT 因账号年龄或旧账号字段被冷启动压低

#### Scenario: 冷启动全局路径仅在显式 opt-in 时生效

- **WHEN** 运维显式设 `AIDCP_COLDSTART_RAMP=true`，且当前环境未开启慢启动
- **THEN** 历史爬坡按账号 `created_at` 起点生效，`effectiveQuotas() = min(冷启动当日天花板, 风控缩放安全限额)`

#### Scenario: 环境级慢启动独立于全局开关生效

- **WHEN** `AIDCP_COLDSTART_RAMP` 未设为 `true`，但账号当前唯一绑定环境的 `slow_start_since` 为 3 天前
- **THEN** 该账号 `effectiveQuotas() = min(该平台曲线第 4 天天花板, 风控缩放安全限额)`
- **AND** 其它未开启环境的账号逐位不受影响

#### Scenario: 环境换号后设置留在环境

- **WHEN** 已开启慢启动的环境从账号 A 换绑为账号 B，两个账号的 controller 均已缓存
- **THEN** 账号 B 下一次 `effectiveQuotas()` 使用该环境起点，账号 A 下一次调用不再使用该起点
- **AND** MUST NOT 重启进程、驱逐 controller 或把起点写入账号 B

#### Scenario: 账号移动到另一环境后采用目标环境设置

- **WHEN** 账号 A 从已开启慢启动的环境 E1 移到未开启的环境 E2
- **THEN** 账号 A 不再受 E1 设置影响，按 E2 的关闭态计算
- **AND** E1 的设置逐位保留，供 E1 之后绑定的新账号使用

#### Scenario: 两条路径不合成起点

- **WHEN** `AIDCP_COLDSTART_RAMP=true` 且当前环境起点为今天、账号 `created_at` 为 30 天前
- **THEN** 该账号按环境起点算作第 1 天，MUST NOT 因 `created_at` 已过窗口而毕业或合成两个起点

#### Scenario: 旧账号字段不再参与运行时

- **WHEN** 环境 `slow_start_since` 为 NULL、历史 `accounts.slow_start_since` 非 NULL 且迁移阶段已经完成
- **THEN** `effectiveQuotas()` MUST 不因旧账号字段叠加 clamp

#### Scenario: 平台无法确认时不 clamp 也不回落曲线

- **WHEN** 环境慢启动已开启，但其当前账号平台无法确认
- **THEN** MUST NOT 按小红书曲线或任何其它平台曲线 clamp
- **AND** 对外投影 MUST 标注当前不适用慢启动及其原因

#### Scenario: 开关改动无需重启即生效

- **WHEN** 某环境的 `slow_start_since` 被写入或清空，而当前账号的 `RiskController` 已存在
- **THEN** 同一实例的下一次 `effectiveQuotas()` MUST 反映新环境值

#### Scenario: 多环境歧义不得任取配置

- **WHEN** 同一账号异常出现在两个环境绑定中且两环境慢启动设置不同
- **THEN** 运行时 MUST NOT 任取一行、最近一行或更宽松一行作为该账号设置
- **AND** 系统 MUST 产生可诊断冲突，MUST NOT 声称任一环境设置已生效

#### Scenario: 全局停用闸无视环境级开关

- **WHEN** `AIDCP_SLOW_START_DISABLED=true`，而若干环境的 `slow_start_since` 非 NULL
- **THEN** 全体账号不叠 clamp，且投影如实标注云端全局停用，MUST NOT显示为环境未开启

#### Scenario: 慢启动只收紧不放宽

- **WHEN** 某环境开启慢启动，与同一环境同一账号同一时刻未开启相比
- **THEN** `effectiveQuotas()` 的每个窗口每个动作 MUST 逐位小于或等于未开启时的值
- **AND** MUST NOT 断言必然严格更小

#### Scenario: 关闭慢启动不动风控缩放语义

- **WHEN** 环境慢启动关闭且账号为 `warned` 或 `restricted`
- **THEN** 既有缩放与互动清零照常作用，账号威胁态单写不变量不受影响

#### Scenario: 慢启动不进风控单写链

- **WHEN** 某环境的慢启动被开启、关闭或换绑账号
- **THEN** 涉及账号的 `risk_state.status` 与 `quotaLevel` MUST 逐位不变，MUST NOT 触发风控状态迁移

### Requirement: 慢启动状态投影必须与实际 clamp 同源同格

云端对外投影的慢启动状态（`state` / `day` / `binding`）与 `applyColdStartClamp` 实际采用的天数 MUST 由同一个当前环境 anchor 解析函数与同一次时钟读取得出，MUST NOT 各自独立计算。任何“投影来自环境 A、clamp 来自环境 B”或“投影第 7 天、clamp 已按第 8 天放行”的错位 MUST 不可能出现。

`binding` SHALL 如实表达本次 clamp 是否至少收紧一项配额。当没有当前账号、账号平台未知或绑定有歧义时，投影 MUST NOT 返回肯定的 `binding` 或生效配额。环境未绑定账号时允许返回环境配置的 `state/day/since`，但 MUST 同时标注 `binding_unknown` 并与 controller 生效投影区分。

#### Scenario: 投影天数与 clamp 天数逐格相等

- **WHEN** 某账号唯一绑定环境开启慢启动、处于第 1 至第 8 天中任一天
- **THEN** 投影的 `day` 与该次 `effectiveQuotas()` 内 clamp 采用的天数相等
- **AND** 第 8 天时投影毕业且 clamp 同时放行

#### Scenario: 未绑定环境不编造生效状态

- **WHEN** 环境已开启慢启动但当前没有有效账号绑定
- **THEN** 投影可返回环境配置的起点与天数，但 MUST 标注 `binding_unknown`
- **AND** MUST NOT 返回 `binding=true`、当日生效配额或“已压低”表述

#### Scenario: 曲线不比档位更严时如实标注

- **WHEN** 当前账号的慢启动曲线上界在所有窗口所有动作上均不严于风控缩放后的档位配额
- **THEN** `binding` MUST 为 false，投影 MUST NOT 表述为配额已被压低

### Requirement: 慢启动起点写入时对齐运营自然日

写入环境 `slow_start_since` 时 MUST 将其对齐到该时刻所属运营自然日（上海时区）的起点，使勾选当天整天计为第 1 天。天数递进与「今日进展」计数窗口 MUST 同相，环境换绑账号 MUST NOT 重置该起点。

#### Scenario: 深夜勾选不在次日夜间跳档

- **WHEN** 运营于某日 23:50 开启某环境慢启动
- **THEN** 环境 `slow_start_since` 存为该日 00:00（上海时区）
- **AND** 次日 23:51 仍处于第 2 天，MUST NOT 在计数未清零时跳到下一天

#### Scenario: 天数换档与计数清零同时发生

- **WHEN** 某开启慢启动的环境跨过运营自然日边界
- **THEN** 其 `day` 递增与当前账号当日计数窗口清零发生在同一时刻

#### Scenario: 换绑不重置环境起点

- **WHEN** 慢启动第 4 天的环境从账号 A 换绑为账号 B
- **THEN** 账号 B 使用同一环境起点并处于第 4 天，MUST NOT 从第 1 天重新开始
