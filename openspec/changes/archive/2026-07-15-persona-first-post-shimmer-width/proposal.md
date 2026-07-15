## Why

首轮预期文字的流光带目前只占容器宽度 42%，经过单行信息时覆盖范围偏短，视觉存在感不足，不容易让用户注意到“20 条 → 1 条”的预期表达。

## What Changes

- 将文字流光带宽度从 42% 放大到 72%。
- 保持 2800ms 播放时长、2680ms 启动点、颜色、运动方向和 reduced-motion 行为不变。
- 不改变卡片结构、文案、触发条件或 CTA 链路。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 扩大首轮预期横向流光的覆盖范围。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`
- `aidcp-edge/test/electron/fleet-console.test.ts`
