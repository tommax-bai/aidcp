# Tasks — client-preview-image-delete

> 客户端稿件预览抽屉「逐张删配图」。cloud（协议 + 闸序 + 复用既有单写编辑方法）+ edge（协议 + stdin 桥 + IPC + 渲染层）。
> **已 land + 已部署 dev**：cloud master `d0d8967`（2026-07-14 部署 dev）/ edge master `f32e8c3`（edge-only，需重建安装包或从 master 起客户端才生效）。
> 测试：cloud 1946 全量 + 50 acceptance 绿；edge 1186 全量 + 19 acceptance 绿；两侧 typecheck 绿；协议两端 `MessageType` 逐字一致、同为 76。
> **偏离**：闸序单独成 `src/publish-agent/draft-image-remove.ts`（原计划直接写在 server.ts 内联）——理由是应用内审批那套闸序至今**无任何单测**，而本通道带租户隔离红线，不能也裸奔；抽成纯函数后 14 条闸序单测可覆盖。
> **顺带**：`notifyPublishPreviewChanged` 由面板 deps 内联箭头提为共享 `refreshPublishPreview`（两条编辑路径复用，行为不变）。
> **热点文件警示（§7 单写者）**：两份 `src/comm/protocol.ts` 属并行开发热点，本 change 期间需独占；`command-bridge.ts` **不需要**改动（本消息对不是动作↔消息映射）。
> **部署序**：cloud 必须先于 / 同时于 edge 上线含本 change 的版本（旧云端不认新消息类型）。

## 1. aidcp-cloud — 协议

- [x] 1.1 `src/comm/protocol.ts`：`MessageType` 增 `publish.draft_image_remove`（边→云）与 `publish.draft_image_remove.result`（云→边） <!-- aidcp-cloud d0d8967 -->
- [x] 1.2 `src/comm/protocol.ts`：增 `PublishDraftImageRemovePayload { requestId; contentVersion; imageUrl }` 与 `PublishDraftImageRemoveResultPayload { requestId; ok; images?; contentVersion?; reason?; currentVersion? }` <!-- aidcp-cloud d0d8967 -->
- [x] 1.3 `src/comm/protocol.ts`：`MessageTypePayloadMap` 补两条映射 <!-- aidcp-cloud d0d8967 -->
- [x] 1.4 `test/acceptance/protocol-contract.test.ts`：`Record<MessageType,true>` 补两键 + 计数 74 → 76（AC-PROTO 绿） <!-- aidcp-cloud d0d8967 -->

## 2. aidcp-cloud — 闸序与落库（复用 editDraft，不新起写路径）

- [x] 2.1 `src/server.ts`：新增 `handlePublishDraftImageRemove(payload, session)`，闸序 = `invalid_request` → `account_unavailable` → `not_found` → **`account_mismatch`（账号归属，面板缺的那道）** → `already_decided` → `not_pending` → `version_stale`（回带 `currentVersion`） → `image_not_found` → **`last_image`** <!-- aidcp-cloud d0d8967 -->
- [x] 2.2 `src/server.ts`：保留子集在**云端真态**上算出（`kept = draft.imageUrls.filter(u => u !== imageUrl)`），交 `publishLogStore.editDraft(recordId, contentVersion, { images: kept }, 'edge-client:' + accountId)`；store 拒因映射回具名拒因（`version_conflict→version_stale`、`invalid_field→image_not_found`、`not_pending→not_pending`、`not_found→not_found`） <!-- aidcp-cloud d0d8967 -->
- [x] 2.3 `src/server.ts`：成功后调既有 `notifyPublishPreviewChanged(recordId)`（best-effort 重推预览）；应答回带 **store 回读的真态** `images` + `contentVersion`（MUST NOT 回本地推算值） <!-- aidcp-cloud d0d8967 -->
- [x] 2.4 `src/comm/handler.ts`：`CommHandlerDeps` 增 `publishDraftImageRemove`；增 `case 'publish.draft_image_remove'` 路由，应答 `publish.draft_image_remove.result`（按信封 id 关联）；dep 未注入时诚实回 `{ ok:false, reason:'unavailable' }` <!-- aidcp-cloud d0d8967 -->
- [x] 2.5 `src/server.ts`：把 dep 接到 handler（与 `publishApprovalAction` 同处接线） <!-- aidcp-cloud d0d8967 -->
- [x] 2.6 单测：`test/handler.test.ts` 新消息 → `.result` 应答；server 闸序单测覆盖 account_mismatch / version_stale（回带 currentVersion） / already_decided / not_pending / image_not_found / **last_image** / 成功回带真态 <!-- aidcp-cloud d0d8967 -->
- [x] 2.7 `npm run test:acceptance`（AC-PROTO-* / AC-PUB-* / AC-RISK-* 全绿）→ `npm test` → `npm run typecheck` <!-- aidcp-cloud d0d8967 -->

## 3. aidcp-edge — 协议 + 核心 stdin↔WS 桥

- [x] 3.1 `src/comm/protocol.ts`：与 cloud 1.1–1.3 **逐字同步**（MessageType + 两个 payload 接口 + payload map） <!-- aidcp-edge f32e8c3 -->
- [x] 3.2 `test/acceptance/protocol-contract.test.ts`：Record 补两键 + 计数 74 → 76 <!-- aidcp-edge f32e8c3 -->
- [x] 3.3 `src/client/publish-approval-onboarding.ts`：桥的准入从「只认 `publish.approval_action`」放宽为「客户端发起的 publish RPC 集合」（本期两条）；**转发逻辑 / 回执前缀 `[publish-approval-reply]` / pending 表 / 30s 超时一律不变**，不新增 stdin 监听器、不新增回执前缀 <!-- aidcp-edge f32e8c3 -->
- [x] 3.4 单测：桥收到新 type 会 `client.request(type, payload, 30_000)` 并回 `[publish-approval-reply]`；收到未知 type 仍静默丢弃（零回归） <!-- aidcp-edge f32e8c3 -->

## 4. aidcp-edge — Electron 主进程 + preload

- [x] 4.1 `src/electron/main.cjs`：发送函数泛化为可按 type 下发（复用同一 pending 表 / **35s** 超时，MUST 保持 35s > 核心 30s 的阶梯） <!-- aidcp-edge f32e8c3 -->
- [x] 4.2 `src/electron/main.cjs`：新 IPC `publish:image-remove`，入参校验（`requestId` 匹配 `^publish-\d+$`、`contentVersion` 非负整数、`imageUrl` 非空字符串）→ 不合法回 `invalid_request` <!-- aidcp-edge f32e8c3 -->
- [x] 4.3 `src/electron/main.cjs`：应答 `ok` 时**就地更新** `handle.status.publishPreview` 的 `images` + `contentVersion` 并 `updateStatus` 广播；更新前校验应答 recordId **等于**当前 `publishPreview.recordId`（防过期应答写进新草稿） <!-- aidcp-edge f32e8c3 -->
- [x] 4.4 `src/electron/preload.cjs`：暴露 `publishImageRemove(envId, payload)`（与既有 `publishApproval` 同形，**必带 envId**） <!-- aidcp-edge f32e8c3 -->

## 5. aidcp-edge — 渲染层交互

- [x] 5.1 `renderer/renderer.js`：`renderPublishPreviewContent` 配图区——可审批态且 `images.length >= 2` 时每张渲染删除角标（`aria-label="删除配图 N"`） <!-- aidcp-edge f32e8c3 -->
- [x] 5.2 `renderer/renderer.js`：**就地二次确认**（点角标 → 该张切确认态「删除 / 取消」）；确认态存**模块级变量**（键为 URL），MUST NOT 只存 DOM（抽屉每帧重建会抹掉） <!-- aidcp-edge f32e8c3 -->
- [x] 5.3 `renderer/renderer.js`：确认 → 置忙态（**发布 / 取消 / 其余角标一并禁用**）→ 调 `publishImageRemove` → **非乐观**：等应答后以真态重绘，MUST NOT 先行移除缩略图 <!-- aidcp-edge f32e8c3 -->
- [x] 5.4 `renderer/renderer.js`：只剩一张时不渲染角标 + 显示「至少保留一张配图」 <!-- aidcp-edge f32e8c3 -->
- [x] 5.5 `renderer/renderer.js`：拒因中文映射（`version_stale` / `image_not_found` / `last_image` / `already_decided` / `not_pending` / `account_mismatch` / `account_unavailable` / `edge_request_timeout` / `edge_not_running`）；失败后该张 **仍在**界面上 <!-- aidcp-edge f32e8c3 -->
- [x] 5.6 `renderer/styles.css`：角标 + 确认态样式（复刻管理后台形态：右上角 danger 圆形 ✕） <!-- aidcp-edge f32e8c3 -->
- [x] 5.7 `test/electron/companion-ui.test.ts`（jsdom）：≥2 张显角标 / 只剩 1 张无角标 + 提示 / 点角标先确认再调用 / 调用参数为 `{requestId:'publish-<id>', contentVersion, imageUrl}` / 忙态下发布按钮禁用 / 失败后缩略图仍在且显示拒因 / **发布卡仍零按钮**（既有断言零回归） <!-- aidcp-edge f32e8c3 -->

## 6. 控制仓 — 协议文档

- [x] 6.1 `docs/protocol.md`：头部消息计数 74 → 76；§2 表补两条（注明：客户端发起、按信封 id 关联的应答，**不需要**进边缘主动命令白名单、**不需要**动 `command-bridge`） <!-- aidcp docs/protocol.md 74→76 -->

## 7. 集成 / 部署 / 验收

- [x] 7.1 cloud：rebase 最新 master → `test:acceptance` + `test` + `typecheck` 全绿 → ff 合并 → push <!-- aidcp-cloud d0d8967 --> <!-- landed master (rebase 撞并发 import 冲突，已合解) -->
- [x] 7.2 edge：rebase 最新 master → `test` + `typecheck` 全绿 → ff 合并 → push（**按长期授权，不打安装包**） <!-- aidcp-edge f32e8c3 --> <!-- landed master；未打安装包（长期授权：默认不打） -->
- [x] 7.3 部署 cloud 到 **dev**（§5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck；红线：不碰同机 isales） <!-- 2026-07-14 deployed dev（备份 cloud.bak.20260714-153114.tar.gz；8787+8090 在听、飞书长连已建、--delete 零误删核过） -->
- [x] 7.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（新簇，见下） <!-- docs/real-machine-acceptance-backlog.md 簇 73（8 项） -->

## 8. 真机验收（登记 backlog，不在本 change 内勾选）

- [ ] 8.1 客户端预览抽屉里配图**能真显示**（对象级 public-read 已确认，但需真机确认非兜底态）
- [ ] 8.2 真删一张 → 界面剩余保序正确、张数更新 → 点发布 → **不撞 `version_stale`** → 帖子真发出且只带剩余配图
- [ ] 8.3 删**封面**（第一张）→ 第二张成为封面 → 发出的帖以新首图为封面
- [ ] 8.4 只剩一张时无删除入口；伪造请求时云端拒 `last_image`
- [ ] 8.5 删图后**原飞书审核卡失效**（`content_version + 1`，卡片点击应提示到控制台审批）
- [ ] 8.6 后台同时删另一张 → 客户端删除撞 `version_stale` → 提示后刷新为真态
