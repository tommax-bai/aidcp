## MODIFIED Requirements

### Requirement: 配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）

`effectiveQuotas()` 的每日 / 分钟 / 小时窗口配额 MUST 直接采用**安全限额配置**（经注入的配额提供者读 `quota_config` 表，缺值 / 缺行回落 `quotas.ts` 写死默认三档），MUST NOT 按账号年龄（`accounts.created_at` 现算的「入库天数」）压低为逐日爬坡的冷启动天花板。新账号自第一天起即按其风控档位（conservative / normal / aggressive）的安全限额浏览与互动；浏览（`view`）MUST NOT 被封顶在某个低于安全 `view` 配额的冷启动值（例如 Facebook 旧曲线第 7 天的 `view=70`）。

逐日爬坡 MAY 作为 opt-in 机制在代码中保留（曲线数据与 clamp 逻辑不删除），且 SHALL 有且仅有两条互相独立的启用路径，**缺省两条都关**：

1. **进程级全局路径**（既有）：仅当运维显式设 `AIDCP_COLDSTART_RAMP=true` 时启用，起点取 `accounts.created_at`。生产接线默认与 `RiskController` 的类默认 MUST 一致为「关」，MUST NOT 出现「类默认开、服务默认关」的口径分裂。
2. **账号级慢启动路径**（本 change 新增）：仅当该账号 `accounts.slow_start_since` 非 NULL 时对**该账号**启用，起点取 `slow_start_since` 自身。

anchor（起点）解析 MUST 严格按「谁开用谁的起点」的优先级：账号级非 NULL → 用 `slow_start_since`；否则 env 全局开且 `created_at` 存在 → 用 `created_at`；否则不叠任何 clamp。两条路径的起点 MUST NOT 以 OR / AND / min 或任何其它方式合成——合成会把未开慢启动的账号按 `created_at` 夹回冷启动天花板，即本要求首段禁止的那个行为。

账号级慢启动的起点 MUST NOT 取 `accounts.created_at`。该列语义是「该 accountId 第一次握手连上本云端库的时刻」（`DEFAULT now()`，且账号重连时 `ON CONFLICT DO NOTHING` 保留原值），既非平台注册时间、亦非首次运行时间；以它为起点会使导入的老号被当作第 1 天、复活的旧号被当作已毕业。

`AIDCP_SLOW_START_DISABLED=true` MUST 作为全局停用闸：置真时无视所有账号级 `slow_start_since`、全体不叠 clamp，且对外投影 MUST 如实标注该原因。

冷启动天花板的平台曲线选择 MUST 建立在**已确认的平台**之上。当账号平台无法确认时，MUST NOT 回落到任一平台的曲线（含默认小红书曲线），MUST 不叠 clamp 并如实标注不可用原因。

慢启动是 `effectiveQuotas()` 的**输入**，不是账号风控状态：它 MUST NOT 写入 `risk_state`、MUST NOT 经 `setQuotaLevel` / `applySignal` 或风控终态单写链，MUST NOT 改变账号威胁态。

本要求 MUST NOT 改变既有不变量：安全限额**数字**不变；`warned` 的缩放、`restricted` / `frozen` 的互动清零 / 归零语义仍照常作用于安全限额基准；账号风控终态（`normal` / `warned` / `restricted` / `frozen`）MUST 仍仅由云端 `RiskController` 单写。与本机制无关的「重启防 burst 静默期」（进程重启后首次成功前的临时抑制）MUST NOT 受本要求影响。

#### Scenario: 新号默认按安全配额浏览、不被冷启动压低

- **WHEN** 某 Facebook 账号建号未满 7 天（历史冷启动窗口内）、`AIDCP_COLDSTART_RAMP` 未设为 `true`、该账号 `slow_start_since` 为 NULL，`effectiveQuotas()` 被调用
- **THEN** 其 day 窗口 `view` 配额等于该账号风控档位的安全 `view` 限额（如 aggressive 写死默认 `300`），MUST NOT 被压到冷启动第 7 天的 `70`

#### Scenario: 冷启动全局路径仅在显式 opt-in 时生效

- **WHEN** 运维显式设 `AIDCP_COLDSTART_RAMP=true`
- **THEN** 逐日养号爬坡按 `created_at` 起点重新生效，`effectiveQuotas() = min(冷启动当日天花板, 风控缩放安全限额)`（原机制供养号需要时回退，行为与开启前一致）

#### Scenario: 账号级慢启动独立于全局开关生效

- **WHEN** `AIDCP_COLDSTART_RAMP` 未设为 `true`，但某账号 `slow_start_since` 为 3 天前
- **THEN** 该账号 `effectiveQuotas() = min(该平台曲线第 4 天天花板, 风控缩放安全限额)`
- **AND** 同云端其它 `slow_start_since` 为 NULL 的账号逐位不受影响

#### Scenario: 两条路径不合成起点

- **WHEN** `AIDCP_COLDSTART_RAMP=true` 且某账号 `slow_start_since` 为今天、而其 `created_at` 为 30 天前
- **THEN** 该账号按 `slow_start_since` 算作第 1 天，MUST NOT 因 `created_at` 已过 7 天窗口而被判毕业、MUST NOT 取两者之中任一合成值

#### Scenario: 慢启动起点绝不取入库时间

- **WHEN** 某账号 `slow_start_since` 为 NULL 且 `AIDCP_COLDSTART_RAMP` 未设为 `true`，无论其 `created_at` 为何值
- **THEN** MUST 不叠任何冷启动 clamp，`effectiveQuotas()` 与本 change 前逐位相同

#### Scenario: 平台无法确认时不 clamp 也不回落曲线

- **WHEN** 某账号 `slow_start_since` 非 NULL，但其平台无法确认（元数据解析失败或平台字段不可信）
- **THEN** MUST NOT 按小红书曲线或任何其它平台曲线 clamp，`effectiveQuotas()` 与不开慢启动逐位相同
- **AND** 对外投影 MUST 标注该账号当前不适用慢启动及其原因

#### Scenario: 开关改动无需重启即生效

- **WHEN** 某账号的 `slow_start_since` 被写入或清空，而该账号的 `RiskController` 实例已存在于进程内且不被重建
- **THEN** 同一实例的下一次 `effectiveQuotas()` MUST 反映新值
- **AND** MUST NOT 要求重启进程、驱逐 controller 缓存或重新解析账号元数据

#### Scenario: 全局停用闸无视账号级开关

- **WHEN** `AIDCP_SLOW_START_DISABLED=true`，而若干账号 `slow_start_since` 非 NULL
- **THEN** 全体账号 MUST 不叠 clamp，`effectiveQuotas()` 与不开慢启动逐位相同
- **AND** 对外投影 MUST 如实标注「本云端已全局停用慢启动」，MUST NOT 把停用显示成未开启

#### Scenario: 慢启动只收紧不放宽

- **WHEN** 某账号开启慢启动，与同一账号同一时刻未开启慢启动相比
- **THEN** 其 `effectiveQuotas()` 的每个窗口每个动作 MUST 逐位小于或等于未开启时的值
- **AND** MUST NOT 断言必然严格更小——曲线与档位取更严者，档位数字可经 `quota_config` 热编辑，故某些档位下部分动作可能逐位相等

#### Scenario: 关闭冷启动不动风控缩放语义

- **WHEN** 冷启动关闭（默认）且账号为 `warned` 或 `restricted`
- **THEN** `warned` 的缩放与 `restricted` 的互动清零仍照常作用于安全限额基准，账号威胁态单写不变量不受影响；MUST NOT 因关闭冷启动而放宽被限账号的互动闸

#### Scenario: 慢启动不进风控单写链

- **WHEN** 某账号的慢启动被开启或关闭
- **THEN** 其 `risk_state` 的 `status` 与 `quotaLevel` MUST 逐位不变，MUST NOT 触发任何风控状态迁移或持久化写

## ADDED Requirements

### Requirement: 慢启动状态投影必须与实际 clamp 同源同格

云端对外投影的慢启动状态（下发客户端的 `state` / `day` / `binding`）与 `applyColdStartClamp` 实际采用的天数 MUST 由**同一个 anchor 解析函数**与**同一次时钟读取**得出，MUST NOT 各自独立计算。任何「投影说第 7 天、clamp 已按第 8 天放行」的错位 MUST 不可能出现。

`binding` SHALL 如实表达「本次 clamp 是否至少收紧了一项配额」：当曲线天花板在所有窗口所有动作上均不严于风控缩放后的档位配额时，`binding` MUST 为 false。投影 MUST NOT 在 `binding` 为 false 时宣称配额已被压低。

#### Scenario: 投影天数与 clamp 天数逐格相等

- **WHEN** 某账号开启慢启动、处于第 1 至第 8 天中任一天
- **THEN** 投影的 `day` 与该次 `effectiveQuotas()` 内 clamp 采用的天数 MUST 相等
- **AND** 第 8 天时投影 MUST 为毕业态且 clamp MUST 放行，两者同时发生

#### Scenario: 曲线不比档位更严时如实标注

- **WHEN** 某小红书账号处于 conservative 档、开启慢启动且处于第 5 至 7 天，此时曲线上界在 view / like / comment / publish 上均不低于该档位配额
- **THEN** `binding` MUST 为 false
- **AND** 投影 MUST NOT 表述为「配额已被压低」

### Requirement: 慢启动起点写入时对齐运营自然日

写入 `slow_start_since` 时 MUST 将其对齐到该时刻所属运营自然日（上海时区）的起点，使勾选当天整天计为第 1 天。天数递进与「今日进展」计数窗口 MUST 同相，MUST NOT 出现「上限已按新的一天放开、而当日计数尚未清零」的窗口。

#### Scenario: 深夜勾选不在次日夜间跳档

- **WHEN** 运营于某日 23:50 开启某账号慢启动
- **THEN** `slow_start_since` 存为该日 00:00（上海时区）
- **AND** 次日 23:51 该账号仍处于第 2 天（自次日 00:00 起即为第 2 天），MUST NOT 在当日计数未清零时把上限抬到下一天的天花板

#### Scenario: 天数换档与计数清零同时发生

- **WHEN** 某开启慢启动的账号跨过运营自然日边界
- **THEN** 其 `day` 递增与当日计数窗口清零 MUST 发生在同一时刻
