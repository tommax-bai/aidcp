# Tasks — console-role-model-config

> 代码改动落 sub-repo（cloud / console），进度回写本节。实装前先 `openspec list` / 读本文件定位当前 task。

## 1. aidcp-cloud — 角色目录 + 配置存储

- [x] 1.1 `src/config/role-catalog.ts`：合并浏览 `RoleName` 与发布 `RoleConfig.name` 为统一形状 `{ roleId, displayName, group, llmKind, tunable }`；`roleId` 加 `browse:` / `publish:` 前缀；**白名单制**只列现役且真调 LLM 角色（浏览 11 + 发布 5 + 图像 1），标 `llmKind` 与 `tunableTemperature`（仅 comment_composer/comment_de_ai_flavor/ContentCreator/ImagePlanner 为 true）<!-- aidcp-cloud 5a162ca -->
- [x] 1.2 `migrations/0008_role_config.sql`：幂等建 `role_config(role_id PK, model, temperature, updated_at, updated_by)`（与 store `CREATE TABLE IF NOT EXISTS` 同源，沿用 0007 风格）<!-- aidcp-cloud 5a162ca -->
- [x] 1.3 `src/config/role-config-store.ts`：内存镜像 + `init()` / `getForRole(roleId)`（同步、缺/空/无效回落、**永不抛**）/ `set(roleId, patch, by)`（**先写库成功再刷镜像**）/ `getAll()`（含审计字段，供面板视图）<!-- aidcp-cloud 5a162ca -->
- [x] 1.4 单测 `test/role-config-store.test.ts`：缺行回落 / 越界温度归一 null / 空模型清除 / set 后即时变更 / 写库失败镜像不变 / getAll 审计（6 pass）<!-- aidcp-cloud 5a162ca -->

## 2. aidcp-cloud — LLM 客户端 per-call 覆盖（向后兼容）

- [x] 2.1 `src/llm/qwen.ts`：`chat()/complete()` 加 `opts?: { role?, model?, temperature?, timeoutMs? }`；请求体 opts 优先、回落 `getModel(role)/this.temperature/this.timeoutMs`；`getModel` 升级接收 role，新增 `getTemperature(role?)`；**不传 opts 行为逐字不变**；新增 `onCall` 可观测钩子<!-- aidcp-cloud 5a162ca -->
- [x] 2.2 统一接口：`LlmClient`（complete-only，handler/planner 沿用不变）+ 新 `ChatLlmClient`（complete+chat）；发布 5 角色 `llmClient` 字段由具体 `QwenClient` 放宽为 `ChatLlmClient`<!-- aidcp-cloud 5a162ca 偏离：未把 LlmClient 直接加 chat（会破坏 handler/planner/edge 既有 complete-only 桩），改为新增 ChatLlmClient 子接口，更小回归面 -->
- [x] 2.3 护栏单测 `test/qwen-per-call-opts.test.ts`：不传 opts 零回归 / opts.role 解析 / 显式覆盖优先 / getTemperature undefined 回落 / onCall 不含 prompt（5 pass）<!-- aidcp-cloud 5a162ca -->
- [x] 2.4 既有 qwen / 发布角色单测仍绿（full suite 296 pass / 0 fail）<!-- aidcp-cloud 5a162ca -->

## 3. aidcp-cloud — 按角色注入 + 装配 + 接口 + 可观测

- [x] 3.1 `resolveModelForRole/resolveTempForRole`（server 内闭包，读 RoleConfigStore，缺/空/无效回落全局/默认）<!-- aidcp-cloud 5a162ca -->
- [x] 3.2 `src/agents/base-role.ts`：`decide()` 传 `{ role: 'browse:'+roleName }`；llm 类型加可选 opts（弱接口，测试桩仍只需 complete）。浏览角色内部零改动<!-- aidcp-cloud 5a162ca 偏离：注入侧未在 dispatcher 包 wrapper，而是 BaseRole 自带 roleName 直接透传 role，更省改动 -->
- [x] 3.3 `src/server.ts`：装配 roleConfigStore（init）+ QwenClient 注入 resolveModel/resolveTemp/onCall；发布侧 5 个 `new XxxRole` 用 `roleLlm('publish:'+name)` 包 role-bound wrapper；LLM 出口结构化日志（role + model + ms，无密钥/prompt）<!-- aidcp-cloud 5a162ca -->
- [x] 3.4 `src/panel/types.ts`：PanelDeps 加 `roleConfig`（getCatalog / setRoleConfig）+ RoleConfigRowView / RoleConfigCatalogView / RoleConfigSetResult 类型<!-- aidcp-cloud 5a162ca -->
- [x] 3.5 `src/panel/panel-server.ts`：`GET /api/roles`、`PUT /api/roles/:roleId/config`（JWT、非乐观回真态、温度仅 tunable 角色且区间校验、非空模型名**保存前探活**不过 400 model_invalid 绝不落库、空模型名=回落、未知角色 404、未注入 503）<!-- aidcp-cloud 5a162ca 偏离：GET /api/roles/:roleId/config 折叠进 catalog GET（catalog 已回每角色生效值），未单列单角色 GET -->
- [x] 3.6 校验/探活逻辑抽到 `src/config/role-config-facade.ts`（注入式 probe，可单测）；`test/role-config-facade.test.ts`（8 pass）+ `test/role-config-panel.test.ts`（HTTP 路由 401/200/404/400/503，2 pass）<!-- aidcp-cloud 5a162ca 增项：facade 抽取使红线校验+探活可脱离 server 单测 -->
- [x] 3.7 回归：`npm run typecheck` 干净 + `npm run test:acceptance`（AC 红线 18/18）+ 全量 `npm test`（296/0）<!-- aidcp-cloud 5a162ca -->

## 4. aidcp-console — 角色配置页

- [x] 4.1 `src/types/api.ts`：`RoleConfigRow` / `RoleConfigCatalog` DTO（与 cloud RoleConfigRowView 手动同步）<!-- aidcp-console c1e7841 -->
- [x] 4.2 `src/api/queries.ts`：`useRoleConfig()` GET /api/roles（apiPut 已通用）<!-- aidcp-console c1e7841 -->
- [x] 4.3 `src/pages/RolesPage.tsx`：AntD Table（显示名/组/类型/生效模型/温度）+ Modal 编辑；模型名**自由输入**（空=回落）；判定类无温度字段；图像角色只读（全局配置）；非乐观写 + 诚实文案（model_invalid → 探活未通过）<!-- aidcp-console c1e7841 -->
- [x] 4.4 `src/App.tsx` 加 `/roles` 路由、`src/pages/AppShell.tsx` 加「角色配置」导航项（RobotOutlined）<!-- aidcp-console c1e7841 -->
- [x] 4.5 `npm run build`（tsc + vite）绿 + `npm test`（vitest）pass<!-- aidcp-console c1e7841 -->

## 5. 校验

- [x] 5.1 `openspec validate console-role-model-config --strict` 通过

## 6. 部署（显式动作，单独确认后执行）—— 未执行，待确认

- [ ] 6.1 cloud 安全序列部署（备份 → dry-run 暴露范围 → rsync 无 --delete → restart → healthcheck active/8787/8090/PG/飞书长连，isales 全 active）+ console rebuild & rsync dist
- [ ] 6.2 线上验证：登录面板 `GET /api/roles` 返回白名单角色与生效值；按角色改模型后该角色调用切换、无需重启；无效模型名被拒；未鉴权 401
