## ADDED Requirements

### Requirement: 每日配额派生的分钟窗口采用十分之一密度

云端将每日配额派生为内置分钟窗口或慢启动分钟天花板时，SHALL 对每个动作使用 `daily <= 0 ? 0 : max(1, min(MINUTE_BURST_CAP[action], ceil(daily / 10)))`。小时窗口与每日窗口 MUST 保持既有公式和值不变。

合法的 `quota_config.per_minute` 显式覆盖 SHALL 继续优先于档位内置派生值；慢启动 SHALL 继续把派生出的分钟天花板与风控缩放后的分钟值逐动作取更小值，MUST NOT 因新公式越过更严格的账号档位或显式覆盖。

#### Scenario: Facebook 慢启动第一天浏览分钟天花板为二

- **WHEN** Facebook 环境处于慢启动第 1 天，曲线的浏览每日上限为 20，且账号风控缩放后的浏览分钟上限不低于 2
- **THEN** 慢启动派生的浏览分钟天花板为 2，最终 `effectiveQuotas().minute.view` 为 2
- **AND** 浏览每日上限仍为 20，小时上限仍按既有小时公式计算

#### Scenario: 零额度与突发硬上限保持不变

- **WHEN** 某动作每日额度为 0，或按 `ceil(daily / 10)` 计算出的值超过该动作 `MINUTE_BURST_CAP`
- **THEN** 零额度的分钟值仍为 0，超出值仍被夹到对应突发硬上限

#### Scenario: 显式分钟覆盖仍然优先

- **WHEN** 某档位动作存在合法的 `quota_config.per_minute` 覆盖
- **THEN** 该档位基准分钟值采用显式覆盖而不是从每日值派生
- **AND** 若慢启动分钟天花板更严格，最终值仍取两者中更小者
