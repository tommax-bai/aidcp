## Context

后台「角色配置页」已有只读 prompt 预览（change role-prompt-visibility + prompt-viewer-persona-source，需求并入 `role-llm-config` spec）。其渲染链路坐实如下：

- 预览 provider：`createRolePromptProvider(() => previewDispatcher.getRoles())`（`aidcp-cloud/src/server.ts:1058`），`get(roleId)` 调角色实例的同步 `previewPrompt()`。
- 预览 dispatcher：`previewDispatcher = buildDispatcher({ accountId: 'default', ... })`（`server.ts:847`）——独立私有总线、从不启动会话/下发指令，**当前账号恒为 `default`**。
- 人设解析：角色实例的 `getSoul` 注入为 `() => this.resolveSoul()`（`role-dispatcher.ts:390`），`resolveSoul()` 读**可变**的 `currentAccountId` 并经 `getSoulFn(currentAccountId)` 解析（`:289`）。`getSoulFn` 即 `getSoul = (accountId?) => resolvePersona(accountId)`（`server.ts:479`），`resolvePersona = createPersonaResolver({ store: personaStore, fallbackSoul })`——按账号取人设行，**缺行回落打包 `soul.yaml`**（永不 brick）。
- 当前账号可切：`RoleDispatcher.setCurrentAccountId(accountId)`（`:364`）+ `get accountId()`（`:369`）。
- 人设是否真有行可判：`personaStore.getForAccount(accountId) !== null`（`server.ts:814` 已用于诚实闸 `isPersonaBound`，**不走会回落默认的解析器**）。

约束（红线）：纯只读、不改任何角色 `buildPrompt`/`previewPrompt` 逻辑、单角色失败优雅降级不连累闭环、绝不误标人设段（软性「静默假成功」）、向后兼容旧查看器。

## Goals / Non-Goals

**Goals:**

- 运营能在角色配置页选一个账号，按**该账号人设**查看任意文本角色的 prompt 预览。
- 选定账号无人设行时**诚实标注**回落默认人设，绝不冒充。
- 不传 `accountId` 时行为与现状逐字一致（向后兼容）。

**Non-Goals:**

- 不改任何角色的 prompt 构建逻辑、不新增可写 prompt 的路径（本期仍纯只读）。
- 不渲染发布侧 prompt（沿用现状：发布侧暂只标 available:false）。
- 不为预览引入按账号的角色/模型配置（角色配置仍全局，本变更只换**人设内容**这一维度）。
- 不动边-云协议、风控、数据库迁移。

## Decisions

### D1：用「临时切预览 dispatcher 当前账号 → 同步渲染 → 还原」注入选定人设（Option C）

`get(roleId, accountId?)` 在 accountId 给定时：读回当前账号 `prev = previewDispatcher.accountId` → `setCurrentAccountId(accountId)` → 同步调 `previewPrompt()`（含人设段派生）→ `finally` 还原 `setCurrentAccountId(prev)`。

- **为何可行且安全**：`previewPrompt()` 与人设段派生全程**同步**，Node 单线程，单次 `get()` 调用内无 await、无交错，故「切—渲染—还原」是原子的，不会与并发预览请求互相污染。还原放 `finally`，渲染抛错也保证账号复位。
- **为何不选「给每个角色加 `previewPrompt(soulOverride)`」**：要改 35 个角色的 previewPrompt + 透传 override 进 buildPrompt，面广、易漂移、违背「不改角色构建逻辑」红线。
- **为何不选「每账号建一束预览 dispatcher 缓存」**：buildDispatcher 造私有总线/控制器/订阅，为只读预览按账号留多束 dispatcher 浪费且状态多；单束 + 切账号已够。

provider 不直接持有 dispatcher，而由 `server.ts` 接线时注入两个薄函数：`getRoles()`（现有）+ `withAccount(accountId, fn)`（封装切—还原），保持 provider 对 dispatcher 解耦、可单测。

### D2：诚实回落标注（绝不冒充）

provider 收到 accountId 后，先用**不回落的** `personaStore.getForAccount(accountId)` 判断该账号是否真有人设行：

- 有行 → 正常渲染，标注「所用账号 = accountId（真实人设）」。
- 无行（且 accountId ≠ 'default'）→ 渲染仍成功（解析器回落 `soul.yaml`），但返回体 `note` 明示「该账号未配人设，预览用默认人设」并置 `personaFallback:true`。
- accountId 缺省 → 现状语义：系统默认人设，note 不变。

判定口同样由 `server.ts` 接线注入（`hasPersona(accountId): boolean`），provider 不直连 store。

### D3：接口与返回体（向后兼容）

- 路由：`GET /api/roles/:roleId/prompt` 解析可选 `?accountId=`（`panel-server.ts`）。非法/未知账号不报错——透传给 provider，按 D2 回落标注即可（预览是只读探查，不该 4xx 挡路）。
- `RolePromptView` 增加两个**可选**字段：`accountId?`（本次预览所用账号）、`personaFallback?`（true=该账号无人设、用了默认）。既有 `prompt` / `available` / `note` / `segments` 字段不变；旧查看器忽略新字段照常工作。

### D4：console 选择框落在「角色模型配置」卡片，驱动既有弹窗

- 在 `/roles` 的「角色模型配置」卡片加一个账号选择框（复用 `GET /api/accounts` 列表；选项展示账号 label/id，可附「未配人设」灰标）。选框值存页面 state，默认空=系统默认人设。
- 「查看 Prompt」按钮打开弹窗时，按当前选框值拉 `GET /api/roles/:id/prompt?accountId=<选定>`；弹窗内复用既有分段渲染；`personaFallback` 为真时在弹窗顶部 Alert 明示「该账号未配人设，下示为默认人设」。
- 选框改变且弹窗已开时重拉刷新（预览随选定账号更新）。

## Risks / Trade-offs

- **[切—还原期间被并发预览请求观察到非默认账号]** → 不会：单次 `get()` 同步执行、无 await，事件循环不会在切与还原之间插入另一个请求的渲染；还原置于 `finally` 兜底渲染抛错路径。
- **[误把默认人设当作选定账号人设展示]** → 由 D2 用不回落的 `getForAccount` 判定 + `personaFallback` 标注堵死；前端必须把该标志显式呈现，绝不静默。
- **[人设段标注在切账号后失配]** → 既有两道诚实闸（每片段唯一定位 + 拼接逐字等值）对**当前渲染的** prompt 与**当前账号的**人设段一起判定，账号切换后两边同源，不过闸即回落扁平不标注，不会误标。
- **[选定账号无在线边缘/未启会话]** → 无关：预览只读人设库 + 同步渲染，不依赖边缘连接或会话状态。
- **[未知/拼错 accountId]** → 解析器回落默认 + `personaFallback:true` 标注，诚实可见，不 500。

## Migration Plan

- 部署：随 cloud 常规发布（rsync + restart），console 重新 build 出静态。无数据库迁移、无协议变更，零数据回填。
- 回滚：纯增量、可选参数与可选字段；回滚 cloud/console 到前一版即恢复「恒默认账号预览」，无残留状态。
- 验证：`AC-*` 安全红线全过（本变更不碰风控/发布，重点回归 prompt 预览既有用例 + 新增 accountId 用例）；console typecheck + build。

## Open Questions

- 选择框是否需要把「无人设的账号」过滤掉而非灰标？默认**保留并灰标**（运营仍可预览其默认人设效果，且与诚实回落标注一致）；若运营更想只列已配人设账号，可在实装期按一行过滤切换。
