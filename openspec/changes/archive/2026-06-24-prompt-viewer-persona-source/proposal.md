## Why

只读「角色 prompt 查看器」已上线（change `role-prompt-visibility`，已归档）：后台能看到每个角色**忠实渲染**的真实 prompt，但展示为**一坨扁平文本**——运营分不清哪段是「该角色独有的指令」、哪段是「带进来的账号人设（soul）」。

随人设抽到账号维度（change `account-persona-config`），人设成为**喂给所有角色 prompt 的共享缝**：运营看某条 prompt 时需要一眼分清「角色独有指令 vs 来自账号人设」，才能判断「改账号人设会波及哪些角色的哪一段」。

本 change 在**不改任何角色 prompt 构建逻辑**（延续 `role-prompt-visibility` 红线：线上 prompt 行为零变化）的前提下，给只读查看器加「人设来源段标注」：**背景色 + 顶部图例**。

## What Changes

- **cloud（预览层分段）**：在只读预览汇集层，对每个浏览角色尝试把 prompt 拆成「角色段 / 人设段」交替的分解。人设段由角色自己用 `this.soul`、以与 `buildPrompt` **相同的拼接逻辑**重新派生，再在**已渲染的** prompt 里**精确定位**——渲染与定位同源（同一次 soul 读取），**不改 buildPrompt、不手抄第二份人设文本**（避免 `role-prompt-visibility` 当初否决的漂移）。
- **cloud（角色只读入口）**：各浏览角色加只读 `personaSegments(): string[]`，返回它构建的人设片段。**尽力标整段人设**（身份 + 兴趣等）；把人设被运行时内容拆开的角色（如搜索/无收获场景：「你是「X」…」与「兴趣领域：…」之间插了运行时场景）返回**多片段**、各自独立定位。这是与既有 `previewPrompt()` 并列的**新增只读方法**，不动 buildPrompt。
- **cloud（两道诚实闸，绝不瞎标）**：定位每个人设片段时——① **唯一性**：片段在渲染 prompt 里必须恰好出现一次（出现 0 次或多于一次即判失败，防止误标到指令体/示例数据里的相同字样）；② **拼接等值**：切出的各段拼回必须**逐字等于**扁平 prompt。任一闸不过 → 该角色**回落为不标注的扁平 prompt**（`available:true` + 诚实 note），**绝不伪造跨度、绝不抛、单角色失败不连累其它角色**。瞎标（声称某段来自人设而其实不是）= 软性「静默假成功」，被此两道闸堵死。
- **cloud（返回体向后兼容）**：预览返回体**保留扁平 `prompt` 字段**，新增**可选** `segments` 字段（`source: 'role' | 'persona'` + `text`）。未升级的查看器仍能用 `prompt` 正常显示。**同 `GET /api/roles/:roleId/prompt` 路由，仅返回体更丰富，无新路由、无写路径。**
- **console（弹窗渲染）**：「查看 Prompt」弹窗——有 `segments` 时按段渲染，人设段加**浅背景色** + 弹窗**顶部一条图例**（「有底色 = 来自账号人设」）；无 `segments` 回落今天的扁平展示。**不做内联文字标记**（保 prompt 整段可复制、不污染等宽文本）；图例是文字说明，不只靠颜色区分。

**明确不做（OUT OF SCOPE / YAGNI）**：
- **覆盖 vs 默认回落** 的来源细分（不把人设存储层 `PersonaFacade` 拖进只读预览层，保持本 change 只在查看器文件内自洽）。
- **发布侧标注**（沿用当前 browse-only；发布预览本就 `available:false`）。
- prompt 编辑 / 模板抽取 / 版本（被否的 Option B）；新路由 / 迁移 / 协议改动。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `role-llm-config`：新增一条要求——只读 prompt 预览 MAY 标注来自账号人设的段（尽力而为 + 唯一定位 + 拼接等值两道闸 + 定位不到则回落扁平不标记，绝不瞎标、绝不改 buildPrompt、返回体向后兼容）。

## Impact

- **cloud（aidcp-cloud）**：
  - 改 `src/config/role-prompt-preview.ts`：在 `safePreview` 渲染 prompt 后对每个浏览角色尝试人设分段（调 `personaSegments()` + 精确定位 + 两道闸 + 回落）。
  - 各 `src/agents/*.ts`（~11 浏览角色）加只读 `personaSegments(): string[]`（从 `this.soul` 同 `buildPrompt` 拼接逻辑派生人设片段；**不改 buildPrompt**）。
  - **APPEND** `src/panel/types.ts`：`RolePromptView` 加可选 `segments` 字段（不改既有 `prompt` / `available` / `note` 形状；按 C→D→F→B 顺序追加）。
  - `src/panel/panel-server.ts`：路由不变（同 `GET /api/roles/:roleId/prompt`），返回体带上 `segments`；**无新路由、无写路径**。
  - **不动** `src/server.ts` 的 stream C resolver 块。
- **console（aidcp-console）**：
  - 改 `src/pages/RolesPage.tsx`：弹窗在有 `segments` 时渲染背景色 + 顶部图例；无则回落扁平。
  - **APPEND** `src/types/api.ts`：`RolePromptView` 加可选 `segments`（镜像 cloud，不改他流条目）。
- **协议 / 迁移**：无（只读、无 DB、不碰协议）。
- **红线**：只读、无写；**不改任何 buildPrompt**（线上 prompt 零变化）；定位不唯一 / 拼接不等 → 回落不标记（**绝不瞎标 = 软性静默假成功**）；单角色失败不连累其它角色与浏览/发布闭环。
- **排序**：本 change 在 stream F（`account-persona-config`）之后落更有意义（那时人设按账号解析，标注的就是当前账号人设）；但标注对「当前解析出的人设」即可工作（今天是全局 soul，F 落地后是按账号），**不硬阻塞 F**。append-only 在共享 chokepoint 文件，遵守 C→D→F→B 顺序，**不碰协议（stream B）与 C 的 resolver 块**。
