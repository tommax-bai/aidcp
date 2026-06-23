# Tasks — diagnose-publish-submit-failure

回归铁律：发布链改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`；红线 `AC-PUB-*`/`AC-PROTO-*`/`AC-RISK-*` 必过。
提交纪律：并发会话在同仓有 WIP；**精确 `git add` 仅本 change 文件、不 `-A`**；改前按符号定位（行号可能漂移）。
红线：MUST NOT 静默假成功**双向**——既不掩盖真失败、也不把未真发的帖误报成功；边缘只忠实执行不加兜底启发式；策略收口云端。背景见 `docs/handoff-publish-submit-failure-2026-06-22.md`。

## 0. 前置坐实（BLOCKING）

- [x] 0.1 坐实改点：读 edge `publish-command-handlers.ts` 的 `runSubmit` / `findShadowButtonCenter` / 后置校验（成功正则 + URL 判定 + 15s 窗口）与 cloud `command-sequencer.ts` 的硬必选（可见范围 `:129-130/:164/:216-218`）与 `failedAt` 构造，记录确切插入点与现役成功 URL/正则于本 task HTML 注释。**验证**：结论带 `文件:行`
<!-- edge publish-command-handlers.ts：findShadowButtonCenter:413-451（取「发布」节点盒模型中心、多命中取最靠下；闭合 shadow 经 DOM.getDocument{pierce}）；runSubmit:457-498（ensureInputEnabled→findShadowButtonCenter('发布')→Input.dispatchMouseEvent 原始坐标点击:478-480→后置校验）；后置校验 CHECK 正则 /发布成功|发布中|笔记已?发布|成功发布|稍后可在/ **或** !location.href.includes('/publish/publish')（:486，弱条件）；deadline=clock()+15_000（:487）；超时 post_validate_failed（:495）。cloud command-sequencer.ts：bestEffort Set=['add_with_candidate','set_option','set_schedule']（:164）；失败/异常 best-effort 跳过 continue（:197/:217）；核心步失败 failedAt return（:201/:221）；可见范围「硬必选」注释（:129）却 set_option best-effort（:130）。诊断插入点=findShadowButtonCenter 末（按钮属性）+ runSubmit 点击后/超时（页面状态）。 -->
- [x] 0.1b 真机已确认排除 (c) 假阴性：用户核账号「帖子没法出去」=真没发出（非已发只是没检测到）→ 真实失败属 (a) 风控/拦截 或 (b) 按钮禁用，靠 Step 1 诊断区分。

## 1. aidcp-edge — Step 1：提交诊断（只观测、零行为变更）

- [x] 1.1 `runSubmit`：点击前用 `Runtime.evaluate`（只读取值、不派发事件、不改主路径）采集并日志化：点击中心坐标、命中「发布」元素 tag/class + `disabled`/`aria-disabled`/`pointer-events`、`document.elementFromPoint(x,y)` 命中元素及最近 `[role=dialog]`/`[aria-modal]`、页面是否存在 `role=dialog`/`aria-modal`；后置校验超时时日志 `location.href` + `document.body.innerText` 头 ~200 字。只含公开状态、不打敏感值。**验证**：`npm run typecheck`；主路径（点击/校验/回报）行为不变的单测
<!-- edge：findShadowButtonCenter 末加 DOM.getAttributes 记按钮 class/disabled/aria-disabled（区分 b 禁用）；新增 logSubmitDiag(x,y,when) 经 Runtime.evaluate 只读捕获 elementFromPoint/role=dialog/toast/href/bodyHead，在 runSubmit 'after-click'（deadline 前、不占 15s 窗）与 'timeout' 各调一次；console.warn `[publish-submit-diag]`。只观测、主路径点击/校验/回报逻辑零变更（cdp 路径，no-cdp 单测不受影响）。typecheck 干净。 -->
- [x] 1.2 edge 回归：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。**验证**：三命令退出码 0
<!-- edge：typecheck 0 err；publish-command-handlers 单测 13/13；test:acceptance 11/11；test 292/292 全绿。 -->

## 2. aidcp-cloud — Step 1：`failedAt` 带 guard 跳过计数

<!-- 暂缓（2026-06-23）：① cloud 工作树当前被并发会话 role-model-category-config WIP 占用且 typecheck 已坏（role-config-facade/panel 缺 category/getCategoryModel），不宜此时叠改纠缠；② 对定位 (a)/(b)/(c) 价值低——edge 诊断（task 1.1）已足够区分，且 edge 在本地跑、本诊断无需部署云端。待 cloud 树干净后再补 2.1/2.2。 -->
- [ ] 2.1 `command-sequencer.ts`：`submit_publish` 失败的 `failedAt` 上下文带出本次 best-effort 跳过的步骤数量/项（让运营一眼区分「6/6 元数据 guard 噪声」vs「硬必选真缺」）。**验证**：单测「failedAt 含跳过计数」
- [ ] 2.2 cloud 回归：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全绿。**验证**：三命令退出码 0

## 3. 部署 Step 1（诊断版，安全序列）

- [ ] 3.1 云端部署：§0 私钥/子仓检查 → ECS 备份 → rsync **仅本 change 文件**（dry-run surface scope）→ restart → healthcheck（active+8787+飞书长连接+PG+isales 未触碰）→ 失败回滚。**验证**：healthcheck 全过
- [ ] 3.2 edge 本地**单实例**重启连 `ws://121.89.85.150:8787`（先确保无残留 edge 进程，避免多实例混淆下发）。**验证**：`已连接云端 … 等待命令` 且仅一个 edge 进程

## 4. 诊断真机跑 + 定位根因（BLOCKING Step 2）

- [ ] 4.1 飞书 `/publish` → 收集 `submit_publish` 诊断日志 + **账号侧确认该帖是否真发出去** → 据 D2 线索定位 (a) 风控/拦截 toast / (b) 按钮禁用 no-op / (c) >15s 假阴性超时。**验证**：结论（哪一类 + 证据）写入本 task HTML 注释

## 5. aidcp-cloud — Step 2a：硬必选缺失判致命（独立成立，不 gated）

- [ ] 5.1 `command-sequencer.ts`：硬必选步骤（可见范围）的失败判**致命**于本次发布、诚实 `failed`，而非静默 best-effort 跳过后继续提交；其余真正可选元数据仍 best-effort。**验证**：单测「硬必选失败→整体 failed、未提交」
- [ ] 5.2 cloud 回归全绿。**验证**：三命令退出码 0

## 6. Step 2b：据诊断的诚实修（gated 于 4.1）

- [ ] 6.1 据 (a)/(b)/(c) 实施诚实修：(a) 发布前/提交后识别拦截并诚实 `failed`；(b) 诚实回报禁用/no-op 失败（**不**加重试/启发式绕过）；(c) 成功判定锚真实成功 URL、**有界**延长等待——**绝不**放松成功匹配/无界重试。edge 一律不加掩盖真失败的兜底。**验证**：单测覆盖对应类别；红线「不双向假成功」断言
- [ ] 6.2 edge/cloud 回归全绿。**验证**：三命令退出码 0

## 7. 部署 Step 2 + 真机验证发布真成功

- [ ] 7.1 云端 + edge 同批部署（安全序列）。**验证**：healthcheck 全过
- [ ] 7.2 真机 `/publish` → **发布真成功**（URL `/publish/success`、`publish_log` 新行 `status=published` 且 == 平台真实显示）。**验证**：records==published==平台真实

## 8. 收尾（中控）

- [ ] 8.1 各 task HTML 注释标 `[x]` + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。**验证**：本文件各 task 带注释
- [ ] 8.2 三仓精确提交推送（本仓 `main`、cloud/edge `master`，Co-Authored-By 行）。**验证**：三仓干净、已 push
- [ ] 8.3 `openspec validate diagnose-publish-submit-failure --strict` → `openspec archive`（delta 并入 `openspec/specs/publish-submit-integrity/`）。**验证**：archive 后不再活跃
