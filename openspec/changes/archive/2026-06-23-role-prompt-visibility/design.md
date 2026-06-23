# Design — role-prompt-visibility（只读，Option A）

## 1. 忠实渲染 vs 描述符目录（决策：忠实渲染）

两条路：
- **A 描述符目录**：另写一份「prompt 文本」常量给后台看。零触运行码，但**生而漂移**——手抄的文本会和真实 buildPrompt 脱节，看到的不是线上真用的。否决为主选。
- **B 忠实渲染**（选）：调各角色**真实的** buildPrompt（传最小示例数据 + 真实 soul），把结果原样展示。看到的就是线上真用的指令文字 + 真实人设，**零漂移**。代价是给每个角色加一个薄预览入口。

选 B。关键约束：**不改 buildPrompt 的任何现有逻辑**（线上 prompt 行为必须零变化），只**新增**一个调用它的预览方法。

## 2. 浏览侧：每角色加 `previewPrompt()`

`buildPrompt` 当前为 `private`，签名各异（cards / note / comments…）。给每个 LLM 角色加一个 public `previewPrompt(): string`，内部用**本角色自造的最小示例数据**调自己的 `buildPrompt`：

```ts
// 例：content-evaluator
previewPrompt(): string {
  const sample: VisibleCard[] = [
    { title: '<示例卡片标题>', author: '<作者>', likeCount: 0, collectCount: 0, isVideo: false } as VisibleCard,
  ];
  return this.buildPrompt(sample, 'feed');
}
```

要点：
- 示例数据**最小且合法**（满足 buildPrompt 不抛）；占位串用 `<…>` 明示「这里运行时填真实数据」。
- 人设用构造时注入的真实 soul（`this.soul`），所以预览里的人设是**真实**的（即当前线上人设）。
- `previewPrompt` 只读、无副作用，不进任何运行闭环路径。

## 3. 发布侧：复用既有 builder

`src/publish-agent/prompts.ts` 的 builder 已是独立纯函数（`buildScoutPrompt(trigger)` / `buildCreatorPrompt(scoutDecision, trigger)` / `buildTitlePrompt(body, persona, styleType, seedTitle?)` …）。预览模块用**示例输入**调它们即可，无需碰发布角色类。

## 4. 汇集与安全降级（绝不崩）

新增 `src/config/role-prompt-preview.ts`：按 `roleId` 汇集预览函数（浏览角色的 `previewPrompt` 经 RoleDispatcher 暴露的实例 / 发布的 builder 调用）。每个预览**单独 try 包裹**：

```ts
function safePreview(fn: () => string): { available: boolean; prompt: string | null; note: string } {
  try { return { available: true, prompt: fn(), note: PLACEHOLDER_NOTE }; }
  catch (e) { return { available: false, prompt: null, note: `预览不可用：${(e as Error).message}` }; }
}
```

红线：单角色渲染失败 → `available:false`，**绝不抛、绝不崩、绝不连累浏览/发布闭环**。

## 5. 面板接口（只读，无写）

`GET /api/roles/:roleId/prompt`（JWT 守护）→ `{ roleId, prompt: string|null, available: boolean, note: string }`。**没有任何 PUT/POST**——本 change 只读。未知 roleId → 404；非 LLM 角色（image/none）→ `available:false` + 说明。

## 6. console（只读弹窗）

角色配置页每个文本角色加「查看 Prompt」按钮 → 点击拉 `GET /api/roles/:id/prompt` → 只读弹窗展示 `prompt`（等宽、可滚），顶部说明「实时数据/人设为示例占位，线上调用时由系统填入真实值」。无编辑控件。

## 7. 砍掉的（YAGNI / 对抗性自审）

- **不**抽模板存库（那是 Option B）。
- **不**改任何 buildPrompt 现有逻辑（只新增 previewPrompt）。
- **不**做 prompt 编辑 / 校验 / 热加载 / 版本。
- **不**碰协议、不建迁移、不进 role-dispatcher 运行时分发逻辑（仅借实例读）。
- 示例数据**不**追求逼真，只求「合法 + 占位明示」。

## 8. 失败模式

- 某角色 buildPrompt 对示例数据假设过强而抛 → `available:false`，前端显示「预览不可用」，其它角色不受影响。
- soul 未就位（理论上启动已 fail-fast）→ 同样降级。
- 与 stream C 共享 `server.ts`/`panel-server.ts`/`panel/types.ts`/console `api.ts`/`queries.ts`：只 **append**，不动 C 的 resolver 块与既有路由。
