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

## 8. 部署（安全序列，云端先于 console）—— DONE 2026-07-03（用户选 Option 2：发整个 master）

<!-- 2026-07-03 部署前探测结论（read-only）：
  · ECS aidcp-cloud active、8787 LISTENING、decouple/dispatch 基座（loadForDispatch）已在线——本 change 的
    下发版本闸基座已具备，publish-trigger-and-apply 的 runDispatch 顾虑消解。
  · 真正阻塞：① 云端本地工作树脏——有并发 session 的第三个改动未提交 WIP（8 文件，含 comm/protocol.ts 的
    dwellMs 字段），rsync 会连带上线未验证代码，绝不可发；② 更关键——ECS 落后于 master：既缺本 change(8eb0664)，
    也缺 account-group-chat-injection 云端(a2c8f09，含 protocol.ts groupChatCode)。二者在 master 同一线、且都改了
    panel-server.ts / panel/types.ts / server.ts 同文件（我方叠在其上），**无法只发我方而不带 account-group-chat-injection**。
  · 结论：发 master HEAD = 我方 + account-group-chat-injection 一起上（后者 openspec 未提交、边缘侧未核，非本人可决其发布）；
    近史「cloud held on live multi-change contention」印证团队正刻意压 cloud 发布。→ HELD，待用户/归属方定夺。
  · 备选安全路径（用户确认后可做）：从 ECS 现网拉基线到隔离目录、只打 8eb0664 的 diff——但因同文件叠 a2c8f09，
    面板/server 三文件需手工摘除其 hunk，易错；或直接发 master HEAD（= 两改动同上）。-->

- [x] 8.1 云端上 ECS：备份 → rsync → restart → healthcheck → 失败回滚；绝不碰 isales <!-- aidcp-cloud d031344 2026-07-03 deployed。从 pinned 干净 worktree(1103/1103 绿) rsync；备份 cloud.bak.20260703-001951.tar.gz + .env.bak.20260703；healthcheck 全绿：active / 8787+8090 LISTENING / 飞书长连接已建立 / content_version·edited_by·edited_at 列启动自建 / /api/version OK；package.json 与 ECS 一致无需 npm install。用户选 Option 2「发整个 master」→ 连带 account-group-chat-injection(a2c8f09) + category-adaptive-images-and-judgment + feed-scroll-card-floor 一并上（全量 1103/1103 绿为门）。 -->
- [x] 8.2 console 上 ECS（发 `/opt/aidcp/console`，rsync 绝不 --delete） <!-- aidcp-console 7c995290 2026-07-03 deployed。备份 console.bak.20260703-002253.tar.gz；nginx 8088 服新 bundle index-BCUsanfL.js（ECS md5==本地构建 be308a0b…，含 already_decided/version_stale//draft）；intro.* 保留。 -->
- [ ] 8.3 `openspec validate --strict`（已过）→ archive <!-- deploy 日期已回写。建议先做一次真机确认（后台开一条 pending_approval 草稿 → 改标题/正文 → 保存并批准 → 真发布）再 archive；本 change delta 独立、与连带上线的其他 change 各自归档互不影响。 -->
