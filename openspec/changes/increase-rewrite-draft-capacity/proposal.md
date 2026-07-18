## Why

运营需要在同一账号下并行比较更多参照洗稿候选；现有全局生成帽默认 2、账号在途帽默认 3，会过早拒绝第三轮洗稿或在少量待审稿存在时阻断继续创作。

## What Changes

- 同账号自主生成（排期、飞书 `/publish`、自动扳机）继续保持单飞，同刻最多 1 轮。
- 全局生成并发帽默认值由 2 调整为 3，使容量空闲时同一账号最多可并行生成 3 篇不同来源的洗稿。
- 每账号在途帽默认值由 3 调整为 20，口径仍为“生成中 claim 数 + 已落库待审稿件数”。
- 保留现有同参照稿单飞、帽满同步诚实拒绝及 env 可覆盖能力。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `publish-generation-concurrency`: 调整全局生成并发帽与每账号在途帽的默认值，同时明确自主生成仍按账号单飞。

## Impact

- `aidcp-cloud/src/server.ts`：生产接线默认值。
- `aidcp-cloud/src/publish-agent/publish-scheduler.ts`：依赖缺省值与并发契约注释。
- `aidcp-cloud/test/publish-agent/publish-scheduler.test.ts`：默认容量及普通稿/洗稿组合回归。
- 与活跃 change `publish-claim-reject-defer-not-fail` 同触 `publish-scheduler.ts`；本 change 先串行完成并集成，后者须基于更新后的默认分支继续。
