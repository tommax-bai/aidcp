## Context

edge 桌面客户端零登录:启动读 `AIDCP_CLOUD_URL` + 派生 edgeId 即连云(`aidcp-edge/src/main.ts:113-124`),hello 握手无凭据(`edge-client.ts:241-252`),云端 WS 无 verifyClient(`aidcp-cloud/src/comm/ws-server.ts:156`)。环境 = AdsPower 分身(edgeId=`ads-<profileId>`,`fleet.cjs:18`),与登录读出的社媒 accountId 约定式 1:1、无绑定表(spec `accounts-master-data`)。`accounts` 表无 owner/tenant 列,唯一分组维度 `group_label` 是通知路由用途的自由文本。

内部运营已有一套登录:console `name+password → JWT`(`aidcp-console/src/auth/AuthContext.tsx`),凭据来自 env `AIDCP_PANEL_USERS`,面板服务 `127.0.0.1:AIDCP_PANEL_PORT`(默认 8090),JWT 收口 `src/panel/jwt.ts`(payload `{sub,iat,exp,jti}`,无 claim 白名单、可干净扩展),撤销 `src/panel/revocation.ts`(内存),建表惯例 = store `init()` 里 `CREATE TABLE IF NOT EXISTS`(无迁移执行器)。cloud 用 tsx 直跑 src。

本设计新增一套**与内部运营物理隔离**的对外客户鉴权,并让 edge 登录后按客户过滤环境可见性。

## Goals / Non-Goals

**Goals:**
- 客户用 name + key 登录 edge;未登录不连云、不启动环境。
- 不同客户只见自己归属的环境;云端为权威过滤点(客户端被改也拿不到他人环境)。
- 客户凭据/归属在内部后台管理;客户体系与内部运营登录彻底隔离(独立密钥、独立服务、独立身份源)。
- 登录页是唯一视觉改动;其余现有界面零重绘。edge↔cloud 协议零改。

**Non-Goals:**
- 不做协议级握手强制(hello 带令牌、云端验不过拒连)——留二期。
- 不做复杂 RBAC/权限矩阵、SSO、客户自助注册/改密。
- 不做跨重启强撤销(撤销/限流内存实现,留 PG 缝)。
- 不复用 `group_label` 做可见性键;不给 `accounts` 加列;不改 WS 广播。

## Decisions

### D1 — 三条隔离不变量(承重)
- **N1 密钥即边界**:客户令牌用独立密钥 `AIDCP_CLIENT_JWT_SECRET` 签发,与 panel secret 不同。客户令牌拿去打内部面板 `verifyJwt`(HS256+timingSafeEqual)必然 `bad_signature`。**启动硬断言** secret 非空、非默认、且 ≠ `AIDCP_PANEL_JWT_SECRET`,否则拒启客户鉴权服务(镜像面板 `missing_secret` 处置)。
- **N2 结构性无泄漏路径**:客户可达的环境读层**只有一个吃 `userId` 的方法**——SQL 内 `INNER JOIN client_env_scope`。不存在"取全量"的方法可调;漏点从"要记得加过滤"变成"想漏都无 API"。
- **N3 每请求回库重导 scope + status**:scope **不进令牌**;每次请求验签后回库查 `status='enabled'` 与当前归属。改可见范围/停用客户,下一请求即生效(避免令牌内嵌 scope 的陈旧性 → 跨租户泄漏窗口)。
- 备选:`/capi/*` 复用 8090 面板端口 —— 否决。独立端口 = 独立 http.Server + 独立路由表 + 独立 authed 集合,物理上内部服务器 attach 不到客户路由、客户服务器不实现内部路由;审计面最小。

### D2 — 数据模型:显式环境归属(否决 group_label)
- `client_users(user_id PK=randomUUID, name UNIQUE, key_hash, key_salt, status enabled|disabled, rotated_at, created_at, updated_at)`。
- `client_env_scope(user_id FK ON DELETE CASCADE, env_key, assigned_at, assigned_by, PRIMARY KEY(user_id, env_key))`;`env_key` = 环境 profileId(客户端真实标识,edgeId=`ads-<profileId>` 的 profileId 部分),**刻意不加 FK 到 accounts**(避免与 accounts 单写者/ensureAccount 时序耦合);孤儿行由 join 自然屏蔽。
- **为何显式归属而非 group_label**:group_label 自由文本可变——运营改一次就静默改变某客户可见范围(定时泄漏);新账号动态 ensureAccount 登记,显式归属下**新环境默认不属任何客户 = fail-closed**(安全默认),group_label 下则 fail-open。
- **不碰 accounts 热点表**(并行开发单写者约束):全走新独立表,store `init()` 自建。

### D3 — key 安全
- 生成:`crypto.randomBytes(32).toString('base64url')`(256-bit),加前缀 `ck_` 便于日志脱敏;**只在创建/轮换响应回显一次**,此后无接口读回。
- 存储:`scrypt` + 每客户随机盐,只存 `key_hash`/`key_salt`;比对 `timingSafeEqual`(与 `jwt.ts`/`auth.ts` 家族一致)。
- 防枚举:name 未命中仍跑一次 decoy scrypt 再返 401,抹平存在性时间差;登录按 name+源 IP 双维内存限流,超阈 429。
- 撤销/轮换:`disable`(status→disabled)= 即时 kill switch(N3 下次请求即 401);`rotate-key` 换 hash+盐、旧 key 立即失效,已签发活令牌活到 exp(短 TTL 兜底)。

### D4 — 客户令牌 claim + 端点
- 复用 `signJwt`/`verifyJwt` 原封不动,payload `sub=userId`,**独立 secret 即独立域**(sub 命名空间重叠无妨)。scope 不进 token(N3)。
- 客户服务(独立端口 `AIDCP_CLIENT_AUTH_PORT`,未设则整个客户鉴权禁用):`POST /login {name,key}→{token,expiresIn}`、`GET /my-environments`(token)→ 该客户 env_key 清单(权威过滤)。独立 `TokenRevocationStore` 实例、独立限流器。
- 端口避开 8787/8090/5432/8788 与同机 isales;双向 forbiddenPorts 自检。

### D5 — edge 登录门 + 环境过滤(协议零改)
- renderer 新增登录视图(vanilla,与现有 `renderer.js`/`ui-logic.js` 同栈);蓝灰 token 与现有 `styles.css`(titlebar `#eef4ff`、文字 `#1a2233`)连续。
- 启动门控:未持有效 token → 显示登录门、**不连云不 syncEnvHandles**;登录成功存 token 于 userData(随 `AIDCP_USER_DATA_DIR` 隔离)→ 正常启动;登出/token 失效 → 停所有环境回登录门。
- 环境过滤:登录后用 user token 拉 `/my-environments`,与本地花名册 `settings.json.environments[]` 求交后再 `syncEnvHandles`;非交集环境不渲染、不启动。**环境栏零视觉改动**——只是喂给它的清单变了。
- 新建环境自动归属:登录态下新建/添加环境时调云端登记 `client_env_scope`(用当前 user token),后台可改。
- 红线:改 `src/electron/**` 启动链守 asar/cwd(edge CLAUDE.md 打包红线);登录取数走 HTTP 到客户鉴权端口,**不动 WS 协议/hello**。

### D6 — 内部管理(复用内部鉴权)
- 面板(8090,受内部 JWT)新增 `/api/client-users*`:列表(不回 key/hash)、创建(响应一次性回明文 key)、改名/启停、轮换 key(一次性回)、读/整批替换某客户归属;候选环境复用现有 `GET /api/accounts`。注入同一 `ClientUserStore` 实例给客户服务做 auth/scope 读(单实例共享 PG 池)。
- console 新页「客户端用户」挂 `routes.tsx` 的 `APP_ROUTES` 一行;key 一次性走 Modal,前端不落 localStorage。

## Risks / Trade-offs

- [两 secret 配成相等 → 边界坍塌] → 启动硬断言 ≠ 且非空非默认,否则拒启客户服务(头号风险)。
- [漏某个按客户过滤点 → 跨租户泄漏] → N2 结构性:客户读层不存在无 scope 方法;补集成测试"客户 A 打任意端点看不到 B 的环境"。
- [纯客户端门可被改版绕过] → v1 云端 `/my-environments` 权威过滤即数据隔离(改客户端也拿不到他人环境清单);WS 逐环境连接仍用 edgeId(无 per-user 鉴权),协议级拒连留二期,当前风险 = 已知 envId 者仍可连(需 profileId + AdsPower 分身,v1 可接受)。
- [key hash 弱/存明文/日志泄漏] → scrypt+盐、只存 hash、只展示一次、`ck_` 前缀便于脱敏、绝不记 token/key。
- [新账号 fail-open 自动可见] → 显式归属表,新环境默认不属任何客户,须后台/客户端登录态显式登记。
- [动 edge 启动链引入打包态回归] → asar/cwd 守卫 + 发版前跑打包产物。
- [撞并行开发热点] → 全新独立表/文件,不碰 accounts/协议/风控单写。

## Migration Plan

- 新表由 store `init()` 幂等自建,无数据迁移。
- 部署:cloud 先 dev;新增 env(`AIDCP_CLIENT_JWT_SECRET`/`AIDCP_CLIENT_AUTH_PORT`/可选 TTL)写入 `.env`;Nginx 反代加 location 到客户鉴权端口。回滚 = 不设 `AIDCP_CLIENT_AUTH_PORT` 即禁用客户鉴权 + 旧 edge 无登录门(向后兼容)。
- edge 发版含登录门属客户端行为变更,真机验收后再推运营/客户机。

## Open Questions

- 存量环境的初始归属由谁一次性分配(运营批量 vs 首个登录客户认领)——v1 取运营后台批量,认领留观察。
- 一个客户是否需要多个子登录名(v1 假设 name=客户=范围,一个客户一个登录名)。
