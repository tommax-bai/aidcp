## 1. 协议同步（串行、单写者，勿与他人并行碰 protocol.ts）

- [ ] 1.1 `aidcp-edge/src/comm/protocol.ts`：`CaptchaAssistCapturePayload` 增 `live?: { intervalMs?; maxDurationMs?; maxFrames? }`。
- [ ] 1.2 `aidcp-cloud/src/comm/protocol.ts`：逐字镜像 `live` 字段。
- [ ] 1.3 `docs/protocol.md`：capture payload 补 live 语义 + "live 帧 snapshotId 语义"与"云端提交允许旧 snapshotId 的近期集窗口"说明。无新增 MessageType，头部计数与 §2 表不变。

## 2. aidcp-edge — 实时循环与帧环

- [ ] 2.1 `browse/captcha-assist.ts`：`snapshots` 由 `Map<incidentId,单条>` 改为每 incident 最近 N（=4）帧环；`handleClick` 按 `snapshotId` 环内查、找不到才 `stale_snapshot`，命中则用该帧自己的 crop 缩放坐标。
- [ ] 2.2 新增 `startLive`/`stopLive` + per-incident 循环状态（timer、迭代计数、maxDuration 截止、`lastPushedHash`、`clicking` 标志）。
- [ ] 2.3 tick：`clicking` 或有 capture 在跑→跳过（互斥）；`probeBlockingKind`→仍挡则 `captureSnapshot` + 便宜哈希，与 `lastPushedHash` 不同才 push；**最小推帧间隔硬地板 + 单帧字节/帧率上限**兜底动画页去重失效。
- [ ] 2.4 自主 `not_blocked` 需**连续 K 次确认 + 最小 settle**才停循环并触发清除路径；单次 probe 未见遮罩 MUST NOT 立即发 `risk.captcha_cleared`；自主 probe 结果**不经 `click_result` 混入 `lastResult`**。
- [ ] 2.5 `handleCapture` 带 `live` 时启动 `startLive`；`handleClick` 全程 `clicking=true`（finally 清）暂停 tick；incident `cleared`/`expired`/`stopLive` 时清循环防孤儿。
- [ ] 2.6 循环收敛用注入 timer + 迭代计数，遵 `edge-poll-helpers-iteration-bounded`（不拿 `now()` 当终止条件）。
- [ ] 2.7 单测：去重（同帧不推/变帧推新 snapshotId）、速率地板兜底动画页、自主 not_blocked 需连续 K 次才清除（单次不清）、自主探测不写 lastResult、`clicking` 暂停 tick、LRU 命中旧 snapshotId 点击落对坐标、循环三重有界不死循环、孤儿清理。

## 3. aidcp-cloud — 编排、近期帧集与守卫

- [ ] 3.1 `comm/captcha-assist.ts`：`requestCapture` 组包带 `live`（默认/env `AIDCP_CAPTCHA_LIVE_*`）；`onDetected` 与手动刷新经 `requestCapture` 自然重新武装。
- [ ] 3.2 **保留每 incident 最近 N 帧集**；`submitClick` 的 `snapshot_mismatch` 守卫放宽为 `snapshotId ∈ 近期集`（否则边缘帧环死代码、白跑不降反升）。
- [ ] 3.3 `onSnapshot` 增 `cleared`/`expired` 守卫（忽略迟到帧、不复活为 `ready`）；可选派生 `liveUntil`。
- [ ] 3.4 **实时窗口绑运营在场**：以控制台既有轮询/GET 作为在场信号 re-arm capture，而非盲目固定窗口。
- [ ] 3.5 单测：`cleared` 后迟到 snapshot 不复活、capture 带 live 字段、近期集内旧 snapshotId 提交放行、超出近期集判 `stale_snapshot`、在场信号 re-arm。

## 4. aidcp-console — 选点冻结与活体展示

- [ ] 4.1 `pages/CaptchaAssistPage.tsx`：第 1 点落下即 pin 当前帧（image+snapshotId），冻结期不换画面、清点 `useEffect`（现 90-92）不触发；提交/清空后解冻采纳最新帧；提交用 pinned `snapshotId`。
- [ ] 4.2 区分"周期自刷新（同挑战）"与"内容实质改变（换问题）"：后者给显式"挑战已变、请重看"提示 + "刷新到最新帧"手动解冻按钮，不静默冻结旧帧让运营点错。
- [ ] 4.3 加"实时"指示（读 `liveUntil`）；轮询 cadence 保持或微降（帧新鲜度由边缘推送保证）；`types/api.ts` 若加 `liveUntil` 同步。
- [ ] 4.4 组件测：冻结期换帧不冲掉选点、内容实质改变时给提示而非静默沿用旧帧。

## 5. 回归与部署

- [ ] 5.1 edge + cloud `npm run typecheck` 双绿（两份 protocol.ts 不漂移） + `npm run test:acceptance` 保 AC-PROTO-* / AC-RISK-*。
- [ ] 5.2 CDP 争用核对：实时截图循环与 overlay-monitor 后台轮询、看门狗、身份监测跨组件不互相拖垮（高频 `captureScreenshot` 比 evaluate 重）。
- [ ] 5.3 三仓 land + tasks.md 回写 sha；dev 部署 cloud + console；edge 真机在运营机 pull 后生效。
- [ ] 5.4 真机验收登记 backlog：多步/换图两类真实点选验证码下活体帧更新与选点冻结、白跑率下降；确认自主清除不误解 restricted。
- [ ] 5.5 `openspec validate captcha-assist-live-snapshot --strict` 通过。
