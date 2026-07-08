# Tasks — feed-hot-lead-group-comment

> 分两段落地：**段一（发现+度量+入队+阈值配置面，可独立上线观测）** = 第 1–6 组；**段二（人审逐条消费）** = 第 7 组。
> 热点文件（两份 `protocol.ts`、`command-bridge.ts`、角色注册 `RoleName`）须与活跃 change `comment-search-command` 等**串行**、单写。
> 分支：cloud/edge/console 各一个同名 worktree 分支；集成走 `scripts/land-change`（未 land）。

## 1. aidcp-edge — 原始发布时刻抽取（段一）

- [x] 1.1 `src/browse/note-extractor.ts` 新增发布时刻文本抽取：窄选择器 `NOTE_PUBLISHED_AT_SELECTORS`（`.bottom-container .date` 等，⚠️需真机标定），只回传原始 `publishedAtText`、不解析 <!-- edge e033ca0 -->
- [x] 1.2 日期选择器独立常量、body 抽取仍白名单制；二次护栏 `.closest()` 落 body 容器即跳过；与 `NOTE_BODY_SELECTORS` 物理隔离 <!-- edge e033ca0 -->
- [x] 1.3 `NoteContent` 扩展可选 `publishedAtText`；`src/browse/browse-session.ts:1455` `note.detail` 组装带上（条件 spread） <!-- edge e033ca0 -->
- [x] 1.4 jsdom 桩单测：双向断言「日期不进正文、正文变更不吞日期」+ denylist 隔离（3 新测，14 pass/0 fail） <!-- edge e033ca0 test/browse/note-extractor.test.ts -->

## 2. 协议同步 + 事件透传（段一·热点·串行）

- [x] 2.1 `src/comm/protocol.ts`（edge）：`NoteDetailPayload` 加可选 `publishedAtText?`（逐字一致文案） <!-- edge e033ca0 -->
- [x] 2.2 `src/comm/protocol.ts`（cloud）：逐字一致加 `publishedAtText?`；`command-bridge` 无需改（note.detail 是上行 payload、非动作映射） <!-- cloud 503eb3e -->
- [x] 2.3 `event-bus/types.ts` 的 `NoteDetailData` 加 `publishedAtText?`；`handler.ts` 整对象透传（未改 handler），`note.detail.arrived` 载荷自动带上 <!-- cloud 503eb3e -->
- [x] 2.4 两仓 `npm run typecheck` 通过（cloud 仅剩 base 预存 text-card satori/resvg；edge 干净） <!-- cloud 503eb3e / edge e033ca0 -->

## 3. aidcp-cloud — 解析 + 速率过滤（段一）

- [x] 3.1 `parsePublishedHoursAgo(text)`：刚刚/分钟→0；X小时前→X；昨天→36h 常数；前天→60/X天前→X*24；裸日期→超龄哨兵；剥离「编辑于」前缀、token 匹配；无法识别→`null`（绝不臆造） <!-- cloud 6231f9c src/hot-lead/heat-velocity.ts -->
- [x] 3.2 `heatVelocity(likeCount, hoursAgo, FLOOR)` = `likeCount / max(hoursAgo, FLOOR)`；`likeCount` 在 `note.detail` 已是 number，云端无需再 parse <!-- cloud 6231f9c -->
- [x] 3.3 过滤闸 `evaluateHotLead`（纯确定性，不调 LLM）：`hoursAgo!=null && ageHours<=MAX_AGE && likeCount>=LIKES_MIN && velocity>=VELOCITY_MIN`；返回 reason；阈值走 `HotLeadGateConfig`（组 4 接 provider 现读） <!-- cloud 6231f9c -->
- [x] 3.4 单测：14 测全过 <!-- cloud 6231f9c test/hot-lead-heat-velocity.test.ts -->

## 4. 阈值全局配置面（段一）

- [x] 4.1 **独立小表** `hot_lead_config_global`（不并进 session_config_global，避 fleet 撞车）：`HotLeadConfigStore` 单行、`post_age_max_hours/velocity_min/min_like_floor` 三列、NULL→写死默认、热加载、启动幂等自建 <!-- cloud fd9cca9 src/config/hot-lead-config-store.ts -->
- [x] 4.2 `hot-lead-config-facade`：非法/越界 400 整块拒、缺字段 no_valid_fields、非乐观回真态；判定角色现读 `getGateConfig()` <!-- cloud fd9cca9 src/config/hot-lead-config-facade.ts -->
- [x] 4.3 `panel-server.ts`：**新端点** `GET/PUT /api/hot-lead-config`（不复用 `/api/quotas`——账号限频≠帖子热度，语义不混用） <!-- cloud fd9cca9 -->
- [x] 4.4 aidcp-console：`QuotasPage.tsx`「安全」页加「内容热度过滤（全局）」卡片 + 编辑弹窗（三 InputNumber），走 `/api/hot-lead-config` <!-- console 8540b1e -->
- [x] 4.5 facade 单测：非法值整块拒不落库、合法热加载回真态、部分字段回落默认（5 测全过） <!-- cloud fd9cca9 test/hot-lead-config-facade.test.ts -->

## 5. aidcp-cloud — 引流线索评估角色（段一·热点·串行）

- [x] 5.1 `src/hot-lead/hot-lead-detector.ts` **接稿件价值判定之后**：订阅 `note.detail.arrived`（缓存最近一篇）+ `quality.pass`（放行 noteId 取缓存跑闸）；`quality.reject` 不入队；fire-and-forget；构造不把 llm 当必需（纯确定性） <!-- cloud 503eb3e -->
- [x] 5.2 roleName `hot_lead_detector` 加进 `RoleName` 穷举；**不进 `role-catalog`**（纯规则、对齐白名单） <!-- cloud 503eb3e -->
- [x] 5.3 `RoleDispatcher.setup()` 条件注册（依赖 `hotLeadQueue` store）；options 加 `hotLeadQueue/hotLeadGateConfig/hasCommentedForLead`；`server.ts` 接线（PgHotLeadQueue init + hasCommented 走 riskStore.hasInteraction） <!-- cloud 503eb3e -->
- [x] 5.4 单测：quality.pass 命中入队、quality.reject 不入队、缓存 miss 跳过、已评过去重、refreshOnly 不误触发（6 测全过） <!-- cloud 503eb3e test/hot-lead-detector.test.ts -->

## 6. aidcp-cloud — 候选队列存储与去重（段一）

- [x] 6.1 `hot_lead_queue` 表 + pending 部分唯一索引，`init()` 幂等自建、无迁移器 <!-- cloud 6231f9c src/hot-lead/hot-lead-queue.ts -->
- [x] 6.2 入队去重：队列内 pending 去重（部分唯一索引 + ON CONFLICT）；`hasInteracted` 前置在角色 5.1；按账号隔离 <!-- cloud 6231f9c + 503eb3e -->
- [x] 6.3 队列读接口 `listPending` + `markActioned`/`markDismissed` 供段二/console 消费 <!-- cloud 6231f9c -->
- [x] 6.4 单测：5 测全过 <!-- cloud 6231f9c test/hot-lead-queue.test.ts -->
- [ ] 6.5 段一验收：真机看速率分布、后台校准三阈值与日期选择器（→ backlog 簇，见 9.4）

## 7. aidcp-cloud — 人审逐条消费（段二）

- [x] 7.1 消费入口：**panel API**（避开热点 `feishu/commands.ts` 的 fleet 撞车）——`GET /api/hot-leads?accountId`（列 pending）+ `POST /api/hot-leads/comment`（选一条触发） <!-- cloud fb5b0eb -->
- [x] 7.2 对选中 lead 调既有 `triggerTargeted(accountId,{noteId,title},{injectGroup:true})`（复用 runTargetedTask → 去AI味 → 群码 verbatim → 飞书人审=发） <!-- cloud fb5b0eb -->
- [x] 7.3 触发 ok → `markActioned(leadId)`；缺码 fail-closed / 已评过 / 边端离线由 triggerTargeted 诚实回执，非 ok 时 lead 不置 actioned（返 409 + reason） <!-- cloud fb5b0eb -->
- [x] 7.4 红线：浏览闭环不因本 change 自动发评论/注群码；群码只经此逐条人审路径 + 既有排期 <!-- cloud fb5b0eb + 全链设计 -->
- [ ] 7.5 单测：逐条发出置 actioned / 缺码 fail-closed / 人审拒诚实失败——**待补**（当前靠 triggerTargeted 既有回执语义 + 类型闸；真机端到端在 backlog）

## 8. 文档与协议台账

- [x] 8.1 `docs/protocol.md`：`note.detail` 示例加 `publishedAtText` 字段（消息类型数不变） <!-- aidcp docs -->
- [x] 8.2 `AC-PROTO-*` 无需改：只加上行 payload 字段、未加 `MessageType`，穷举断言不变（cloud 1588 测含 AC-PROTO 全过）

## 9. 回归与验收

- [x] 9.1 edge：`npm run typecheck` 干净 + note-extractor 桩测 14 pass <!-- edge e033ca0 -->（`test:acceptance`/全量 `npm test` 待 land 前在运营机跑）
- [x] 9.2 cloud：全量 `npm test` **1588 pass / 0 fail**（含 AC-PROTO/AC-PUB/AC-RISK 红线）；`typecheck` 仅剩 base 预存 text-card satori/resvg <!-- cloud fb5b0eb -->
- [x] 9.3 console：`npm run build`（tsc --noEmit && vite build）过 <!-- console 8540b1e -->
- [ ] 9.4 真机验收登记 `docs/real-machine-acceptance-backlog.md`（本条完成即登记）：日期选择器真机形态覆盖（刚刚/小时/昨天/裸日期/编辑于/带地区）+ 广/窄 fallback 选择器是否误命中评论区日期、速率分布与阈值校准、抽取不污染正文、后台改阈值热加载、逐条人审发引流评论端到端、群码 verbatim + 缺码 fail-closed

## 10. 集成与部署

- [x] 10.1 集成：三仓 `scripts/land-change --yes` 全 land 到 origin/master（cloud `fb5b0eb`、edge `a473682`、console `a2d4d20`；edge 干净 rebase、console 修好 pacing 测 mock 后 land）；均通过 rebase+全量 test+typecheck；我提交仍在 master 祖先链（并发 fleet 后续推提交在其上）<!-- landed 2026-07-08 -->
- [x] 10.2 段一部署 dev：cloud 安全序列（备份 `cloud.bak.20260708-231424.tar.gz`+`.env.bak`→rsync 净 master 快照→restart→healthcheck：service active、8787/8090、PG `select 1`、`hot_lead_queue`+`hot_lead_config_global` 自建、`/api/hot-lead-config` 401 路由在、startup「HotLeadQueue 已就绪」无错）；console 构建 rsync（不 --delete，nginx 8088=200、新 bundle 生效）；**未碰 isales**。<!-- 2026-07-08 deployed dev -->
  - ⚠️ **edge 未部署**：edge 跑在运营机、非 ECS——已 land origin/master，需运营机 `git pull` + 重启边端才生效（发布时刻抽取上线）。
- [ ] 10.3 段二启用：**待真机校准段一阈值/选择器满意后**再走人审逐条消费（`/api/hot-leads*` 已部署但队列产出依赖 edge 上线+选择器命中）
- [ ] 10.4 archive：**待真机验收（backlog 簇 16）确认段一有效后** `openspec archive`（当前保留 active；避免并发 fleet spec 合并撞车 + 未真机验证即收口）
