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

- [x] 4.1 各仓 commit / push；本文件回写 sha <!-- aidcp-transport 6b4be41(+tag v0.1.5) / aidcp-automation 6301f3d / aidcp-api fa4b903 / aidcp-content 9cf92aa，全部已推 origin/master -->
- [x] 4.2 dev 部署完成并逐服务健康检查 <!-- 2026-08-07 deployed。探明现状：三派生服务 active、AIDCP_SCHEMA_GATE=enforce（三份 .env 均显式 enforce）。逐服务：备份 tar（automation.bak.20260807-105159 / api.bak.20260807-105333 / content.bak.20260807-105447）→ rsync（--exclude .env/node_modules/.git；api、content 另随包送 node_modules/aidcp-transport@0.1.5，ECS 装不了私有 git 依赖）→ automation stop-then-start、api/content restart → 三服务 active + 启动日志契约门通过行 + 8787/8090 在听。无新迁移，未动账本。文档同步：docs/deployment-environments.md 的 Schema Contract Gate 节与 Rollback 第 5 步已改为分类判定口径 -->
- [x] 4.3 `openspec validate schema-gate-expand-ahead-pass --strict` 通过
