# Tasks — client-user-env-registry

## 1. aidcp-cloud — 独立环境注册表

- [x] 1.1 建表 `client_environments`（env_key PK + label/platform/source + created/updated），`init()` 自建 <!-- cloud 843a0a9 -->
- [x] 1.2 `registerEnvironments(items, source)` 批量幂等 upsert（COALESCE 只补非空、source 冲突不降级、去空白/去重/跳空、只登记不归属） <!-- cloud 843a0a9 -->
- [x] 1.3 `listAllEnvironments()` 改「注册表 ∪ 归属表」并集（未归属环境 assigneeCount=0 也列出；label/platform 优先归属最新非空、回落注册表；缺表 fail-closed） <!-- cloud 843a0a9 -->
- [x] 1.4 `server.ts` `onEdgeRegistered` 自动登记（ads- 前缀去前缀→裸 env_key，昵称/平台带上，source=auto，只登记不归属；self-/host- 跳过；失败只 warn） <!-- cloud 843a0a9 -->
- [x] 1.5 补测：`registerEnvironments` 去空白/去重/跳空/空串归 null/source 透传/每条一次 upsert/返回去重条数（4 用例） <!-- cloud 843a0a9 -->
- [x] 1.6 typecheck + acceptance(47) + 全量(1869) 全绿 <!-- cloud 843a0a9 -->

## 2. aidcp-console — 后台

- [x] 2.1 确认零改：环境归属抽屉「待分配」已从 `/api/client-environments` 渲染，注册表返回未归属环境后自动出现（已核代码路径） <!-- console 无改动 -->

## 3. 部署 + 一次性导入（dev）

- [x] 3.1 cloud 部署 dev（备份 → rsync src → restart → healthcheck：active + 8787/8090/8091 + 飞书长连接 + 客户鉴权已起） <!-- cloud 843a0a9 2026-07-12 deployed -->
- [x] 3.2 一次性导入 11 个存量环境进注册表（只 env_key/名字/平台，凭据一律不入库），dev 真库直查核：11 个 assigneeCount 全 0（全待分配）+ 已归属 k1ejvb06 并入 count 1 <!-- 2026-07-12 seeded -->

## 4. 真机验收（登记 backlog，非本地可核）

- [ ] 4.1 后台打开端用户环境归属抽屉：11 个存量环境出现在「待分配」、可勾选加入、保存后转「已分配」 <!-- 真机簇 61 -->
- [ ] 4.2 新 AdsPower 环境连上 dev 云端后自动出现在「待分配」（source=auto 自维护），且未被误归属任何客户 <!-- 真机簇 61 -->
- [ ] 4.3 客户端登录某端用户：只看到分给他的环境；未分配的 11 个不下发不启动 <!-- 真机簇 61 -->
