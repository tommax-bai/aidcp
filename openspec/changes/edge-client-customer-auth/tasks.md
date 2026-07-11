## 1. aidcp-cloud — 数据模型(独立表,init() 自建)

- [ ] 1.1 新建 `src/client-auth/client-user-store.ts`:`CLIENT_USERS_SCHEMA_SQL`(`client_users(user_id PK, name UNIQUE, key_hash, key_salt, status, rotated_at, created_at, updated_at)`)+ class + `init()`;读写方法均经单写者、写后回读真态、绝不 raw UPDATE/乐观
- [ ] 1.2 同文件或 `client-env-scope-store.ts` 加 `CLIENT_ENV_SCOPE_SCHEMA_SQL`(`client_env_scope(user_id FK ON DELETE CASCADE, env_key, assigned_at, assigned_by, PK(user_id,env_key))` + `env_key` 索引);`env_key` 刻意不加 FK 到 accounts
- [ ] 1.3 归属读层遵守 N2:只暴露吃 `userId` 的 scoped 方法(`listEnvKeysForUser` / `isEnvOwnedBy`),整批替换 `setScope(userId, envKeys[])` 用事务 delete+insert
- [ ] 1.4 在 `src/server.ts` 启动序列 `await store.init()` 串接两表(无迁移器)

## 2. aidcp-cloud — key 安全

- [ ] 2.1 新建 `src/client-auth/key.ts`:`generateKey()`(`randomBytes(32).base64url`,`ck_` 前缀)、`hashKey(key)`(scrypt+随机盐)、`verifyKey(key, hash, salt)`(scrypt + timingSafeEqual)、`decoyVerify()`(固定假盐跑一遍抹平时延)
- [ ] 2.2 name+IP 双维内存登录限流器(超阈 429,重启清零,留 PG 缝)

## 3. aidcp-cloud — 客户鉴权 HTTP 服务(独立端口/密钥)

- [ ] 3.1 新建 `src/client-auth/client-auth-server.ts`:`startClientAuthApi(deps, config)` 镜像 `panel-server.ts` 骨架(forbiddenPorts 自检 → createServer → listen 127.0.0.1 → 失败非致命 started=false);复用 `panel/jwt.ts`、`panel/revocation.ts`(独立实例)、`panel/auth.ts:parseBearer`
- [ ] 3.2 `POST /login {name,key}`:查 client_users(status=enabled)→ verifyKey/decoy → 限流 → `signJwt({sub:userId}, clientSecret, ttl)`;凭据错统一 401 不可区分
- [ ] 3.3 客户令牌鉴权闸:parseBearer → verifyJwt(clientSecret) → 独立 revocation → **每请求回库查 status+scope(N3)**;停用/撤销即 401
- [ ] 3.4 `GET /my-environments`:仅返回该 userId 的 env_key 清单(权威过滤,不信前端传入标识)
- [ ] 3.5 `POST /environments`(客户令牌):登录态新建环境自动归属当前客户(写 client_env_scope)
- [ ] 3.6 `POST /logout` / 续签(如需):独立 revocation 拉黑 jti

## 4. aidcp-cloud — 内部管理端点(受内部面板 JWT)

- [ ] 4.1 面板 `handle()` JWT 闸后新增 `/api/client-users*`:GET 列表(不回 key/hash)、POST 创建(一次性回明文 key)、PATCH 改名/启停、POST `:id/rotate-key`(一次性回)、GET/PUT `:id/scope`(整批替换,事务)
- [ ] 4.2 `PanelDeps` 注入 `clientUsers?`(同一 store 实例既供客户服务 auth/scope 又供内部管理);未注入则相关端点 503
- [ ] 4.3 候选环境列表复用现有 `GET /api/accounts`(不新增)

## 5. aidcp-cloud — 装配 + 密钥断言 + env

- [ ] 5.1 `src/server.ts` 装配 `startClientAuthApi`:读 `AIDCP_CLIENT_JWT_SECRET`/`AIDCP_CLIENT_AUTH_PORT`/`AIDCP_CLIENT_JWT_TTL_SECONDS`;未设端口则禁用(镜像面板)
- [ ] 5.2 **启动硬断言** `AIDCP_CLIENT_JWT_SECRET` 非空、非默认、≠ `AIDCP_PANEL_JWT_SECRET`,否则拒启客户服务(warn + started=false)
- [ ] 5.3 双向 forbiddenPorts 自检:客户端口避开 8787/8090/5432/8788/isales;8090 面板也把客户端口列入禁用

## 6. aidcp-cloud — 测试

- [ ] 6.1 跨租户隔离用例:客户 A 令牌打 `/my-environments` 只见 A 的环境;打内部 `/api/client-users*` 被拒
- [ ] 6.2 N1 用例:两 secret 相等/缺失 → 拒启;客户令牌在内部面板验签失败
- [ ] 6.3 N3 用例:停用客户 / 移除归属后下次请求即时生效
- [ ] 6.4 key 用例:创建回显一次、事后读不回明文;错误凭据不可区分;限流 429;`npm run test:acceptance` + `npm test` + `typecheck` 全过

## 7. aidcp-console — 内部管理页

- [ ] 7.1 新增 `src/pages/ClientUsersPage.tsx`:客户列表 + 创建/停用/改名 + 生成/轮换 key 的一次性展示 Modal(前端不落 localStorage)+ 环境归属维护(穿梭框,候选来自 `/api/accounts`)
- [ ] 7.2 `src/routes.tsx` 的 `APP_ROUTES` 加一行(单一来源);`src/api/queries.ts` + `src/types/api.ts` 加 client-users CRUD 契约
- [ ] 7.3 `npm run build`(tsc+vite)通过;AntD 确认流/Modal 交互测试

## 8. aidcp-edge — 登录门 UI(唯一新增界面)

- [ ] 8.1 renderer 新增登录视图(蓝灰 token 与 `styles.css` 连续):name + key(mono + 显隐)、实心主按钮、错误态(凭据错/停用/网络)、页脚"联系服务顾问获取密钥"+版本号
- [ ] 8.2 克制动效(入场浮现 / 品牌标轨道环慢转 / 冷光呼吸)+ `prefers-reduced-motion` 全降级;适配 820×640 与最小 640×520、titlebar 46px 预留
- [ ] 8.3 **不改其他现有 renderer 视图的样式与结构**(回归核对)

## 9. aidcp-edge — 启动门控 + 令牌生命周期

- [ ] 9.1 启动链(`src/main.ts` / `src/electron/main.cjs`)在连云/syncEnvHandles 前插登录门控:无有效令牌 → 显示登录门、不连云不起环境;守 asar/cwd 打包红线
- [ ] 9.2 令牌持久化于 userData(随 `AIDCP_USER_DATA_DIR` 隔离);临近过期静默续签
- [ ] 9.3 登出 / 令牌失效 → 停所有环境回登录门(与云端 HTTP,不动 WS 协议)

## 10. aidcp-edge — 环境可见性过滤 + 自动归属

- [ ] 10.1 登录后用客户令牌拉 `/my-environments`,与本地花名册 `settings.json.environments[]` 求交后再渲染/启动;非交集不显示不启动(环境栏零视觉改动)
- [ ] 10.2 登录态新建/添加环境时调云端 `POST /environments` 自动归属当前客户
- [ ] 10.3 边缘取数走 HTTP 到客户鉴权端口,**协议/hello 零改**(回归断言)

## 11. aidcp-edge — 测试

- [ ] 11.1 `electron:dev` 本机走全流程:登录 → 环境按客户过滤 → 新建自动归属 → 登出回门
- [ ] 11.2 `npm test` + `typecheck` 通过;动了 electron 启动链 → 发版前跑打包产物验 asar/cwd 红线

## 12. 部署 + 文档 + 真机

- [ ] 12.1 dev 部署 cloud(安全序列:备份 → rsync → restart → healthcheck);新增 env 写 `.env`;Nginx 反代加客户鉴权 location;绝不碰同机 isales
- [ ] 12.2 `docs/deployment-environments.md` 登记新增 env 与端口;不记任何密钥/token 明文
- [ ] 12.3 真机验收项(登录门在运营机/客户机生效、跨客户隔离真机核)登记 `docs/real-machine-acceptance-backlog.md`
