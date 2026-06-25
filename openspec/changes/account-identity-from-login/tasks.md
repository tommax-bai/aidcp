# Tasks — account-identity-from-login

> 进度按 sub-repo 分节回写本仓；代码改动落 edge（主体）/ cloud（近零）。完成项用 HTML 注释标 `<!-- <repo> <sha> 备注 -->`。安全红线回归须全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`。本 change **不动边-云协议**。

## 0. 前置验证（gated，先于动手）

- [ ] 0.1 **成败手（已查实可行，降级为校准）**：核心已坐实——`browse-session.ts:1589` 早已用 `location.href.match(/\/user\/profile\/([A-Za-z0-9]+)/)` 抽作者 userid（URL 结构性、生产已验），登录探测又已定位到自己头像。**只需一次性现场校准**：确认导航栏自己头像 `href` = `/user/profile/<id>`，并选定"就地读 href"或"进我的主页读 URL"。读不出/不像 → 诚实失败，绝不退化成静默 default
- [ ] 0.2 与并行 change 错峰协调：迭代 `multi-account-node-support` 的 D4（其 `persona-gated-session-start` / `chrome-instance-isolation` spec 未归档，对齐待其归档后做）；与 `account-real-nickname`（昵称=显示名）确认落点不撞

## 1. aidcp-edge — 身份确立（登录后读稳定 id）

- [ ] 1.1 新增「登录后读出稳定账号 id」能力：**复用** `extractAuthorProfile` 的 URL 正则 + `evalUrl`/`evalRaw` CDP 助手 + 登录探测已定位的自己头像；读 `href`（结构性）、**不读 cookie 当 id、不读 class 文本拼 id**；一并读昵称/小红书号作显示名；**读不出诚实失败、不回落 default**
- [ ] 1.2 `main.ts` 身份来源改为登录后读出（`AIDCP_ACCOUNT_ID` 降级为**可选覆盖**：设了用之、未设走登录推导；覆盖值与真实 id 不一致时诚实告警）；保持「登录在前、握手在后」，握手携带真实 id
- [ ] 1.3 节点初始化 ⇄ 身份确立分离：身份失效 → 退回**无身份态**、仅重跑身份确立（**不重启浏览器、不重分端口/目录**）
- [ ] 1.4 身份持续校验：检测登出 / session 过期 / 同目录换登别的账号 → 退回无身份态、断连重连触发云端按新 id 重建（加节流，防抖动误退）
- [ ] 1.5 `scripts/launch-multinode.ts` 改为只分配**节点槽位**（端口 / 用户数据目录 / `edgeId`），用户数据目录按 `node-<n>`；**不再分配 accountId**
- [ ] 1.6 edge 测试 + `npm run typecheck`：读身份单测（含读不出诚实失败、覆盖优先级）、身份失效退回无身份态、换号重连；不引入指纹浏览器

## 2. aidcp-cloud — 换账号重绑（多为复用，必要时小补）

- [ ] 2.1 确认「同 `edgeId` 换账号重连」正确重绑：拆旧账号会话、按新真实 id 建运行时 + 过就绪闸（状态单写、不串味）；有缺口才补（复用 `multi-account-node-support` 已部署的按连接运行时 + 就绪闸 + 飞书）
- [ ] 2.2 账号按登录态真实 id 登记进主表（`accounts-master-data` delta：稳定 id 作主键、昵称作显示名）；与 `account-real-nickname` 协调不撞
- [ ] 2.3 安全红线回归：`npm run test:acceptance`（AC-RISK/PROTO/PUB）+ 全量 `npm test` + `npm run typecheck`；确认**协议零改**

## 3. 验证 / 归档

- [ ] 3.1 真机 E2E：节点起 → 无身份态等登录 → 登录真实账号 → 读出稳定 id → 未绑人设被诚实拒 + 飞书 → 后台设人设 → 重连 → 运行；换号 → 旧账号会话拆、新账号起就绪闸；读不出 id → 诚实失败
- [ ] 3.2 `openspec validate account-identity-from-login --strict` 通过
- [ ] 3.3 进度回写本仓（各 task 标 `[x]` + commit-sha）；待 `multi-account-node-support` 归档后，把 `persona-gated-session-start` / `chrome-instance-isolation` 的身份来源修订正式对齐进基线，再 `/opsx:archive`
