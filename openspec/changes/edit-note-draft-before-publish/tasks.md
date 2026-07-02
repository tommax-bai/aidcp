## 0. 前置核实（加列 / 部署前必做）

- [x] 0.1 确认 sub-repo 在本机：`ls -d ../aidcp-cloud ../aidcp-console`（缺失则停手，`aidcp-edge` 本 change 零改动、无需） <!-- cloud+console 均在本机；edge 零改动 -->
- [ ] 0.2 探 ECS 真实现状（有并发部署方也在改同机、schema 启动自建无迁移器）：确认 `aidcp-cloud.service` 现役版本、`publish_log` 现有列 <!-- 部署时做（本 change 未部署，deploy 排在 publish-trigger-and-apply 之后） -->
- [x] 0.3 核实 `publish_metadata` JSONB 实际形状（topics/mentions/location/collection/visibility/permissions/mode/publishTime/compliance/metadataScore），确保 `editDraft` 深合并绝不丢下发依赖的键 <!-- 读 types.ts PublishMetadata 坐实形状；editDraft 深合并只动 visibility/topics、逐字保留其余键（含 compliance）；单测断言 compliance 字节前后一致 -->
- [x] 0.4 确认排期闸：`publish-history-account-and-detail` 是否已归档、`publish-trigger-and-apply` 是否已上 ECS（下发版本闸须排在其后） <!-- 两者均未完（26/27、29/37 未部署）；其 BASE 代码已在 cloud master、我方目标文件均 clean、增量扩展不撞；DEPLOY 保持 HELD 待其上线 -->

## 1. aidcp-cloud — 存储层：加列 + 单写 editDraft

- [x] 1.1 `publish_log` 自愈式加三列 <!-- aidcp-cloud 8eb0664：content_version INT NOT NULL DEFAULT 0 / edited_by TEXT / edited_at TIMESTAMPTZ（ADD COLUMN IF NOT EXISTS） -->
- [x] 1.2 单写 `editDraft(recordId, expectedVersion, patch, editor)` <!-- aidcp-cloud 8eb0664：字段校验(clampTitle/visibility 枚举/topics 数组) → 事务 FOR UPDATE 读版本 → 深合并保 compliance → CAS UPDATE content_version+1 RETURNING → 0 行消歧。偏离：签名 already_decided 预闸移到面板端点（hasDecision），store 只管 DB 层，下发兜底是最终权威 -->
- [x] 1.3 `editDraft` 单测（各拒因可区分 / 成功回读真态 / compliance 字节一致） <!-- aidcp-cloud 8eb0664：test/publish-agent/publish-log-store-editdraft.test.ts 脚本化假 pool，覆盖 invalid_title/invalid_field/missing_visibility/not_found/not_pending/version_conflict/成功深合并 -->
- [x] 1.4 面板依赖接线（缺失则端点 503，不发裸 SQL） <!-- aidcp-cloud 8eb0664：server.ts publishDraft.{edit,liveVersion,hasDecision} 经 publishLogStore 注入面板 -->

## 2. aidcp-cloud — 面板编辑端点 + 授权写时预检

- [x] 2.1 `PUT /api/publish/:recordId/draft`（JWT / sub 审计 / 503 / 拒因→HTTP 404·409·400·422·200） <!-- aidcp-cloud 8eb0664：panel-server.ts；panel-server.test 断言 CAS 拒因映射 + already_decided + 503 -->
- [x] 2.2 approve 入参加 `contentVersion` + 写时活版本预检（不一致拒、不写签名、409 version_stale；O_EXCL 出口不变） <!-- aidcp-cloud 8eb0664：panel-server.ts approve；contentVersion 随 payload 落盘 -->
- [x] 2.3 验收：版本不符授权不写任何签名 <!-- aidcp-cloud 8eb0664：panel-server.test「version_stale 不写签名」+ ws-receiver.test 同断言 -->

## 3. aidcp-cloud — 飞书回调版本预检 + 替换卡

- [x] 3.1 飞书回调活版本预检（一致写签名 contentVersion=baked；不一致不写签名 + 回「请到控制台重新审批」替换卡；authorize 与 cancel 均门控防锁死） <!-- aidcp-cloud 8eb0664：ws-receiver.ts + cards.ts buildSupersededPublishApprovalCard；ws-receiver.test 4 例 -->
- [x] 3.2 fail-safe：读版本失败(null) → 拒到控制台、绝不放行未确认版本 <!-- aidcp-cloud 8eb0664：ws-receiver.ts；ws-receiver.test 断言 -->

## 4. aidcp-cloud — 下发版本闸（排在 publish-trigger-and-apply 之后）

- [x] 4.1 `runDispatch` 版本闸：不符则不发、删过期签名、留 pending_approval（绝不 needs_review/自毁） <!-- aidcp-cloud 8eb0664：publish-dispatcher.ts readApproval+voidApprovalSignal；缺版本→0 兼容 -->
- [x] 4.2 验收：版本不符 → 零串流 + 删签名 + 留待审可重审（不锁死） <!-- aidcp-cloud 8eb0664：publish-dispatcher.test 3 例（不符作废 / 一致照发 / 老签名0==草稿0） -->
- [x] 4.3 与 `publish-trigger-and-apply` 对 runDispatch 归属不相撞 <!-- 基线 runDispatch 已 clean+committed（afc385e），我方为纯加性版本闸；DEPLOY 排其后（见 8.1） -->

## 5. aidcp-cloud — 只读投影增量

- [x] 5.1 `GET /api/content/published` 投影 + item 增量带 `content_version`（加性、不 fork） <!-- aidcp-cloud 8eb0664：panel-store.ts PanelPublish.contentVersion + SELECT -->

## 6. aidcp-console — 编辑工作台

- [x] 6.1 published item 类型 + `apiPut` 草稿；item 带 `content_version` <!-- aidcp-console 7e33ad8：types/api.ts + ContentPage 用 apiPut -->
- [x] 6.2 「查看正文」抽屉 pending_approval 态升级为可编辑（标题 Input / 正文 TextArea） <!-- aidcp-console 7e33ad8。偏离（YAGNI）：本期 UI 只编标题+正文；可见范围/话题后端已就绪（PUT 接受），console UI 待投影带出后跟进 -->
- [x] 6.3 删手贴 requestId；requestId 由行 `publish-<id>` 派生；行内动作携抽屉渲染快照版本 <!-- aidcp-console 7e33ad8：viewing.contentVersion 快照，非活缓存 -->
- [x] 6.4 「保存并批准」clamp 二次确认（截断则中止自动批准、回显截断后再确认） <!-- aidcp-console 7e33ad8：onSaveAndApprove -->
- [x] 6.5 生命周期标签 + 卡片失效 Alert + 拒因码文案 <!-- aidcp-console 7e33ad8：lifecycleTag / Alert(v>0) / reasonMessage -->
- [ ] 6.6 配图占位只读禁用 <!-- 未做：本期 UI 无配图字段（无 Upload 组件），配图整体归后续期 + publish-media-upload；不放空占位以免误导 -->

## 7. 回归与安全红线验收

- [x] 7.1 授权携带抽屉渲染快照版本、非活缓存版本 <!-- aidcp-console 7e33ad8：viewing 快照；panel-server.test 断言授权带 contentVersion -->
- [x] 7.2 clampTitle 单处收口 + 合并动作截断二次确认 <!-- editDraft 单测（收口）+ ContentPage onSaveAndApprove（二次确认） -->
- [x] 7.3 compliance 字节一致 / AI 声明不可下调 / 无图路径未触碰 / 可见范围绝不清空 <!-- editDraft 单测断言 compliance 保留 + missing_visibility；未改无图 / markImagesAttached 路径 -->
- [x] 7.4 brick-recovery（版本不符可重审不锁死）+ 部署兼容（缺版本→0 老审批照发） <!-- publish-dispatcher.test 3 例 -->
- [x] 7.5 云端全绿 test:acceptance→test→typecheck（AC-PUB/AC-PROTO/AC-RISK 必过）+ console build/typecheck 绿 <!-- cloud：acceptance 27/27、full 1089/1089、tsc 0；console：tsc 0、vite build 绿、vitest 绿 -->

## 8. 部署（安全序列，云端先于 console）—— HELD（排在 publish-trigger-and-apply 上线之后）

- [ ] 8.1 云端先上 ECS：备份 → rsync（排除 .env/node_modules/.git）→ restart → healthcheck → 失败回滚；绝不碰 isales <!-- HELD：下发版本闸须与已在 master 但未部署的 publish-trigger-and-apply 协调排序；等其上线或与之合并部署 -->
- [ ] 8.2 云端验证后再发 console 编辑 UI（发 `/opt/aidcp/console`，rsync 绝不 --delete） <!-- HELD -->
- [ ] 8.3 tasks.md 回写 deploy 日期；`openspec validate --strict` → archive <!-- 部署后做 -->
