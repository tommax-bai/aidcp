## Why

验证码远程协助链只有**鼠标**能力（截图 → 标点位 → 拟人回放点击 → fresh 复检）。运营遇到**模糊数字图片类字符识别码**时，协助页上没有任何地方能键入答案——这类验证码在协助页上是**结构性无解**的，只能弃疗或去机器旁人工处置。

同一批调研另外坐实两件事：

1. **协助页右上角的「远程桌面」按钮背后什么都没有**。`AIDCP_REMOTE_ADDR` 全仓只有 2 行源码（edge `main.ts:188` / `wechat-channels/runtime.ts:137`），无 `.env.example`、无文档、无 GUI 入口，从未被填过；console 直接把该字符串当 `href`；飞书卡打一行「远程地址」。**系统自身不提供任何远程桌面能力**，这只是一个放第三方工具链接的空位，其真机验收自 2026-06-21 起 DEFERRED 至今。⇒ 一直被当作「协助不了就走远程桌面」的那条后路**从未点亮过一次**，键入能力没有任何可以推诿的兜底。

2. **点击链路今天就有 4 个诚实缺陷**（在 3–8s 的点击窗口下潜伏，在 10–20s 的键入窗口下会变成常发）：手点「刷新」绕过 K=3 直接上报 `risk.captcha_cleared`；Enter 提交导航 → 探针抛 → **解对的验证码被报成 `failed`**；`sendRiskCleared` 排在 `sendClickResult` 之后 + 断连即抛 ⇒ 解决了的验证码永不到云端、账号无限期暗着；租约只在受理时查一次、无中途 checkpoint。

## What Changes

- **验证码答案键入**：在既有 `captcha.assist.click` 载荷上做 additive optional 扩展（`text?` + `submit?:'enter'`），运营在协助页先点中输入框（1 个落点）再键入答案，边缘用**真实键盘事件**逐字拟人输入并回车提交。**不新增 MessageType**（沿用 `captcha-assist-trajectory-replay` 的 additive 先例）⇒ 边缘主动命令白名单、云端暂停穿透白名单、`docs/protocol.md` 计数三处**全不动**。
- **诚实取证回执**：新增 `no_target` status + `inputMode?` + `typeReport?`（焦点分级 / 清空三态 / 实际派发字符数 / 回读三态 / 是否提交）。运营 MUST 能区分「答案打错了」与「字根本没打进去」。
- **授权面不变**：键入与点击共用**同一条**授权路径（incident 级 scoped token），**不新增身份闸**。协助页从飞书卡点开即可键入——那正是这条链的设计意图，而键入受的约束比点击更紧（只进已聚焦元素 / 仅 24 个 ASCII 可见字符 / 无修饰键与功能键 / 仅在遮罩确认仍在的窗口内）。
- **BREAKING（内部契约）：移除「远程桌面」入口**。删 console 按钮、飞书卡「远程地址」行、edge 两处 env 读取、两份 `protocol.ts` 的 `EdgeHelloPayload.remoteAddr` 及云端 session / incident / panel types 的连带字段。**无外部消费方**（该字段从未被填过），风险为零。
- **准入前置：先修点击链路的 4 个既存诚实缺陷**（可独立合并验证）。
- **反检测红线**：MUST NOT 复用现有逐字输入函数——它内部是逐字符文本插入、**零 keydown/keyup**，「键事件数与字符数不匹配」是厂商成熟判据，而验证码正是其主战场；且它是 FB 发帖 / XHS 搜索 / FB 评论四处的热点依赖。新建 captcha 专用键盘原语。
- **补偿控制**：本 change 走「扩载荷」而非「新消息类型」，`Record<MessageType,true>` 穷举守卫抓不到字段级漂移 ⇒ 必须补两份 `protocol.ts` 的逐字段往返断言（AC-PROTO-07，继 `WelcomePayload.pacing` 之后第二例，写成可复用模板）+ panel HTTP 边界透传断言。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: 增加「远程协助可键入验证码答案」的合同（键入前提 / 焦点分级诚实 / 拟人键盘 / 清空与回读顺序 / 序列中途复检 / 答案明文数据边界 / 跨版本 fail-closed / 协助键入的身份要求）；收紧 `risk.captcha_cleared` 的所有权（补上 `handleCapture` 这个唯一漏网之鱼）；修正「提交后判据不可得」的诚实语义；**移除「保留远程桌面处置文案」条款**（前提已不存在）。

## Impact

- **aidcp-edge**：新建 `src/browse/captcha-type.ts`（ASCII 键位表 / 真 keyDown+keyUp 逐字派发 / 焦点三态探针 / 强制清空 / 机会性回读）；`src/browse/captcha-assist.ts`（task 0 四修 + 键入接线 + 中途复检 ×2 + 有界重试判据）；新建 `src/client/build-capabilities.ts`（构建能力位收进 `EdgeClient` 构造函数，两条装配路径都拿不掉）；`src/comm/protocol.ts` 字段 + 移除 `remoteAddr`；`src/main.ts` 透传 taskId 构造 checkpoint、移除 env 读取；`src/wechat-channels/runtime.ts` 移除 env 读取。
- **aidcp-cloud**：`src/comm/protocol.ts` 逐字一致；`src/comm/captcha-assist.ts`（文本校验 / v1 形状闸 / 能力 fail-closed 闸 / 版本偏斜检测 / 答案明文边界 / 移除 remoteAddr）；`src/comm/captcha-coordinator.ts`（删飞书卡「远程地址」行）；`src/panel/panel-server.ts`（透传 + 错误码穷举表）；`src/panel/types.ts`；`src/comm/ws-server.ts` / `handler.ts` 的 session.remoteAddr 连带清理。
- **aidcp-console**：`src/pages/CaptchaAssistPage.tsx`（答案输入框 + pin 触发扩到键入 + `lastResult` Record 表 + 三句人话展示 + **删「远程桌面」按钮**）；`src/types/api.ts` 手抄镜像同步。
- **aidcp（中控）**：`docs/protocol.md` 两段 jsonc（顺手修 `:757` click 样例漏 `taskId`）；spec delta。顺手修 `spec.md:18` 已腐烂的「消息数断言均为 44」（实测 91）。
- **协议**：动 **3 处**（两份 `protocol.ts` + `docs/protocol.md` 语义段）。**MessageType 总数 91 不变** ⇒ 两份 `protocol-contract.test.ts` 的穷举与计数断言不动；边缘主动命令白名单（`edge-client.ts:679`）与云端暂停穿透白名单（`ws-server.ts:217`）**均已放行 `captcha.assist.click`，不动**。`command-bridge` 与 `action.completed` 动作名**不适用**（assist 直接推 envelope、不发 action.completed）。
- **热点文件单写者**：两份 `protocol.ts`、cloud `src/comm/captcha-assist.ts`、`CaptchaAssistPage.tsx` —— 与活跃 change `captcha-assist-base-url-self-proof`（0/37，未 land）语义正交但同碰文件，**必须串行**。
- **部署**：dev 部署 cloud + console。**edge 需出一次包 + 逐台运营机换装才能真机验收**（能力闸 fail-closed ⇒ 合并后到装包前该能力一直是暗的）。
- **依赖/顺序**：task 0（既存诚实缺陷）为准入、可独立合并；classifier 扩词表**非准入**（用户报障的模糊数字图片类已能被检出——是在协助页上看见的），仅在后续发现漏检时作为条件项。
