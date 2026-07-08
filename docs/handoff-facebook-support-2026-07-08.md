# Handoff — Facebook 支持进展与续做（2026-07-08）

> 面向接手的新 session。读完即可续做，无需回溯上一段对话。语言：正文中文，代码/命令/标识符英文（CLAUDE.md §6）。

## 0-bis. 2026-07-08 晚更新：真发主线已落码（仍 fail-closed，物理不发）

原文档（§0 起）写于「真发未接线（not_wired）」阶段。**此后「真正去 Facebook 发评论」的整条代码已实装 + 单测锁死 + 合入两仓 master**——但仍 **fail-closed 休眠**：kill switch `AIDCP_FB_COMMENT_AUTO` 默认关 → 物理发不出评论，对现役小红书零回归。已落码内容：

- **协议**（两份 `protocol.ts` 逐字镜像 + `docs/protocol.md`）：`search.execute` 加可选 `container?`、`note.open` 加可选 `url?`（复用消息、零新增类型、计数仍 61；AC-PROTO-08 往返锁）。
- **边缘**（aidcp-edge master `9c3ee01`）：`FacebookCommentExecutor`（把 phase-0 探针升格为生产执行器：容器内搜索→开帖→提交+服务器确认）+ `FacebookCommentHandler`（按 driver `comment` 能力注册、镜像小红书回执契约）+ **静默丢弃坑修复**（FB 无 browseHandler 导致 whitelist 命中零回执 → 现按能力注册 + 不支持命令回 `capability_unsupported`）+ 两个 F1 补丁（滚动催出懒加载评论框 / 成功判定收窄到「本人数字 id + 目标帖评论区 + 文本片段」，替换全页 indexOf）。FB driver 加 `comment` 能力（**不加 `browse`**）。
- **云端**（aidcp-cloud master `757a8fc`）：`buildFacebookEdgeSteps`（`sendAndRace` 有界超时 28s，此路径无看门狗）+ `runFacebookTargetedTask` 真发路径替换 `not_wired`：搜索容器→选未评候选→开帖→提交；诚实 outcome 映射；**防重复真发**（提交派发前打去重标记、与成功计数解耦）；真发成功记风控走既有 `interaction.occurred` 自动路径、绝不重复 record、绝不碰 `manualCommentAccounts`。
- **测试**：edge 全绿 743/743 + acceptance 14/14；cloud 全绿 1558/1558 + acceptance 45/45；两仓 typecheck clean；`openspec validate --strict` 通过。change 仍 **ACTIVE**（未归档）——剩真机验收（簇 14）+ 两块纯云 follow-up（task 2.6/2.7）。

**真发前必清的 BLOCKING（见 `docs/real-machine-acceptance-backlog.md` 簇 14）**：① 生产执行器上再证 F1（scoped 服务器确认可区分乐观 vs 真落库）；② per-profile 代理就绪（中国 IP 无代理写操作高风险）。dev 若要观察影子，需**重部署 cloud master `757a8fc`**（旧 dev 部署 `24ef9d4` 只到影子编排层，无真发编排 + 无 `facebook-edge-steps.ts`）。edge 是本地安装包、要用需重打包。

以下 §0–§9 为落码前的原始交接，`§4/§5` 的「待接入」项现已全部落码（对照上面这段读）。

## 0. 一句话现状

Facebook 支持已把「从桌面建号 → 启动打开 Facebook → 云端登记账号 → 后台配搜索词 → 云端影子编排（安检+审计，不真发）」整条**入口到编排**打通并入库；**唯一剩下的主线是「真正去 Facebook 发评论」**（边缘评论能力 + 协议两个可选载荷字段 + 真机验收），这是全功能里最高风险的一段，评审已列出真发前必清的硬闸。全部已落地部分都是 **fail-closed 休眠态**（kill switch 默认关、真发未接线、物理发不出评论），对现役小红书零回归。

## 1. 整体闭环（已通的路径）

桌面选 Facebook 建 AdsPower 环境（平台存进 remark）→ 点启动，桌面壳注入 `AIDCP_PLATFORM=facebook` → 核心用 FB 驱动打开 facebook.com、读身份、握手上报 `platform=facebook` → 云端握手 insert-time 按 facebook 登记账号（修了首连死锁）+ 平台闸拒起小红书浏览循环 → 账号页显示 Facebook、能配「关键词列表 + 容器（自己的/已加入的主页群）」→ 云端两个评论入口（排期 + 飞书 `/comment`）按 `accounts.platform` 路由到 `runFacebookTargetedTask` → 闸链（kill switch → 配置 fail-closed → 随机选词/容器 → 撰写 → 只拒不修校验）→ **影子模式到此止步、写审计、绝不发**；真发路径再加 canDo+日上限闸 → **真发执行未接入（诚实 not_wired、绝不假成功）**。

## 2. 各仓 landed 状态 + 提交 SHA

| 仓 | 分支 | 相关 SHA | 内容 |
|---|---|---|---|
| aidcp-cloud | master | `8f942e0` | FB 影子编排 `runFacebookTargetedTask` + 审计 store（迁移 0035）+ server 接线 |
| aidcp-cloud | master | (更早) | 握手 provisioning + registry.facebook + 会话平台闸（`fd92ffb`）、确定性校验器（`6269a18`）、每账号关键词+容器配置 store + 面板 API（`5a557d2`） |
| aidcp-edge | master | `9cda1d4` | FB 驱动 + 探针（identity/overlay/page-structure/editor/gated-submit） |
| aidcp-edge | master | `a2fac2a` | 桌面壳每环境平台选择 + 启动注入 `AIDCP_PLATFORM` |
| aidcp-console | master | `e13626d` | 账号页平台列 + Facebook「配置搜索词」弹层（关键词+容器）+ 面板 API 调用 |
| aidcp（控制） | main | — | 三个 change 已在 main 且保持 **active**：`facebook-scheduled-comment`、`facebook-browser-env-and-login`、`edge-environment-platform-select` |

## 3. dev 部署态（重要）

- **cloud dev 已部署到「配置存储 + provisioning + 平台闸 + 校验器」层**（早前 `24ef9d4` 部署已验证：`account_facebook_comment_config` 表已自建、小红书 platform 值未变、服务健康、isales 未受影响）。
- **cloud 影子编排（`8f942e0`）在 master 但尚未部署 dev**（dev 上 `facebook-comment-audit-store.ts` 不存在、`facebook_comment_audit` 表未建）。**续做若要在 dev 观察影子，需重新部署 cloud master 到 dev**（走 CLAUDE.md §5 安全序列：先探 ECS 现状 → 备份 → rsync 排除 .env/node_modules/.git → restart → healthcheck；dev=`121.89.85.150`，key `~/codes/isales-4.pem`；红线：绝不碰同机 isales-api/engine/scheduler/worker）。dev cloud 以 `tsx src/` 直接跑源码（不是 dist），部署=rsync src。
- **console dev 已部署**（平台列 + 配搜索词 UI 在 dev）。
- **edge 是本地安装包、不上 ECS**：FB 驱动+选平台虽在 master，运营要用得**重新打包 edge 安装包**分发（`cd ../aidcp-edge && npm run <打包脚本>`，安装包在 `dist-electron`；注意仓库有「默认不打安装包、仅显式要求才打」的约定）。

## 4. 剩余关键路径：FB 评论真发（唯一主线）

真发 = 边缘评论能力（4.x）+ 协议两个可选载荷字段 + 云端接线，全部是**单独 gated 的真机 follow-up**。设计已在 change specs/tasks 里，要点：

### 4a. 协议（复用，零新增消息）
两个来回全部复用现有消息，**均已在边缘主动命令白名单**（不碰第 4 处同步坑）：
- 容器内搜候选：`search.execute`（**加可选 `container?: { kind:'page'|'group'; url?; id?; label? }`**）→ 上行 `page.cards`（候选帖填 `cards[]`，permalink 放 `noteId`）。
- 开帖+评论：`note.open`（**加可选 `url?`**，permalink 直驱，F1 已证评论框在 permalink.php 懒加载）→ `note.detail`；`interaction.comment`（`noteId`+`text`，不动）→ `action.completed{action:'comment', ok}`。
- **改动仅两处**：两份 `src/comm/protocol.ts` 逐字一致加两个可选字段 + `docs/protocol.md` 字段说明（**消息计数不变**）。`command-bridge` 不改（字段经 `command.params` 透传）。白名单不改（三消息已放行）。**热点文件单写者**：两份 protocol.ts 属并行禁区，改时标串行。
- typecheck 盲区：`Record<MessageType,true>` 穷举只守消息集合、**不守 payload 字段跨仓一致**，两份 protocol.ts 的可选字段必须人工保证逐字镜像。

### 4b. 边缘 FB 评论能力（把探针升格为生产执行器）
edge master 已有探针可复用（`aidcp-edge/src/facebook/probes/*`）：
- `page-structure.ts` 抽候选帖（permalink/author/text/comment-region/membership）→ 直接升格。
- `editor-probe.ts` 找懒加载评论框（`role=textbox` aria-label「写评论…」）、聚焦、受控输入、清空不提交 → 升格。
- `gated-submit.ts` 提交+reload+区分乐观 vs 服务器确认 → 升格为主流程。
- **两个 F1 补丁（必做）**：① 提交前**滚动催出懒加载评论框**（现状未滚到位直接 `editor_not_found`；参照 browse-session `pollDomUntil` 有界轮询）；② **成功判定收窄到「本人身份 + 目标帖评论区」**（现状 `buildMarkerVisibleJs` 是全页 `body.indexOf(text)`，会假阳；改为 reload 后定位目标帖 article、在其评论区匹配「本人 accountId 的评论行 + 文本片段」）。
- **In-container 搜索是唯一净新增**（探针不做搜索框交互）：进容器 URL（云端下发）→ 站内搜（group `/groups/<id>/search/?q=`、page 帖搜索）→ `classifyFacebookSurface` 应判 `search` → 取候选。容器白名单 fail-closed（`isUrlAllowedByTargetDescriptor` + membership 非成员/待批准 → `permission_gated`），**绝不回退全站搜**。
- **命令路由修静默丢弃坑**：edge `client/edge-client.ts` 里 `note.open`/`interaction.comment` 路由到 `this.browseHandler?.(env)`，FB 无 browse 能力 → `browseHandler` undefined → **可选链静默吞、零回执**（notification-monitor 240s 卡死重演，且此路径无巡视看门狗）。必须按 driver 能力注册一个 FB 评论 handler（不锁在 `if(autoBrowse)` 内），且白名单命中但无处理器时**显式回诚实失败回执**（`capability_unsupported`）。

### 4c. 云端接线（补齐真发那半截）
`runFacebookTargetedTask`（`aidcp-cloud/src/comment-agent/comment-scheduler.ts`）当前真发路径过闸后回 `not_wired`。补：注入 FB edge-steps（复用 `edge-steps.ts` 的 `sendAndAwait` 模式：发 `search.execute{container}` 等 `page.cards` → 选候选 → 发 `note.open{url}` 等 `note.detail` → 发 `interaction.comment` 等 `action.completed{ok}`），**每步有界超时**（这条路无巡视看门狗，超时即诚实非成功，别无限等）。成功（`ok:true`）经既有 `interaction.occurred → RiskController.record('comment')` 自动路径记账——**绝不走 `onCommentTakeoverStart`**（会塞进 `manualCommentAccounts` 跳过风控，违反 task 2.4）。

## 5. BLOCKING 安全闸（真发前必须全清，来自对抗性评审）

1. **边缘静默丢弃坑必须与「首次给 FB 边端发命令」同增量修好**（`browseHandler?.(env)` 对 FB 是零回执）+ **云端 FB 评论命令必须自带有界超时**（此路径无看门狗）。否则每次派发都会挂死云端。
2. **F1 未在真机证明「验证能区分乐观渲染 vs 服务器确认」之前，绝不开真发**（kill switch 关、影子先行）。注：F1 已于 2026-07-07 用一次性账号手动验过一次（服务器确认可区分；发现了懒加载评论框需滚动），记录在 `facebook-browser-env-and-login` change 的 tasks 6.1；但生产执行器换了实现，真发前应在生产执行器上再确认。
3. **kill switch（`AIDCP_FB_COMMENT_AUTO`）必须在两入口汇聚后的单一收口点判定**（已在 `runFacebookTargetedTask` 收口，勿在别处重复漏判）。
4. **验证假阴性 → 重复真发**：提交派发即打冷却/软 attempted 标记（与「成功计数」解耦），否则确认撞网络抖动会对同一目标重复真评。当前 5.2「冷却仅成功后打」不覆盖这一面，真发增量内必须补。

## 6. 关键文件索引

- 云端编排：`aidcp-cloud/src/comment-agent/comment-scheduler.ts`（`runFacebookTargetedTask`）；校验器 `facebook-comment-validators.ts`；配置 store `src/config/facebook-comment-config-store.ts`（`effectiveConfigFor` fail-closed）；审计 store `src/comment-agent/facebook-comment-audit-store.ts`；平台注册 `src/platform/registry.ts`（facebook 条目，capabilities `['comment']`）；I/O 底座 `src/comment-agent/edge-steps.ts`（`sendAndAwait`）；记账链 `src/comm/handler.ts`（`interaction.occurred`）+ `src/server.ts`（`eventBus.on('interaction.occurred')`，注意 `manualCommentAccounts` 跳记账陷阱）。
- 边缘：`aidcp-edge/src/facebook/driver.ts`（capabilities）、`src/facebook/probes/{page-structure,editor-probe,gated-submit}.ts`（可升格）、`src/facebook/{identity,overlay}.ts`、`src/client/edge-client.ts`（白名单 + `browseHandler?.` 坑）、`src/main.ts`（`supportsBrowse` / autoBrowse 分支，FB 评论 handler 注册点）、`src/platform/driver.ts`（契约，可加可选 comment 能力工厂）。
- 桌面壳：`aidcp-edge/src/electron/{ads-create-flow,ads-local-api,main}.cjs` + `renderer/renderer.js`（平台经 remark `plat` 存储、`buildProviderEnv` 注入 `AIDCP_PLATFORM`）。
- 协议：两份 `src/comm/protocol.ts`（edge+cloud，逐字一致）+ `aidcp-cloud/src/comm/command-bridge.ts` + `docs/protocol.md`。

## 7. 运营/环境注意

- kill switch/影子/上限 env（默认全安全）：`AIDCP_FB_COMMENT_AUTO`（默认关，真发总闸）、`AIDCP_FB_COMMENT_SHADOW`（默认关，影子）、`AIDCP_FB_COMMENT_DAILY_CAP`（默认 2）。dev 上要观察影子先部署 cloud master 再设 `AIDCP_FB_COMMENT_SHADOW=true`。
- **网络出口/代理 v1 未做**（探针 profile 无代理、中国大陆 IP）——真发前是硬前置（AdsPower per-profile 固定代理），已登记在 `facebook-scheduled-comment` proposal 的 Scale-out 边界。中国 IP 上写操作 checkpoint/封号风险高。
- **冷却全局统一**（不做 FB 独立长冷却）、**目标=关键词+限定容器（绝不全站搜）**、**console UI 已做**——这三条是用户已定案，勿再提反向方案。
- 长稳定性（F3 多日观察、多日真发观察、冷却/日计数持久化）按用户决定**延后到末尾统一补**（`facebook-scheduled-comment` tasks §8），不阻塞功能推进。

## 8. 真机验收 backlog（桩测不了、需登录的一次性运营 FB 账号）

- 懒加载评论框滚动参数（步距/屏数/settle ms）。
- scoped own-identity confirm 的真实评论行 DOM 标记。
- 乐观 vs 服务器确认时序（submit 后/reload 后等待）。
- 评论框/发布按钮的真实 aria-label 中英文案。
- 容器内搜索真行为（group/page 站内搜、`search` surface 稳定性、入群问答/待批准）。
- F3 多日环境稳定 + 多日真发观察。

## 9. 新 session 第一步建议

1. 读本文档 + `openspec show facebook-scheduled-comment` + `facebook-browser-env-and-login`（both active）。
2. 若做**真发主线**：按 §4 分解，建议顺序——先 edge FB 评论 handler + 命令路由修静默丢弃坑（§4b 末 + §5.1）→ 协议两个可选字段（§4a，热点文件串行）→ 边缘执行器（升格探针 + 两个 F1 补丁）→ 云端接线真发路径 + 有界超时 + 防重复发（§4c/§5.4）→ 影子先行真机 sanity → 真发单账号 1-2/天。**每步都 fail-closed，真发前 kill switch 一直关**。
3. 若先做**云端可独立收尾**：连续阻塞 outcome 告警器（task 2.7 剩余，仿 `pacing-saturation-alerter` / `captcha-coordinator` 的 store-then-Feishu）+ 登录/checkpoint 标记恢复闭环（2.6，复用 alertStore + 飞书 `/pause` `/resume`）——这两块纯云、可假边端测、不依赖边缘。
4. 并发纪律：edge/cloud 主 checkout 常被并发 session 弄脏且落后——**集成/部署只从干净 worktree 或 `git archive` 快照走，push 遇 non-ff 一律 rebase 重来绝不 force**；改协议/风控状态机/角色注册等热点文件标串行。

---
*相关 change：`facebook-scheduled-comment`（云端定时评论，主）、`facebook-browser-env-and-login`（边缘环境/登录/驱动+探针）、`edge-environment-platform-select`（桌面选平台）。三者均 active、未归档。*
