## Why

后台「角色配置页」目前把 18 个现役 LLM 角色平铺为一张表（仅按 `browse` / `publish` 两组分隔），缺少可运营的**分组维度**：运营想「把一批同类角色统一切到某模型」时，只能逐角色改，重复且易漏。同时模型解析当前只有**两层**（per-role 覆盖 → 全局 `textModel`），缺少介于二者之间的「一类角色共用一个默认模型」的中间层。

三条产品诉求（worklist 5 / 6 / 7）：
- **分类层（item 5）**：在角色之上引入一个**可配置的「分类」维度**（如「浏览判定类」「发布创作类」），用于后台分组查看 / 编辑 / 批量管理。分类高于现有扁平 `group`，是配置目录层概念，不进运行时角色注册表。
- **分类级模型默认 + 角色回落分类（item 6）**：让运营给「一个分类」设默认模型，分类下未单独覆盖的角色自动继承。解析顺序从两层扩成：**per-role 覆盖 → 分类默认 → 全局默认 → 代码默认**。
- **「默认模型」正名（item 7，仅正名）**：全局 `textModel` 已端到端存在、已经是事实上的默认模型、已可在「设置」页改。本期**不新造任何冗余层级**，只把它在 UI 上正名为「默认模型」，让分类 / 角色页的「回落到默认」指向清晰。坚持 YAGNI，不引入第二个全局层。

此外，按账号绑定模型是已知的未来需求（item 9 评估结论）。本 change **建好「账号维度」的数据缝**（schema 预留可空 `account_id` 列，`NULL=全部账号`），并把完整优先级链**写进契约**——但**本期不把 `accountId` 串到任何 LLM 调用点**，等真正的多账号调度落地再接线。这是 item 9 在本 change 里唯一的产出。

## What Changes

- **cloud — 分类目录层**：在 `role-catalog.ts` 给每个 `RoleCatalogItem` 加 `category`（稳定 key + 显示名），并导出分类清单与「分类 → 角色」映射。分类是**配置目录层**概念，**MUST NOT 进 `role-dispatcher.ts` 运行时角色注册表**（运行时仍按 roleId 注册 / 分发）。
- **cloud — 分类配置存储**：新增按分类的模型默认存储（落 PG，缺/空/无效一律回落，**绝不 brick**，复刻 `RoleConfigStore` 的「写库成功才刷内存镜像」时序）。
- **cloud — 解析器扩成四层（本 stream 拥有并先落）**：`server.ts` 的 `resolveModelForRole` 的回落顺序改为 **per-role 覆盖 → 分类默认 → 全局 `textModel` → 代码默认**；`resolveTempForRole` 维持现状（温度暂不引入分类层，避免过度设计）。**本 stream 拥有 server.ts 的 resolver 块并最先落地**，D / F 两 stream 把各自的 store-init / 面板依赖 wiring **append** 到其后，不得改本块。
- **cloud — 账号维度数据缝（item 9，仅建缝不接线）**：分类 / 角色配置 schema 预留可空 `account_id`（`NULL=全部账号`）；优先级链文档化为 **账号覆盖 → per-role 覆盖 → 分类默认 → 全局默认 → 代码默认**。**本期不在任何 LLM 调用点传 `accountId`**（解析永远以 `account_id IS NULL` 行命中），留缝待多账号调度落地无痛接入。
- **cloud — 面板 API**：暴露分类目录 + 分类默认的读 / 写接口（受 JWT 守护、写非乐观、无效模型名诚实拒绝），形状与现有 `/api/roles*` 一致。
- **console — /roles UI**：角色配置页按**分类**分组呈现，支持给分类设默认模型、查看各角色「生效来源」（覆盖 / 继承分类 / 继承默认）；把全局 `textModel` 在文案上**正名为「默认模型」**（不新增控件层级）。
- **DB 迁移 0009**：分类默认表 + 预留可空 `account_id` 列（见 design.md schema）。
- **不动协议**：本 change 不触 WebSocket 协议 v2（无 edge↔cloud 消息变更），不动 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`。

## Capabilities

### New Capabilities
<!-- 无新增 capability（在既有两个 capability 上增量） -->

### Modified Capabilities
- `role-llm-config`：新增「角色分类目录层（配置层、不进运行时注册表）」「分类级模型默认 + 角色回落分类的四层优先级」「可空 account_id 账号维度数据缝（NULL=全部、本期不接线，文档化五层优先级）」三条要求。
- `model-provider-config`：新增一条澄清「全局 `textModel` 即被正名为『默认模型』，是优先级链末端的全局默认，本 change 不新造冗余全局层」。

## Impact

- **cloud（aidcp-cloud）**：
  - `src/config/role-catalog.ts`：`RoleCatalogItem` 加 `category`；导出分类清单与「分类→角色」映射、`isKnownCategory()`。
  - `src/config/category-config-store.ts`（新增）：分类默认模型存储（PG + 内存镜像，绝不 brick）。
  - `src/server.ts`：**本 stream 拥有的 resolver 块**——`resolveModelForRole` 扩成四层回落（per-role → 分类 → 全局 → 代码）；append 分类 store 的 init。
  - `src/panel/panel-server.ts` + `src/panel/types.ts`：分类目录 / 分类默认读写路由与类型（reserved-order append：本 stream 为链首 C）。
  - `migrations/0009_role_category_config.sql`（新增）：分类默认表 + 可空 `account_id` 列（含 `NULL=全部` 约定）。
  - **不碰**：`src/orchestrator/role-dispatcher.ts`（运行时注册表）、`src/comm/protocol.ts`、`src/comm/command-bridge.ts`。
- **console（aidcp-console）**：`src/pages/RolesPage.tsx`（按分类分组 + 分类默认编辑 + 生效来源标注）、`src/types/api.ts` / `src/api/queries.ts`（reserved-order append，链首 C）、`src/pages/SettingsPage.tsx`（「文本模型」正名为「默认模型」文案）。
- **docs / 协议**：无协议改动；优先级链与账号缝写在本 change 的 `design.md` 与 spec delta，归档后并入 `openspec/specs/role-llm-config`。
- **迁移号**：`0009`（本 stream 独占；D=0010 / F=0011 / B=0012）。
- **红线 / 不变量**：分类 / 账号回落**绝不 brick**（任一层缺/空/无效逐级回落到代码默认）；无效模型名**诚实拒绝、不静默假成功**（沿用既有探活）；账号缝**只建不接**（本期解析恒命中 `account_id IS NULL`）。
