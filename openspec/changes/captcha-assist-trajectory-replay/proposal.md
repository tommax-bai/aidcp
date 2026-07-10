## Why

验证码远程协助现在只上送 ≤2 个离散落点，边缘用合成路径逐点点击——这是运营响应链（检测→协助→清除）里唯一还在用合成输入的一环，且落在风控最敏感的验证码现场。采集运营在处理页的**真实鼠标轨迹**并复刻到原浏览器，把"人类怎么移动的"这一最难合成的信号带回现场，抬高人工协助通过率、降低协助后二次触发风控的概率。落点仍由离散点权威决定（映射精度与今天一致），轨迹只贡献"怎么移动（HOW）"与"何时按下（WHEN）"。无轨迹或轨迹无效时诚实回落到 `captcha-assist-humanize-click` 的合成路径。

## What Changes

- 控制台在协助页画面上采集运营真实鼠标轨迹（节流采样归一化坐标 + 相对时间戳），随既有 `/click` 一并上送。
- 协议在既有 `captcha.assist.click` 命令上做 **additive optional** 扩展（不新增 MessageType）：`CaptchaAssistClickPayload` 增可选 `trajectory`（`{ v; samples:{x,y,t}[]; clicks:number[] }`）。
- 边缘按 crop 缩放逐帧 `mouseMoved` 回放轨迹，保留（带安全钳制的）相对时序；**落点始终取权威离散点，样本仅供移动与时序**。
- **每次 `mousePressed` 前必须补一帧 `mouseMoved` 到该权威落点**，保证 mousedown 坐标 == 最后 mousemove 坐标，消除"mousedown 无前驱 move"的瞬移伪影（否则比现合成路径更可检测）。
- `clicks[i]` 对齐 `points[i]` 的按下时机；`clicks.length` 必须等于 `points.length`，按样本下标建 press 查找表、允许 clicks 非单调；不满足即丢 trajectory、诚实回落合成。
- **缩时语义定死为"只裁剪长停顿（Δt clamp）"**，MUST NOT 等比压缩总时长（避免超人速度）。
- 云端 `submitClick` + panel `/click` 路由 + `panel/types.ts` 三处透传 `trajectory` 并 sanitize（采样数/单调/总时长/坐标/clicks 越界钳制）；**丢弃 trajectory 时产生可观测日志/计数**，绝不静默丢。
- 反检测悖论对冲：回放前 sanitize + 帧间 `dt` 叠对数正态抖动 + 坐标 ±1px 亚像素；不做 verbatim 原样重放、不做"过均匀重采样"（后者反成伪影）。
- 度量：`captcha.assist.click_result` 增最小 `replayMode`（`trajectory | synthetic`）回执，让 cloud/console 能把结果（cleared/still_blocked）与所用模式关联，衡量本变更成效。
- 红线保持：回放中途抛错→如实回 `failed`；轨迹无效→回落合成但日志标 `synthetic`，绝不谎称用了轨迹。风控语义零改。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: 增加"远程协助可复刻运营真实鼠标轨迹"的合同（采集/协议扩展/边缘回放几何与时序约束/诚实回落/可观测丢弃/度量回执）。

## Impact

- `aidcp-console`: `pages/CaptchaAssistPage.tsx`（stage 上 `pointermove` 节流采样 + `pointerdown` 记 clicks 下标；缓冲上限；`snapshotId` 变更时连同 points 一起重置；`canClick` 假不采样；submit 带 trajectory）、`types/api.ts` 补请求侧类型。
- `aidcp-cloud`: `comm/protocol.ts` 镜像新字段、`comm/captcha-assist.ts`（submitClick sanitize+透传、可观测丢弃）、`panel/panel-server.ts`（`/click` 解析校验）、`panel/types.ts`。
- `aidcp-edge`: `comm/protocol.ts` 逐字镜像、新增 `humanize/trajectory-replay.ts`（纯函数 sanitize+timing，注入 random/sleep，脱 CDP 单测）、`browse/captcha-assist.ts`（handleClick 增 trajectory 分支，press 前补 move 到权威点）、`browse/cdp-util.ts`（复用/补 move+press 原语）。
- 协议：动 **3 处**（两份 `protocol.ts` 逐字一致 + `docs/protocol.md` 的 `captcha.assist.click` 示例与"点权威/轨迹供移动时序/edge 钳制+抖动"说明）。**第 4 处 edge onMessage 白名单无需改**——trajectory 是既有 `captcha.assist.click` 的可选字段、非新主动命令（`edge-client.ts:540` 已放行）；command-bridge 动作映射不涉及（assist 直接推 envelope）。字段级漂移 typecheck 抓不到（`Record<MessageType,true>` 只穷举消息类型），须加两份 `protocol.ts` 结构镜像回归断言。
- 部署：dev 部署 cloud + console；edge 真机在运营机 pull 后生效。真机验收：处理页实采轨迹→原机回放通过率/是否二次触发风控。
- 依赖/顺序：依赖 `captcha-assist-humanize-click` 作为无轨迹兜底；与其及 `captcha-assist-live-snapshot` 同碰热点 `protocol.ts` / `captcha-assist.ts`（两侧）/ `CaptchaAssistPage.tsx`，须串行、单写者。
