<!-- landed: cloud master 0b6ef42 / edge master 85d0528 / console master ef8e356 · dev 部署+启用 2026-07-12 -->

## 1. aidcp-cloud — 数据模型(独立表,init() 自建)

- [x] 1.1 新建 `src/client-auth/client-user-store.ts`:`CLIENT_USERS_SCHEMA_SQL`(`client_users`)+ class + `init()`;单写者、写后回读、绝不 raw UPDATE <!-- cloud 0b6ef42 -->
- [x] 1.2 同文件加 `client_env_scope`(显式归属,`env_key`=profileId 不加 FK 到 accounts)+ env_key 索引 <!-- cloud 0b6ef42 -->
- [x] 1.3 归属读层遵守 N2:只暴露吃 userId 的 scoped 方法(listEnvScope/isEnabled);整批替换 setScope 事务 delete+insert <!-- cloud 0b6ef42 -->
- [x] 1.4 `src/server.ts` 启动序列 `await clientUserStore.init()` 串接(无迁移器) <!-- cloud 0b6ef42; dev init 自建表已验(冒烟绿) -->

## 2. aidcp-cloud — key 安全

- [x] 2.1 `src/client-auth/key.ts`:generateKey(ck_ 前缀 256bit)/hashKey(scrypt+盐)/verifyKey(timingSafeEqual)/decoyVerify <!-- cloud 0b6ef42 -->
- [x] 2.2 name+IP 双维内存登录限流器(超阈 429) `src/client-auth/rate-limiter.ts` <!-- cloud 0b6ef42 -->

## 3. aidcp-cloud — 客户鉴权 HTTP 服务(独立端口/密钥)

- [x] 3.1 `src/client-auth/client-auth-server.ts`:startClientAuthApi 镜像面板骨架;复用 jwt/revocation(独立实例)/parseBearer <!-- cloud 0b6ef42 -->
- [x] 3.2 `POST /login`:verifyLogin/decoy + 限流 + signJwt(独立密钥);凭据错统一 401 不可区分 <!-- cloud 0b6ef42; dev 冒烟绿 -->
- [x] 3.3 客户令牌鉴权闸 + **每请求回库查 status(N3)**;停用即时 401 <!-- cloud 0b6ef42; dev after-disable=401 已验 -->
- [x] 3.4 `GET /my-environments`:仅返回该 userId env_key(权威过滤) <!-- cloud 0b6ef42; dev 冒烟绿 -->
- [x] 3.5 `POST /environments`(客户令牌):登录态新建环境自动归属 <!-- cloud 0b6ef42 -->
- [x] 3.6 `POST /logout` + `/auth/refresh`(独立 revocation 拉黑 jti / 滑动续签) <!-- cloud 0b6ef42 -->

## 4. aidcp-cloud — 内部管理端点(受内部面板 JWT)

- [x] 4.1 面板闸后 `/api/client-users*`:列表(不回 key/hash)/创建(一次性回明文)/PATCH 改名启停/rotate-key/GET·PUT scope(整批替换事务) <!-- cloud 0b6ef42 -->
- [x] 4.2 `PanelDeps` 注入 `clientUsers`(同一 store 实例既供客户服务又供内部管理);未注入则 503 <!-- cloud 0b6ef42 -->
- [x] 4.3 后台候选环境:改为「已归属 env_key 列表 + 按 profileId 自由输入」(accounts 按 accountId 编址、无 profileId,故不复用 /api/accounts) <!-- cloud 0b6ef42 / console ef8e356 -->

## 5. aidcp-cloud — 装配 + 密钥断言 + env

- [x] 5.1 `src/server.ts` 装配 startClientAuthApi(AIDCP_CLIENT_AUTH_PORT/_JWT_SECRET/_TTL);未设端口则禁用 <!-- cloud 0b6ef42; dev 未设时正确报「已禁用」-->
- [x] 5.2 **启动硬断言** client secret 非空、≠ 面板 secret,否则拒启(secret_collision) <!-- cloud 0b6ef42; 单测锁 N1 -->
- [x] 5.3 双向 forbiddenPorts 自检(客户端口避 8787/8090/5432/8788;面板也列入客户端口) <!-- cloud 0b6ef42 -->

## 6. aidcp-cloud — 测试

- [x] 6.1 跨租户隔离用例:客户 A 只见自己环境;打内部端点被拒 <!-- cloud 0b6ef42; client-auth-server.test.ts -->
- [x] 6.2 N1:两 secret 相等/缺失拒启;客户令牌在面板验签失败 <!-- cloud 0b6ef42 -->
- [x] 6.3 N3:停用/移除归属后下次请求即时生效 <!-- cloud 0b6ef42; dev 冒烟 after-disable=401 -->
- [x] 6.4 key 用例 + 错误不可区分 + 限流 429;`test:acceptance` 47 + `test` 1862 + typecheck 全绿 <!-- cloud 0b6ef42 -->

## 7. aidcp-console — 内部管理页

- [x] 7.1 `src/pages/ClientUsersPage.tsx`:列表 + 创建/停用/改名 + 一次性 key Modal(不落 localStorage) + 环境归属 Drawer(按 profileId 增删 + PUT 整批替换) <!-- console ef8e356 -->
- [x] 7.2 `routes.tsx` APP_ROUTES 加一行(客户端用户/KeyOutlined);`api/queries.ts` + `types/api.ts` + `errorText.ts` 加契约与 hooks <!-- console ef8e356 -->
- [x] 7.3 `npm run build`(tsc+vite)通过;enum-drift 灰底兜底测试锁白屏风险(create→key-reveal→copy portal 交互 flaky → 真机簇 61.4) <!-- console ef8e356 -->

## 8. aidcp-edge — 登录门 UI(唯一新增界面)

- [x] 8.1 `renderer/login.html`(独立窗口,蓝灰 token):name + key(mono + 显隐)、实心主按钮、错误态(凭据错/停用/网络/限流)、页脚 + 版本号 <!-- edge 85d0528 -->
- [x] 8.2 克制动效(入场浮现 / 品牌标轨道环慢转 / 冷光呼吸)+ prefers-reduced-motion 全降级;窗口 820×640 / min 640×520 <!-- edge 85d0528 -->
- [x] 8.3 **不改其他现有 renderer 视图**(独立窗口方案 → 现有 index.html/renderer.js 零改) <!-- edge 85d0528 -->

## 9. aidcp-edge — 启动门控 + 令牌生命周期

- [x] 9.1 启动链在连云/syncEnvHandles 前插登录门控:无有效令牌 → 登录窗、不连云不起环境;守 asar/cwd(login.html 走 loadFile) <!-- edge 85d0528 -->
- [x] 9.2 令牌持久化 userData/client-session.json(随 AIDCP_USER_DATA_DIR 隔离);会话维护滑动续签 <!-- edge 85d0528 -->
- [x] 9.3 登出(托盘)/ 令牌失效 → 停所有环境回登录门(走 HTTP,不动 WS 协议) <!-- edge 85d0528 -->

## 10. aidcp-edge — 环境可见性过滤 + 自动归属

- [x] 10.1 登录后拉 `/my-environments` 与本地花名册求交,syncEnvHandles 按 allowedProfileIds 过滤(环境栏零视觉改动) <!-- edge 85d0528 -->
- [x] 10.2 settings:save 检测新增 profileId → POST /environments 自动归属 + 乐观即时可见 <!-- edge 85d0528 -->
- [x] 10.3 取数走 HTTP 到客户鉴权端口,**协议/hello 零改**(AC-PROTO 全绿) <!-- edge 85d0528 -->

## 11. aidcp-edge — 测试

- [x] 11.1 代码级:`node --check` main.cjs/preload.cjs + `typecheck` + `test` 1050 + `test:acceptance` 16 全绿。**electron:dev GUI 全流程 → 真机簇 61.1**(此环境无法安全驱动 Electron GUI) <!-- edge 85d0528 -->
- [x] 11.2 协议零改回归(AC-PROTO 全绿)。**打包产物 asar/cwd 红线 → 真机簇 61.6**(发版前本机跑打包产物) <!-- edge 85d0528 -->

## 12. 部署 + 文档 + 真机

- [x] 12.1 dev 部署 cloud(备份 → rsync src → restart → healthcheck 全绿)+ 启用客户鉴权(8091,ECS 生成密钥)+ 真库端到端冒烟绿;console 部署 dev(备份+rsync 不 --delete+清旧 js) <!-- cloud/console dev 2026-07-12 -->
- [x] 12.2 `docs/deployment-environments.md` 登记 AIDCP_CLIENT_AUTH_PORT/_JWT_SECRET/_TTL + N1 断言 + reachability 说明(不记密钥值) <!-- aidcp main -->
- [x] 12.3 真机验收项(GUI 登录 / 跨客户隔离 / 自动归属 / console 管理流 / reachability / 打包门控)登记 `docs/real-machine-acceptance-backlog.md` 簇 61 <!-- aidcp main -->
