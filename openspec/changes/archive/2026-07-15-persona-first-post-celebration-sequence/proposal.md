## Why

首作引导当前虽已有一次 `scale(1) → scale(1.09) → scale(1)` 与六粒撒花，但放大幅度、撒花起点和视觉密度都偏弱，用户实际看到时难以感知庆祝反馈。同时“首轮观察约 20 条推荐内容，通常筛出 1 条创作灵感”作为关键预期说明静态呈现，注意力容易停在吉祥物而略过这段信息。

## What Changes

- 将首次人设完成时的吉祥物单次放大峰值提高到 `scale(1.12)`，仍回到原尺寸、不循环、不漂浮。
- 让撒花从吉祥物周围向外展开，并适度增加粒子数量与可见度。
- 在吉祥物与撒花结束后短暂停顿，再让首轮预期整行播放一次轻抬升与青绿色聚焦动效。
- `prefers-reduced-motion` 下关闭两段动效与撒花，直接展示完整静态内容。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 调整首次首作引导的庆祝幅度与“20 条 → 1 条”预期说明的分段动效时序。

## Impact

- `aidcp-edge/src/electron/renderer/index.html`
- `aidcp-edge/src/electron/renderer/styles.css`
- `aidcp-edge/test/electron/fleet-console.test.ts`
- 不改变首次触发条件、CTA、浏览进度或首作生成链路。
