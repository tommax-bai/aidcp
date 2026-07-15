## Why

首作引导现有庆祝段在弹窗出现后立即启动，840ms 内完成放大，用户刚开始阅读时动作已经接近结束，感知过快。随后“20 条 → 1 条”使用轻抬升和缩放聚焦，形成了用户不希望看到的弹跳感，且 640ms 持续时间不足以形成稳定注意力。

## What Changes

- 弹窗出现后先留出短暂停顿，再以约 1.4 秒完成吉祥物放大与归位。
- 撒花与吉祥物同步延后并延长，保持围绕吉祥物单次展开。
- 移除首轮预期文字的位移与缩放，改为约 1.7 秒的青绿到暖色流光横向扫过。
- 流光在吉祥物结束后再停顿约 320ms 才开始；全部动效仍只播放一次。
- `prefers-reduced-motion` 下关闭吉祥物、撒花和流光动画。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 放慢首作庆祝节奏，并将首轮预期强调从弹跳改为长时流光。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`
- `aidcp-edge/test/electron/fleet-console.test.ts`
- 不改变弹窗结构、触发条件、CTA 或首作运行链路。
