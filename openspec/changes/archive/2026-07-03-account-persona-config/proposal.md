## Why

账号"人设"（soul：identity / interests / behavior_guidelines / session_limits）当前是**一份全局 YAML**（`../aidcp-cloud/src/soul/soul.yaml`），启动时 `loadSoul()` 一次性 fail-fast 读入，并被注入**两条链路**：浏览侧经 `RoleDispatcher` 构造参数 `commonOptions.soul → this.soul`（约 11 个 agent 在各自 `buildPrompt` 内联 `soul.identity` / `soul.interests`），发布侧经 `trigger.generateInput.soul`。也就是说：**改人设必须改文件 + 重启进程，且全局只有一份**——无法按账号区分，运营在管理后台改不了。

随多账号方向（item 9），每个账号应有自己的人设。`accounts` 主表早已留有一列 `persona_ref`（当前未用）。本 change 把人设做成**管理后台可编辑、且天然按账号**：新建按 `account_id` keyed 的人设存储，沿用 soul 加载器的校验，把全局快照换成"派发时按当前账号解析"的取值口，使后台编辑**无需重启即热加载**。

短期单账号现实 = 只有 `default` 行被填充，但 schema 与 UI 从一开始就按账号设计（对齐 item 9 多账号方向；人设是喂给所有角色 prompt 的共享缝，见 item 4 结论）。

## What Changes

- **cloud（新存储）**：新建 `persona_config` 表（按 `account_id` 主键，FK 到 `accounts`，迁移号 **0011**）+ `PersonaStore`（落库 + 内存镜像，复刻 `RoleConfigStore` 时序：写库成功才刷镜像）+ `PersonaFacade`（目录 / 读 / 校验写，复刻 `role-config-facade` 外观）。写入用 soul 加载器 `loadSoulFromValue` 校验——非法人设**诚实拒绝**、绝不静默接受。
- **cloud（never-brick 回落）**：某账号无人设行 / 行为空 / 校验失败 → 回落到打包随源码的 `soul.yaml`（`loadSoul()` 的默认）。**绝不 brick**：缺人设不影响该账号正常浏览 / 发布。
- **cloud（热加载取值口）**：把 `RoleDispatcher` 启动时拍下的全局 soul 快照（`commonOptions.soul → base-role.ts this.soul`）改造为**派发时按当前账号解析人设的取值口**（getter），使后台 `PUT` 后浏览 / 发布两侧角色 prompt 即时改用新人设、无需重启。
- **console（新页）**：新增 `/persona` 路由 + 导航。列出账号、按账号编辑其人设（表单回显当前生效值 + 来源是覆盖还是回落），写**非乐观**（round-trip 后据服务端真态渲染），受 JWT 守护。
- **不动协议**：人设只在云端 prompt 注入层使用，不经边-云协议下发；**本 change 不碰 protocol.ts / command-bridge.ts / docs/protocol.md**（协议红线属 stream B）。

## Capabilities

### New Capabilities
- `account-persona-config`：账号人设可在管理后台按账号配置、按账号热加载、并以打包 soul.yaml 为永不 brick 回落。

### Modified Capabilities
<!-- 无既有 capability 被修改：人设此前无 spec，全部为新增。 -->

## Impact

- **cloud（aidcp-cloud）**：
  - 新文件 `src/config/persona-store.ts`（`persona_config` 表 + 内存镜像，复刻 `role-config-store.ts`）、`src/config/persona-facade.ts`（目录 / 校验写外观，复刻 `role-config-facade.ts`）。
  - 新迁移 `migrations/0011_persona_config.sql`（FK 到 `accounts(account_id)`）。
  - 复用 `src/soul/loader.ts` 的 `loadSoulFromValue`（写前校验）+ `loadSoul()`（打包默认回落）。
  - 改 `src/orchestrator/role-dispatcher.ts`：`commonOptions.soul` 由快照改为按当前账号解析的取值口（**本 change 是 role-dispatcher soul 访问的唯一改动方**）。
  - 改 `src/agents/base-role.ts`：`soul` 由构造期快照字段改为读取值口的 getter（约 11 个 agent 的 `this.soul` 读法不变，零回归）。
  - **APPEND** `src/server.ts`（store init + facade 装配 + 注入取值口；**只追加，绝不改 stream C 的 model-resolver 块**）、`src/panel/panel-server.ts`（人设路由，按 C→D→F→B 顺序追加）、`src/panel/types.ts`（人设面板类型，按序追加）。
  - 与 stream B 共享 `src/account-store.ts`：B 加昵称、F 激活按账号人设（`persona_ref` 语义）——**加性改动，需协调**。
- **console（aidcp-console）**：新页 `src/pages/PersonaPage.tsx`；`src/App.tsx` + `src/components/AppShell.tsx` 加 `/persona` 路由与导航；**APPEND** `src/types/api.ts`、`src/api/queries.ts`（按 C→D→F→B 顺序追加，不改他流条目）。
- **协议 / docs**：无改动（人设不经协议）。
- **迁移号**：cloud **0011**（reserved for stream F）。
- **设计**：见 `design.md`（按账号人设 schema、派发时取值口替换启动快照、回落链、人设如何到达浏览 + 发布两侧角色 prompt、留给多账号的缝）。
