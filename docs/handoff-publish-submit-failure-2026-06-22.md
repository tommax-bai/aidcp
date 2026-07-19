# 交接 — 发布提交失败（post_validate_failed @ submit_publish）根因评审

> **历史证据，不是当前故障指南。** 本文因仍被归档 OpenSpec 引用而保留，只描述
> 2026-06-22/23 的诊断现场；旧 DOM、测试数量、分支和结论不能直接用于当前运行态。
> 当前发布故障应从对应 OpenSpec、Edge/Cloud 代码与实时日志重新取证。
>
> 2026-06-22。多 agent 评审（4 探针 → 综合排名 → 对抗性证伪）。这是与标题改动**无关的、早就存在的独立提交 bug**；`dedicated-title-creator-role`（标题保真）已达成并归档，本问题另开 change 跟踪。

## 0. 现象（真机 publish-12，2026-06-22）

- 标题链路【正常】：TitleCreator 线上产出 `title="TP 设置踩坑实录"`（9 可见字），DB `publish_log` id=12 records == 序列下发 == 审批卡 三方同一字符串、≤18 未切碎。**标题失真红线已修复并验证**。
- 发布【失败】：`failedAt={"seq":11,"kind":"submit_publish","error":"post_validate_failed"}`，`status=failed`，`images_attached=t`、无 `platform_post_id`。
- 时间线（云端日志）：seq1-4（导航/填标题/填正文/传图）静默成功；seq5-10 元数据每步 0-1s `guard_persist` 失败（best-effort 跳过）；**seq11 点击发布按钮后等约 21s 才 `post_validate_failed`**（= 后置校验轮询 15s 窗口超时）。

## 1. 评审结论（经对抗性证伪后站得住的）

**这是独立的、早存在的提交 bug，不是标题改动引入。** `runSubmit` / `findShadowButtonCenter` / 发布按钮锚点自 `3590f3c`(06-21) **逐字未变**，`8cb8d01` 只动了标题填充；**id 11 用同一套提交代码发成功**。提交失败在 id 8/9/10 也出现过。

**两个"看似相关"的方向被证伪（别去追）：**
1. **6 个 `guard_persist` 是 jsdom 可见性误判，不是真遮挡层。** 边缘 guard 在 `cdp/dom-provider.ts:38,43-45` 的 **jsdom outerHTML 快照**上扫；`extractor.ts:173-180` 的 `defaultIsVisible` 只过滤**行内** `display:none/visibility:hidden/hidden/aria-hidden`。小红书那种**用 CSS class 隐藏、但 HTML 预渲染**的 `role=dialog` 节点会被判"可见"→命中 `guard.ts:44` 的 `modal_dialog`。所以**每个走定位引擎(`runAtom`)的元数据步都误报 guard，每个走原始 CDP 的步(标题/正文/图/提交)都不受影响**——这恰好解释了为什么标题/正文在同一页能成功。
2. **不是"元数据留了个没关的下拉挡住按钮"。** guard 在定位**之前**就返回(`engine.ts:98` 先于 execute)，`attempts:0`，根本没打开任何 picker。`runSubmit` 是独立的原始 CDP，与元数据路径不共享状态。

## 2. 真正的提交失败 — 候选（按可能性）

| | 原因 | 机制 | 关键 file:line |
|---|---|---|---|
| a | 发布时平台弹拦截/提示（风控"操作频繁"、二次确认框、图仍在后处理） | 后置校验 15s 只认固定成功正则，匹配不上 → 误判失败。**发布处理器无任何风控/验证码/拦截层处理** | `aidcp-edge/.../publish-command-handlers.ts:486`(正则)`:487`(硬15s)`:495` |
| b | 按钮在但禁用/点了 no-op | `runSubmit` 点击前**零禁用态检查**；`findShadowButtonCenter` 按文字 `发布` 匹配、不校验 disabled，禁用按钮照样有坐标，点上去 no-op。被删旧代码注释正记录这类"按钮在、点了没用"静默失效 | `:466-484`、`:427-445`、`git show 8cb8d01` |
| c | 假阴性超时：其实发出去了，`/publish/success` 在 15s 之后才跳 | 15s 硬上限无重试 | `:487`。**需账号侧确认 id 12 是否真发** |

> 另一矛盾点（值得一并修）：`aidcp-cloud/.../command-sequencer.ts:129` 自注释「可见范围 **硬必选**」，但 `:130/:164` 却当 `set_option` best-effort、`:216-218` 失败即跳过——硬必选字段可能在 submit 时缺失。

## 3. 下一步：先诊断、后修（评审明确反对盲修）

放宽 15s 或放松成功正则会踩**反向红线**（把真失败粉饰成假成功）。所以：

**Step 1 — 只观测不改行为（安全）：** `runSubmit` 点击前记录 ①resolved center {x,y}、②匹配到的 `发布` 元素 tag/class + `disabled`/`aria-disabled`/`pointer-events`、③`document.elementFromPoint(x,y)`（坐标最顶层到底是按钮还是别的）、④是否有 `role=dialog`/`aria-modal`；15s 超时时记录 `location.href` + `document.body.innerText` 头 200 字。云端把 `guard_persist` 跳过计数带进 `failedAt` 上下文。

**Step 2 — 账号侧确认：** id 12 的「TP 设置踩坑实录」到底有没有真发出去？有→候选 c（假阴性超时）；没有→候选 a/b。

**Step 3 — 诚实修（收口云端，边缘不加策略）：** 据诊断结果，若是硬必选字段缺失 → `command-sequencer.ts` 把 visibility 等硬必选步骤的 `guard_persist` **判致命而非跳过**，让系统**响亮失败**而不是去点发不出去的按钮；若是风控/拦截 → 加发布前云端检查并诚实 `failed`。**边缘禁止**加 disabled 启发式/重试/放宽窗口等可能掩盖真失败的兜底。

## 3.5 突破：mock 自驱真机复跑（2026-06-23）翻转结论

用 env-guarded mock 触发（`AIDCP_MOCK_PUBLISH=true` + `touch /tmp/aidcp-mock-publish-trigger`，等价飞书 /publish）+ 信号文件自动审批，**干净 fresh edge（新诊断码）自驱复跑**：

- **publish-14 端到端发布成功**（`status=published`、has_img、`images_attached`、title="智能体老犯傻？可能是提示词没写对" 16 可见字）→ **标题保真红线端到端彻底验证（含==平台真实显示这一腿）**；真帖已上账号。
- **submit 成功路径诊断**（`[publish-submit-diag] after-click`）：`button '发布' class="ce-btn bg-red" disabled=false`、`atPoint="XHS-PUBLISH-BTN"`（点击落在按钮、未被遮挡）、仅一个空 `el-overlay-dialog` + "原创声明" 提示 → 提交成功。`capture_postId no_target`(seq12) 为非致命（帖已提交、只是没抓到 postId）。
- **翻转结论**：**publish-12 的 submit `post_validate_failed` 八成是「旧代码残留 edge + day-old Chrome 页面」的环境锅**（见 §1：当时跑在 50418 旧 edge 上），**不是硬 submit bug**——干净 edge 上 submit 可靠成功（id 14、id 11）。**唯一可复现的真实脆点 = 配图超时**（publish-13）：wan2.7-image-pro 慢于 90s（万相 18 轮）→ ImageGenerator 降级无图 → `input.images` 空 → 图文编辑器「先传图门控」下标题框不渲染 → `fill_field no_target` → 整帖 failed。

**修复方向收敛（据此翻转）**：
1. **主修：配图超时 → 无图的诚实失败 / 给足时间**。已做 env 缓解 `AIDCP_WANXIANG_MAX_POLL`（ECS 已设 23≈115s，受 ImageGenerator 角色闸 120s 上限约束）。正解应在 PublishExecutor/sequencer：**无图（imageUrl 缺）→ 诚实 failed（无有效图文帖），不进 fill_field 去 no_target**（红线：不静默走必然失败的纯文字路径）；或让配图更可靠/可重试。
2. **submit 诚实性（次要）**：成功路径已验证健康；若未来再现间歇 post_validate_failed，诊断日志（已部署 edge b2d69f7）会落实是风控 toast / 慢往返；**绝不盲目放宽 15s 或放松成功正则**。
3. `command-sequencer.ts:129` 可见范围「硬必选」却 best-effort 跳过的矛盾仍应修（独立成立）。

> mock 基建现状（ECS）：cloud 跑 master `c8cad82`（并发会话部署，含 role-category + 我的 mock-trigger）；`.env` 有 `AIDCP_MOCK_PUBLISH=true` + `AIDCP_WANXIANG_MAX_POLL=23`。**mock 触发是 file-gated 后门**（仅 `touch /tmp/aidcp-mock-publish-trigger` 才发），用完应 `AIDCP_MOCK_PUBLISH` 移除 + 重启清理。同机多会话部署会竞态覆盖/打断 run（实测 15:34 撞 c8cad82），错峰。

## 4. 指针

- 评审 workflow 全量结果：本会话 task `w8iuswnhq` 输出（`.../tasks/w8iuswnhq.output`）。
- 相关记忆：[[publish-pipeline-deployed]]、[[edge-no-strategy-honest-failure]]（边缘只忠实执行、不兜底）。
- 已归档 change：`dedicated-title-creator-role`（标题保真，2026-06-22）。
