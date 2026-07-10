# Tasks — facebook-consent-overlay-auto-accept

> 全部落 `aidcp-edge`，edge-only，无 ECS 部署。热点只碰 Facebook 专属文件，不动两份 protocol.ts / command-bridge.ts / 角色注册 / 风控状态机。

## 1. aidcp-edge — 浮层类别与识别

- [ ] 1.1 在 `src/browse/overlay-monitor.ts` 的 `OverlayKind` 联合类型新增 `'consent'`；同步 `isOverlayKind` 守卫；确认 `isBlockingKind` **不**将 `consent` 计入阻断类别（consent 不暂停会话、不上报云端）。
- [ ] 1.2 在 `src/facebook/overlay.ts` 的 `classifyFacebookOverlayFromSignals` 新增 `consent` 判定：命中 cookie 政策语义（「Cookie 政策」/「允许…Cookie」/「Allow…cookies」）**且**存在接受按钮文案（「允许所有 Cookie」/「Allow all cookies」/「仅允许必要 Cookie」/「Only allow essential cookies」）**且** URL 非登录/验证门 → 返回 `consent`。锚点只用可见文案 / aria-label /（若稳定）`[data-testid]`，不锁哈希 class。
- [ ] 1.3 收紧 login 分支：真登录门以 URL（`/login`、`/checkpoint`、`/recover`）为主信号；确保判定优先级 `captcha` > 真登录门 > `consent`，含「登录 Facebook」字样的同意条不再命中 login 分支。
- [ ] 1.4 在浮层扫描 JS（`FACEBOOK_OVERLAY_SCAN_JS`）中补齐 consent 识别所需信号（接受按钮文案 / aria 的采集），保持只读、无副作用。

## 2. aidcp-edge — 边缘本地拟人自动接受

- [ ] 2.1 新增 `acceptFacebookConsent(cdp, policy)`（可放 `src/facebook/consent.ts` 或 `overlay.ts` 邻近）：按 policy（accept_all | necessary_only）定位对应按钮 → 拟人点击 → 复探确认清除。
- [ ] 2.2 复用 `src/browse/captcha-assist.ts` 的拟人点击（`dispatchClick` + humanize：移动/过冲/落点抖动/停留），不裸 instant click；按钮定位失败返回 `no_target`，绝不点其他按钮。
- [ ] 2.3 后置校验：点击后复跑 `classifyFacebookOverlay`，仍为 `consent` 则进入有界重试（上限如 2–3 次，带拟人间隔）；到上限仍在则停手、返回 `blocked_by_consent` 升级；全程绝不谎报 `ok`。
- [ ] 2.4 新增 env 开关 `AIDCP_FB_COOKIE_CONSENT`（`accept_all` 默认 / `necessary_only`），读取一处收口。

## 3. aidcp-edge — 接入动作前 pre-clear

- [ ] 3.1 `src/facebook/probes/gated-submit.ts`：preflight 遇 `consent` 不直接阻断，先调 `acceptFacebookConsent`；清除成功当作 `none` 放行原动作，失败返回新原因 `blocked_by_consent`（扩 `FacebookGatedSubmitPreflightReason`）。
- [ ] 3.2 `src/facebook/join-executor.ts`：`blockingReason()` 遇 `consent` 同样先自动接受再复判；清不掉则回报 `blocked_by_consent`（扩加群结果 reason 联合类型）。
- [ ] 3.3 若 `src/facebook/comment-executor.ts` 有独立提交入口，确认同样经过 pre-clear（避免绕过）。
- [ ] 3.4 确认 `consent` 处理**不**触发验证码远程协助、**不**上报为 blocking 浮层、**不**暂停会话（守 `overlay-report-gate.ts` 只放 `captcha`/`unknown` 的现状）。

## 4. aidcp-edge — 测试（jsdom 桩，脱离浏览器）

- [ ] 4.1 分类器单测：同意条 → `consent`；含「登录 Facebook」字样的同意条不误判为 `login`；真登录门（/login、/checkpoint）仍 `login`；验证码仍 `captcha`（优先级）；无浮层 `none`。
- [ ] 4.2 自动接受单测：accept_all / necessary_only 各点对应按钮；后置校验成功放行；仍在则重试；到上限 `blocked_by_consent`；按钮定位失败 `no_target` 且不误点。
- [ ] 4.3 pre-clear 集成向单测：gated-submit / join-executor 遇 consent → 自动接受成功后原动作放行；失败诚实回报，不假成功。
- [ ] 4.4 回归红线：`npm run test:acceptance`（AC-* 不回归）+ 全量 `npm test` + `npm run typecheck`（`OverlayKind` 新增值的穷举 switch 全部处理）。

## 5. 验证与收口

- [ ] 5.1 本地 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿。
- [ ] 5.2 提交推送 edge（master）；edge-only 无 ECS 部署（运营机 pull 后生效，记入交接）。
- [ ] 5.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：新环境首开 Facebook 触发同意条 → 自动接受 → 评论/加群不再卡；含「登录 Facebook」字样不误判；真验证码不被误点；accept_all 生效。
- [ ] 5.4 `openspec validate facebook-consent-overlay-auto-accept --strict` 通过。
