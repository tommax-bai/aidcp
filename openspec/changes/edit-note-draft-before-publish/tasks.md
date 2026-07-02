## 0. 前置核实（加列 / 部署前必做）

- [ ] 0.1 确认 sub-repo 在本机：`ls -d ../aidcp-cloud ../aidcp-console`（缺失则停手，`aidcp-edge` 本 change 零改动、无需）
- [ ] 0.2 探 ECS 真实现状（有并发部署方也在改同机、schema 启动自建无迁移器）：确认 `aidcp-cloud.service` 现役版本、`publish_log` 现有列
- [ ] 0.3 核实 `publish_metadata` JSONB 实际形状（topics/mentions/location/collection/visibility/permissions/mode/publishTime/compliance/metadataScore），确保 `editDraft` 深合并绝不丢下发依赖的键；与未部署的 `publish-metadata-compliance-roles` / 重建链对齐
- [ ] 0.4 确认排期闸：`publish-history-account-and-detail` 是否已归档（面板 / 抽屉扩展待其归档后增量做）、`publish-trigger-and-apply` 是否已上 ECS（下发版本闸须排在其后）

## 1. aidcp-cloud — 存储层：加列 + 单写 editDraft

- [ ] 1.1 `publish_log` 自愈式加三列：`content_version INT NOT NULL DEFAULT 0`、`edited_by TEXT`、`edited_at TIMESTAMPTZ`（启动期 `ADD COLUMN IF NOT EXISTS`，既有行回填 0）
- [ ] 1.2 在拥有者对象上实现单写 `editDraft(recordId, expectedVersion, patch{title?,content?,visibility?,topics?}, editor)`，内部顺序：① 签名已存在预闸 → `already_decided`；② `clampTitle(≤18)` 拒空 → `invalid_title`；③ 校验 visibility 非空且合法枚举 → `missing_visibility`；④ 深合并 `publish_metadata`（只拼 visibility/topics，compliance 等逐字保留，不重算棘轮）；⑤ 乐观 CAS `UPDATE … content_version+1 … WHERE status='pending_approval' AND content_version=$expected RETURNING`；⑥ 0 行经补充查询消歧 `not_found`/`not_pending`/`version_conflict`
- [ ] 1.3 `editDraft` 单测：`version_conflict` / `already_decided` / `not_pending` / `not_found` / `invalid_title` / `missing_visibility` 各拒因可区分；成功回读真态版本自增 1；compliance 字节前后一致
- [ ] 1.4 面板依赖接线：把草稿写对象经依赖注入挂到面板（缺失则端点 503），不发裸 SQL

## 2. aidcp-cloud — 面板编辑端点 + 授权写时预检

- [ ] 2.1 新增 `PUT /api/publish/:recordId/draft`（落 JWT 闸下、以 JWT 主体作 `editor` 审计、依赖缺失 503、请求体类型校验、拒因→HTTP：404/409/400/422/200 携写回真态）
- [ ] 2.2 `POST /api/publish/:requestId/approve` 入参加 `contentVersion`；对 `publish-` requestId 加写时活版本预检：不一致则拒、**不写签名**，回可区分 `version_stale{currentVersion}`；签名 payload 附 `contentVersion`；保 O_EXCL 出口逐字节不变、同版本先到先得不变
- [ ] 2.3 验收断言：一次「版本不符」的授权**不写任何签名**（O_EXCL 槽位留空、记录留待审可编辑）

## 3. aidcp-cloud — 飞书回调版本预检 + 替换卡

- [ ] 3.1 飞书卡片回调加活版本读取与烤入版本比对（缺→0）：一致 → 写签名 `contentVersion=baked`；不一致 → **不写签名** + 回一张就地替换卡「请到控制台重新审批」（平台唯一允许的卡片更新方式，无主动补发）
- [ ] 3.2 fail-safe：活版本读取出错（PG 抖动）→ 拒到 console（「暂时无法确认版本，请到控制台审批」），绝不放行未确认版本

## 4. aidcp-cloud — 下发版本闸（排在 publish-trigger-and-apply 之后）

- [ ] 4.1 `runDispatch` 在既有 `status`+`isApproved` 闸之后加版本闸：`signal.contentVersion`（缺→0）≠ 行 `content_version` → 不发任何东西、**先删过期签名**、行留 `pending_approval`（自愈可重审），绝不落 `needs_review`、不自毁
- [ ] 4.2 验收断言：版本不符 → 零串流、签名被删、行留待审可被重新授权（**不锁死**）；两处 `needs_review` 语义分明（本 change 版本作废绝不用 needs_review）
- [ ] 4.3 确认此改动与 `publish-trigger-and-apply` 对 `runDispatch` 的归属不相撞（land 在其部署之后，或并入之）

## 5. aidcp-cloud — 只读投影增量

- [ ] 5.1 `GET /api/content/published` 投影 + 面板 item 形状增量带 `content_version`（加性、不 fork 端点 / 抽屉，与已归档 publish-history item 形状协调）；待审轮询不动

## 6. aidcp-console — 编辑工作台

- [ ] 6.1 published item 类型 + api client 加 `apiPut` 草稿；item 带 `content_version`
- [ ] 6.2 「查看正文」抽屉在 `pending_approval` 态升级为可编辑 Form（复用人设编辑页 Modal+Form+TextArea + react-query 失效 + 诚实写回 + 拒因码映射）：标题 Input（纯长度提示、**不做 18 字硬镜像**）、正文 TextArea、可见范围 Select（必填合法枚举）、话题 tags Select；其余状态仍只读
- [ ] 6.3 删手贴 requestId 输入，requestId 由行 `publish-<id>` 派生；行内 编辑 / 保存草稿 / 保存并批准 / 驳回 / 废弃，各携**抽屉渲染时快照的不可变版本号**（绝不点击时从活缓存重取）
- [ ] 6.4 「保存并批准」clamp 二次确认：PUT 草稿后若返回标题 == 提交标题 → 自动 approve 带返回版本；若被截断 → 中止自动批准、回显截断后字节、要求就该版再点一次批准
- [ ] 6.5 生命周期标签（待审 v0 / 已编辑待审 v>0 琥珀 / 已发布 / 失败 / 已否决）+ v>0 抽屉 Alert「此草稿已在控制台修改（第 N 版），原飞书卡片已失效，请在此审批」；拒因码文案（version_conflict / already_decided / not_pending / version_stale 各异）
- [ ] 6.6 编辑模式下 配图 占位只读禁用（本期不接线，留 `publish-media-upload` 归属）

## 7. 回归与安全红线验收

- [ ] 7.1 验收：授权携带的是抽屉渲染快照版本、**非活缓存版本**（否则闸形同虚设）
- [ ] 7.2 验收：clampTitle 单处收口 + 合并动作截断二次确认（记录==下发==审批面==真实发布收敛）
- [ ] 7.3 验收：编辑前后 compliance 字节一致、AI 声明不可下调、无图路径未被触碰、可见范围绝不被清空
- [ ] 7.4 验收：brick-recovery（版本不符 → 可重审不锁死）+ 部署兼容（缺版本→0，老审批照常发）
- [ ] 7.5 云端全绿：先 `npm run test:acceptance` 再 `npm test` 再 `npm run typecheck`（AC-PUB / AC-PROTO / AC-RISK 必过）；console `npm run build` / typecheck 绿

## 8. 部署（安全序列，云端先于 console）

- [ ] 8.1 云端先上 ECS（列 + editDraft + 写时闸 + 下发闸 + 签名 payload + 飞书回调）：备份（cloud.bak + .env.bak）→ rsync（排除 .env/node_modules/.git）→ restart → healthcheck（active + 8787 + 飞书长连 + PG select 1）→ 失败回滚；**绝不碰同机 isales**
- [ ] 8.2 云端验证后再发 console 编辑 UI（发 `/opt/aidcp/console`，rsync 绝不 `--delete`）
- [ ] 8.3 tasks.md 按 sub-repo 分节回写 commit-sha / 部署日期；`openspec validate --strict` → archive
