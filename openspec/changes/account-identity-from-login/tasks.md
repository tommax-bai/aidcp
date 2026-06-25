# Tasks — account-identity-from-login

> 进度按 sub-repo 分节回写本仓；代码改动落 edge（主体）/ cloud（近零）。完成项用 HTML 注释标 `<!-- <repo> <sha> 备注 -->`。安全红线回归须全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`。本 change **不动边-云协议**。

## 0. 前置验证（gated，先于动手）

- [x] 0.1 **成败手（已查实可行，真机 0.1 过）**：2026-06-25 探针 `scripts/self-identity-probe.ts` 对已登录真账号实测——**就地读**（顶栏头像祖先 `<a>` 带 `/user/profile/<id>`，导航区两个同 id 锚点）与**跳转读**（进我的主页读 `location.href`）两路都成立、互校一致（同一 24 位 hex id）；**就地读定为首选**（零副作用）、跳转兜底；**硬形态闸定 `/^[A-Za-z0-9]{20,}$/`**（实测 24 位 hex）。读不出/形态不匹配 → 诚实失败，绝不退化成静默 default <!-- aidcp-edge scripts/self-identity-probe.ts 真机探针；本仓 design D8 已据此更新 -->
- [ ] 0.2 与并行 change 错峰协调：迭代 `multi-account-node-support` 的 D4（其 `persona-gated-session-start` / `chrome-instance-isolation` spec 未归档，对齐待其归档后做）；与 `account-real-nickname`（昵称=显示名）确认落点不撞

## 1. aidcp-edge — 身份确立（登录后读稳定 id）

- [ ] 1.1 新增「登录后读出稳定账号 id」能力（**来源已由 0.1 定**）：**首选就地读**——从顶栏头像 `<img>`（`chrome-launcher.ts:410` 选择器）上溯祖先 `<a>`、取其 `href`、套捕获正则 `/\/user\/profile\/([A-Za-z0-9]+)/`（与生产逐字一致）；**兜底跳转读**——进我的主页读 `location.href` 套同一正则。**复用** `evalRaw` CDP 助手；**不要整段复用 `extractAuthorProfile`**（它把 `authorId` 返回耦合在「粉丝/笔记/获赞至少有一个」上，`browse-session.ts:1635`）——读自己 id 只取 href/URL 的 id、不依赖统计数。**不读 cookie 当 id、不读 class 文本拼 id**；读出的 id **必须过 `/^[A-Za-z0-9]{20,}$/` 硬形态闸**、不匹配=诚实失败（云端零校验，此闸是防畸形 id 污染主表的唯一防线）；一并读昵称/小红书号作显示名；**读不出诚实失败、不回落 default**
- [ ] 1.2 `main.ts` 身份来源改为登录后读出（现状 `:77` 取 `process.env.AIDCP_ACCOUNT_ID`、`:89` `launchChrome` 先于 `:125` `client.connect()`）；`AIDCP_ACCOUNT_ID` 降级为**可选覆盖**（设了用之、未设走登录推导；覆盖值与真实 id 不一致时诚实告警）。**注意**：现状 `launchChrome` 只在首启（profile 不存在）阻塞等人扫码，带已登录 profile 重启时直接 attach、不等——新读身份步骤须自己插一个「等到确实登录」的就绪等待 + 处理「还没登录」的无身份态，不能假设 connect 时一定登好了。握手携带真实 id
- [ ] 1.3 节点初始化 ⇄ 身份确立分离：身份失效 → 退回**无身份态**、仅重跑身份确立（**不重启浏览器、不重分端口/目录**）
- [ ] 1.4 身份持续校验：检测登出 / session 过期 / 同目录换登别的账号 → 退回无身份态、断连重连触发云端按新 id 重建（加节流，防抖动误退）
- [ ] 1.5 `scripts/launch-multinode.ts` 改为只分配**节点槽位**（端口 / 用户数据目录 / `edgeId`），用户数据目录按 `node-<n>`；**不再分配 accountId**。**目录改名代价**：现状目录名为 `<base>-<accountId>-<n>`，改 `node-<n>` 后存量已登录 profile 按旧名找不到、被迫重新扫码——cutover 须接受一次性重登，或为存量节点保留旧目录名/做一次目录迁移（在 Migration Plan 记明）
- [ ] 1.6 edge 测试 + `npm run typecheck`：读身份单测（含读不出诚实失败、覆盖优先级）、身份失效退回无身份态、换号重连；不引入指纹浏览器

## 2. aidcp-cloud — 换账号重绑（多为复用，必要时小补）

- [ ] 2.1 回归确认「同 `edgeId` 换账号重连」正确重绑——**经查已实现、预期无需补**：`connection-runtime.ts:89-101` `onHandshake` 已对「同 edgeId 不同 sessionId」`closeEdge` 旧连接 → `teardown`（endSession + 解 tee + 清私有总线）→ 用新 accountId 起新 controller/dispatcher，私有总线保证状态单写不串味。本任务只跑回归坐实，真有缺口才补
- [ ] 2.2 账号按登录态真实 id 登记进主表（`accounts-master-data` delta：稳定 id 作主键、昵称作显示名）；与 `account-real-nickname` 协调不撞
- [ ] 2.3 安全红线回归：`npm run test:acceptance`（AC-RISK/PROTO/PUB）+ 全量 `npm test` + `npm run typecheck`；确认**协议零改**

## 3. 验证 / 归档

- [ ] 3.1 真机 E2E：节点起 → 无身份态等登录 → 登录真实账号 → 读出稳定 id → 未绑人设被诚实拒 + 飞书 → 后台设人设 → 重连 → 运行；换号 → 旧账号会话拆、新账号起就绪闸；读不出 id → 诚实失败
- [ ] 3.2 `openspec validate account-identity-from-login --strict` 通过
- [ ] 3.3 进度回写本仓（各 task 标 `[x]` + commit-sha）；待 `multi-account-node-support` 归档后，把 `persona-gated-session-start` / `chrome-instance-isolation` 的身份来源修订正式对齐进基线，再 `/opsx:archive`
