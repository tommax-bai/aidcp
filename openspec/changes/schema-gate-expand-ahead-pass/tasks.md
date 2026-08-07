# Tasks — schema-gate-expand-ahead-pass

## 1. aidcp-transport — 闸门拷贝（api / content 消费方）

- [x] 1.1 `src/schema/schema-contract.ts`：判定输入加 `ledgerKinds?`（version→kind 映射）；ahead 分支按类别分流——全 expand ⇒ pass + `aheadExpandOnly`，含 contract / kind 不明 ⇒ 拒绝并在结论列出 blocking 版本与其 kind；waiver 语义与优先级不变；`formatGateConclusion` 补分类段 <!-- aidcp-transport 6b4be41 -->
- [x] 1.2 `src/schema/schema-gate.ts`：账本读取改查 `version, kind`，42703 回退只查 `version`（kind 全未知）；kind 映射不随属主裁剪（判定层按超前版本逐条查表）；扩张类放行进 `pendingWaiverAlert` 告警缓存（与人工放行合并 detail、可区分） <!-- aidcp-transport 6b4be41 -->
- [x] 1.3 bump `package.json` 版本（0.1.3→0.1.5）并出 annotated tag v0.1.5，push master + tag <!-- aidcp-transport 6b4be41; 注：v0.1.4 与 package.json 0.1.3 的错位是历史遗留，本次起版本号与 tag 对齐 -->

## 2. aidcp-automation — 闸门拷贝（自持）+ 测试

- [x] 2.1 `src/schema/schema-contract.ts` + `src/schema/schema-gate.ts` 同步落地，判定逻辑层与 transport 逐字一致（diff 校验：仅剩常量区既有差异） <!-- aidcp-automation 6301f3d -->
- [x] 2.2 `test/schema/schema-contract.test.ts` 补用例：全 expand 超前放行、含 contract 拒绝、kind 缺失拒绝、waiver 兜底仍有效且与机制放行可区分 <!-- aidcp-automation 6301f3d -->
- [x] 2.3 `test/schema/schema-gate-per-owner.test.ts` 补用例：全 expand 经属主裁剪路径放行 + 告警缓存、含 contract enforce 拒绝并点名、42703 回退 <!-- aidcp-automation 6301f3d -->
- [x] 2.4 automation 全量 `npm test`（2356 过 0 挂 3 跳）+ `npm run typecheck` 通过 <!-- aidcp-automation 6301f3d -->

## 3. 消费方对齐

- [x] 3.1 aidcp-api pin 抬到 v0.1.5；npm install 未重解析 git 依赖（lock 钉旧 sha），补 `npm update aidcp-transport` 后 lock 解析到 6b4be41、pin 未被改写；typecheck 干净、583/583 <!-- aidcp-api fa4b903 -->
- [x] 3.2 aidcp-content pin v0.1.1→v0.1.5（中间带上 v0.1.2–v0.1.4 的 transport 变更）；typecheck 干净、472/472 <!-- aidcp-content 9cf92aa -->
- [x] 3.3 transport 自身 `npm test`（41/41）+ `npm run typecheck` 干净 <!-- 前置修复：transport 本地 node_modules 里 kernel 装机滞后于 pin（panel-config-http 缺 RestrictedPolicy* 导出、干净 HEAD 也红），npm ci 重装后绿——纯本地装机问题，非代码问题 -->
- 注：aidcp-automation 的 transport pin 留在 v0.1.4（其闸门为自持拷贝，本 change 不依赖 transport 的 schema 模块；升级按该仓自己的节奏，检查器只报告不拦）

## 4. 收尾

- [ ] 4.1 各仓 commit / push；本文件回写 sha
- [ ] 4.2 探明 dev ECS 现状（AIDCP_SCHEMA_GATE 模式、三服务运行形态）后按派生服务部署机制部署 dev 并健康检查
- [ ] 4.3 `openspec validate schema-gate-expand-ahead-pass --strict` 通过
