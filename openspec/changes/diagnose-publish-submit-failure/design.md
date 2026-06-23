## Context

发帖流水线最后一步由 edge `runSubmit`（`aidcp-edge/src/flows/publish-command-handlers.ts`）执行：用 `findShadowButtonCenter` 在闭合 shadow 里按文字「发布」取按钮中心坐标 → `Input.dispatchMouseEvent` 原始坐标点击 → 15s 内轮询「成功正则 OR URL 离开 `/publish/publish`」，超时则回报 `post_validate_failed`（`:486-495`）。真机 publish-12 标题正确（9 字）、图已附，仍卡在此步。

多 agent 对抗性评审（背景 `docs/handoff-publish-submit-failure-2026-06-22.md`、本会话 task `w8iuswnhq`）已坐实：
- 这是**与标题无关、早存在**的独立 bug——`runSubmit` 自 `3590f3c` 逐字未变、id 11 同套代码发成功。
- 6 个元数据 `guard_persist` 是 **jsdom 可见性误判**（`cdp/dom-provider.ts:38,43-45` 在 outerHTML 快照上扫，`extractor.ts:173-180` 只过滤行内隐藏，CSS class 隐藏的预渲染 dialog 被误判可见 → 命中 `guard.ts:44` modal_dialog），非真遮挡；标题/正文同页能成功即反证。
- 真实失败三类候选：(a) 发布时风控/拦截 toast 不匹配固定成功正则；(b) 按钮禁用 no-op（`runSubmit` 零禁用态检查）；(c) >15s 假阴性超时（可能其实已真发）。

约束：MUST NOT 静默假成功（含反向：不可把真失败粉饰成假成功）；边轻云重、策略收口云端、边缘只忠实执行；不动协议 v2 / DB / 风控 / 同机 isales。

## Goals / Non-Goals

**Goals:**
- 让 `submit_publish` 失败**可定位**：每次失败留下足够线索区分 (a)/(b)/(c)。
- 据真机诊断 + 账号侧确认**定位**根因。
- 对「硬必选字段缺失」做**诚实**处理：响亮失败，而非点一个发不出去的按钮。

**Non-Goals:**
- 不在诊断前盲修（不预先放宽 15s / 放松成功正则 / 加禁用态重试）。
- 不在 edge 加任何可能掩盖真失败的兜底启发式。
- 不动标题链路（已归档）、协议、DB、风控、isales。

## Decisions

### D1：先诊断、后修（两阶段，诊断阶段只观测不改行为）
- **选**：Step 1 仅加观测日志（零行为变更，可安全部署）→ 一次 instrumented 真机跑 + 账号侧确认 → Step 2 据结果诚实修。
- **因为**：三类候选 (a)/(b)/(c) 修法互斥（拦截层 vs 禁用态 vs 超时窗），且评审明确「盲修会踩反向红线」。**弃**「直接放宽 15s 或重试」——会把真失败/风控拦截粉饰成假成功。

### D2：edge `runSubmit` 诊断点（只读，CDP `Runtime.evaluate`）
- 点击**前**记录：解析出的中心 `{x,y}`、命中的「发布」元素 `tagName/className` + `disabled`/`aria-disabled`/`pointer-events`、`document.elementFromPoint(x,y)` 命中元素的 `tag/class/closest('[role=dialog],[aria-modal]')`、页面是否存在 `role=dialog`/`aria-modal`。
- 15s 超时**时**记录：`location.href`、`document.body.innerText` 头 ~200 字。
- 这直接区分：坐标顶层是按钮还是遮挡（→a）、按钮是否禁用（→b）、还是 URL 已跳/有成功痕迹只是晚于 15s（→c）。日志只含页面公开状态、不含敏感值。

### D3：云端 `failedAt` 带 `guard_persist` 跳过计数
- `command-sequencer.ts` 在 `submit_publish` 失败的 `failedAt` 上下文里带上「本次 best-effort 跳过了几步 / 哪几步」，让运营一眼看到 6/6 元数据被 guard 拦——区分「噪声」与「真缺字段」。

### D4：硬必选字段缺失判致命（诚实修，gated 于诊断）
- `command-sequencer.ts:129` 自注释「可见范围 **硬必选**」，却在 `:130/:164` 当 `set_option` best-effort、`:216-218` 失败即跳过——硬必选字段可在 submit 时缺失却不报错。
- **修法**：把**硬必选**步骤（可见范围）的失败判**致命**，整体 `failed` 并诚实回报，而非静默跳过后去点按钮。其余真正可选的元数据仍 best-effort。**是否是本次 id-12 失败的直接主因 gated 于 D1 诊断**；但「硬必选却 best-effort 跳过」本身就是个应修的诚实性缺陷，无论诊断结果都成立。

### D5：成功校验只锚真实成功信号、不盲目放宽
- 若诊断为 (c) 假阴性超时：成功判定应锚定**实测的真实成功 URL**（`/publish/success`，待真机确认）/ 平台真实成功痕迹，必要时**有界**延长等待——但绝不退化为「URL 一离开 `/publish/publish` 就算成功」这种会把风控拦截误判为成功的弱条件。**弃**无界重试。

## Risks / Trade-offs

- **[(c) 假阴性：id 12 其实已真发，却记 failed]** → 账号侧确认 + 诊断日志（超时时 href/正文）；若确为假阴性，按 D5 有界修成功判定，绝不无脑放宽。
- **[诊断日志噪声/性能]** → 仅在 submit 这一步、每次一两条 `Runtime.evaluate`，可忽略；不打敏感值。
- **[诊断改动意外引入行为变化]** → Step 1 严格只读（`Runtime.evaluate` 取值、不派发事件），单测/typecheck 守护；与点击/校验主路径解耦。
- **[修法在诊断前过度承诺]** → D4 的硬必选致命化是独立成立的诚实性修复；其余修法 gated 于 D1，tasks 里显式分阶段。
- **[edge 撤标题截断的副作用]** → `8cb8d01` 移除了 edge 最后一公里 20 字兜底；当前云端 TitleCreator `clampTitle` 已保证 ≤18，故无回归；但若未来某路径产出超长标题到达页面，会复发「按钮静默失效」且成功正则无法区分——本 change 的诊断日志正好能暴露之（按钮 disabled 态）。

## Migration Plan

1. **Step 1 实装**：edge `runSubmit` 观测日志（无行为变更）+ cloud `failedAt` 带 guard 跳过计数 → edge `test:acceptance`/`test`/`typecheck` + cloud 同 → 全绿。
2. **部署**：cloud ECS 安全序列（备份→dry-run→rsync→restart→healthcheck→isales 未触碰）；edge 本地重启（单 edge，避免多实例混淆）。
3. **诊断跑**：飞书 `/publish` → 收集 submit 诊断日志 + 账号侧确认是否真发 → 定位 (a)/(b)/(c)。
4. **Step 2 诚实修**（据诊断）：硬必选致命化（D4）+ 据类别的诚实成功判定/拦截处理（D5）→ 回归 → 再部署 → 再真机验证（发布真成功、records==published==平台真实）。
5. **回滚**：cloud 解 `.bak.<ts>.tar.gz`+restart；edge 回退本 change commit。

## Open Questions

- (a)/(b)/(c) 哪一类是 id-12 的真因？——D1 诊断跑坐实（BLOCKING Step 2）。
- id 12「TP 设置踩坑实录」到底有没有真发到平台？——账号侧确认（决定是否 (c)）。
- 真实成功 URL 是否确为 `/publish/success`、风控拦截 toast 的实测文案？——诊断跑实证后再定 D5 的成功判定/拦截处理。
