## Why

首轮预期流光带已经加宽，但 2800ms 内完成整段横向扫过，实际观看仍然偏快，用户难以持续感知流光对“20 条 → 1 条”的强调。

## What Changes

- 将文字流光播放时长从 2800ms 延长到 5600ms，速度降低一半。
- 保持流光带宽度 72%、启动点 2680ms、颜色、运动路径和 reduced-motion 行为不变。
- 不改变卡片结构、文案、触发条件或 CTA 链路。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 将首轮预期流光速度降低一半。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`
- `aidcp-edge/test/electron/fleet-console.test.ts`
