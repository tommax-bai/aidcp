# Design — prompt-viewer-persona-source

## 背景与现状（带文件:行）

- 只读查看器已上线（`role-prompt-visibility`，已归档 `2026-06-23`）：cloud `src/config/role-prompt-preview.ts` 按 `roleId` 汇集预览，每个浏览角色 `previewPrompt()` 调自己**真实的** `buildPrompt(示例数据)` + 真实 `this.soul` 渲染；`safePreview()` try 包裹降级，返回 `{ available, prompt, note }`（`src/panel/types.ts` 的 `RolePromptView`）。面板 `GET /api/roles/:roleId/prompt`（JWT，**只读无写**）。console `src/pages/RolesPage.tsx`「查看 Prompt」弹窗等宽可滚展示**扁平** prompt + 顶部 Alert 说明占位。
- 人设注入（soul）：各浏览角色在 `buildPrompt` 内联读 `this.soul`（identity / interests 等）。**多数角色**把人设作为开头一句**连续**文本（例 `src/agents/comment-composer.ts:118` `你是「${identity.name}」，${identity.role}。语气：${identity.tone}。兴趣：${interestsStr}。`）；但**并非全部连续**——搜索/无收获场景角色 `src/agents/search-evaluator.ts:159-162` 把「你是「name」，role。」与「兴趣领域：…」用**运行时内容**（连续滚动无收获场景）隔开，人设被拆成**多片段**。
- 痛点：查看器把 prompt 当一坨，分不清「角色独有指令」vs「账号人设」；随人设抽账号维度（`account-persona-config`），「哪段是共享人设」是运营关心的信息。

## 决策一：在预览层重新派生人设段 + 精确定位（不改 buildPrompt，不手抄第二份）

两条歧路都否决：
- **字符串包裹**（在模板里给人设加标记）→ 要改 `buildPrompt` = `role-prompt-visibility` 红线。否决。
- **描述符目录**（另写一份人设文本给前端标）→ 重蹈 `role-prompt-visibility` 当初否决的**漂移**（手抄第二份会和真 `buildPrompt` 脱节）。否决。

**选**：预览层用**同一份** `this.soul` 重新派生人设片段、在 `previewPrompt()` **已渲染的结果**里精确定位。渲染与定位**同源**（同一次 soul 读取），无第二份可漂移；`buildPrompt` 不动。

## 决策二：人设片段来源 = 角色自己的只读 `personaSegments()`

- 给每个浏览角色加只读 `personaSegments(): string[]`，用 `this.soul` 以与 `buildPrompt` **相同的拼接逻辑**产出人设片段。新增只读代码、不改 `buildPrompt`（与既有 `previewPrompt()` 并列）。
- **尽力标整段人设**（用户决策）：连续人设角色返回**单片段**；把人设拆开的角色（如 `search-evaluator`）返回**多片段**（身份句 + 兴趣句），各自独立定位。
- 角色没实现 `personaSegments()` / 返回空 → 预览层对该角色**直接不出** `segments`（扁平）。

## 决策三：两道诚实闸（绝不瞎标 = 软性静默假成功）

预览层定位每个片段时：
1. **唯一性**：片段在渲染 prompt 里必须**恰好出现一次**（`indexOf === lastIndexOf`）。0 次（定位失败）或 >1 次（歧义，可能误标到指令体 / 示例数据里相同字样）→ 判失败。
2. **拼接等值**：把按定位切出的 `[{role,before},{persona,seg},{role,mid},…]` 全部 `text` 拼回去，必须**逐字等于**扁平 prompt。

任一闸不过 → 该角色**丢弃 segments、回落扁平 prompt 不标记**，`available:true` + note 说明「该角色暂不可标来源」。**绝不伪造跨度、绝不抛、绝不连累其它角色**。这把「瞎标」（声称某段来自人设但其实不是）这种软性静默假成功堵死。

> 对抗评审纠正点：不要假设「全部 11 角色人设连续」。`search-evaluator.ts:159-162` 即反例（人设被运行时内容拆开）。故按角色**尽力而为 + 硬回落**，实装时**逐角色验证**，不假设。

## 决策四：返回体加可选 `segments`（向后兼容）

`RolePromptView` 保留扁平 `prompt: string`；新增可选 `segments?: Array<{ source: 'role' | 'persona'; text: string }>`。
- **成功标注**：`segments` 为人设片段与其余文本交替的连续分解（空的首/尾 `role` 段省略），拼接逐字等于 `prompt`。
- **不可标注 / 无人设**：省略 `segments`，前端回落渲染扁平 `prompt`。

旧前端不认 `segments` 也能照常用 `prompt`（零破坏）。同 `GET /api/roles/:roleId/prompt` 路由，仅返回体更丰富，**无需新路由**。

## 决策五：console 渲染（背景色 + 顶部图例）

- **有 segments**：按段渲染；`source:'persona'` 段加**浅背景色**；弹窗顶部一条**图例**说明「有底色 = 来自账号人设」。**不做内联文字标记**（保 prompt 整段可复制、不污染等宽文本）。
- **无 segments**：回落今天的扁平展示（零变化）。
- 可访问性：图例是文字说明，不只靠颜色区分。

## 决策六：与 account-persona-config 热加载天然一致

人设标注纯粹是「`previewPrompt()` 当下解析出的 soul」的函数。一旦 `account-persona-config` 把 `this.soul` 改成按账号解析的取值口，`previewPrompt()` 与 `personaSegments()` 自动反映**当前账号人设**——标注的就是热加载刚改的那段，**无需额外接线**。本 change 对「当前解析出的人设」即可工作（今天是全局 soul，F 落地后是按账号），故**不硬阻塞 F**。

## 砍掉的（YAGNI / 对抗性自审）

- **不**做「覆盖 vs 默认回落」的来源细分（不把 `PersonaFacade.getCatalog` 拖进只读预览层；保持本 change 只在查看器文件内自洽）。运营真要再说。
- **不**标发布侧（沿用当前 browse-only；发布预览本就 `available:false`）。
- **不**做 prompt 编辑 / 模板抽取 / 版本（被否的 Option B）。
- **不**开新路由、不建迁移、不碰协议。
- **不**追求「逼真」片段——`personaSegments()` 只需与 `buildPrompt` 同源拼接即可。

## 失败模式

- 人设值与指令体 / 示例数据撞字（如某兴趣词在正文也出现）→ 唯一性闸判 >1 次 → 回落扁平不标记（**不误标**）。
- 角色把人设拆成多段且其中一段定位失败 → **整角色**回落扁平（不半标）。
- 未来某角色改模板致人设跨度变化 → 拼接等值闸兜底，回落扁平。
- 与 5 流共享 `panel/types.ts`、console `api.ts`：只 append `segments` 可选字段，不动他流条目；不碰协议（stream B）与 C resolver 块。

## 协调约束

- append-only 在 `src/panel/types.ts`（`RolePromptView` 加可选字段）、console `src/types/api.ts`；按 **C→D→F→B** 顺序追加；本 change 排在 stream F 之后落更有意义。
- 无新路由（同 `/api/roles/:roleId/prompt`）、无迁移、无协议改动。
- **不改任何 `buildPrompt`**（`role-prompt-visibility` 红线延续）。
