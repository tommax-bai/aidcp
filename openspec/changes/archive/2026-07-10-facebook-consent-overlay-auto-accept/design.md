## Context

Facebook 接入在边缘是一条**独立于小红书浏览闭环**的处理线：Facebook 平台驱动的能力集刻意不含 `browse`，评论 / 加群走独立执行器，不复用浏览 loop（`../aidcp-edge/src/facebook/driver.ts:22-25`）。这条线上每次动作提交前都会跑一道浮层探针：`../aidcp-edge/src/facebook/probes/gated-submit.ts:265-268`（提交前 `classifyFacebookOverlay`，浮层 ≠ `none` 即中止）与 `../aidcp-edge/src/facebook/join-executor.ts:275-285`（`probeNow()` → captcha/unknown/login 各自阻断原因）。

浮层类别复用通用定义 `OverlayKind = 'none' | 'login' | 'captcha' | 'dismissible' | 'unknown'`（`../aidcp-edge/src/browse/overlay-monitor.ts:34`）。但 Facebook 专属分类器 `classifyFacebookOverlayFromSignals`（`../aidcp-edge/src/facebook/overlay.ts:10-42`）只产出 `captcha / login / unknown / none`，**从不产出同意条这一类**。于是 cookie 同意浮层落进两种坏结局：其正文含「登录 Facebook」字样可能命中 login 分支正则（`overlay.ts:27-31`）被误判成 `login` → 动作被误报 `login_required` / `blocked_by_login` 中止；即便判 `none`，模态仍盖在页面上挡住真正的评论 / 加群点击 → `no_target`。

同意浮层与验证码性质相反：验证码是风控挑战，fail-closed、交既有远程协助（`captcha-incident-handling` spec，只对 `captcha`/`unknown` 生效，`../aidcp-edge/src/browse/overlay-report-gate.ts:18/38`），同意浮层明确在其射程之外；同意浮层是每个真人首次访问都会点掉的合规横幅，自动点掉才是拟人行为。拟人点击基建已存在（`../aidcp-edge/src/browse/captcha-assist.ts` 的 `dispatchClick` + humanize：贝塞尔 / 过冲 / 落点抖动 / 停留）。

## Goals / Non-Goals

**Goals:**
- Facebook 浮层分类器新增 `consent` 类别，靠稳定语义锚点识别，并修正判定优先级消除「登录 Facebook」误判碰撞。
- Facebook 动作前对 `consent` 做边缘本地拟人自动接受，点完后置校验确认浮层消失、页面可交互。
- 失败诚实回执（`blocked_by_consent` / `no_target`）、有界重试后升级；全程不假成功。
- 复用既有拟人点击基建，不新增协议消息、不加云端角色、不引入云端 LLM。

**Non-Goals:**
- 不做「关闭任意模态」的通用 dismisser（会点穿真门 / 验证码）。
- 不改验证码远程协助 `captcha-incident-handling`（同意条不进该链路、不上报为 blocking、不暂停会话）。
- 不改平台驱动接口 `platform-runtime-abstraction`。
- 不碰 Electron 主窗口的**原生**权限弹窗处理器（`../aidcp-edge/src/electron/main.cjs:758`）——那是不同浏览器、不同层，与页面内 DOM 同意浮层无关。
- 不动小红书通用分类器 `buildClassifyOverlayJs`（本 change 仅改 Facebook 专属分类器）。

## Decisions

### 决策 1（已定稿）：专门的同意浮层探测器，**不**扩共享 `OverlayKind`、**不**改 4 类分类器
实装采用 `src/facebook/consent.ts` 一个独立模块：纯判定 `classifyFacebookConsentFromSignals` + CDP 探测 `detectFacebookConsent` + 拟人接受器 `acceptFacebookConsent`，与既有 `classifyFacebookOverlayFromSignals`（4 类：captcha/login/unknown/none）分层平行、互不侵入。
- **为何不扩共享 `OverlayKind`（`browse/overlay-monitor.ts`）**：那是小红书浏览闭环与 Facebook 共享的热点类型，扩它会牵动 `OverlayMonitor` 接口（`state`/`probeNow` 返回 `OverlayKind`）与所有穷举消费点，且并行有多个 FB / overlay change 在改邻近文件——按 §7 单写者纪律应避让。专门探测器把同意条完全收在 `src/facebook/`，冲突面最小。
- **为何不复用 `dismissible`**：`dismissible` 语义是「运营 / 营销弹窗，有关闭按钮可关」，动作是点关闭；同意条动作是「点接受主按钮」+ accept-all/necessary-only 策略 + 严格后置校验，语义与动作都不同。
- **为何无需改 4 类分类器**：自动接受作为「动作前 pre-clear 一步」置于 `classifyFacebookOverlay` 之前——同意条在分类器看到它之前已被清掉，故分类器保持 4 类不变（既有 `overlay.test.ts` 零回归，含 `text:'登录 Facebook'→login` 那条）。若探测器漏判（Facebook 改文案），退化为今日行为（分类器可能判 login），不比现状更差。
- **消费点**：`gated-submit` preflight（classify 前）、`join-executor.joinGroup`（`blockingReason` 前）、`comment-executor.blockingReason`（`probeNow` 前）三处 fresh 复检卡点前置调用；各自 reason 联合类型加 `blocked_by_consent`（无穷举 never 检查，新增安全）。consent **不**计入阻断类别、不暂停会话、不上报云端、不进验证码远程协助。

### 决策 2：识别只锁语义锚点，判定优先级 captcha > 真登录门 > consent
在 `classifyFacebookOverlayFromSignals` 中，于 captcha 分支之后、login 分支之前（或将 login 分支收紧为「URL 命中登录/恢复路径 且 无 cookie 接受特征」）插入 consent 判定。
- consent 命中条件：正文含 cookie 政策语义（「Cookie 政策」/「允许…Cookie」/「Allow…cookies」）**且**存在接受按钮文案（「允许所有 Cookie」/「Allow all cookies」/「仅允许必要 Cookie」/「Only allow essential cookies」）**且** URL 非登录 / 验证门。
- login 分支收紧：真登录门以 URL（`/login`、`/checkpoint`、`/recover`）为主信号，避免同意条正文「登录 Facebook」字样触发纯文案匹配。
- **为何不锁 class**：Facebook class 名哈希 / 轮转，锁 class 一改版即失效；按钮可见文案 / aria-label / `[data-testid]`（若稳定）跨改版更稳，符合项目反混淆理念。
- **为何不引入云端 LLM**：同意条 DOM 指纹稳定、本地确定性判定召回高、误报低，且在热路径（动作前），符合 `overlay-monitor.ts` 既定理念。

### 决策 3：自动接受是「动作前 pre-clear 一步」，边缘本地闭环，无新协议
在 `gated-submit` preflight 与 `join-executor` 的阻断判定处，遇 `consent` 不再直接返回阻断，而是先调用一个新的边缘本地 `acceptFacebookConsent(cdp, policy)`：定位接受按钮 → 拟人点击 → 复探确认清除。清除成功则视作 `none` 放行原动作；失败则返回 `blocked_by_consent`。
- **为何不走云端命令**：零决策的固定动作，走云→边命令要新增 MessageType + 协议四处同步 + 边缘 onMessage 白名单，纯负担无收益。edge 本地一步最省。
- **可选遥测**：可沿用现有边→云状态 / 日志通道记「已自动接受同意」，但 MUST NOT 作为 blocking 浮层上报、不路由验证码协助、不暂停会话。

### 决策 4：策略开关用 env flag，默认 accept-all
新增 env 开关（如 `AIDCP_FB_COOKIE_CONSENT=accept_all|necessary_only`，默认 `accept_all`）。
- **为何默认 accept-all**：最低摩擦、最常见真人路径、会话最稳（拒绝非必要有时改变站点行为）；necessary-only 作为隐私保守选项可切。
- **为何不做成协议 / 角色配置**：低频、低风险的运营策略，env flag 足够，YAGNI。

### 决策 5：后置校验 + 有界重试 + 诚实回执
点击后复探（`classifyFacebookOverlay` 再跑一次）：仍为 `consent` 则重试，最多 N 次（如 2–3 次，每次带拟人间隔）；到上限仍在则停手，返回 `blocked_by_consent` 升级。按钮定位失败直接返回 `no_target`，绝不乱点其他按钮。所有失败路径都诚实回报，绝不谎报 `ok`（红线：MUST NOT 静默假成功）。

## Risks / Trade-offs

- **[误点真门 / 验证码风险]** → 自动接受严格只对 `consent` 触发；识别要求「同时命中 cookie 政策语义 + 接受按钮文案 + 非登录/验证 URL」三条；优先级保证 captcha / 真登录门先胜出。绝不实现通用「关任意模态」。
- **[Facebook 文案 / 布局按地区与 AB 漂移]** → 锚点用多语言按钮文案 / aria 集合（中英至少），并保留 `[data-testid]` 备选；定位失败即诚实 `no_target`，不猜点。上线后按真机反馈补锚点。
- **[「登录 Facebook」字样误判碰撞]** → login 分支收紧为 URL 主信号 + consent 优先在 login 之前判；补单测：含「登录 Facebook」字样的同意条必须判 `consent` 而非 `login`。
- **[点击后横幅异步消失 / 页面重排]** → 后置校验带短暂等待 + 复探，而非点完即认成功；仍在则重试而非误判成功。
- **[重复弹窗 / 死循环]** → 有界重试上限；cookie 接受写入 AdsPower 持久 profile，通常一个环境只需处理一次，重试上限兜住异常反复弹的情况。
- **[与并发 change 的热点碰撞]** → 本 change 只改 Facebook 专属文件（`facebook/overlay.ts`、`facebook/probes/gated-submit.ts`、`facebook/join-executor.ts`），不碰两份 `protocol.ts` / `command-bridge.ts` / 角色注册 / 风控状态机等串行热点；`OverlayKind` 联合类型新增值属低冲突改动，但与同期改浮层分类的 change 需协调（当前无同类活跃 change 触及 `facebook/overlay.ts`）。

## Migration Plan

- edge-only，无 ECS 部署；改动落 `aidcp-edge`，本地 `npm run typecheck` + `npm test`（新增分类器与自动接受单测，jsdom 桩脱离浏览器）+ `npm run test:acceptance`（红线不回归）。
- 回滚：env 开关可关闭自动接受（回落为「遇 consent 即诚实 `blocked_by_consent` 中止」的保守行为，不再误判 login）；代码层面 revert 分类器与 pre-clear 一步即可。
- 真机验收登记到 `docs/real-machine-acceptance-backlog.md`：新环境首开 Facebook 触发同意条 → 自动接受 → 评论 / 加群不再卡；含「登录 Facebook」字样不误判；真验证码不被误点。

## Open Questions

- 接受按钮的权威多语言文案 / `[data-testid]` 集合以真机 DOM 为准（首版给中英常见文案，真机补齐）。
- necessary-only 是否有运营需求，抑或长期只用 accept-all（默认 accept-all，开关先留）。
- 是否需要一条轻量遥测让后台可见「本环境已自动接受同意」（可选，非阻断，不进本 change 硬需求）。
