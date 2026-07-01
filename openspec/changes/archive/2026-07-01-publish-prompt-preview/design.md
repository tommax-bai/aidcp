## Context

后台角色配置页的只读 prompt 查看器由 change `role-prompt-visibility`（Option A，忠实渲染）引入：

- 预览提供方 `createRolePromptProvider(getBrowseRoles, opts)`（`aidcp-cloud/src/config/role-prompt-preview.ts`）按 roleId 分派：浏览侧从已注册角色实例取 `previewPrompt()` 忠实渲染；发布侧当前直接返回 `available:false` + 诚实占位 note（V1 只做浏览侧）。
- 浏览侧的忠实渲染范式：每个浏览角色暴露 `previewPrompt()`（内部调既有 `buildPrompt(示例数据)`，占位串用 `<示例…>`），可选 `personaSegments()` 供按账号人设高亮。
- 接口 `GET /api/roles/:roleId/prompt`（JWT 守护，`panel-server.ts`）；返回形状 `RolePromptView`（`prompt|null` / `available` / `note` / 可选 `segments` / `accountId` / `personaFallback`）。前端 `RolesPage.tsx` 已能渲染 `available:true` 的扁平 prompt（无 segments 走扁平分支）。

发布侧 prompt 不是角色实例上的方法，而是发布管线里一组**独立构建函数**（`aidcp-cloud/src/publish-agent/prompts.ts`），各吃强类型入参（类型在 `publish-agent/types.ts`）：

| 角色（roleId） | 显示名 | 构建函数 | 入参 |
| --- | --- | --- | --- |
| `publish:ContentScout` | 发布选题侦察 | `buildScoutPrompt` | `TriggerInput` |
| `publish:ContentCreator` | 技术帖文案创作 | `buildCreatorPrompt` | `ScoutDecision, TriggerInput` |
| `publish:TitleCreator` | 技术帖标题创作 | `buildTitlePrompt` | `body, persona, styleType, seedTitle?` |
| `publish:ImageSetPlanner` | 配图选题 | `buildImageSetPlanPrompt` | `CreatedContent, maxImages` |
| `publish:ImagePromptComposer` | 配图指令 | `buildImagePromptComposerPrompt` | `{subject,intent?}, styleHint\|null` |
| `publish:QualityScorer` | 内容质量评分 | `buildAssemblerPrompt` | `CreatedContent, {aiScore,flaggedPhrases,rewritten}` |
| `publish:ApprovalGatekeeper` | 发布审批裁决 | `buildGatekeeperPrompt` | `AssembledContent` |
| `publish:ImageGenerator` | 配图生成执行 | （无文本 prompt） | 吃配图指令输出 + 固定风格常量 |

关键差异：**发布侧 prompt 骨架基本是写死字面量**（角色设定、评分规则、输出 JSON 契约、few-shot/负例、禁用词均为常量），运行时数据只填进带标签的占位槽；其正文人设是构建函数**内置默认写死**（如文案创作里的默认人设），并**不随账号切换**（浏览侧才用 per-account 的 soul）。

## Goals / Non-Goals

**Goals:**
- 让 7 个发布文本角色在后台 `available:true` 显示真实 prompt，与浏览侧同为「忠实渲染」——复用其真实 `build*Prompt` + 最小合法示例输入。
- 发布侧人设口径诚实：按内置默认渲染；给定 `accountId` 时明示「发布侧人设为内置默认、不随账号切换」，绝不伪造账号维度。
- 全程只读、渲染失败优雅降级，不改任何 `build*Prompt` 逻辑（线上 prompt 零变化）。

**Non-Goals:**
- 不做发布侧「按账号人设高亮/回落」（`segments` / `personaFallback`）——发布人设当前不随账号切，V1 不附来源段，留后续。
- 不做可编辑 prompt（Option B 模板抽存库，仍 YAGNI）。
- 不改发布侧 prompt 构建逻辑、不改配图生成执行（保持不可预览）。

## Decisions

**决策一：发布预览用「示例输入注册表」调真实 builder，而非另抄一份 prompt 文本。**
新增一个 roleId → 渲染闭包的小注册表（`Record<publishRoleId, () => string>`，每个闭包用示例入参调对应 `build*Prompt`），置于 `publish-agent/` 下（如 `prompts-preview.ts`）或预览提供方内。预览提供方发布分支由「统一 `available:false`」改为「查表 → 有则忠实渲染 → 无则回落既有诚实 note」。
- 为什么：与浏览侧一致的「忠实渲染」范式——看到的就是线上真用的字面量，零漂移；「另抄一份常量」生而漂移，否决（与 `role-prompt-visibility` 同一理由）。
- 示例输入沿用浏览侧 `<示例…>` 占位约定（如 `title: '<示例正文标题>'`、metrics 用小整数、concepts/materials 给 1 条示例），实时字段一望即知是占位；`PLACEHOLDER_NOTE` 复用。

**决策二：注册表只调既有 builder、不改其逻辑。** 闭包纯粹构造示例入参并调用导出的 `build*Prompt`。`build*Prompt` 本体一字不改（线上 prompt 行为零变化，回归可断言）。示例入参用 `publish-agent/types.ts` 的类型对齐，编译期即锁形状。

**决策三：发布侧不接 `accountId` 人设维度，但诚实标注。** 发布正文人设是内置默认、渲染与账号无关。故：
- 不传 `accountId`：忠实渲染，`available:true`，用 `PLACEHOLDER_NOTE`。
- 传 `accountId`：仍按内置默认渲染，note 明示「发布侧 prompt 的人设为内置默认，不随账号切换」；**不**设 `personaFallback`（那是「本该按账号、但该账号没配」的语义，此处不适用，设了会误导）；**不**附 `segments`。
- 为什么：绝不把「不随账号切」伪装成「按账号切了/回落了」——误标等同软性静默假成功。

**决策四：配图生成执行保持 `available:false`。** 它无文本 prompt，命中 `llmKind !== 'text'` 分支返回既有图像 note，本 change 不动。

**决策五：发布渲染失败与浏览侧同样降级。** 注册表闭包渲染以 try 包裹（复用 `safePreview` 或等价包裹），单角色抛错 → `available:false` + 原因，绝不抛、绝不崩、绝不连累发布闭环。

## Risks / Trade-offs

- **[示例输入与 builder 形状漂移]** builder 若日后改签名/字段，示例输入可能编译不过或渲染异常 → 用 `types.ts` 强类型入参（编译期兜底）+ 单测断言 7 角色 `available:true` 且 prompt 非空（CI 兜底）。
- **[示例输入不代表性/误导运营]** 占位数据太假可能让运营误读 → 沿用 `<示例…>` 显式占位 + 保留 `PLACEHOLDER_NOTE`「实时数据为示例占位」；骨架（规则/契约/few-shot）本就是线上真字面量，代表性由骨架保证。
- **[发布人设未来改为按账号]** 若发布转向 per-account 人设，本 change 的「内置默认」标注会失真 → 届时另开 change 补发布侧 `accountId` 人设 + 来源段（本 change 已在 spec/note 里把「内置默认」讲清，升级点明确）。
- **[渲染副作用]** builder 理论上应纯函数、无副作用；示例输入不触真实发布 → 复核 7 个 builder 均为纯拼串（无 IO/无状态写），注册表只在预览请求时调用。

## Migration Plan

纯只读、无 DB/协议/迁移。落 cloud 后经既有安全序列部署（备份 → rsync → restart → healthcheck）；上线后逐个发布 roleId `GET /api/roles/:id/prompt` 核 `available:true` 且 prompt 非空、配图生成仍 `available:false`。回滚即还原上一版 `role-prompt-preview.ts`（发布分支退回 `available:false`），零数据影响。

## Open Questions

- 无。（发布侧人设按账号切与否已定：V1 不做、诚实标注、留后续。）
