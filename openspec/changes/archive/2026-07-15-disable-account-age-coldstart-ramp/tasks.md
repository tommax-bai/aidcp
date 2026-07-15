# Tasks

## 1. openspec（控制仓 aidcp）

- [x] 1.1 在 `interaction-risk-gating` 规格新增「配额闸默认不做账号年龄冷启动爬坡（直接走安全限额配置）」要求 + 三个场景
- [x] 1.2 `openspec validate disable-account-age-coldstart-ramp --strict` 通过

## 2. aidcp-cloud — 冷启动改 opt-in（默认关）

- [x] 2.1 `src/server.ts`：`coldStartRampEnabled` 由 opt-out（`!== 'false'`，默认开）改 opt-in（`=== 'true'`，默认关）；更新注释与启动日志文案 <!-- aidcp-cloud 2c3d6e5 -->
- [x] 2.2 `src/risk/risk-controller.ts`：类默认由 `coldStartRampEnabled ?? true` 改 `?? false`；更新构造注释 <!-- aidcp-cloud 2c3d6e5 -->
- [x] 2.3 `test/risk-cold-start-clamp.test.ts`：对「启用态」用例显式传 `coldStartRampEnabled: true`；新增两条「默认关」用例（年轻 FB aggressive 走安全 view / 小红书 Day1 走 normal） <!-- aidcp-cloud 2c3d6e5 -->
- [x] 2.4 `npm run typecheck` + `npm run test:acceptance`(52) + `npm test`(2141) 全过（AC-RISK-* 红线不破） <!-- aidcp-cloud 2c3d6e5 -->

## 3. 集成与部署

- [x] 3.1 land 到 canonical master、推 origin <!-- aidcp-cloud 2c3d6e5 landed origin/master -->
- [x] 3.2 部署 dev（备份 → rsync 2 文件 → restart → healthcheck），确认启动日志「冷启动配额爬坡 已禁用(默认·直接走安全限额配置)」；8787 监听 / PG 就绪 / 飞书长连接已建立均通过 <!-- 2026-07-15 deployed dev(121.89.85.150) backup cloud.bak.20260715-171254 -->
- [x] 3.3 真机验收登记 backlog（FB 号 `61591753702668` aggressive 档，日 view 上限 70→500；仍受 quota_config 小时突发闸约束——**aggressive per_hour=12 疑似倒挂配置，已在收尾提示运营核对 /quotas**） <!-- 归并簇82 FB 浏览灰度 -->
