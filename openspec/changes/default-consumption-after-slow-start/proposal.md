# Change: default-consumption-after-slow-start

## Why

冷启动（慢启动）毕业后的回落模式目前写死为 `persona`（普通人设模式）：统一模式 API 选 `slow_start` 时、以及客户端建号默认开慢启动时，都把 resumable base 写成 `persona`。后果有二：

1. 用户期望「冷启动完成后默认进入消费模式」，现状不满足——毕业后回到人设浏览闭环，需要人手动切消费。
2. 毕业时若账号未绑人设，环境直接停摆（`no_persona` blocker）；回落消费模式不依赖人设，顺带消除这类停摆。

## What Changes

- **统一模式 API**：操作员选 `slow_start` 时，同事务写入的 resumable base 由 `persona` 改为 `consumption`。
- **建号完成路径**：`facebookOperationMode=slow_start`（含 legacy `slowStartEnabled`）建号时，初始 `base_mode` 写 `consumption`。
- **存量一次性迁移**：当前处于 active 慢启动且 `base_mode='persona'`（自动写入的旧默认）的环境翻为 `consumption`，逐行发新 policy revision + audit，并推进 `facebook_operation_policy` 镜像版本；`rule`（legacy 迁移保证）与非 active 环境一律不动。
- **不变**：慢启动生命周期权威、覆盖层语义（active ⇒ 生效 slow_start）、显式选 `persona`/`rule`/`consumption` 的行为、毕业判定与 sticky graduation、模式切换的 revision/计数器语义全部不变。已毕业且正在按 persona 运行的环境不回头翻动（可由操作员在后台自行切换）。

## Impact

- Affected specs: `facebook-operation-policy`（Mode and revision transitions）、`client-facebook-operation-policy`（provisioning resumable base）
- Affected code: `aidcp-api` 两处写点 + 迁移 0117；automation / edge / console 零改动（它们只消费存储的 base mode，无第二份回落实现）
- **共库注意**：迁移入账后，OL 侧 api 旧构建下次重启会被迁移契约门拦下（dev/OL 共库）。OL 需在下次重启前跟上包含 0117 的版本；OL 部署等用户明确要求。
