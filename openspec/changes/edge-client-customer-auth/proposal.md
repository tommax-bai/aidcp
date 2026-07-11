## Why

edge 桌面客户端当前没有任何操作员登录——启动即连云、直接可用,所有环境对任何打开客户端的人可见。要把客户端交付给**外部客户**使用,必须加一层对外鉴权:客户用凭据登录后**只能看到属于自己的那批环境**,凭据与归属由内部运营在后台掌控。这套对外客户体系必须与内部运营 console 的登录体系彻底分开。

## What Changes

- **edge 新增登录门**(唯一新增/重做界面):客户用 **name + key** 登录;未登录时客户端不连云、不启动任何环境;登录成功后进入现有主界面;登出或凭据失效回到登录门。登录页视觉为蓝灰简约风,其余现有界面一律不重绘、不改结构。
- **按客户隔离环境可见性**:环境栏零视觉改动,渲染的环境清单换成"云端按登录客户下发的那一份";非本客户的环境不显示、不启动。登录态下客户端新建/添加的环境自动归属当前登录客户。
- **aidcp-cloud 新增客户鉴权后端**:独立数据模型(客户身份 + 客户↔环境显式归属,fail-closed)与独立鉴权服务(独立 JWT 密钥,与内部面板密钥物理隔离;登录限流 + 防用户名枚举;每请求回库校验启用状态与可见范围)。云端是环境可见性的**权威过滤点**——即便客户端被改也拿不到他人环境。
- **aidcp-console 新增内部管理页**:运营创建/停用客户、生成与轮换 key(明文只展示一次)、维护客户↔环境归属。管理接口受**内部**面板 JWT 保护。
- 默认决策:v1 **不改 edge↔cloud WebSocket 协议**(通信零改),环境隔离靠云端权威清单实现;协议级"握手带令牌、云端验不过拒连"留作二期加固。

## Capabilities

### New Capabilities
- `client-customer-auth`: 云端对外客户鉴权与多租户环境归属——客户身份存储(name 唯一、key 以 scrypt+盐 hash、启用状态、轮换时间)、name+key 登录签发**隔离密钥**的客户令牌、按客户显式环境归属(fail-closed)、权威 `/my-environments` 过滤、每请求回库校验启用与范围、登录限流与防枚举、以及受内部面板 JWT 保护的客户管理端点(CRUD / 生成轮换 key / 归属维护)。
- `edge-client-login-gate`: edge 桌面客户端登录门——蓝灰简约登录视图、启动门控(未登录不连云不启动环境)、令牌持久化与生命周期(登出 / 失效回登录门)、以及环境栏按登录客户过滤渲染(仅数据范围收窄,现有界面零视觉改动)。

### Modified Capabilities
<!-- 无:客户鉴权体系与内部运营登录物理隔离,不改现有 console-panel-api / edge-companion-ui 的既有要求;管理端点作为 client-customer-auth 新能力承载。 -->

## Impact

- **aidcp-cloud**:新增 `src/client-auth/`(客户身份 store + 归属 store + 独立 HTTP 鉴权服务);复用 `src/panel/{jwt.ts,revocation.ts,auth.ts}` 骨架;`src/server.ts` 装配新服务 + 启动断言 `AIDCP_CLIENT_JWT_SECRET` 非空且 ≠ panel secret;面板新增受内部 JWT 保护的 `/api/client-users*`(注入 PanelDeps)。**不碰 accounts 热点表**,新表走 store `init()` 自建(无迁移器)。
- **aidcp-edge**:renderer 新增登录视图(`src/electron/renderer/`);启动链在连云前插入登录门控(`src/main.ts` / `src/electron/main.cjs`,守 asar/cwd 打包红线);环境清单取数改为云端按客户下发(`src/client/edge-client.ts` / fleet 渲染)。**协议零改**。
- **aidcp-console**:新增「客户端用户」管理页(`src/pages/ClientUsersPage.tsx` + `routes.tsx` 一行 + `api/queries.ts` / `types/api.ts`)。
- **新增 env**:`AIDCP_CLIENT_JWT_SECRET`、`AIDCP_CLIENT_AUTH_PORT`(未设则整个客户鉴权禁用,镜像面板端口门控)、可选 `AIDCP_CLIENT_JWT_TTL_SECONDS`;部署文档 `docs/deployment-environments.md` 登记。
- **部署**:dev 先行;客户鉴权服务监听独立端口,避开 8787/8090/5432/8788 与同机 isales;Nginx 反代新增 location。
