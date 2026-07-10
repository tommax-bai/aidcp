## Why

验证码远程协助把运营的离散落点注入原浏览器时，用的是**刻意削弱的合成路径**：`dispatchClick(cdp, x, y, { jitter:0, overshoot:false, moveDelayMs:6 })`（`aidcp-edge/src/browse/captcha-assist.ts:136`）——比日常浏览点击（默认 `jitter:3` + overshoot + 略慢移动）还机械。而验证码恰恰是平台反爬审查最严、且**专门用鼠标轨迹熵（速度剖面、路径曲率、落点抖动、overshoot-and-correct、落点前 dwell、点间时距方差、光标连续性）做指纹**的场景。本系统已有成熟的贝塞尔 + ease-in-out + overshoot 拟人配方（`aidcp-edge/src/humanize/mouse-path.ts`），却在最该用的地方把它关了，等于自废武功。

本变更把协助注入点击的合成拟人度提到**不低于日常点击**，全部落在边缘执行层，复用既有 `mouse-path` / `timing` / `feed-scroller` 范式，不发明新机制、不动协议。它同时是 `captcha-assist-trajectory-replay`（真实轨迹回放）在缺轨迹时的**兜底层**。

## What Changes

- 协助注入点击恢复到不低于日常点击的合成拟人度：贝塞尔路径 + 适度 overshoot 概率 + 小幅落点 jitter + 落点前读图 dwell + 点间对数正态停顿。
- **多点之间保持光标连续**：把上一点的真实落点作为下一点的移动起点（复用 `feed-scroller` 的 `lastCursor` 范式），消除"每点从随机点瞬移冒出"这一强 bot 信号。
- **逐帧移动延迟必须带抖动**（不得是固定周期）：现状每帧 `mouseMoved` 等间隔会让事件间 `dt` 方差为 0，本身是强 bot 信号——按轻量对数正态抖每帧延迟。
- **节奏分布参数按 `edgeId` 派生每机偏置**，避免全 fleet 逐字相同的节奏常量自成"车队级指纹"。
- 所有随机与停顿走可注入随机源，保证桩测确定性。
- 红线保持：`settle → reprobe → cleared / still_blocked / failed / 回传新截图` 的诚实回执整段不改；找不到目标/失败如实回报，绝不静默假成功。风控语义（detected→restricted、cleared 不自动回 normal）不变。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: 增加"协助注入点击必须达到不低于日常点击的合成拟人度"的合同（光标连续、逐帧 dt 抖动、每机偏置、诚实回执不变）。

## Impact

- `aidcp-edge`: `browse/captcha-assist.ts`（handleClick 循环重写）、`browse/cdp-util.ts`（`DispatchClickOptions` 增落点前 dwell 缝、`dispatchClick` 返回真实落点供光标连续）、`humanize/` 复用 `timing`/`mouse-path`，配套单测。
- `aidcp-cloud`: 无（协助点击由 `CaptchaAssistService` 直接推 envelope，不经 command-bridge；坐标缩放/时序是边缘执行细节）。
- `aidcp-console`: 无（运营仍只提交离散归一化落点，拟人化是边缘细节）。
- 协议：不动。不新增/删除 MessageType，不加 cloud→edge 主动命令，`edge onMessage` 白名单与两份 `protocol.ts`、`docs/protocol.md` 全不触碰。
- 部署：edge-only，无 ECS cloud 部署；真机核在运营机 pull 后生效，登记真机验收 backlog（协助点击拟人度肉眼观察 + 是否降低验证码复现/被拒）。
- 依赖/顺序：与 `captcha-assist-trajectory-replay`、`captcha-assist-live-snapshot` 同碰 `browse/captcha-assist.ts` 热点文件，须串行；本变更为轨迹回放的兜底层，应先落。
