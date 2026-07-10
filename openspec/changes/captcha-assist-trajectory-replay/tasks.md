## 1. 协议同步（串行、单写者，勿与他人并行碰 protocol.ts）

- [ ] 1.1 `aidcp-edge/src/comm/protocol.ts`：新增 `CaptchaAssistTrajectorySamplePayload{x,y,t}` 与 `CaptchaAssistTrajectoryPayload{v; samples[]; clicks:number[]}`；`CaptchaAssistClickPayload` 加 `trajectory?`；`CaptchaAssistClickResultPayload` 加 `replayMode?: 'trajectory'|'synthetic'`。
- [ ] 1.2 `aidcp-cloud/src/comm/protocol.ts`：逐字镜像 1.1 全部改动。
- [ ] 1.3 `docs/protocol.md`：更新 `captcha.assist.click` 示例与说明（"points 权威 / 轨迹供移动时序 / edge 须钳制采样数与时长并叠抖动 / press 前补 move 到权威点"），`click_result` 加 `replayMode`。无新增 MessageType，头部计数与 §2 表不变。
- [ ] 1.4 加两份 `protocol.ts` 结构镜像回归断言，弥补 `Record<MessageType,true>` 的字段级盲区（字段漂移 typecheck 抓不到）。

## 2. aidcp-edge — 回放

- [ ] 2.1 新增 `src/humanize/trajectory-replay.ts`：纯函数 sanitize（去零 `dt`、`Δt` clamp 长停顿而非等比压缩、样本数上限、坐标 ±1px 亚像素）+ 注入 random/sleep，脱 CDP 可单测（比照 `mouse-path.ts`）。
- [ ] 2.2 `browse/captcha-assist.ts` `handleClick` 增 trajectory 分支：有效→`replayTrajectory`，否则走合成路径（`captcha-assist-humanize-click`）；复用现有 crop 缩放、settle、reprobe、click_result 尾部。
- [ ] 2.3 回放几何：落点取 `points[i]` 缩放坐标；`clicks[i]` 定 press 时机；**每次 press 前补一帧 `mouseMoved` 到 `points[i]`**；`clicks.length !== points.length` 或下标越界→丢 trajectory 回落合成。
- [ ] 2.4 `browse/cdp-util.ts` 复用/补 `mouseMoved` + press/release 原语供逐帧派发。
- [ ] 2.5 回放模式记进 `click_result.replayMode`（trajectory|synthetic）；丢弃轨迹时日志标注原因（可观测、非静默）。
- [ ] 2.6 单测：sanitize 钳制与确定性（注入 random）、`replayTrajectory` 对 fake CDP 产出预期事件序列（mouseMoved 数、press 前有 move 到权威点、press/release 落在 `points` 坐标与正确时机）、无轨迹回落合成、clicks 长度不符/越界诚实回落、空轨迹不硬回放。

## 3. aidcp-cloud — 透传与守卫

- [ ] 3.1 `comm/captcha-assist.ts` `submitClick` 入参加 `trajectory`：sanitize（降采样/单调化/时长上限），有效才外发、丢弃记原因并保留 `points` 继续（可观测计数）。
- [ ] 3.2 `panel/panel-server.ts` `/click` 路由解析 + 校验可选 `trajectory`（`samples` 为 `{x,y,t:number}[]`、`clicks` 为 `number[]`），非数组畸形 400、可救透传由 `submitClick` 钳制。
- [ ] 3.3 `panel/types.ts` 扩展 `submitClick` 入参签名。
- [ ] 3.4 单测：submitClick 转发已 sanitize 轨迹、超量降采样、畸形丢弃且 `points` 保留 + 计数、panel 路由解析、`replayMode` 随 click_result 透出。

## 4. aidcp-console — 采集

- [ ] 4.1 `pages/CaptchaAssistPage.tsx`：stage 上 `pointermove` 节流采样 `{x,y,t}`（与 `onImageClick` 同一元素 rect 基准，`t` 相对首样本）+ `pointerdown` 记 `clicks` 下标；客户端缓冲上限（超则降采样）；`snapshotId` 变更连同 points 一起重置；`canClick` 假不采样。
- [ ] 4.2 submit 把 `trajectory` 放进 POST body；`types/api.ts` 补请求侧类型（仅请求侧、无新枚举，无白屏风险）。
- [ ] 4.3 组件测：采样归一化基准与 points 一致、clicks 对齐、`snapshotId` 变更重置。

## 5. 回归与部署

- [ ] 5.1 edge + cloud `npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿（AC-PROTO-* 两份 protocol.ts 不漂移）。
- [ ] 5.2 声明协助期间浏览会话暂停语义 + 确认回放窗口不与浏览/身份监测子系统争用同一 CDP、且不阻塞入站命令/心跳。
- [ ] 5.3 三仓 land + tasks.md 回写 sha；dev 部署 cloud + console；真机验收登记 backlog（处理页实采轨迹→原机回放通过率 / 是否二次触发风控，按 `replayMode` 分组看效果）。
- [ ] 5.4 `openspec validate captcha-assist-trajectory-replay --strict` 通过。
