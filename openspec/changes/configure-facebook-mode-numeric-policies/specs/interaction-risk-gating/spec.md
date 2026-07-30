## MODIFIED Requirements

### Requirement: 配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）

云端 SHALL 保留两条显式、互不合成的慢启动路径：

1. 历史 env 全局旁路：仅当 `AIDCP_COLDSTART_RAMP=true` 时，按账号 `created_at` 启用历史冷启动爬坡；默认与 `RiskController` 类默认均为关。
2. 环境级慢启动：仅当账号当前唯一绑定环境的 `client_environments.slow_start_since` 非 NULL 且同一环境持有有效 `slow_start_policy_revision_id` 时，对该环境当前账号启用；起点与七日数字分别取环境自身 anchor 和该生命周期 pin 的不可变 revision。

anchor 解析 MUST 严格按「当前环境设置优先，否则才考虑历史旁路」：当前唯一绑定环境起点与 policy pin 均有效 → 使用该环境七日策略；否则 env 全局旁路开且账号 `created_at` 存在 → 使用既有代码历史曲线；否则不叠 clamp。两条路径的起点 MUST NOT 以 OR / AND / min 或任何其它方式合成。环境起点存在但 policy pin 缺失、未知、陈旧、不完整或 schema 不兼容时 MUST 产生具名 unavailable blocker 并停止新的平台动作，MUST NOT 回落历史曲线、全局当前 revision 或编译期 Facebook 表。

环境慢启动的起点 MUST NOT 取 `accounts.created_at` 或 `accounts.slow_start_since`。前者只是账号第一次连上本云端库的时刻；后者是迁移前遗留数据。部署切换后两者均 MUST NOT 成为环境级开关的运行时事实源。

环境慢启动第 1 至第 7 天 MUST 使用开启时 pin revision 的每日值，并按既有公式派生 minute/hour 天花板。全局发布新 revision MUST NOT 改写在途环境的 pin、day、since 或额度；关闭后再次开启才 pin 届时全局当前 revision。环境换绑账号 MUST 保留环境起点与 pin。

`AIDCP_SLOW_START_DISABLED=true` MUST 作为全局停用闸：置真时无视所有环境级慢启动设置与历史 env 旁路、全体不叠 clamp，且对外投影 MUST 如实标注该原因。

冷启动天花板的平台曲线选择 MUST 建立在已确认的平台之上。账号平台无法确认时 MUST NOT 回落到任一平台曲线，MUST 不叠 clamp并如实标注不可用原因。

慢启动是 `effectiveQuotas()` 的输入，不是账号风控状态：它 MUST NOT 写入 `risk_state`、MUST NOT 经 `setQuotaLevel` / `applySignal` 或风控终态单写链，MUST NOT 改变账号威胁态。安全限额数字、warned/restricted/frozen 语义和重启防 burst 静默期均 MUST 保持不变。每个窗口每个动作的最终额度 SHALL 继续取风控缩放/显式配置与 pin 策略派生天花板中的更小值。

同一账号若异常映射到多个环境，运行时 MUST NOT 任取某个环境的设置，也 MUST NOT把某个环境设置永久复制到账号。系统 SHALL 报出可诊断的绑定冲突并停止声称某个环境设置已对该账号生效；不得自动删除或重写绑定来掩盖异常。

#### Scenario: 新号默认按安全配额浏览、不被冷启动压低

- **WHEN** 某 Facebook 账号所在环境的 `slow_start_since` 为 NULL、`AIDCP_COLDSTART_RAMP` 未设为 `true`
- **THEN** 其 day 窗口配额等于该账号风控档位的安全限额，MUST NOT 因账号年龄或旧账号字段被冷启动压低

#### Scenario: 冷启动全局路径仅在显式 opt-in 时生效

- **WHEN** 运维显式设 `AIDCP_COLDSTART_RAMP=true`，且当前环境未开启慢启动
- **THEN** 历史爬坡按账号 `created_at` 起点生效，`effectiveQuotas() = min(历史冷启动当日天花板, 风控缩放安全限额)`

#### Scenario: 环境级慢启动独立于全局开关生效

- **WHEN** `AIDCP_COLDSTART_RAMP` 未设为 `true`，但账号当前唯一绑定环境的 `slow_start_since` 为 3 天前且 pin revision 有效
- **THEN** 该账号 `effectiveQuotas() = min(pin 策略第 4 天派生天花板, 风控缩放安全限额)`
- **AND** 其它未开启环境的账号逐位不受影响

#### Scenario: 发布新曲线不热改在途环境

- **WHEN** 某环境按 revision 3 处于慢启动第 4 天，此时全局当前发布为 revision 4
- **THEN** 该环境第 4 至第 7 天继续使用 revision 3
- **AND** 之后新开启的环境使用 revision 4

#### Scenario: 环境换号后设置留在环境

- **WHEN** 已开启慢启动的环境从账号 A 换绑为账号 B，两个账号的 controller 均已缓存
- **THEN** 账号 B 下一次 `effectiveQuotas()` 使用该环境原起点与原 pin revision，账号 A 下一次调用不再使用它们
- **AND** MUST NOT 重启进程、驱逐 controller 或把起点/pin 写入账号 B

#### Scenario: 账号移动到另一环境后采用目标环境设置

- **WHEN** 账号 A 从已开启慢启动的环境 E1 移到未开启的环境 E2
- **THEN** 账号 A 不再受 E1 起点与 pin 影响，按 E2 的关闭态计算
- **AND** E1 的起点与 pin 逐位保留，供 E1 之后绑定的新账号使用

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

- **WHEN** 某环境在同一事务写入或清空 `slow_start_since` 与 active policy pin，而当前账号的 `RiskController` 已存在
- **THEN** 同一实例的下一次 `effectiveQuotas()` MUST 反映新环境生命周期真态

#### Scenario: pin 缺失或不可读时失败关闭

- **WHEN** 环境 `slow_start_since` 非 NULL，但其 policy pin 缺失、引用不存在、镜像陈旧、payload 不完整或 schema 不兼容
- **THEN** Cloud 停止该账号新的平台动作并暴露具名 blocker
- **AND** MUST NOT 回落全局当前、历史曲线或编译期 Facebook 数字

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

- **WHEN** 某环境的慢启动被开启、关闭、换绑账号或全局发布新数字
- **THEN** 涉及账号的 `risk_state.status` 与 `quotaLevel` MUST 逐位不变，MUST NOT 触发风控状态迁移

### Requirement: 慢启动状态投影必须与实际 clamp 同源同格

云端对外投影的慢启动状态（`state` / `day` / `binding` / `eligible` / `ineligibleReason`）、active policy revision、完整七日策略，以及 `applyColdStartClamp` 实际采用的天数、平台准入结论、revision 与数字 MUST 由同一个慢启动上下文解析函数和同一次时钟读取得出，MUST NOT 各自独立计算。环境级路径 SHALL 从当前唯一绑定环境的 anchor 与 active pin 解析；历史 `AIDCP_COLDSTART_RAMP=true` 路径 SHALL 从账号 `created_at` 与既有历史曲线解析。两条 anchor 路径 MUST 使用同一平台准入判定，但 MUST NOT 合成 anchor、revision 或曲线。任何“投影来自环境 A、clamp 来自环境 B”“投影 revision 与 clamp revision 不同”“投影说不适用但 clamp 仍在生效”或“投影第 7 天、clamp 已按第 8 天放行”的错位 MUST 不可能出现。

平台准入闸 MUST 在选择或应用任何慢启动曲线之前同时约束投影与 clamp，且与 anchor 来源无关。慢启动 SHALL 只对白名单内且已确认的平台生效；平台不在白名单内时，投影 MUST 返回 `eligible=false`、`ineligibleReason=platform_unsupported` 与 `binding=false`，平台未知时 MUST 返回对应的 `platform_unknown` 不可用原因。两种情况的 `applyColdStartClamp` 均 MUST 原样返回风控缩放后的安全配额，MUST NOT 叠加 Facebook、小红书或其它平台曲线。实现 MUST NOT 通过为个别动作增加豁免来近似平台级准入；准入不通过即整体不 clamp，避免遗漏动作或未来新增动作被静默夹为 0。

环境级 Facebook 慢启动的 `state`、`day`、active policy revision、完整七日策略与每个窗口每个动作的派生天花板 SHALL 全部来自本次解析所得的同一个 active pin。全局 current revision 只能作为之后开启采用的独立事实，MUST NOT 与 active revision 拼接。环境 anchor 存在但 active pin 缺失、未知、陈旧、不完整或 schema 不兼容时，投影 MUST 返回具名 policy unavailable，新的平台动作 MUST 停止，MUST NOT 回落历史曲线、全局 current revision 或编译期 Facebook 表。

`binding` SHALL 如实表达本次 clamp 是否至少收紧一项风控缩放后的配额。当曲线在所有窗口所有动作上均不严于风控缩放后的安全配额时，`binding` MUST 为 false，投影 MUST NOT 表述为配额已被压低。平台明确不支持时 `binding` MUST 为 false；没有当前账号、绑定有歧义、平台未知或 pin/策略不可用时，投影 MUST NOT 返回肯定的 `binding` 或生效配额，其中 policy unavailable MUST NOT 被伪装成 `binding=false`。环境未绑定账号时允许返回环境配置的 `state/day/since`、active revision 与完整七日策略，但 MUST 同时标注 `binding_unknown` 并与 controller 生效投影区分。

平台准入闸只关闭慢启动 clamp 这一条通路，MUST NOT 改变账号的风控档位缩放、显式 quota、限频计数、风险状态或其它安全闸。把一个平台加入慢启动白名单必须是显式代码或配置能力变更，纳入后投影与 clamp MUST 同时开始生效，不得出现只生效一半的中间态。

#### Scenario: 投影天数版本与 clamp 逐格相等

- **WHEN** 某账号唯一绑定的 Facebook 环境开启慢启动、处于第 1 至第 8 天中任一天
- **THEN** 投影的 `day`、平台准入、active revision 与该次 `effectiveQuotas()` 内 clamp 采用的天数、准入结论、revision 和数字逐位相等
- **AND** 第 8 天时投影毕业且 clamp 同时放行

#### Scenario: 历史旁路与环境路径共用平台准入

- **WHEN** 同一已确认平台分别由环境 anchor+pin 路径和 `AIDCP_COLDSTART_RAMP=true` 历史路径进入慢启动判断
- **THEN** 两条路径使用同一个平台白名单与同一次解析结果驱动各自投影和 clamp
- **AND** MUST NOT 合成两个 anchor、把历史曲线冒充 active revision 或让旁路绕过平台准入

#### Scenario: 历史旁路下白名单外平台整体不 clamp

- **WHEN** `AIDCP_COLDSTART_RAMP=true`，某视频号账号入库 1 天，而视频号不在慢启动平台白名单内
- **THEN** 投影返回 `eligible=false`、`ineligibleReason=platform_unsupported`、`binding=false`
- **AND** `effectiveQuotas()` 逐位等于风控缩放后的安全配额，`comment` 与 `dm_reply` MUST NOT 被夹成 0

#### Scenario: 环境路径下白名单外平台同样整体不 clamp

- **WHEN** 一个白名单外平台的环境存在慢启动 anchor
- **THEN** 投影返回平台不支持且 `binding=false`，`applyColdStartClamp` 原样返回风控缩放后的安全配额
- **AND** MUST NOT 因该路径带有环境配置就选择 Facebook、小红书或任意其它曲线

#### Scenario: 白名单内平台继续采用各自权威曲线

- **WHEN** Facebook 环境持有完整 active pin，或小红书账号经历史旁路处于慢启动窗口内
- **THEN** Facebook 使用该 active revision 的对应日数字，小红书使用其既有权威曲线
- **AND** 二者均继续逐动作计算 `min(慢启动派生天花板, 风控缩放安全配额)`

#### Scenario: 未绑定环境不编造生效状态

- **WHEN** 环境已开启慢启动但当前没有有效账号绑定
- **THEN** 投影可返回环境配置的起点、天数、active revision 与完整七日策略，但 MUST 标注 `binding_unknown`
- **AND** MUST NOT 返回 `binding=true`、当日最终生效配额或“已压低”表述

#### Scenario: 曲线不比档位更严时如实标注

- **WHEN** 当前账号 pin 策略的当日派生上界在所有窗口所有动作上均不严于风控缩放后的档位配额
- **THEN** `binding` MUST 为 false，投影 MUST NOT 表述为配额已被压低

#### Scenario: 策略不可读不是关闭态

- **WHEN** 环境起点存在但 active revision 或完整策略不可读
- **THEN** 投影显示 revision/policy unavailable 并停止新的平台动作
- **AND** MUST NOT 返回 `state=off`、`binding=false` 或编译期默认日表

### Requirement: 每日配额派生的分钟窗口采用十分之一密度

云端将每日配额派生为内置分钟窗口或慢启动分钟天花板时，SHALL 对每个动作使用 `daily <= 0 ? 0 : max(1, min(MINUTE_BURST_CAP[action], ceil(daily / 10)))`。小时窗口与每日窗口 MUST 保持既有公式和值不变。

合法的 `quota_config.per_minute` 显式覆盖 SHALL 继续优先于档位内置派生值；慢启动 SHALL 使用 active policy revision 的 `dailyCap` 派生分钟天花板，再与风控缩放后的分钟值逐动作取更小值，MUST NOT 因数字策略越过更严格的账号档位或显式覆盖。

#### Scenario: 非默认慢启动浏览值按十分之一派生

- **WHEN** Facebook 环境 active revision 的当日 `view.dailyCap=37`，且账号风控缩放后的浏览分钟上限不低于 4
- **THEN** 慢启动派生的浏览分钟天花板为 4，最终 `effectiveQuotas().minute.view` 为 4
- **AND** 浏览每日上限仍为 37，小时上限仍按既有小时公式计算

#### Scenario: 零额度与突发硬上限保持不变

- **WHEN** 某动作 `dailyCap` 为 0，或按 `ceil(daily / 10)` 计算出的值超过该动作 `MINUTE_BURST_CAP`
- **THEN** 零额度的分钟值仍为 0，超出值仍被夹到对应突发硬上限

#### Scenario: 显式分钟覆盖仍然优先

- **WHEN** 某档位动作存在合法的 `quota_config.per_minute` 覆盖
- **THEN** 该档位基准分钟值采用显式覆盖而不是从每日值派生
- **AND** 若慢启动 active policy 派生的分钟天花板更严格，最终值仍取两者中更小者
