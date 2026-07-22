## ADDED Requirements

### Requirement: 搜索按既成平台事实接入账号风险单写路径

`search` SHALL 是 `RiskAction` 的完整成员，受 `RiskController.explain/canDo/record`、分钟/小时滑动窗口、Asia/Shanghai 自然日窗口、配额配置、风控状态缩放与可选慢启动控制。搜索下发前 SHALL 由 Cloud 权威 `RiskController` 预闸；Edge 证明 `actuated=true` 后，回执 SHALL 无条件驱动同一控制器记录事实，MUST NOT 在回执阶段二次 `canDo` 后丢弃证据。Cloud `RiskController` 仍是最终账号风险状态和计数的单写者。

#### Scenario: 搜索预闸阻止尚未发生的动作

- **WHEN** 自治搜索意图产生，但该账号 `search` 的任一配额窗口已饱和
- **THEN** Cloud 不下发搜索命令，并回报/记录具体配额拒因

#### Scenario: 已发生搜索不因配额到顶而丢证据

- **WHEN** Edge 回报一次 `actuated=true` 的搜索，而该账号回执时 search 配额已饱和
- **THEN** `RiskController.record('search')` 仍把该事实写入计数，后续预闸据此拒绝更多搜索

#### Scenario: 操作员搜索绕过权限闸但仍计数

- **WHEN** 操作员明确授权一次搜索，产品规则允许其绕过自动配额预闸，且 Edge 证明平台动作已发生
- **THEN** 该搜索照常记入账号 search 计数；“操作员全权”MUST NOT 被解释为免记事实

### Requirement: 搜索配额参与配置、投影与慢启动全量映射

`RISK_ACTIONS` 的所有穷举映射 SHALL 包含 search，包括三档 daily 默认、minute/hour burst、`quota_config` 读写与校验、effective quota、daily usage、dashboard action totals、慢启动区间、restricted/frozen 清零和 PG action 约束。任一配额提供者缺值或非法 SHALL 回落 search 代码默认，MUST NOT 抛错或静默放开。

#### Scenario: 配额热更新立即影响搜索预闸

- **WHEN** 运营通过既有配额配置端点修改某档位 search 的 daily/minute/hour 数值
- **THEN** 对应账号后续 `RiskController.canDo('search')` 现读新值，无需进程重启

#### Scenario: PG 可持久保存 search 事实

- **WHEN** Cloud 记录一次已执行搜索
- **THEN** `risk_counters` 的 action 约束接受 `search`，今日聚合与窗口查询可读到该事实

