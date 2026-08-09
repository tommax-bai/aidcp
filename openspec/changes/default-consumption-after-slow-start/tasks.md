# Tasks — default-consumption-after-slow-start

## 1. aidcp-api — 慢启动回落模式默认改为消费

- [x] 1.1 统一模式 API：选 `slow_start` 时写入的 resumable base 由 `persona` 改为 `consumption`（`src/config/facebook-operation-policy-store.ts` 的 nextBaseMode 三元）。 <!-- aidcp-api c4e5cae -->
- [x] 1.2 建号完成路径：`facebookOperationMode=slow_start`（含 legacy `slowStartEnabled` 解析到 slow_start 的路径）初始 `base_mode` 写 `consumption`（`src/client-auth/client-user-store.ts` 建号事务）。 <!-- aidcp-api c4e5cae；省略运行字段的 legacy 建号解析到 persona、不受影响（该默认在客户端不在服务端） -->
- [x] 1.3 迁移 0117（DML-only）：`base_mode='persona'` 且慢启动 active（`slow_start_since` 非空、无 completion 行、且未按 起点+全局总天数 推导毕业）的环境翻为 `consumption`；逐行取新 revision、写 audit（`actor_class='migration'`）；同迁移内 `facebook_operation_policy` 镜像版本 +1。`rule` 行与非 active 环境不动。 <!-- aidcp-api c4e5cae migrations/0117；推导毕业的排除条件是写迁移时补的（比 1.3 原文多一条）：它们正按 persona 运行，回头翻动等于改运行中环境的模式 -->
- [x] 1.4 测试：更新 store 测试中「选 slow_start ⇒ baseMode persona」类断言为 consumption；建号测试同步；显式选 persona 的断言保持不变。 <!-- aidcp-api c4e5cae：store 测试 4 处断言翻转 + legacy 开关用例改写为「慢启动结束后基线为消费 ⇒ mode_conflict 零变更零审计」（该守卫既有，本 change 扩大其命中场景）+ 新增 0117 取值方向测试（沿 0110 的 SQL 文本断言写法）。edge 9bbde45：建号收据校验接受 consumption/persona 双基线（混版期两端互通），test 同步。cloud 4d1efe3：panel/client-auth 两处夹具 + legacy-slow 预期 + store 双份测试拷贝同步 -->
- [x] 1.5 `npm run test:acceptance` → `npm test` → `npm run typecheck`，记录结果。 <!-- aidcp-api: acceptance 28/28、全量 586/586、typecheck CLEAN（rebase 到 ea8e239 后复跑同绿）。edge: 收据聚焦测试 3/3 + typecheck CLEAN。cloud 集成仓: acceptance 73/73、全量 2441/2441；cloud typecheck 有 3 个既有报错（api-contract-drift / mirror-stale-stop-work / panel-config-http，属并行 restricted-policy 与 transport 分类改动未跟平的双份测试欠账，与本 change 无关、未代修） -->

## 2. 集成与部署

- [x] 2.1 aidcp-api 合回 `master` 并推送。 <!-- aidcp-api c4e5cae（rebase 后 ff）；edge 9bbde45 / cloud 4d1efe3 同批推送 -->
- [x] 2.2 部署 dev（安全序列：target 检查 → 备份 → rsync → migrate `--owner=api` → restart → healthcheck）。 <!-- 2026-08-09 deployed；备份 api.bak.20260809-151909.tar.gz + api.env.bak.20260809；git archive c4e5cae 快照 rsync；migrate status 干净后 up 应用 0117（8ms）；重启后 aidcp-api active、NRestarts=0、8090/8091/8093 在、契约门通过（账本顶=0117）、飞书 onReady -->
- [x] 2.3 部署验收：dev 上抽查冷启动中环境投影与镜像。 <!-- 库内实测：翻 50 行（audit 同 50）、base_mode 分布 consumption=111 / persona=56 / rule=5、facebook_operation_policy 镜像版本推进至 165；剩余「persona+有慢启动痕迹」14 行全部为按 totalDays=5 推导已毕业无完成行的存量（按设计排除，正按 persona 运行）；automation 近 10 分钟日志 stale/payload_drift/error 计 0 -->
- [x] 2.4 OL 风险登记：共库，0117 入账后 OL api 旧构建重启会被契约门拦（重启前零症状）。OL 跟版等用户明确要求，届时走发布分支。 <!-- 已在 proposal 与对话总结中显式告知；0117 为 expand/DML，OL 旧构建运行期不受影响，只有 restart 才触发契约门 -->
- [x] 2.5 OL 部署（2026-08-09 用户明确要求）。 <!-- 发布分支 release/20260809-ol-slow-start-consumption（=api master c4e5cae，纯建分支指针未动 canonical checkout）；上一发布分支 cherry 核查零独有提交。范围=api 单服务。探明 OL api 已被并行会话更过（认识 0114、kernel pin v0.1.1），真实内容差异仅 8 文件（transport pin 清单×2、server.ts ahead-gate 接线、本 change 源码×2 + 迁移 + 测试×2，rsync -c 校验和核定）。安全序列：备份 api.bak.20260809-153947.tar.gz + api.env.bak.20260809 → 快照 rsync → transport v0.1.5 包目录随包送（OL 拉不了私有 git 依赖；kernel v0.1.1 已在）→ migrate status 74/74 全应用 0 待应用（0117 经共库已在账）→ restart → 契约门通过（账本顶=0117，重启陷阱解除）、三服务 active、NRestarts=0、8787/8090/8091/8093 全在、飞书 onReady、panel 8090 与 capi 8091 均 200、automation 零 stale/drift/error、isales 未碰。发布分支 tip=master 提交本身，零回流欠账 -->

## 3. 控制仓收口

- [x] 3.1 tasks 回写 sha、`openspec validate default-consumption-after-slow-start --strict`。 <!-- 见本文件；validate 通过 -->

## 4. 真机验收（未完成，留待 backlog 归并）

- [ ] 4.1 一个环境真实走完慢启动毕业 → 无人工干预自动进入消费模式浏览（`action=like` 消费节奏出现、无 `no_persona` 停摆）。部署时点无环境临近毕业，无法当场观测。
