# Tasks — facebook-consent-overlay-auto-accept

> 全部落 `aidcp-edge`，edge-only，无 ECS 部署。热点只碰 Facebook 专属文件；**未动**两份 protocol.ts / command-bridge.ts / 角色注册 / 风控状态机 / 共享 `overlay-monitor.ts` 的 `OverlayKind`。
> 偏离说明：原设计设想「新增 `consent` 到共享 `OverlayKind`」，实装改为**专门的同意浮层探测器**（`src/facebook/consent.ts`），零碰共享热点、零改 4 类分类器（详见 design.md 决策 1）。全部落地于 edge master `d8a83ca`。

## 1. aidcp-edge — 同意浮层识别（专门探测器）

- [x] 1.1 新增 `src/facebook/consent.ts`：纯判定 `classifyFacebookConsentFromSignals`（优先级 captcha/登录门优先；present = cookie 政策文案 + 接受按钮 + 非登录 URL + 非验证码）。<!-- aidcp-edge d8a83ca -->
- [x] 1.2 只读 CDP 探测 `detectFacebookConsent`：`CONSENT_SCAN_JS` 采集 href / cookie 政策文案 / 验证码特征 / 接受按钮（accept-all + necessary-only）坐标，锚定可见文案 / aria，不锁哈希 class。<!-- aidcp-edge d8a83ca -->
- [x] 1.3 判定优先级：登录/验证 URL（`/login` `/checkpoint` `/recover` `/two_step_verification`）或验证码特征 → present=false；含「登录 Facebook」字样但有接受按钮 → present=true（不误判 login）。**未改 4 类分类器**，故 `overlay.test.ts` 零回归。<!-- aidcp-edge d8a83ca -->

## 2. aidcp-edge — 边缘本地拟人自动接受

- [x] 2.1 `acceptFacebookConsent(cdp, opts)`：按 policy 挑按钮 → 拟人点击 → 复探确认清除；返回 `{handled, cleared, attempts, reason?}`。<!-- aidcp-edge d8a83ca -->
- [x] 2.2 复用 `browse/cdp-util` 的 `dispatchClick`（内建鼠标路径 + 落点抖动 + 偶发 overshoot）；策略所需按钮缺失 → `no_target`，绝不改点另一个。<!-- aidcp-edge d8a83ca -->
- [x] 2.3 后置校验 + 有界重试（默认上限 3、settle 700ms）：仍在则重试，到上限 `blocked_by_consent` 升级；探测/点击异常不假成功。<!-- aidcp-edge d8a83ca -->
- [x] 2.4 env 开关 `AIDCP_FB_COOKIE_CONSENT`（`accept_all` 默认 / `necessary_only`），`facebookConsentPolicyFromEnv` + `defaultFacebookConsentAccepter` 收口一处。<!-- aidcp-edge d8a83ca -->

## 3. aidcp-edge — 接入动作前 pre-clear

- [x] 3.1 `src/facebook/probes/gated-submit.ts`：preflight 在 classify 前调 `acceptConsent`（可注入，默认 env 策略）；clear/无同意条 → 照常，`handled && !cleared` → `blocked_by_consent`（扩 `FacebookGatedSubmitPreflightReason`）。<!-- aidcp-edge d8a83ca -->
- [x] 3.2 `src/facebook/join-executor.ts`：`joinGroup` 导航后、`blockingReason` 前置 `acceptConsent`；清不掉 → `blocked_by_consent`（扩 `FacebookJoinReason`）。<!-- aidcp-edge d8a83ca -->
- [x] 3.3 `src/facebook/comment-executor.ts`：`blockingReason` 卡点前置 `acceptConsent`（4 处复检统一经此）；清不掉 → `blocked_by_consent`（扩 `FacebookCommentStepReason`）。<!-- aidcp-edge d8a83ca -->
- [x] 3.4 consent 处理**不**触发验证码远程协助、**不**上报 blocking、**不**暂停会话（未碰 `overlay-report-gate`）。三执行器加可注入 `acceptConsent` 依赖；`src/facebook/index.ts` 导出 consent。<!-- aidcp-edge d8a83ca -->

## 4. aidcp-edge — 测试（jsdom / 桩，脱离浏览器）

- [x] 4.1 `test/facebook/consent.test.ts`：纯判定（同意条→present；含「登录 Facebook」→present、非 login；登录/验证 URL→不 present；验证码→不 present；无按钮/无文案→不 present）+ env 策略。<!-- aidcp-edge d8a83ca -->
- [x] 4.2 接受器：accept_all/necessary_only 各点对应按钮；后置校验成功；仍在重试到上限 `blocked_by_consent`；策略按钮缺失 `no_target` 不误点；探测失败当无同意条。<!-- aidcp-edge d8a83ca -->
- [x] 4.3 pre-clear wiring：gated-submit / join / comment 遇清不掉 → `blocked_by_consent`；清掉后原动作照常。既有序列型桩测注入 no-op 隔离。<!-- aidcp-edge d8a83ca -->
- [x] 4.4 回归：全量 907 绿 + acceptance 16 绿 + typecheck 干净（rebase 合并 `facebook-group-join-observe-i18n` 后复跑）。<!-- aidcp-edge d8a83ca -->

## 5. 验证与收口

- [x] 5.1 本地 typecheck + test（907）+ test:acceptance（16）全绿。<!-- aidcp-edge d8a83ca -->
- [x] 5.2 land 到 edge master（`10f5f9b..d8a83ca` ff）；主 checkout 已同步；edge-only 无 ECS 部署（运营机 pull 后生效）。<!-- aidcp-edge d8a83ca -->
- [x] 5.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（新环境首开触发同意条→自动接受→评论/加群不再卡；含「登录 Facebook」不误判；真验证码不误点；accept_all 生效）。<!-- 控制仓 backlog 已登记 -->
- [x] 5.4 `openspec validate facebook-consent-overlay-auto-accept --strict` 通过。<!-- 归档前校验 -->
