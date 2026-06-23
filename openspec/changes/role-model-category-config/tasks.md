> **并行协调（5-stream 同期作业，本 stream = C：role-model-category-config）**
> - **迁移号**：本 stream 独占 `0009`（D=0010 safety-quota / F=0011 account-persona / B=0012 account-real-nickname；A 看板无迁移）。勿占用他号。
> - **server.ts resolver 块归属**：本 stream **拥有** `resolveModelForRole` / `resolveTempForRole` 与共享 LLM 客户端 wiring，且 **最先落地（LANDS FIRST）**。D / F 只把各自 store-init + 面板依赖 wiring **append** 在其后，**绝不改本 resolver 块**；D / F 把自己的 server.ts wiring rebase 到本 stream 之上。
> - **协议红线**：协议 v2 由 stream B 独占（两份 `protocol.ts` + `command-bridge.ts` + `docs/protocol.md` + edge `edge-client.ts` onMessage 白名单）。**本 stream 不触协议**（无 edge↔cloud 消息变更）。
> - **共享卡点文件 reserved-order append（C→D→F→B）**：本 stream 为链首 C，可先落但须为后续 stream 留干净 append 缝——
>   - cloud `src/panel/panel-server.ts` 路由链、`src/panel/types.ts`；
>   - console `src/types/api.ts`、`src/api/queries.ts`。
> - **console 路由 / 导航**：本 stream 复用既有 `/roles`（不新增路由）；D 加 `/quotas`、F 加 `/persona`（App.tsx + AppShell.tsx）—— 本 stream 不动这两处导航注册。
> - **item 9 边界**：本 stream 是 item 9 唯一产出方 —— 只建可空 `account_id` 数据缝，**不**把 `accountId` 串进任何 LLM 调用点（不为 item 9 单开 change）。
> - **不碰运行时注册表**：分类是配置目录层，**不进** `src/orchestrator/role-dispatcher.ts`。

## 1. aidcp-cloud — 分类目录层 + 分类默认存储 + 四层解析器（拥有 resolver，先落）

- [ ] 1.1 `src/config/role-catalog.ts`：`RoleCatalogItem` 加 `category`（稳定 key）；给 18 个角色归类（判定 / 撰写改写 / 发布创作 / 发布裁决 / 图像）。
- [ ] 1.2 `src/config/role-catalog.ts`：导出分类清单（key + 中文显示名 + 排序）、`categoryOf(roleId)`、`rolesInCategory(categoryId)`、`isKnownCategory(categoryId)`。
- [ ] 1.3 `migrations/0009_role_category_config.sql`：建 `category_config`（`category_id` / 可空 `account_id` / `model` / 审计列）+ 两个部分唯一索引（`account_id IS NULL` 全局唯一、非空 (category,account) 唯一）；幂等，含 `NULL=全部账号` 注释。
- [ ] 1.4 `src/config/category-config-store.ts`（新增）：分类默认模型存储（PG + 内存镜像）；读路径恒 `account_id IS NULL`；缺/空/异常返「无覆盖」、绝不抛、绝不 brick；写库成功才刷镜像；建表 SQL 与 0009 同源幂等。
- [ ] 1.5 `src/server.ts`（**本 stream 拥有的 resolver 块**）：`resolveModelForRole` 扩成四层回落（per-role → 分类默认 → 全局 textModel → 代码默认）；`resolveTempForRole` 不变（温度不引入分类层）；不传 role 仍走全局（planner/select/探活零回归）。
- [ ] 1.6 `src/server.ts`：append `categoryConfigStore` 的构造 + `init()`（init 失败 catch 块照现状 warn 并继续，退化为两层），位置在既有 store init 之后，**不动 resolver 块以外的 D/F append 缝**。
- [ ] 1.7 确认 `src/orchestrator/role-dispatcher.ts` 零改动（分类不进运行时注册表）。

## 2. aidcp-cloud — 面板 API（reserved-order append，链首 C）

- [ ] 2.1 `src/panel/types.ts`：append 分类目录行 + 分类默认读写形状类型（含「生效来源」标注：覆盖 / 继承分类 / 继承默认）。
- [ ] 2.2 `src/panel/panel-server.ts`：append 分类目录读路由 + 分类默认 `GET`/`PUT` 路由（受 JWT 守护、写非乐观回真态、未知 `category_id` 拒、非空模型名保存前探活失败诚实拒 `model_invalid`）。
- [ ] 2.3 `GET /api/roles`（或其分类视图）返回每角色的 `category` + 当前生效模型与「生效来源」。

## 3. aidcp-console — /roles UI 按分类分组 + 默认模型正名

- [ ] 3.1 `src/types/api.ts`：append 分类目录 / 分类默认 / 生效来源类型（reserved-order，链首 C，留 D/F append 缝）。
- [ ] 3.2 `src/api/queries.ts`：append 分类目录读 + 分类默认读写 query（reserved-order）。
- [ ] 3.3 `src/pages/RolesPage.tsx`：角色列表按分类分组；每分类可设默认模型（保存非乐观、无效模型名诚实文案）；每角色标注「生效来源」（覆盖 / 继承分类 / 继承默认）。
- [ ] 3.4 `src/pages/SettingsPage.tsx`：把「文本模型」文案正名为「默认模型」（不新增控件 / 层级，仅文案与说明）；RolesPage 回落说明同步指向「默认模型」。

## 4. 验证

- [ ] 4.1 cloud 单测：`resolveModelForRole` 四层回落（per-role > 分类 > 全局 > 代码）+ 不传 role 零回归 + 分类存储异常退化两层不 brick。
- [ ] 4.2 cloud 单测：`category-config-store` 缺/空/无效回落、写库成功才刷镜像、未知 category 拒、无效模型名探活失败 `model_invalid` 不落库。
- [ ] 4.3 cloud 单测：0009 迁移幂等可重复执行；`account_id IS NULL` 全局行唯一约束生效；本期读路径恒命中 NULL 行（账号专属行不参与解析）。
- [ ] 4.4 cloud `npm run typecheck` 绿（两份 protocol.ts 未漂移——本 change 不触协议，AC-PROTO 应零变化）→ `test:acceptance`（AC-PROTO/PUB/RISK 全过）→ `test`。
- [ ] 4.5 console `npm run typecheck` + build 绿；/roles 分类分组与「默认模型」正名页面手测（分类设默认→同类无覆盖角色生效来源变「继承分类」；改默认模型→回落角色随动）。
- [ ] 4.6 确认 role-dispatcher 运行时分发未受影响（浏览闭环 / 发布管线角色注册与调度无变化）。

## 5. 收尾与部署

- [ ] 5.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）。
- [ ] 5.2 `openspec validate role-model-category-config --strict` 通过。
- [ ] 5.3 cloud 改动按 §5 安全序列部署 ECS（先备份 → rsync → restart → healthcheck：0009 迁移已跑 / 分类存储就绪 / 解析四层生效 / PG select 1）；console 部署到 8088（与 isales 隔离）。
- [ ] 5.4 上线后核对：分类默认改动热加载即生效、生效来源标注正确、默认模型正名文案落地；账号缝仅建未接（解析恒 NULL 行）。
- [ ] 5.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/role-llm-config` 与 `openspec/specs/model-provider-config`）。
