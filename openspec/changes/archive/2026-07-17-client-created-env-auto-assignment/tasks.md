## 1. Cloud 权威创建归属

- [x] 1.1 新增 `client_env_provisioning_intents` 自建 schema 与顺序迁移，存储客户绑定、proof hash、过期和完成真态；保持 active env 全局唯一 owner 与旧 `POST /environments` 403 不变。 <!-- aidcp-cloud e8b16d6: migrations/0043 + CLIENT_USERS_SCHEMA_SQL；rebase 时避让上游 0042 runtime-control 迁移 -->
- [x] 1.2 在 `ClientUserStore` 实现创建 intent 与事务化完成方法：enabled user/intent 锁、proof/TTL 校验、新环境注册、唯一 owner 写入、同 intent+envKey 幂等和冲突回滚。 <!-- aidcp-cloud e8b16d6；malformed intent 在入库前拒绝，真实 PostgreSQL 事务 2/2 -->
- [x] 1.3 在 customer-auth 新增创建 intent/完成端点，严格校验输入、映射具名拒因且不记录 proof；补 server/store/真实 PostgreSQL 边界测试。 <!-- aidcp-cloud e8b16d6；targeted server/store/migration 32/32 -->

## 2. Edge 程序化新建闭环

- [x] 2.1 在 Electron 主进程为 gated `ads:createEnv` 增加“创建前 intent → 本地建号 → Cloud 完成 → `/my-environments` 回读”的单建和批量编排；renderer 不得取得 proof 或提交 envKey。 <!-- aidcp-edge 239c44c；proof 仅主进程内存，envKey 只取 AdsPower create 回执 -->
- [x] 2.2 权威回读确认后由主进程把新环境去重加入、落盘运行花名册并广播离线行；失败时如实返回本机已创建/未分配且绝不入册，未 gated 行为保持不变。 <!-- aidcp-edge 239c44c；保存失败同步回滚内存，不调用 spawn/start，未 gated 批量零回归 -->
- [x] 2.3 更新创建成功/失败文案与 edge 契约测试，锁定“已分配并加入、未配代理可后补、不会自动启动”以及旧自绑定/renderer 注入路径不存在。 <!-- aidcp-edge 239c44c；targeted Electron tests 51/51 -->

## 3. 验证、集成与 dev 部署

- [x] 3.1 Cloud 依次通过 `npm run test:acceptance`、`npm test`、PostgreSQL 相关集成测试、`npm run typecheck` 与 `npm run build`；Edge 依次通过 `npm run test:acceptance`、`npm test`、`npm run typecheck`，不运行 installer/package 构建。 <!-- 最新 master: Cloud acceptance 54/54, full 2290 pass + 5 gated skip, ephemeral PostgreSQL 2/2, typecheck/build pass；Edge acceptance 22/22, full 1520/1520, typecheck pass；未运行 electron:build* -->
- [x] 3.2 分别提交并 fast-forward 集成 cloud/edge 到默认分支并推送；回写 commit SHA、验证与偏离说明，显式路径提交控制仓 OpenSpec 文件且不触碰现有未跟踪文件。 <!-- aidcp-cloud e8b16d6、aidcp-edge 239c44c 已 ff push origin/master；上游迁移占用 0042，故本变更迁移顺延 0043 -->
- [x] 3.3 运行 `scripts/deploy-target dev --check`，从干净的 cloud 默认分支提交快照备份/部署 `dev`，验证 service、监听端口、customer-auth/public/panel health、Feishu 与 PostgreSQL；失败则按文档回滚，不碰 `isales`。 <!-- dev 已部署 e8b16d6；backup cloud.bak.20260716-180737.tar.gz；active/NRestarts=0，8787/8090/8091、local+public health、PG provisioning 表+3 indexes、Feishu WS onReady、文件 SHA 均通过；未碰 isales -->
- [x] 3.4 在不做真实 Windows/AdsPower 建号和不构建安装包的前提下，登记真机验收 backlog；运行 `openspec validate client-created-env-auto-assignment --strict`，完成任务证据同步。 <!-- backlog 簇 89 已登记；strict validate 通过；Windows 新包/真机建号因无显式打包授权保持未执行 -->

## 4. 创建后删除与添加页状态回归

- [x] 4.1 Cloud：仅对 completed provisioning intent 可证明来源、仍归属当前客户且无 `interaction_auth_state` 的视频号环境，事务化写入终态 offboard/审计并撤销 scope；普通管理员/存量环境缺绑定继续 `offboard_binding_missing`，补真实 PostgreSQL 回归。 <!-- aidcp-cloud 993960c；原始 client-provision grant + 同 env advisory lock；ephemeral PostgreSQL 3/3，含迟到 auth 状态被 tombstone 拒绝 -->
- [x] 4.2 Edge：主进程自动入册成功后，renderer 在刷新添加环境列表前从 `settings:get` 同步已落盘花名册，立即显示“已加入”；锁定终态 offboard 仍须 Cloud 回读后才物理删除，补 Electron 契约测试。 <!-- aidcp-edge bcca8cc；targeted Electron contract 11/11 -->
- [x] 4.3 运行 Cloud acceptance/full/PostgreSQL/typecheck/build、Edge acceptance/full/typecheck 与 OpenSpec strict validation；提交并 fast-forward 集成默认分支、推送，随后从干净 Cloud master 部署 dev 并验证服务/端口/health/Feishu/PostgreSQL，不构建桌面安装包。 <!-- rebase 后 Cloud acceptance 54/54、full 2302 pass + 6 gated skip、typecheck/build；Edge acceptance 22/22、full 1522/1522、typecheck；两仓已 ff push master。dev 从 993960c git archive 部署，backup cloud.bak.20260716-185429.tar.gz；active/NRestarts=0，8787/8090/8091、本机+公网 panel/client health、PG、Feishu onReady、文件 SHA 通过；未构建 installer。现场 k1eoujd8 于部署前已出现 active auth binding，未代用户执行删除 -->
