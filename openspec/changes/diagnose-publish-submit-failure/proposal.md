## Why

真机发帖在最后一步 `submit_publish` 反复失败（`post_validate_failed`）。多 agent 对抗性评审确认：这是与标题无关、早就存在的独立 bug（`runSubmit`/发布按钮锚点自 `3590f3c` 逐字未变、id 11 用同套代码发成功；6 个元数据 `guard_persist` 是 jsdom 可见性误判噪声、非真遮挡）。当前失败**不留任何可定位线索**：点击发布按钮后只在 15s 内认一个固定成功正则，无风控/拦截/禁用态处理；失败时既看不出是 (a) 平台风控/拦截 toast、(b) 按钮禁用 no-op、还是 (c) >15s 假阴性超时（可能其实已真发）。同时云端把**自注释「硬必选」的可见范围**当 best-effort 静默跳过，硬必选字段可能在提交时缺失却不报错。这违反「MUST NOT 静默假成功」的精神——既可能假失败（真发了却记 failed），也可能掩盖真失败。先把失败变得**可定位**、再**诚实修**，是当下唯一不盲猜的走法。

## What Changes

- **先诊断（只观测、不改行为，安全）**：edge `runSubmit` 在点击发布按钮前后记录可定位状态（按钮元素 tag/class + `disabled`/`aria-disabled`/`pointer-events`、`document.elementFromPoint(x,y)` 命中元素、是否存在 `role=dialog`/`aria-modal`）；15s 后置校验超时时记录 `location.href` + 页面正文开头。云端把 `guard_persist` 跳过计数带进 `failedAt` 上下文。
- **据真机诊断 + 账号侧确认**定位失败类别 (a)/(b)/(c)。
- **诚实修（收口云端）**：硬必选元数据步骤（可见范围）的 `guard_persist` 判**致命**而非 best-effort 静默跳过，让系统在硬必选缺失时**响亮失败**，而不是去点一个发不出去的按钮；或加发布前云端校验、诚实 `failed`。具体修法 gated 于诊断结果（防盲修）。
- **红线（强约束）**：edge **禁止**加 disabled 启发式 / 重试 / 放宽 15s 窗口 / 放松成功正则等任何可能掩盖真失败的兜底——**反向的「把真失败粉饰成假成功」同样是红线**；长度/策略收口云端、边缘只忠实执行、如实回报。

## Capabilities

### New Capabilities
- `publish-submit-integrity`: 发布提交步（submit_publish）的**可观测性**（失败留可定位线索）、**诚实失败**（不静默假成功、不假阴性误判）、以及**硬必选元数据字段缺失时判致命**（不静默跳过）。

### Modified Capabilities
<!-- 无 spec 级 requirement 变更需要改写既有 spec；publish-pipeline 当前仅覆盖标题链路，不在此 change 范围。 -->

## Impact

- **edge** `aidcp-edge/src/flows/publish-command-handlers.ts`：`runSubmit` 加观测日志（Step 1，无行为变更）；据诊断结果可能加诚实失败回报（不加兜底启发式）。
- **cloud** `aidcp-cloud/src/publish-agent/command-sequencer.ts`：硬必选步骤（可见范围 `:129-130/:164/:216-218`）的 `guard_persist` 判致命；`failedAt` 带 `guard_persist` 跳过计数。
- **部署**：edge 本地重启 + cloud ECS（安全序列：备份→dry-run→rsync→restart→healthcheck→isales 未触碰）。
- **真机**：需一次 instrumented `/publish` 跑 + 账号侧确认 id 12/下一条是否真发，才能定位并诚实修复。
- **不动**：协议 v2、DB 结构、风控/浏览闭环、同机 isales；标题链路（已归档 `dedicated-title-creator-role`）。
- **背景文档**：`docs/handoff-publish-submit-failure-2026-06-22.md`（评审 findings + 先诊断后修方案）。
