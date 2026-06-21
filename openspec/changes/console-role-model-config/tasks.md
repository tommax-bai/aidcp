# Tasks — console-role-model-config

> 代码改动落 sub-repo（cloud / console），进度回写本节。实装前先 `openspec list` / 读本文件定位当前 task。

## 1. aidcp-cloud — 角色目录 + 配置存储

- [ ] 1.1 `src/config/role-catalog.ts`：合并浏览 `RoleName` 与发布 `RoleConfig.name` 为统一形状 `{ roleId, displayName, group, llmKind, tunable }`；`roleId` 加 `browse:` / `publish:` 前缀；**白名单制**只列现役且真调 LLM 角色（浏览 ~11 + 发布 5），标 `llmKind` 与 `tunable.temperature`（仅生成/改写类 true）
- [ ] 1.2 `migrations/000N_role_config.sql`：幂等建 `role_config(role_id PK, model, temperature, updated_at, updated_by)`（与 store `CREATE TABLE IF NOT EXISTS` 同源，沿用 0007 风格）
- [ ] 1.3 `src/config/role-config-store.ts`：内存镜像 + `init()` / `getForRole(roleId)`（同步、缺/空/无效回落全局 textModel 与默认温度 0、**永不抛**）/ `set(roleId, patch, by)`（**先写库成功再刷镜像**，复刻 model-config-store 时序）
- [ ] 1.4 单测：缺行回落 / 无效字段回落 / set 后 getForRole 即时变更 / 写库失败镜像不变

## 2. aidcp-cloud — LLM 客户端 per-call 覆盖（向后兼容）

- [ ] 2.1 `src/llm/qwen.ts`：`chat()/complete()` 加可选 `opts?: { role?, model?, temperature?, timeoutMs? }`；请求体 opts 优先、回落 `getModel(role)/this.temperature/this.timeoutMs`；`getModel` 升级为可接收 role；**不传 opts 行为逐字不变**
- [ ] 2.2 统一 `LlmClient` 接口（`complete + chat + 可选 opts`）；发布角色 `llmClient` 字段类型由具体 `QwenClient` 放宽为接口
- [ ] 2.3 护栏单测：不传 opts 时 model/temperature/timeout 与改造前完全一致（零回归）；传 opts 时按覆盖解析
- [ ] 2.4 既有 qwen / 发布角色单测仍绿（fetchImpl 桩签名不破坏）

## 3. aidcp-cloud — 按角色注入 + 装配 + 接口 + 可观测

- [ ] 3.1 `resolveRoleLlmConfig(roleId)` 解析器（读 RoleConfigStore，缺/空/无效回落）
- [ ] 3.2 `src/orchestrator/role-dispatcher.ts`：`commonOptions.llm` 换为 role-bound wrapper（`complete: p => llm.complete(p, resolve('browse:'+roleName))`），角色内部零改动
- [ ] 3.3 `src/server.ts`：装配 roleConfigStore（init）+ roleCatalog 注入 panel；发布侧每个 `new XxxRole` 包 wrapper（`publish:`+name）；LLM 出口记结构化日志（role + 生效 model + 耗时，不含密钥/提示词正文）
- [ ] 3.4 `src/panel/types.ts`：PanelDeps 加 `roleConfig`（getCatalog / getRoleConfig / setRoleConfig）+ 类型
- [ ] 3.5 `src/panel/panel-server.ts`：`GET /api/roles`、`GET /api/roles/:roleId/config`、`PUT /api/roles/:roleId/config`（JWT、非乐观回真态 + updatedBy/At、温度仅 tunable 角色且区间校验、非空模型名**保存前探活**不过则 400 model_invalid 绝不落库、空模型名=回落）
- [ ] 3.6 面板路由单测：GET 形状（白名单、含生效值）、PUT 回真态、无效模型 400 不落库、判定类拒温度、未鉴权 401
- [ ] 3.7 回归：`npm run typecheck` + `npm run test:acceptance`（AC-PROTO/AC-PUB/AC-RISK 红线全过）+ 全量 `npm test`

## 4. aidcp-console — 角色配置页

- [ ] 4.1 `src/types/api.ts`：`RoleCatalogItem` / `RoleConfig` DTO（与 cloud 手动同步）
- [ ] 4.2 `src/api/queries.ts`：`useRoleCatalog()` / `useRoleConfig()` + setRoleConfig mutation（invalidate）
- [ ] 4.3 `src/pages/RolesPage.tsx`：AntD Table 列表（显示名/组/模型类型/当前生效模型/温度），行内或抽屉编辑；模型名**自由输入**（空=回落）；纯规则/遗留角色不出现；判定类无温度字段；非乐观写 + 诚实文案（已保存 / 模型名无效无法保存）
- [ ] 4.4 `src/App.tsx` 加路由、`src/pages/AppShell.tsx` 加导航项
- [ ] 4.5 `npm run typecheck` + `npm test` + `npm run build` 绿

## 5. 校验

- [ ] 5.1 `openspec validate console-role-model-config --strict` 通过

## 6. 部署（显式动作，单独确认后执行）

- [ ] 6.1 cloud 安全序列部署（备份 → dry-run 暴露范围 → rsync 无 --delete → restart → healthcheck active/8787/8090/PG/飞书长连，isales 全 active）+ console rebuild & rsync dist
- [ ] 6.2 线上验证：登录面板 `GET /api/roles` 返回白名单角色与生效值；按角色改模型后该角色调用切换、无需重启；无效模型名被拒；未鉴权 401
