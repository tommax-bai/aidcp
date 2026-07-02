## Why

今天运营对一条「待审」的正文草稿只能**看**或**通过 / 驳回**——标题、正文、可见范围但凡有一处想改，唯一出路是整条作废、重新触发一次约 3 分钟的全量生成、落成一条全新记录。运营真实诉求是「就地改几个字再发」，而系统本就把草稿冻存进数据库、下发时**原样重读那条草稿**（绝不重生成）——「改完再发」在架构上天然可行，缺的只是一条从后台安全落到那条草稿的编辑通路，以及一条「人审看到的 = 真正发出去的」的保真闸。本 change 补上这条通路，并顺手把后台「手贴 requestId 才能审批」的临时做法收口成按行审批。

## What Changes

- **【新·正文草稿就地编辑】** 给「待审」状态的正文草稿加一条后台编辑通路：运营可改**标题 / 正文 / 可见范围 / 话题**，改动**就地 UPDATE 同一条待审记录**（不新起草稿行、不重生成），下发端照旧原样重读那条记录发出去。经账号属性同型的**单写通道**落库（拥有者对象单写、面板受 JWT 保护、绝不裸 UPDATE、不乐观假成功、写后回读真态）。
- **【新·版本号即「审=发」凭证】** 给草稿记录加一个**每行版本号**（`content_version`，每次编辑 +1）。授权时必须带上「人当时看到的那一版」版本号：**写时**——通过 / 驳回入口（含飞书卡片回调）先比对活版本，不一致则当场拒绝、连授权签名都不写（旧飞书卡片点了也白点）；**下发时**——发布端再比一次版本，不一致则**什么都不发、删掉过期签名、把草稿退回「待审」可重审**。既杜绝「把没人看过的内容发出去」，也杜绝「好草稿被永久锁死」。
- **【新·飞书卡片失效即引导】** 已发出的老版飞书卡片无法被云端主动刷新；一旦草稿在后台被改过，飞书卡片点击命中版本不一致时，回调**就地替换成一张「请到控制台重新审批」提示卡**（平台唯一允许的卡片更新方式），不做主动补发。
- **【改·后台审批工作台化】** 把现有只读的「查看正文」抽屉在「待审」态升级为可编辑表单 + 就地审批；**删除「手贴 requestId」的临时输入**，requestId 由行 `publish-<id>` 派生。标题长度仍在云端一处收口（`clampTitle ≤18 字素`）——「保存并批准」若发现标题被截断，**中止自动批准、回显截断后文案、要求就那版再点一次批准**，杜绝「批的是截断前、发的是截断后」。
- **【向后兼容】** 部署时在飞书回调与下发闸两处把「缺版本号」一律当 0；部署前所有在飞的老审批（烤入版本 0 == 活版本 0）照常发布，不被 deploy 卡死。
- **【范围裁剪·YAGNI】** 本期**仅正文文本 + 元数据、仅后台、边缘零改动**；**不做**评论编辑（评论无草稿库 + 90 秒内存窗口 + 边缘 @/# 保真限制，留孪生 `editDraft` 契约缝、后续独立期）、**不做**配图编辑 / 上传（后台无上传组件、面板无传图接口，配图保真闸归 `publish-media-upload` 所有、后续期建）、**不做**版本历史表 / diff 日志（`content_version` 已是干净的将来扩展键）、**不做** aiEnforced 合规重算（本期合规字节保留、不可编辑）。

> 非 BREAKING：编辑通路、版本号列、写时 / 下发版本闸均为**新增**；不带编辑（版本恒 0）时既有发布链一字不变，签名文件跨进程契约、requestId 格式、待审轮询、评论 / 正文判别、边缘逐字填入全部不动。

## Capabilities

### New Capabilities
<!-- 无新增独立能力：编辑通路是对既有「发布流水线 + 面板写」能力的需求扩展，按 YAGNI 不新造能力/抽象。 -->

### Modified Capabilities
- `publish-pipeline`：新增「下发前对待审草稿就地编辑」的合法路径与「版本作用域授权」不变量——下发仍从落库草稿重建、绝不重生成；授权凭「人看到的版本」，下发时版本不一致则**作废过期签名、草稿留「待审」**（绝不误发、绝不锁死、绝不落 `needs_review`）。**不改**发布放行阈值 / 降级公式 / forced 必发语义 / 无授权绝不下发。
- `console-write-operations`：新增一条 Requirement——「待审正文草稿」经拥有者对象的一等单写方法（乐观 CAS + `content_version` 自增）编辑，面板受 JWT 保护、绝不裸 UPDATE、绝不乐观假成功、写后回读真态、可区分拒因（`not_found` / `not_pending` / `version_conflict` / `already_decided` / `invalid_title` / `missing_visibility`）；并给共享的 Web+飞书授权出口加一道**写时活版本预检**（不一致则不写签名），`writeApprovalSignal` 出口保持字节不变、`contentVersion` 随既有 payload 附带。
- `console-panel-api`：`GET /api/content/published` 投影**增量**带出 `content_version`（前端渲染生命周期标签 + 快照授权版本）；新增 `PUT /api/publish/:recordId/draft` 编辑端点（JWT、依赖缺失 503、拒因→HTTP 映射）。均为**增量扩展**，不 fork 抽屉 / 端点（与已归档的 `publish-history-account-and-detail` 的 item 形状协调）。
- `publish-submit-integrity`：可见范围变为**可编辑**，但编辑侧强制校验其为非空且合法枚举、JSONB 深合并保留未改键——绝不持久化一条无可见范围的草稿（硬必选致命闸不破）。

## Impact

- **aidcp-cloud**：`src/publish-agent/publish-log-store.ts`（`publish_log` 自愈式加列 `content_version INT NOT NULL DEFAULT 0` / `edited_by TEXT` / `edited_at TIMESTAMPTZ`；新单写方法 `editDraft` = 签名预闸 → `clampTitle` → 可见范围校验 → `publish_metadata` JSONB 深合并保 compliance 字节 → CAS `UPDATE … WHERE status='pending_approval' AND content_version=$expected` 自增版本 → 0 行拒因消歧）、`src/panel/panel-server.ts`（`PUT /api/publish/:recordId/draft` + approve 入参加 `contentVersion` + 写时活版本预检）、`src/panel/types.ts`（`EditDraftResult` + item 形状 `content_version`）、`src/publish-agent/publish-dispatcher.ts`（下发版本闸 + 作废过期签名并留待审，**排在 `publish-trigger-and-apply` 落地之后**、协调 `runDispatch` 归属）、`src/feishu/ws-receiver.ts`（回调活版本预检 + 替换卡；签名 payload 带 `contentVersion`；缺版本→0 兜底）、`src/server.ts`（published 投影 +`content_version`；待审轮询不动）。
- **aidcp-console**：`ContentPage`（「待审」态抽屉升级为编辑表单 + 行内 编辑/保存草稿/保存并批准/驳回/废弃、抽屉渲染时快照不可变版本号、`clampTitle` 截断二次确认、生命周期标签、卡片失效 Alert；移除手贴 requestId、下客户端 18 字硬镜像只留提示）、`api/client`（`apiPut` 草稿）、published item 类型 +`content_version`。
- **aidcp-edge**：**零改动**（边缘保持无状态 / 逐字忠实；签名 payload 变化在云端侧、`params.value` 填入不变）。
- **协议 / 授权契约**：不改边-云 WebSocket 协议 v2；签名文件路径 / O_EXCL 先到先得 / requestId 格式 / 评论-正文判别全不动，仅 payload 增 `contentVersion` 字段、版本比对留在调用侧。
- **DB**：仅 `publish_log` 自愈加三列（`content_version` 为真列、非塞 JSONB，令版本闸是原子 `WHERE` 谓词），既有行回填 0，无迁移器（启动期 `ADD COLUMN IF NOT EXISTS`）。
- **排期约束**：① 跟随——待 `publish-history-account-and-detail`（26/27，近归档）归档其只读抽屉 + published API + item 形状后，本 change 增量扩展、独立拥有 `ContentPage`/`panel-server`/`panel-store` 相关行；② 下发端那一处版本闸**严格排在 `publish-trigger-and-apply`（29/37，未上 ECS，拥有 `runDispatch`）部署之后**或并入之，两处 `needs_review` 语义各自分明；③ 与 `publish-metadata-compliance-roles`（未上线 aiEnforced 棘轮）**解耦**——`editDraft` 不重算棘轮、深合并保 compliance 字节，部署前先核实 `publish_metadata` JSONB 形状一致；④ 每批改后 `test:acceptance` → `test` → `typecheck` 全绿（AC-PUB / AC-PROTO / AC-RISK 必过）；⑤ 云端（列+editDraft+写时闸+下发闸+签名 payload+飞书回调）**必须先于**控制台编辑 UI 上线，缺版本→0 兜底护住在飞审批；部署走安全序列、先探 ECS 现状再加列、绝不碰同机 isales。
