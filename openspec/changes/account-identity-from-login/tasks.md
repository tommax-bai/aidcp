# Tasks — account-identity-from-login

> 进度按 sub-repo 分节回写本仓；代码改动落 edge（主体）/ cloud（近零）。完成项用 HTML 注释标 `<!-- <repo> <sha> 备注 -->`。安全红线回归须全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`。本 change **不动边-云协议**。

## 0. 前置验证（gated，先于动手）

- [x] 0.1 **成败手（已查实可行，真机 0.1 过）**：2026-06-25 探针 `scripts/self-identity-probe.ts` 对已登录真账号实测——**就地读**（顶栏头像祖先 `<a>` 带 `/user/profile/<id>`，导航区两个同 id 锚点）与**跳转读**（进我的主页读 `location.href`）两路都成立、互校一致（同一 24 位 hex id）；**就地读定为首选**（零副作用）、跳转兜底；**硬形态闸定 `/^[A-Za-z0-9]{20,}$/`**（实测 24 位 hex）。读不出/形态不匹配 → 诚实失败，绝不退化成静默 default <!-- aidcp-edge scripts/self-identity-probe.ts 真机探针；本仓 design D8 已据此更新 -->
- [x] 0.2 与并行 change 错峰协调：迭代 `multi-account-node-support` 的 D4（其 `persona-gated-session-start` / `chrome-instance-isolation` spec 未归档，对齐待其归档后做）；与 `account-real-nickname`（昵称=显示名）确认落点不撞

## 1. aidcp-edge — 身份确立（登录后读稳定 id）

- [x] 1.1 新增「登录后读出稳定账号 id」能力（**来源已由 0.1 定**）：<!-- aidcp-edge b47286d src/cdp/self-identity.ts: 纯helper(extractIdFromHref/isValidStableId/deriveInPlaceSelfId)+readSelfIdentity(就地首选/跳转兜底/形态闸/诚实失败不回落default)+8单测全绿+typecheck净 -->**首选就地读**——从顶栏头像 `<img>`（`chrome-launcher.ts:410` 选择器）上溯祖先 `<a>`、取其 `href`、套捕获正则 `/\/user\/profile\/([A-Za-z0-9]+)/`（与生产逐字一致）；**兜底跳转读**——进我的主页读 `location.href` 套同一正则。**复用** `evalRaw` CDP 助手；**不要整段复用 `extractAuthorProfile`**（它把 `authorId` 返回耦合在「粉丝/笔记/获赞至少有一个」上，`browse-session.ts:1635`）——读自己 id 只取 href/URL 的 id、不依赖统计数。**不读 cookie 当 id、不读 class 文本拼 id**；读出的 id **必须过 `/^[A-Za-z0-9]{20,}$/` 硬形态闸**、不匹配=诚实失败（云端零校验，此闸是防畸形 id 污染主表的唯一防线）；一并读昵称/小红书号作显示名；**读不出诚实失败、不回落 default**
- [x] 1.2 `main.ts` 身份来源改为登录后读出 <!-- aidcp-edge 4d1bcc6: readSelfIdentity 取代 env 标签;env降为可选覆盖(mismatch告警);读不出+无覆盖=诚实停手exit(1)不握手不连云端不回落default;优先级抽为纯 decideHandshakeIdentity+5单测;已验 launchChrome 在 fresh+reuse 两路都 await waitForLogin(登录在前已保证,task 顾虑moot) -->（现状 `:77` 取 `process.env.AIDCP_ACCOUNT_ID`、`:89` `launchChrome` 先于 `:125` `client.connect()`）；`AIDCP_ACCOUNT_ID` 降级为**可选覆盖**（设了用之、未设走登录推导；覆盖值与真实 id 不一致时诚实告警）；握手携带真实 id。<!-- 实测纠偏：launchChrome 在 fresh+reuse 两路都 await waitForLogin，登录在前已保证，不需另插就绪等待 -->
- [x] 1.3 节点初始化 ⇄ 身份确立分离：身份失效 → 退回**无身份态**、仅重跑身份确立（**不重启浏览器、不重分端口/目录**）<!-- aidcp-edge 6db3814: main.ts reestablishIdentity 复用同一 session.cdp(浏览器不重启/端口目录不重分)只重跑身份确立;halt则留无身份态不回落default -->
- [x] 1.4 身份持续校验：检测登出 / session 过期 / 同目录换登别的账号 → 退回无身份态、断连重连触发云端按新 id 重建（加节流，防抖动误退）<!-- aidcp-edge 6db3814: IdentityWatcher 周期就地重读(不导航)+连续阈值防抖(默认2/30s,env可调)→emit lost/changed→reestablish 断连重连setAccountId新id;6单测;云端重绑已验connection-runtime:89-101 -->
- [x] 1.5 `scripts/launch-multinode.ts` 改为只分配**节点槽位**<!-- aidcp-edge 9471a8e: 槽位规格(个数N或edgeId列表),每槽位 port/dir(node-<n>)/edgeId;删 AIDCP_ACCOUNT_ID(身份登录读出)+清继承避免标签泄漏;迁移代价(目录改名→重登)在 file+Migration 记明 -->（端口 / 用户数据目录 / `edgeId`），用户数据目录按 `node-<n>`；**不再分配 accountId**。**目录改名代价**：现状目录名为 `<base>-<accountId>-<n>`，改 `node-<n>` 后存量已登录 profile 按旧名找不到、被迫重新扫码——cutover 须接受一次性重登，或为存量节点保留旧目录名/做一次目录迁移（在 Migration Plan 记明）
- [x] 1.6 edge 测试 + `npm run typecheck`：读身份单测（含读不出诚实失败、覆盖优先级）、身份失效退回无身份态、换号重连；不引入指纹浏览器 <!-- aidcp-edge: self-identity 13单测(就地/跳转/诚实失败/畸形id形态闸/覆盖优先级 decideHandshakeIdentity)+identity-watcher 6单测(防抖/lost/changed/不重复/rebaseline);全量 npm test 345/345、acceptance 11/11、typecheck 净;未引入指纹浏览器 -->

## 2. aidcp-cloud — 换账号重绑（多为复用，必要时小补）

- [ ] 2.1 回归确认「同 `edgeId` 换账号重连」正确重绑——**经查已实现、预期无需补**：`connection-runtime.ts:89-101` `onHandshake` 已对「同 edgeId 不同 sessionId」`closeEdge` 旧连接 → `teardown`（endSession + 解 tee + 清私有总线）→ 用新 accountId 起新 controller/dispatcher，私有总线保证状态单写不串味。本任务只跑回归坐实，真有缺口才补
- [ ] 2.2 账号按登录态真实 id 登记进主表（`accounts-master-data` delta：稳定 id 作主键、昵称作显示名）；与 `account-real-nickname` 协调不撞
- [ ] 2.3 安全红线回归：`npm run test:acceptance`（AC-RISK/PROTO/PUB）+ 全量 `npm test` + `npm run typecheck`；确认**协议零改**

## 3. 验证 / 归档

- [ ] 3.1 真机 E2E：节点起 → 无身份态等登录 → 登录真实账号 → 读出稳定 id → 未绑人设被诚实拒 + 飞书 → 后台设人设 → 重连 → 运行；换号 → 旧账号会话拆、新账号起就绪闸；读不出 id → 诚实失败
- [ ] 3.2 `openspec validate account-identity-from-login --strict` 通过
- [ ] 3.3 进度回写本仓（各 task 标 `[x]` + commit-sha）；待 `multi-account-node-support` 归档后，把 `persona-gated-session-start` / `chrome-instance-isolation` 的身份来源修订正式对齐进基线，再 `/opsx:archive`
