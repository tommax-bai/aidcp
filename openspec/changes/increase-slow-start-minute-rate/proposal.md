## Why

当前从每日上限派生分钟突发上限时使用 `ceil(daily / 20)`，使 Facebook 慢启动第 1 天的浏览上限 `20/day` 被压为 `1/minute`。需要把通用派生密度提高到 `ceil(daily / 10)`，在不放宽每日总量和既有突发硬上限的前提下允许更高的分钟内吞吐。

## What Changes

- 将 `deriveWindowQuotasFromDaily()` 的分钟窗口派生分母从 `20` 改为 `10`，保留零额度为零、非零额度至少为一以及 `MINUTE_BURST_CAP` 夹逼。
- 让该公式同时作用于缺少 `quota_config` 覆盖时的档位默认分钟值，以及慢启动每日曲线派生出的分钟天花板。
- 保持每日上限、小时窗口公式、显式 `quota_config.per_minute` 覆盖、风控状态缩放及慢启动逐位取更严值的语义不变。
- 增加精确回归测试，锁定 Facebook 慢启动第 1 天浏览从 `1/minute` 调整为 `2/minute`，并覆盖通用派生、零值和突发硬上限。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `interaction-risk-gating`: 修改每日配额向默认分钟突发窗口与慢启动分钟天花板的派生密度。

## Impact

- Cloud 风控配额计算：`aidcp-cloud/src/risk/quotas.ts`。
- Cloud 风控与慢启动测试；不涉及协议、数据库迁移、Console/Edge 接口或 UI。
- 对 `quota_config` 中没有合法分钟覆盖的档位/动作，默认分钟值可能提高；已有合法 `per_minute` 覆盖仍保持权威。
