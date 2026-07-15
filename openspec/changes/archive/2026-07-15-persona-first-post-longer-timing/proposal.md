## Why

首作引导的吉祥物 1400ms 缩放和 1700ms 文字流光仍然偏快，用户希望两段强调更从容、更容易被完整感知。

## What Changes

- 将吉祥物单次放大归位延长到 2100ms，保留 260ms 初始停顿和既有最大缩放。
- 将首轮预期横向流光延长到 2800ms。
- 将流光启动点顺延到 2680ms，继续保持吉祥物结束后约 320ms 的分段停顿。
- 不改变撒花时长、弹窗结构、触发条件、CTA 或首作运行链路。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 进一步延长首作庆祝和首轮预期流光的单次播放时长。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`
- `aidcp-edge/test/electron/fleet-console.test.ts`
