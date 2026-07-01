## Why

浏览闭环在「离页巡视/深读后返回」时会一脚踩回一条 `xsec_token` 已失效的旧笔记详情页，触发小红书反爬错误页 `error_code=300031「当前笔记暂时无法浏览」`。这一瞬的坏页被旁路遮罩监测的形状启发式误判为账号级 `unknown` 风控，边缘随即上报 `risk.captcha_detected`，云端把账号打成 `warned` 并暂停整台边缘下发（`sent=0`），且 `warned` 持久化、不自动回滚——一次瞬时坏页闪现换来整会话停摆 + 账号被无谓标黄。

事故实证：account `66cd1d4f000000001d0314ee` / edge `ads-k1e0awu5`，2026-07-01 19:39:00，序列「开笔记（读正常）→ 开通知 → 返回」后云端记 `captcha detected kind=unknown status=warned url=/explore`，边缘 TCP 仍连接但被暂停至今。

## What Changes

- **根因·返回导航修复**：把「返回时是否走浏览器后退」的判据从「按 URL 猜是不是作者主页」升级成「返回时头上是否盖着笔记浮层」这一语义判据。凡是**无浮层的整页离页返回**（通知 / 作者主页 / 未来任何整页跳转）一律**直接前向导航回来源列表**，永不经浏览器后退回踩到 token 已失效的笔记详情，从源头消灭 300031 闪现。「笔记浮层盖在列表上」这条正常返回仍用浏览器后退以保住滚动位。既有「落错页→整页导航回 feed」健康校验兜底原样保留当安全网。
- **纵深防御·低置信 unknown 上报加一轮持续性确认**：边缘对最低置信的 `unknown` 阻断遮罩不再第一轮探测差异就上报云端；延后约一个轮询周期再核对，仍为 `unknown` 才发 `risk.captcha_detected`。瞬时（一闪而过）的 `unknown` 不上报、不迁移账号状态、不产生无配对的 `cleared`。**验证码指纹类 / 登录墙保持即时 fail-CLOSED，秒报秒停，安全不弱化。**
- 自愈时自动上报 `risk.captcha_cleared` 已存在，不新写，仅补「只有发过 `detected` 才发 `cleared`」的配对不变量。
- **无新能力、无破坏性变更。** 代码只落 `aidcp-edge` 一仓；`aidcp-cloud` 零改动；两份 `protocol.ts` 与消息类型不动（不触发 AC-PROTO）。

## Capabilities

### New Capabilities
<!-- 无新增能力：本 change 是对既有两个 spec 的行为加固 -->

### Modified Capabilities
- `browse-loop-resilience`: 新增「无浮层的整页离页返回 MUST 直连来源列表、不得经浏览器后退回踩到 token 已失效的笔记详情页」这一要求（返回不落坏页），与既有「落地后对 404/坏页自愈、看门狗有界 idle」互补——本条管「不落到坏页」，既有条款管「万一落了也不死锁」。
- `captcha-incident-handling`: 新增「边缘对低置信 `unknown` 阻断遮罩的云端上报 MUST 经一轮持续性确认；单轮瞬时 `unknown` MUST NOT 上报、MUST NOT 迁移账号状态；`captcha`/`login` 指纹类 MUST 保持即时 fail-CLOSED」，并补钉「瞬时阻断自愈时自动 `cleared`、且 MUST NOT 产生孤儿 `cleared`」不变量。云端 kind→signal→state 映射、暂停/恢复语义不变。

## Impact

- **代码**：仅 `aidcp-edge`。
  - `src/browse/browse-session.ts:1364-1396`（`navigateBack` 返回手势三分支重写，用现成 `modalCtrl.isModalOpen()` 探浮层）。
  - `src/main.ts`（约 412-445 行 `watcherSupervisor` overlay 上报分支：`unknown` 上报前加一轮持续性确认 + `detected`/`cleared` 配对位；`captcha`/`login` 即时不变）。
- **协议 / 云端**：零改动。两份 `src/comm/protocol.ts`、`docs/protocol.md`、`command-bridge`、主动命令白名单均不动。`aidcp-cloud` 只是收到更少、更准的 `unknown` 上报。
- **风控安全红线**：不碰 `interaction-risk-gating` 的 kind→signal→state 映射（其映射正确，修复在其上游）；不弱化真验证码 / 未授权发布相关的 AC-RISK/AC-PUB 路径。
- **回归**：`aidcp-edge` `npm run test:acceptance`（AC-PROTO/AC-RISK 需仍全绿）→ `npm test` → `npm run typecheck`。
- **真机验收（gated）**：真机分身跑「开笔记→开通知→返回」，确认无 300031 闪现、地址栏直接回 `/explore`、云端收不到 `captcha_detected`、账号维持 `normal`；反向造持续遮罩确认真阻断照报、真滑块秒停。
