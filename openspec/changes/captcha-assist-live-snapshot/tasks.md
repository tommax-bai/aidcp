## 1. 协议同步（串行、单写者，勿与他人并行碰 protocol.ts）

- [x] 1.1 `aidcp-edge/src/comm/protocol.ts`：`CaptchaAssistCapturePayload` 增 `live?: { intervalMs?; maxDurationMs?; maxFrames? }`。
  <!-- aidcp-edge e73dd3e 未新增 MessageType，仅加可选字段 -->
- [x] 1.2 `aidcp-cloud/src/comm/protocol.ts`：逐字镜像 `live` 字段。
  <!-- aidcp-cloud 210183a verbatim 与 edge 一致 -->
- [x] 1.3 `docs/protocol.md`：capture payload 补 live 语义 + "live 帧 snapshotId 语义"与"云端提交允许旧 snapshotId 的近期集窗口"说明。无新增 MessageType，头部计数与 §2 表不变。
  <!-- aidcp 本提交 -->

## 2. aidcp-edge — 实时循环与帧环

- [x] 2.1 `browse/captcha-assist.ts`：`snapshots` 由 `Map<incidentId,单条>` 改为每 incident 最近 N（=8）帧环；`handleClick` 按 `snapshotId` 环内查、找不到才 `stale_snapshot`，命中则用该帧自己的 crop 缩放坐标。
- [x] 2.2 新增 `startLive`/`stopLive` + per-incident 循环状态（token、clearStreak、lastPushedHash、lastPushAt）。
- [x] 2.3 tick：`clicking`/`capturing` 互斥跳过→`probeBlockingKind`→仍挡则 `captureSnapshot` + FNV 哈希去重（+最小推帧间隔 600ms 地板 + 实时帧降质 quality=60）→变了才 push。
- [x] 2.4 自主 `not_blocked` 需连续 K=3 次确认才停循环 + 发 `risk.captcha_cleared`；单次 probe 未见遮罩不清除；自主结果**不经 `click_result`**（不污染 lastResult）。
- [x] 2.5 `handleCapture` 带 `live` 时启动 `startLive`；`handleClick` 全程 `clicking=true`(finally 清) 暂停 tick；`cleared` 时 `stopLive` 防孤儿。
- [x] 2.6 循环收敛用注入 sleep + for-loop maxFrames 上界 + token 抢占，遵 `edge-poll-helpers-iteration-bounded`（不拿 `now()` 当唯一终止条件）。
- [x] 2.7 单测：去重（同帧不推/变帧推新 snapshotId）、maxFrames 有界终止、自主 not_blocked 需连续 K 次才清除（单次/双次不清）、只发 risk_cleared 不发 click_result、帧环命中稍旧 snapshotId、环外判 stale。
  <!-- aidcp-edge e73dd3e edge full 879 绿 + acceptance AC-PROTO 绿 -->

## 3. aidcp-cloud — 编排、近期帧集与守卫

- [x] 3.1 `comm/captcha-assist.ts`：`requestCapture` 组包带 `live`（config/env）；`onDetected` 与手动刷新经 `requestCapture` 自然重新武装；置 `liveUntil`。
- [x] 3.2 保留每 incident 最近 N=5 帧 `snapshotId` 集；`submitClick` 的 `snapshot_mismatch` 守卫放宽为"最新 或 近期集内"。
- [x] 3.3 `onSnapshot` 增 `cleared`/`expired` 守卫（忽略迟到帧、不复活为 `ready`）；`liveUntil` 派生入 view。
- [x] 3.4 实时窗口绑运营在场：`noteViewerPresence` 在窗口到期时用 `keepStatus` re-arm（不 flicker）；panel GET 触达它。env `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED` 默认关（零回归）。
- [x] 3.5 单测：`cleared` 后迟到 snapshot 不复活、capture 带 live 字段+liveUntil、近期集内旧 snapshotId 放行、环外判 `stale`、presence 窗口到期才 re-arm、关闭恒 no-op。
  <!-- aidcp-cloud 210183a cloud full 1748 绿 + acceptance AC-PROTO/AC-RISK 绿；panel test 补 noteViewerPresence mock -->

## 4. aidcp-console — 选点冻结与活体展示

- [x] 4.1 `pages/CaptchaAssistPage.tsx`：第 1 点落下即 pin 当前帧（`pinned`），冻结期显示 pinned、不换画面/不清点；提交/清空/看最新才解冻；提交用 pinned `snapshotId`。
- [x] 4.2 冻结期实时帧推进到不同 snapshotId → 出「画面已更新，挑战可能已变」提示 + 「看最新画面」手动解冻按钮（不静默沿用旧帧）。
- [x] 4.3 轮询改为直到终态（不再 ready 停）以持续拉新帧 + 发在场信号；「实时」指示读 `liveUntil`；`types/api.ts` 加 `liveUntil`。
- [x] 4.4 组件测：冻结期新帧不冲掉选点、提交用被冻结帧、内容变给提示、看最新解冻清点。
  <!-- aidcp-console e63568c console full 90 绿 -->

## 5. 回归与部署

- [x] 5.1 edge + cloud `npm run typecheck` 双绿（两份 protocol.ts 不漂移） + `npm run test:acceptance` 保 AC-PROTO-* / AC-RISK-*。
  <!-- edge/cloud acceptance 全绿 -->
- [x] 5.2 CDP 争用核对：`clicking`/`capturing` 互斥 + 单 incident 单 token 循环 + 点击全程暂停 tick；实时循环只读截图。
- [x] 5.3 三仓 land + dev 部署 cloud + console；edge 真机在运营机 pull 后生效。
  <!-- landed: edge e73dd3e / cloud 210183a / console e63568c；dev 部署见收尾 -->
- [x] 5.4 真机验收登记 backlog（簇 35）：多步/换图两类真实点选验证码下活体帧更新与选点冻结、白跑率下降；确认自主清除不误解 restricted（env 开启 AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED 后核）。
- [x] 5.5 `openspec validate captcha-assist-live-snapshot --strict` 通过。
