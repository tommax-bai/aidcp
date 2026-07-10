## Why

验证码交互中现场会自变（定时自刷新、"一点就换新图/新问题"的多步点选），但边缘只在初检/手动刷新/点击后三时机抓帧，处理页看到的是陈旧快照。运营对着过期图点会被 `snapshotId` 陈旧守卫挡回（白跑一趟、非点错），但每次白跑都拖长账号 `restricted` 停摆、增加复检往返、拉低协助成功率。目标：incident 处于可交互态时边缘按有界低帧率自动重抓、内容变才推新帧，让运营总看到活体挑战。

**范围界定（红队校正）**：本变更服务**自刷新 / 多步换图的点选类**验证码。滑块/旋转/拖拽类**不在范围**——当前交互模型是 ≤2 个离散落点 + 单击，无拖拽原语，把流畅滑块动画推给运营只会诱发非人类瞬移落点；滑块须靠 `captcha-assist-trajectory-replay` 的轨迹 + 未来的拖拽原语，另行立项。

## What Changes

- 复用既有 `captcha.assist.capture` 命令 + 可选 `live` 字段进入有界实时抓帧（不新增 MessageType、不动 edge onMessage 白名单）；退出靠边缘三重自终止（时长/帧数上限 + 遮罩消失）+ 终端态，无需独立 stop 命令。
- 边缘实时循环：可交互态时按有界低帧率（clamp 区间）`probe → 抓帧 → 内容去重后 push`；`clicking` 互斥暂停 tick；用注入 timer + 迭代计数收敛（遵 `edge-poll-helpers-iteration-bounded`，绝不拿 `now()` 当终止条件）。
- **去重加最小推帧间隔硬地板 + 单帧字节/帧率上限**：带倒计时/动画的验证码页精确哈希永不命中会导致全速推大图，速率闸兜底成本。
- **陈旧守卫两端配套放宽（关键接线）**：边缘保留每 incident 最近 N 帧环，**云端也保留最近 N 帧集**，`submitClick` 的 `snapshot_mismatch` 守卫放宽为"`snapshotId ∈ 近期集"——否则实时开启后运营提交被云端上游拦死、白跑不降反升，边缘帧环成死代码。
- **自主清除必须连续确认（关键红线）**：实时循环单次 probe 看不到遮罩 MUST NOT 立即发 `risk.captcha_cleared`；多步验证码在旧挑战消失、新挑战未绘出之间有瞬时无遮罩窗口，需连续 K 次确认 + 最小 settle 才允许自主判 cleared，避免提前解 `restricted` 的自残。
- **自主探测结果不混入运营点击回执**：实时循环的 probe 结果 MUST NOT 经 `click_result` 混进 `incident.lastResult`，保审计诚实（前端"上次复检"不显示非运营发起的结果）。
- `onSnapshot` 增 `cleared`/`expired` 守卫：迟到实时帧 MUST NOT 把已清除态复活为 `ready`（修既有隐患）。
- **实时窗口绑运营在场**：复用控制台既有轮询作为免费在场信号 re-arm 抓帧，而非盲目固定 45s（远程运营常在检测数分钟后才开页，盲目窗口在到场前就自终止）。
- **控制台选点期冻结 + 多步换图区分**：运营放下第 1 个点即 pin 当前帧、冻结期不换显示画面/不清点；但"挑战内容实质改变（换问题）"MUST NOT 一味静默冻结旧帧让运营点错——需区分"周期自刷新（同挑战）"与"内容实质改变"，后者给显式"挑战已变、请重看"提示。
- 红线保持：诚实回执（`stale_snapshot` / `still_blocked` / `failed`）、风控语义（detected→restricted、cleared 不自动回 normal）不变。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: 增加"可交互态近实时回传现场帧"合同；并修订"点击 snapshot 绑定"为近期帧集、"恢复由 edge 复检清除驱动"为自主清除需连续确认且自主探测不混入运营回执。

## Impact

- `aidcp-edge`: `comm/protocol.ts`（capture payload 加 `live`）、`browse/captcha-assist.ts`（`snapshots` 改每 incident 最近 N 帧环、`startLive`/`stopLive` + 循环状态、tick 去重与自终止、`clicking` 互斥、`handleClick` 按 snapshotId 环内查）。
- `aidcp-cloud`: `comm/protocol.ts` 同步 `live` 字段、`comm/captcha-assist.ts`（`requestCapture` 带 live、**保留最近 N 帧集并放宽 `submitClick` 守卫**、`onSnapshot` cleared/expired 守卫、自主 probe 结果与运营 click_result 分离、可选派生 `liveUntil`）。
- `aidcp-console`: `pages/CaptchaAssistPage.tsx`（选点期冻结、多步换图显式提示、"刷新到最新帧"手动解冻、在场信号 re-arm）、`types/api.ts`（若加 `liveUntil`）。
- 协议：动 **3 处**（两份 `protocol.ts` 的 `CaptchaAssistCapturePayload` 加 `live?` 逐字一致 + `docs/protocol.md` 补 live 语义与"云端提交允许旧 snapshotId 窗口"说明）。**不新增 MessageType**、不动白名单（`capture` 已放行）、不涉及 command-bridge。
- 部署：dev 部署 cloud + console；edge 真机在运营机 pull 后生效。真机验收：多步/换图两类真实点选验证码下活体帧更新与选点冻结、白跑率下降。
- 依赖/顺序：与 `captcha-assist-humanize-click`、`captcha-assist-trajectory-replay` 同碰热点 `protocol.ts` / `captcha-assist.ts`（两侧）/ `CaptchaAssistPage.tsx`，须串行、单写者；云端最近帧集可与轨迹变更共用同一改动，宜在其后落。
