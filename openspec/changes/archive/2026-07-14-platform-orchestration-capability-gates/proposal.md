## Why

C1a 把编排能力矩阵砍到只保留有真消费者的 `browse` / `feed_refresh`，显式砍掉了当时零读点的 `follow` / `profile_visit` / `patrol` / `notification`。今天这四类对 Facebook 是**声明了没人读**的空转：12 个通知巡视角色对 FB 连接照常注册订阅（FB 不上报 `notification.detected` 所以事实上不触发），AuthorEvaluator/FollowAgent 对 FB 也照常挂着（FollowAgent 拿不到数据自然不发）。这是 cleanliness 而非 correctness——今天 FB 对这四类已诚实回 `capability_unsupported`、巡视角色纯 inert。

本变更把这四个能力词加回矩阵，并**同批接线它们的消费者**（不留「声明了没人读」的旧病）：按平台能力闸决定 AuthorEvaluator/FollowAgent 与 12 巡视角色是否注册。低优先，放在所有 Facebook 相关 change 稳定后走。

## What Changes

- `capabilities` 追加 `follow` / `profile_visit` / `patrol` / `notification`（Record 形状，与 C1a 一致）。
- 同批接线消费者：`RoleDispatcher.setup()` 按 `capabilities.patrol`/`notification` 决定 12 巡视角色是否注册；按 `capabilities.follow`/`profile_visit` 决定 AuthorEvaluator/FollowAgent 是否注册。
- **闸判据 fail-open**：仅显式 `supported===false` 才不注册；缺项 / 异常照今天注册（绝不因查表失败静默砍 XHS 巡视）。
- 补 XHS「12 巡视角色仍全注册」的注册快照断言，别把 XHS 回归推给零覆盖真机。

## Capabilities

### New Capabilities

- `platform-browse-surface`（延续 C1a）：编排能力矩阵扩到 follow/profile_visit/patrol/notification 并同批接线注册消费者，能力闸 fail-open。

## Impact

- Cloud dispatcher: `aidcp-cloud/src/orchestrator/role-dispatcher.ts`（`setup()` 角色注册闸；🔴 热点，与其他 FB change 串行）。
- Cloud registry: `aidcp-cloud/src/platform/registry.ts`（capabilities 追加四词）。
- 前置：C1a / C1b land。无协议改动；edge、console、数据库、`ol` 不受影响。XHS 阶段行为不变（fail-open + 显式 supported）。
