# 真机验收专项（Real-Machine Acceptance Backlog）

> **为什么有这份文档**：本系统的 openspec change 归档门槛里，大量是「真机验收」（边缘节点在线、
> 运营放行、浏览器点测、飞书肉眼确认）。这些验收**彼此高度关联**、且只能在真机上做，逐个 change
> 都单独验一次效率太低。于是**把归档与真机验收解耦**：代码写完 + 已部署即归档清账（不再等真机），
> 待验的真机项**统一收拢到这里**，按「共享真机环境」聚类，一簇一次性验完。
>
> **纪律**：
> - 归档**不再** gate 在真机验收上；但真机项**必须**登记到本文件，不得随归档丢失。
> - 每簇标注**前置环境**；同簇项在**一次真机 session** 内一起验。
> - 验过就勾 `[x]` 并注日期；某项若暴露问题 → 回对应（已归档）change 或起修复 change。
> - 源 change 已归档，位置见 `openspec/changes/archive/<YYYY-MM-DD>-<name>/`（tasks.md 仍留完整上下文）。
>
> 建立日期 2026-07-03。来源 = 2026-07-03 openspec change 分诊清账批次。

---

## 簇 1 — 多账号 / 多租户内核 ⭐最关键

**前置**：≥2 台在线 edge 节点，各以 `AIDCP_ACCOUNT_ID=<非 default>` 启动；对应账号已在后台配好人设。
**为何最关键**：多租户内核随 publish-history + multi-account **co-ship 上线，但部署时无 edge 在线、
现网握手从未真机验过**；现网 edge **必须**带 `AIDCP_ACCOUNT_ID`，否则被内核拒握手、浏览闭环不起。

- [ ] **multi-account-node-support 7.1** — 两不同账号 + 同账号两节点，均不串号
- [ ] **publish-history-account-and-detail 8.2** — 非 default 账号节点握手成功 + 发布历史按账号隔离；**重点确认现网多租户握手真的通**
- [ ] **account-identity-from-login 3.1** — 登录身份 E2E
- [ ] **account-persona-config** — 非 default 账号**未配人设时应诚实拒启**（人设闸生效）
- [ ] **nickname-capture-on-login 3.1/3.2** — 登录昵称捕获真机回归
- [ ] **adspower-browser-provider 8.2**（可选）— `AIDCP_BROWSER_PROVIDER=adspower` 单账号完整 cloud 闭环灰度

## 簇 2 — 通知巡视链路

**前置**：飞书 Bot 在线 + 一个有真实通知态的账号 + 真机浏览。

- [ ] **notification-monitor 6.5** — 飞书肉眼终验 + CDP 断连复现（看门狗有界恢复）
- [ ] **notification-clear-to-zero 5.3 / 5.4** — 通知清零真机验收
- [ ] **notification-clear-to-zero 4.3** — 低优先口径校准（待真机通知样本）

## 簇 3 — 发布链路（会真发一条帖）

**前置**：运营机 edge 在线、已授权发布；确认要真发一条。

- [ ] **publish-media-upload 8.4** — 运营机真机端到端发一条（**带配图**，验 upload_image / set_cover 落地）
- [ ] **edit-note-draft-before-publish 8.3** — 草稿在位编辑后再发布，确认一次
- [ ] **publish-edge-command-runtime 6.2.1** — 飞书全链发布烟测：`/publish` 触发→草稿→飞书审批→`publish.command` 序列逐条回报（`ok/value/error`）→发布落地（URL 跳 `/publish/success`）；未授权时序列截止于提交前（AC-PUB）。注：2026-06-21 曾手动 CDP 直驱跑通发布（标题 20 字截断修复后），待新一轮飞书全链；与上面 8.4 同一次真机 session 可一并覆盖
- [ ] **edge-companion-ui 真数据流转（handoff §5.1/§5.2）** — 前置**已满足**（2026-07-04 09:06 cloud 1f013e7 与 console 首帧鉴权构建同步上线，healthcheck 全绿）+ 客户端用 2026-07-03 22:37 重打的安装包（`../aidcp-edge/dist-electron/`）。验：①发布卡真数据全链——云端出草稿→客户端发布卡**自动**展开「等你确认」（带编号 #n，与飞书卡「编号」一致）→飞书通过→卡转「择时发布」→发布落地→卡收「上次发布 · 刚刚」+活动流一条+今日小结不计数；飞书拒绝→卡收「暂不发布」；②清 userData 模拟新装机→标题带显真实小红书昵称（@ 前缀）、发布卡直显云端返回的上次发布；③界面红线复核：零审批控件、reminded 永不出现、无事件不造活跃

## 簇 4 — 浏览闭环行为（真机浏览观察）

**前置**：任一在线账号真机浏览。

- [ ] **return-to-feed-on-follow-block 3.1 / 3.2** — follow 受阻后返回 feed 续刷、不死锁
- [ ] **recency-aware-revisit-pacing 4.4 + 3.2 / 3.3** — 新鲜度重访节奏，上线后校准观察
- [ ] **restore-auto-resume-and-global-safety-config 10.3 / 10.4** — 断点自动续跑 + 全局安全配置生效
- [ ] **fix-interaction-and-comment-capture 7.1** — 互动栏是否存在「只带 `.engage-bar` 不带 `.interactions`」布局变体（定 E1 逗号选择器兜底是否够；打开一篇笔记核 engage-bar 真实 class）
- [ ] **fix-interaction-and-comment-capture 7.2** — 评论行 `[id^="comment-"]` 与可滚容器种子选择器真机校准（定评论采集命中率；核评论行真实 id 前缀与内容/作者 class）
- [ ] **edge-companion-ui 顺手修（评论点赞白名单）** — edge ≥b0055bd 分发后观察：云端 `comment_like`→`interaction.like_comment` 此前在边缘入口被静默丢弃（云端 sent=1 边缘零执行零回执），修复后评论点赞**首次真实执行**——观察边缘日志「✓ 评论点赞成功」出现、云端配额/风控计数口径符合预期（AIDCP_COMMENT_LIKE 线上已开，行为从无害空转变为真点击）
- [ ] **fix-interaction-and-comment-capture 7.3** — 线上抓日志佐证：`skip reason=cooldown`（限流占比、佐证「偶尔没点着」主因是设计限速）、`recover_after_like_failed|recover_after_collect_failed` 频次应降、`未找到可滚动的评论区容器`(no_target) vs candidates 长度分布、`btn_no-bar` vs `state_unchanged` 分布（验 E1 是否消掉 no-bar）（2026-07-03 实装，部署后观察）

## 簇 5 — 后台配置生效（浏览器点后台 UI）

**前置**：管理后台可访问（console `8088`）+ 一个账号有流量出数。

- [ ] **role-model-category-config 5.5** — 「设分类默认 → 同类继承」点测
- [ ] **editable-account-group-label 4.4** — 账号表分组列 inline 编辑落库
- [ ] **session-limits-to-quota-layer 7.4** — 配额层真机校准
- [ ] **llm-token-usage-stats 7.5 + 6.4** — token 用量曲线真机出数 + 视觉/数据核对
- [ ] **dashboard-refresh-clarity 4.4/3.2** — 总览页新鲜度标识随 10s 轮询推进；零边缘在线时「系统未在浏览」提示可见（能一眼区分「无新活动」vs「界面冻结」）（2026-07-03 集成，部署后验）
- [ ] **persona-driven-content-pipeline 3.2** — 人设页：留空保存被拦 + 诚实提示；未绑定账号红标「未绑定」（非「回落默认」）（2026-07-03 集成，部署后验）
- [ ] **content-schedule-group-comments 前置一条** — 开启任一账号自动群评前，先手动 `/comment <昵称> group:on` 真机端到端发一条（确认生产链路「审=发」：边端 split-typing 原样送达含码文本）；随后再验排期群评：到点触发→人审→发出、尝试满额停、同码开关被硬拒（2026-07-03 部署，行为默认关）
- [ ] **content-schedule-auto-publish / content-schedule-comments 端到端** — 排期页圈三态白点 + 开账号发帖/评论开关与日上限 → 到点（该账号该动作的错峰分钟）飞书出草稿人审卡 / 评论任务卡；空槽（无素材 / 无强相关目标）黄卡如实；浏览休眠小时绝不自动（自动 ⊆ 活跃闸）；日上限达标后不再触发（2026-07-03 双 change 已部署开闸，边端在线时段观察）

## 簇 6 — 精选库（数据自然积累后，机会性验）

**前置**：账号跑一段时间、精选库有沉淀。

- [ ] **curated-note-actions 5.3** — 精选笔记触发洗稿：飞书人审卡出现→通过→边端发布成功，草稿正文与参照有可辨识差异
- [ ] **curated-note-actions 5.4** — 精选笔记触发内容评论：搜索定位命中→人审→发布→去重记账；观察搜索命中率与标题截断策略
- [ ] **curated-note-actions 5.5** — 精选笔记触发带群评论：口令追加、审=发；抽查拒绝路径（壳行 / 已评论 / 未配口令 / 评论行禁用）
- [ ] **curated-admission-eval-roles** — 评论链路 `curated_comment_evaluator` 真机补采样本（单测已覆盖，机会性补）
- [ ] **curated-inspiration-corpus** — Phase 2b：边端逐条评论赞数 / 笔记评论数上报（11.1/11.2 deferred，搭下次评论抽取便车）

## 簇 7 — 桌面打包（需人扫码 / 需 Windows 真机）

**前置**：可出桌面打包产物 + 人在场扫码；Windows 项另需一台真 Windows 机。

- [ ] **edge-desktop-packaging 4.6 / 6.4** — 打包产物启动 + 人工扫码登录闭环
- [ ] **edge-companion-ui 6.3（win 半段）** — Windows 真机装 `AIDCP Setup 0.2.0.exe`（mac 交叉构建，2026-07-03）：验 titleBarOverlay 观感（46px 叠加窗控、最小/最大/关闭可用）、标题带随风控染色时 `setTitleBarOverlay` 同步换色、拖拽区与控件岛不打架（mac 半段已当日真机验过）
- [ ] **adspower-auto-create-env（UI 半段）** — 真实客户端里在设置抽屉点「创建环境」：挑模板→建号成功、环境列表刷出新环境、无代理显「无代理配置」；点某行「删」按钮两次确认→删除成功刷新。（底层 user/create + user/delete 已由 `scripts/adspower-fingerprint-probe.ts` 真机验过，此项仅验 Electron UI 路径；2026-07-03 归档）

## 簇 8 — 真模型行为回归（LLM 运行时，prompt 面已由 AC 锁死）

**前置**：真模型出口可用 + 一个非技术领域人设账号真实跑一轮浏览 / 发布。
**说明**：prompt 渲染面已有 acceptance 断言锁死（AC-CONCEPT-NEUTRAL / content-detech），
此处验的是**真模型在新 prompt 下的产出行为**，单测桩覆盖不了。

- [ ] **persona-driven-content-pipeline 1.3** — 非技术笔记（美食/旅行/穿搭）真模型能抽到领域概念并写库；纯情绪/无信息仍返回空
- [ ] **persona-driven-content-pipeline 4.6** — 非技术人设账号真模型生成的正文/标题体现该账号领域、无技术腔残留

---

## 附：两个「部署存疑」项 —— 已了结（2026-07-03）

只读探 ECS 确认：两者的角色文件均在 `/opt/aidcp/cloud`、md5 与本地 master 逐字节一致、服务
active（部署载体 = 整机 ECS→HEAD 升级，见控制仓 `c4ef902`）。已补 deployed 标记并归档：

- **split-topic-roles** ✓ 已上线、已归档（`2026-07-03-split-topic-roles`）
- **publish-metadata-compliance-roles** ✓ 已上线、已归档（stage-4 显式延后项随归档 tasks.md 留档）

---

## 簇 9 — console-cloud-panel-hardening 真机验收（面板加固批，登记于 2026-07-03）

**前置**：cloud 已部署新面板层 + console 已发新构建（**WS 协议 breaking：首帧鉴权取代 ?token=，cloud 与 console 必须同步部署**，否则旧 console 连新 cloud 会 auth_timeout）+ ECS 运维项已执行；一个真实运营会话在跑。<!-- 2026-07-04 09:06 前置已满足：cloud master 1f013e7 + console 首帧鉴权构建同步上线（cloud restart 切换、healthcheck 全绿、/api 鉴权 401 生效） -->

- [ ] **#3/#24 会话续签** — 活跃使用超过 TTL 不被踢；临近过期自动换新令牌（网络面板见周期性 `/api/auth/refresh`、令牌 exp 推进）；登出后原令牌立即 401 revoked
- [ ] **#25 WS 首帧鉴权 + 到期断连** — Nginx access log 的 `/ws` 行不含 `?token=`（token 走首帧）；令牌到 exp 时连接被主动 close(4401)、前端不无限重连而是跳登录
- [ ] **#26 令牌撤销** — 登出/管理撤销后该令牌 HTTP 与 WS 均立即被拒；cloud 重启后黑名单清空属预期（短 TTL + 续签使窗口有界）
- [ ] **#20 WS 背压 / 大载荷截断** — 高频事件下慢客户端（后台标签/弱网）被跳帧/断开而非拖垮主编排进程；超 256KB 的 page.cards/note.detail 前端收到 truncated 摘要帧
- [ ] **#21/#22/#23 索引与保留** — 生产库 `\d risk_counters`/`interaction_feed`/`llm_token_usage` 见 occurred_at/bucket_start 打头索引；面板今日聚合/全局互动流/用量窗查询 EXPLAIN 无 seq scan；保留清理日频删超窗行（7d/30d/45d）
- [ ] **#4/#5/#6 漂移哨兵 live 对拍** — 设 `AIDCP_PANEL_URL` 指向 ECS 面板端点跑 console 哨兵 live 用例（`aidcp-enums.test` 的 skipIf），确认 riskAction(7 含 comment_like)/imageProvider(含 volcengine)/dtoFields.panelAccount 与 cloud live 一致
- [ ] **#5 图片厂商** — 线上切图片厂商为火山即梦后，设置页与角色页显示火山（不再钉死通义）
- [ ] **#26 httpOnly 迁移评估** — 评估 token 从 localStorage 迁 httpOnly cookie 的条件（跨 8088 console/8090 面板端口的 cookie 作用域需 Nginx same-origin 反代配合），决定是否落地（本批仅留 setToken/getToken 抽象缝）

### ECS 运维项（部署时执行，对应 tasks 1.8/1.9/1.10）
- [ ] `AIDCP_PANEL_JWT_TTL_SECONDS` 设值（续签已落地故可短，如 3600；不设则默认 3600）<!-- 2026-07-04 部署时未设值，走代码默认 3600（续签已落地，够用；要更短再上机加 env） -->
- [x] Nginx `aidcp-console.conf` 去 `/downloads/` 的 `autoindex on`（#27，`curl /downloads/` 应返 403/404）<!-- 2026-07-04 09:06 随 cloud+console 同步部署执行：autoindex off + nginx reload，curl 实测 403；conf 备份 aidcp-console.conf.bak.20260704-090427 -->
- [x] 生产库补 occurred_at/bucket_start 索引（上机执行 `CREATE INDEX IF NOT EXISTS` 或确认随重启自建）<!-- 2026-07-04 重启后 \di 实测六索引齐备（risk_counters/interaction_feed/llm_token_usage 各 2），随启动自建确认 -->

## 簇 10 — identity-recheck-page-context-guard 真机验收（身份误判停摆修复，登记于 2026-07-03）

**前置**：edge 本地重建到 master `0765e00`+ 一个真实账号跑一轮「浏览 + 发布」（发布会把共用标签页带到 `creator.xiaohongshu.com`）。
**背景**：修复的是「发布把标签页带离消费端 feed → 身份监测体不看页面就误判登出 → 断连停摆」的系统性假阳性（2026-07-03 同账号当天复现两次）。分域判据/inconclusive/断连前诚实回执/自愈归位四条逻辑单测已锁，此处验真机页面行为。

- [ ] **创作发布页登录门禁判据** — 未登录访问 `creator.xiaohongshu.com/publish/publish` 确会 302 到 `creator.xiaohongshu.com/login`（判据 `path.includes('/login')` 成立的前提）；已登录停在真实发布页 URL host=`creator.xiaohongshu.com`、path 非 `/login`
- [ ] **发布期间身份监测不误判** — 真实账号一边浏览一边发布，发布跨越 ≥1 次 30s 身份轮询时，日志出现「creator-app 判健康」或「无法确认本轮跳过」，**绝不**再出现「身份失效（登出/过期）→ 退回无身份态」+「重新确立身份失败 → 停摆」
- [ ] **消费端真登出仍判 lost** — 真在消费端登出（或 session 过期弹登录浮层）时，身份监测体仍连续判 lost 达阈值、正常退回无身份态（分域闸不漏判真登出）
- [ ] **自愈能回消费页恢复** — 若在创作页/弹层态触发一次重新确立身份，`reestablishIdentity` 先 `Page.navigate` 回 explore 首页再读身份、健康账号真恢复重连（而非停摆待人工）
- [ ] **在途发布断连诚实回执** — 身份翻转断连若撞上在途发布，云端收到 `[recycled] identity_flip:*` 失败 `publish.command.result`（不再干等），且绝不重复发帖

## 簇 11 — cloud-oss-storage-integration 真机验收（配图转存 OSS 根治过期掉图，登记于 2026-07-04）

**前置**：cloud 部署含 `d0e865e`（OSS 上传出口 + 配图转存）；ECS 设好 OSS 凭据（env `OSS_ACCESS_KEY_ID`/`OSS_ACCESS_KEY_SECRET` 或 SQL 写 `provider_credentials` 的 `oss/*`）；桶 `aidcp`（`oss-cn-beijing`）允许对象级公读 ACL；启动日志应见「OSS 对象存储已就绪（bucket=aidcp region=oss-cn-beijing …）」。<!-- ✓ 前置已全部满足 2026-07-04 ~13:45：外科式部署上线 + AK 写 .env + 用户关桶「阻止公共访问」+ 冒烟测试 PUT/匿名 GET 200/DELETE 全通 + 启动日志见「OSS 已就绪」。只等真机发一帖跑真链路。 -->
**背景**：当前 `publish_log.image_url`/`images` 存的是文生图厂商临时 URL（~24h 过期）；审批延迟超 TTL → 边缘去下载已死链 → 笔记少图/无图。本 change 在图生成后把每张转存 OSS、以公读永久链接持久化。红线：转存失败诚实少一张、绝不伪造 URL、绝不静默回退 provider 临时 URL。

> **✓ 核心验收通过 2026-07-04**：用户真跑 `/publish` → `publish_log` id=42 status=published，3 张配图全为 `https://aidcp.oss-cn-beijing.aliyuncs.com/publish/63e2ff05…/<runToken>/<seq>` OSS 链接、`images_attached_count=3=n_images` 诚实、键含真实账号 id、ImageGenerator ~48s 无「转存失败/部分成功」告警=逐张洁净转存、edge 从 OSS 下载 3 张并成功贴帖闭环。change 已 archive。

- [x] **配图落 OSS 稳定链接** — ✓ id=42 三张全为 `aidcp.oss-cn-beijing/publish/<真实accountId>/<runToken>/<seq>` OSS URL，非厂商临时域名
- [x] **边缘从 OSS 下载并上传成功** — ✓ status=published + k=3 = n_images：edge 收到 OSS URL、下载 3 张并成功贴到小红书，张数与生成一致（诚实 M=K）
- [x] **过期根治（核心价值）** — ✓ 由构造保证（永久公读链接，无 TTL）+ 冒烟匿名 GET 200 已证；不再等 24h 实测「隔天仍可下载」（机制上不可能失效）
- [ ] **转存失败诚实降级** — 逻辑+单测+acceptance(AC-OSS-*)已覆盖；真机本帖 3 张全成功、未诱发失败。留待自然遇到坏源/OSS 抖动时观察 `images_attached_count` 是否如实减一（非阻塞）
- [ ] **未配置零回归** — 生产已配 OSS，本项不适用于生产；未配环境的零回归由 acceptance AC-OSS-05 守（非阻塞）
- [ ] **内/公网 endpoint（若开 OSS_INTERNAL）** — 当前 `OSS_INTERNAL` 未设=公网上传；若确认 ECS 在 cn-beijing 可后置开内网省流量（非阻塞增强）
- [x] **未触碰同机 isales** — ✓ 全程只动 aidcp-cloud.service + /opt/aidcp/cloud + 桶 aidcp；部署后核 isales-api 仍 active

## 簇 12 — publish-select-mode-layout-robust 真机验收（发布选「上传图文」跨双布局稳健，登记于 2026-07-04）

**前置**：edge 本地重建到 master `130acd7`（含 `runSelectMode` 双布局稳健修复）；AdsPower 该账号浏览器已登录（`user_id=k1e0ero8`=大白 / `k1e0awu5`=Tmax）。
**背景**：创作发布页宽/窄双布局导致 tab 重复渲染两套（一套可见一套隐藏），旧 `select_mode`「取第一个文本匹配、不挑可见、只等 12s」→ 生产偶发 `no_target`（recordId=37，2026-07-03）。修复=取可见 + 幂等早退（保守 MODE_STATE）+ 有界重试（20s<云端30s）+ 辅助信号 video 否决 + 诚实失败；**窄布局精确形态是 best-effort、待此处标定**。逻辑单测已锁（587 绿），此处验真机页面行为。

- [x] **窄布局 tab 形态标定（最大不确定）** — ✅ 2026-07-04 CDP 只读 dump（大白，`scripts/calibrate-select-mode-layout.ts`）。**关键发现：隐藏副本不是 display:none 而是移到屏幕外** `rect≈{x:-9758,y:-9934}`（offsetParent 非空、getClientRects 非空）——消费端 `offsetParent||getClientRects` 判据会误判其可见、且它文档序更靠前，旧「取首个」正点了它。**且不是宽/窄差异**：600×900 窄视口 tab 栏形态与 1904 完全一样、克隆仍在 -9758 → 持久屏幕外克隆、与视口无关（创作页 tab 栏无独立窄形态）。**修**：`IS_VISIBLE` 改「与视口相交」判据（`getBoundingClientRect` 非零盒 + 落在视口内），排除屏幕外克隆（edge `f51ae9c`）。
- [x] **宽布局取可见 tab 真点中** — ✅ 端到端实测（`scripts/verify-select-mode-live.ts` 驱动真实 dispatcher）：默认 `mode=video`/accept 视频类 → `select_mode` `ok:true` **531ms**（点屏内 `369,81`、未误点屏外克隆、无重试）→ `mode=image`/`accept=.jpg,.jpeg,.png,.webp`（模式真切换）。
- [x] **窄布局取可见 tab 真点中** — ✅ 窄视口（600×900）dump 确认取的是屏内可见 tab（视口相交判据在窄视口下仍正确排除屏幕外克隆）。
- [ ] **幂等早退真机验** — 已在图文模式时再触发 `select_mode`，确认直接成功、不重复点击、不误报 `no_target`（逻辑单测已锁；真机顺带在簇 3 全链路重入时观察）。
- [ ] **接簇 3 端到端** — 与簇 3 发布链路一并跑**整条** `/publish`：审批→`navigate_entry`→`select_mode`→填写→提交→落地；`select_mode` 步已单独端到端验、剩全链路把它串起来跑一次真发帖。
- [ ] **辅助信号 video 否决不误伤** — 真机 `select_mode` 经权威 `MODE_STATE==='image'` 判成功（531ms 实测走的就是权威信号、辅助未用上）；簇 3 全链路时再确认无「点了没切上谎报成功」也无「真切上却被 video 否决误判失败」。

## 簇 13 — humanize-interaction-prompts 真机验收（互动决策链 prompt 拟人化，登记于 2026-07-07）

**前置**：cloud 部署到含 master `14eda68` 的 dev；某绑定人设的真实账号跑浏览闭环。
**背景**：8 角色 prompt 拟人化精修（人设性格注入、口味判据人设派生、决策上下文注入、选卡好奇豁免、评论链语境穿透 + 去 AI 味评论体裁召回、评论门槛 300/100）。改动全是 prompt 文本与注入逻辑，逻辑单测已锁（cloud 1406 绿）；以下是**只有真机/真 LLM 才能判**的观感项。

- [ ] **多账号判定差异** — 两个兴趣相近、性格（tone/style/like_principle）不同的账号跑同一批 feed，抽查是否在「翻不翻评论区 / 是否评论 / 点赞收藏」上产生可区分差异（改前逐条一致）。
- [ ] **评论文本观感 + 去 AI 味触发率** — 观察自主评论文案是否不再千篇一律「一句共鸣/提问」；`comment_de_ai_flavor` 对评论体裁的改写触发率是否从近 0 恢复到有效区间（客套句「感谢分享」类被改写）；`nothing_genuine` 弃权是否在没真话可说时如实出现、不硬凑客套。
- [ ] **门槛 300/100 后候选量与人审压力** — 评论候选量较改前放大多少、进入 LLM/飞书人审的量是否可控；观察放进来的是否主要为中腰部高收藏内容（教程/攻略），必要时回调常量。
- [ ] **好奇豁免命中观感** — 命中好奇豁免（~12%）的那些轮次，选卡是否偶发打开兴趣外但标题确实有趣的内容、且未越品牌安全禁区；未命中轮从严口径不变。
- [ ] **会话状态 / 阅读体验注入生效** — 判定 prompt 里「本场已看 N 篇 / 最近互动 / 翻了 N 张图」是否真随会话推进变化并影响判定（序列依赖）；确认 keyPoints 休眠钩子当前不产出（等未来深读角色填充）。

## 簇 13 — textcard-cover-form 真机验收（文字卡封面形态跟随，登记于 2026-07-07）

**前置**：dev cloud 已部署 `a23f8e5`（依赖+字体+渲染冒烟均已过）；影子模式已开（`AIDCP_COVER_FORM_SENSING=true`，渲染旗标未设=关）。探活已证：qwen-vl-plus 对本 change 缘起原图（`curated-reference/66cd1d4f…/6a4be93d…/01.webp`）判 `text_card` conf=0.95。
**背景**：洗稿封面与原文字卡形态脱节的治本 change。感知→决策→渲染全链已实装并单测锁死（1531 全绿）；剩余项全部依赖真机洗稿发布自然积累，与归档解耦。

- [ ] **影子模式感知准确率（放行渲染的门槛）** — 积累 ≥5 次带参照图的洗稿发布后，经 panel API / psql 查 `publish_log.publish_metadata->'coverFormAudit'`：`sensedForm` 对原图形态判定是否准确、`no_image`/`error` 占比是否可接受；**photo→text_card 假阳性是最伤方向，重点核对**。二次洗稿同笔记应 `sensedSource='cached'`（零重复调用）。
- [ ] **放行渲染真机首帖** — 准确率达标后 ECS `.env` 加 `AIDCP_PUBLISH_TEXTCARD_COVER=true` + 重启，选一条文字卡原图的精选笔记触发洗稿：审计应 `coverForm='text_card'` + `renderStatus='rendered'` + 带 themeKey；飞书人审复核卡面（排版/文案/无引流词）后放行发布；发布成功后小红书端目检封面。回滚=删该行重启。
- [ ] **渲染降级链真机观察** — 自然遇到渲染失败/OSS 抖动时核对 `render_failed_generative` 如实落审计、封面由生成式顶上（非阻塞，机会性验）。
- [ ] **48 组合色板目检（非阻塞 follow-up）** — 渲对比页供用户目检冻结 hex；对比度 ≥4.5 已由单测全表锁，目检只调审美。

## 簇 14 — facebook-scheduled-comment 真发 真机验收（Facebook 定向评论真正发出，登记于 2026-07-08）

**前置**：真发编排全链已实装 + 单测锁死（edge master `9cda1d4`→`9c3ee01`：FacebookCommentExecutor + handler + 静默丢弃修复；cloud master `757a8fc`：buildFacebookEdgeSteps + runFacebookTargetedTask 真发路径 + 防重复真发）。**全链 fail-closed：`AIDCP_FB_COMMENT_AUTO` 默认关 → 物理发不出评论**。dev cloud 需重部署 master `757a8fc` 才有真发编排（旧部署 `24ef9d4` 只到影子编排层）；edge 是本地安装包、要用需重打包分发。以下项都要一次性运营 FB 账号（一次性、非生产号）+ 已登录 + 配好关键词/容器。

**BLOCKING（翻 `AIDCP_FB_COMMENT_AUTO=true` 之前必须全清）**：
- [ ] **生产执行器上再证 F1（服务器确认可区分乐观渲染 vs 真落库）** — phase-0 gated-submit 探针用的是全页 indexOf；生产执行器 `submitComment` 改用「本人数字 id 作者链接 + 目标帖评论区 + 文本片段」三重收窄确认（`buildScopedVerifyJs`）。用一次性账号自有帖手动跑一遍生产执行器：提交后 reload，确认命中 `confirmed=true` 只在真服务器落库时、乐观渲染/草稿残留不误判。**未证之前 kill switch 一直关、只跑影子**。
- [ ] **per-profile 代理（§8.4）** — 中国 IP 无代理写操作 checkpoint/封号风险高；真发前 AdsPower profile 必须配固定代理。

**真机调参 backlog（桩测不了、需登录一次性 FB 账号）**：
- [ ] **懒加载评论框滚动参数** — `editorScrollRounds` / `editorScrollDistancePx` / `settleMs` 真机标定（评论框在 permalink.php 首屏之下懒渲染，F1 已知需滚动催出）。
- [ ] **scoped own-identity 确认的真实评论行 DOM 标记** — 真机核对本人评论行的作者链接形态（`profile.php?id=<numericId>` / `/people/.../<id>` / vanity URL）与评论区容器选择器；`buildScopedVerifyJs` 的选择器按真机校准，防假阴/假阳。
- [ ] **乐观 vs 服务器确认时序** — `waitAfterSubmitMs` / `waitAfterReloadMs` 真机标定。
- [ ] **评论框/发布按钮真实 aria-label 中英文案** — 校准 `fbIsCommentEditor` / 发布控件正则（`发布评论|发表评论|Post|Comment|Reply|Send`）。
- [ ] **容器内搜索真行为** — group `/groups/<id>/search/?q=` 与 page 站内搜的真实路由、`search` surface 稳定性、入群问答/待批准门槛（`permission_gated` 是否如实触发、绝不回退全站）；容器标识符（当前 PIN 为运营方粘贴的 FB URL）真机确认。
- [ ] **短影子 sanity（task 7.3）** — dev 重部署 cloud `757a8fc` + `AIDCP_FB_COMMENT_SHADOW=true`，跑数小时：查 `facebook_comment_audit` 审计行、校验器拒率、候选相关性；确认影子绝不下发命令（`posted==[]` 已单测锁，真机复核审计侧）。
- [ ] **真发单账号首帖（task 7.4）** — F1 生产执行器复证 + 代理就绪后，`AIDCP_FB_COMMENT_AUTO=true` + 日上限 1–2/天，跑通一条「服务器确认成功」端到端；确认防重复真发（提交前打去重标记）在确认假阴性时不重复真评同一目标。
- [ ] **纯云 follow-up（不阻塞真发、可假边端测）** — task 2.6 登录/checkpoint 告警 + 跳过账号 + `/resume` 恢复闭环；task 2.7 连续阻塞 outcome（login_required/quota_denied/no_targets/compose_skipped）告警器（仿 pacing-saturation-alerter / captcha-coordinator 的 store-then-Feishu）。当前 `login_required` 等 outcome 已如实落审计，为这两块打好了数据面。

## 簇 15 — remote-captcha-assist 真机验收（云端远程处理验证码，登记于 2026-07-08）

代码与部署已就绪并经只读核验：dev 上 `AIDCP_CAPTCHA_ASSIST_ENABLED=true`、就绪门通过（token secret 走 `AIDCP_PANEL_JWT_SECRET` 回退、`AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL=http://aidcp.tommax.cc`）、协助页 `http://aidcp.tommax.cc/captcha-assist/<id>` 外网 200、`/api/captcha-assist/<id>` 无 token 401、启动无「未启用」告警。剩人机在环走查（需运营机 edge + 真/模拟验证码）：

- [ ] 运营机 edge 连 dev（`ws://121.89.85.150:8787`），账号刷到点选类验证码浮层、进入阻断态。
- [ ] 飞书验证码/未知告警卡出现「打开协助处理」按钮；点开进协助页，看到边缘截下的现场图（账号昵称/机器/风控态/URL 上下文齐）。
- [ ] 图上标点（最多两点）→ 提交 → 点击真的打进原账号原会话浏览器；处理期间普通浏览/互动仍被拦、只放行截图与点击。
- [ ] 复检遮罩：验证码真清除 → 回执 `cleared` + 边缘发 `risk.captcha_cleared` → 云端恢复下发；未清除 → `still_blocked` + 刷新新截图。
- [ ] 截图只在受保护协助页出现，不落飞书卡片/普通告警列表；令牌过期后页面正确提示、不可再读。
- [ ] 手动「解决告警」仍只记日志，不误标事故 `cleared`、不擅自恢复下发。

## 簇 16 — feed-hot-lead-group-comment 真机验收（浏览闭环发现热帖→引流待评队列→人审逐条群评，登记于 2026-07-08）

**前置**：cloud/edge/console 三仓各一 `feed-hot-lead-group-comment` worktree 分支（cloud `6231f9c..fb5b0eb`、edge `e033ca0`、console `8540b1e`），**尚未 land、未部署**。本地：cloud 全量 1588 测过、edge 桩测 14 过、console build 过。
**背景**：浏览闭环打开详情→稿件价值判定 `quality.pass` 后，云端新角色 `hot_lead_detector` 算「每小时点赞」热度速率、过滤闸（帖龄≤上限 且 速率≥阈值 且 赞≥下限）命中即入 `hot_lead_queue`（只发现不发布）；人审逐条经 `/api/hot-leads/comment` → 既有 `triggerTargeted(injectGroup)` → 飞书人审=发。**边缘日期选择器与三阈值均为 best-effort 占位、待真机标定**。红线：浏览闭环永不自动发群码。

- [x] **边缘发布时刻选择器真机标定（最大不确定）** — ✅ 2026-07-09 CDP 只读探针（`scripts/calibrate-note-date-probe.ts`，工程师大白/tom 分组，导航带 xsec_token 笔记链接开详情）：production `extractPublishedAtText` 经 **`.bottom-container .date`**（首选择器、count=1、精确）在 **宽(1512) / 窄(800) / 窄(500) 三布局均首命中**，抽到真发布时刻（实测「2天前 广东」「33分钟前 四川」，含地区后缀，云端 token 匹配自动忽略）。**广 fallback 风险坐实并已修**：`.date`/`[class*="date"]` 共命中 12 个＝1 笔记日期+11 评论时间戳（`.comment-item .date`）；正常路径被精确首选择器遮蔽、不触发，但为防 XHS 改名 `.bottom-container` 后误抓评论日期，已把评论区加入 denylist（edge `6cac9f7`）。<!-- edge 6cac9f7 verified+hardened 2026-07-09 -->
- [x] **抽取不污染正文（守 f8712f5）** — ✅ 真机三布局：命中日期节点 `inBody=false`（在 `.interaction-container>.note-scroller>.note-content` 内、非正文文本叶子容器）；评论时间戳硬化后 `inBody=true`（被排除）。<!-- edge 6cac9f7 -->
> **注**：`.bottom-container .date` 首命中稳定，末两条宽 fallback 现役为纯保险；边缘 landed origin/master(6cac9f7)、**运营机 pull+重启后生效**。「2天前」在默认 maxAge=48h 为边界通过（用户定用当前阈值）。
- [ ] **速率分布与阈值校准** — 段一先只观测：跑一段真机浏览，看 `hot_lead_detector` 日志的速率/帖龄分布，据此在「安全」页「内容热度过滤」卡片校准 `postAgeMaxHours`/`velocityMin`/`minLikeFloor`（默认 48h/300/500 为保守占位、非最终）。确认后台改阈值**热加载即时生效**（无需重启）。
- [ ] **quality.pass 咬合** — 确认只有过稿件价值判定的帖进队列；`quality.reject`（含 LLM 出错/解析失败）的帖即使很火也不入队；缓存按 noteId 对齐正确（一次一篇、不串篇）。
- [ ] **入队去重** — 本账号已评过（`riskStore.hasInteraction`）与队列内 pending 同 noteId 均不重复入队；按账号隔离。
- [ ] **段二人审逐条端到端** — `/api/hot-leads` 列 pending → `/api/hot-leads/comment` 选一条 → `triggerTargeted(injectGroup:true)` → 飞书人审卡 → 通过后真发带群码引流评论 → lead 置 actioned；群码 **verbatim** 追加、**缺码 fail-closed**（黄卡本次不发）、人审拒/超时/边端离线诚实失败且 lead 不置 actioned。
- [ ] **红线核** — 浏览闭环自治评论**永不**自动带群码（结构上下发 params 无 groupChatCode）；群码只经此逐条人审路径与既有排期。
- [ ] **段二单测补** — 7.5（逐条发出置 actioned / 缺码 fail-closed / 人审拒诚实失败）当前靠 triggerTargeted 既有回执语义 + 类型闸，未加专测；真机验收同时补面板消费层单测。

## 簇 17 — edge-persona-keyword-generation 真机验收（客户端自助建号人设，登记于 2026-07-08）

**前置**：cloud 部署含本 change（persona.generate/persist handler + PersonaGenerator + JSON→soul YAML 序列化器 + role-catalog `browse:persona_generator`）；edge 本地重建含向导（renderer 设置抽屉「账号人设」区 + stdin 桥）；一个真实账号在客户端新建环境扫码登录。角色 `browse:persona_generator` 后台可配模型（默认全局 qwen3.7-plus）。
**背景**：客户在 Electron 客户端扫码登录后，设置抽屉选关键词 → 云端大模型生成 soul 草稿 → 确认落库开跑。逻辑单测已锁（cloud persona-generator 10 / edge persona-onboarding 5 / 两仓 AC-PROTO 65），此处验真机端到端。

- [ ] **向导 gate 时序** — 未登录时「生成人设」按钮 disabled + hint 提示先登录；扫码登录 + 云端已连接后按钮启用（gate=auth='logged in' && cloud='connected'）；状态推送不重置已选关键词/草稿
- [ ] **生成闭环** — 选关键词点「生成人设」→ 十几秒内返回草稿（身份摘要 + soul 预览），soulYaml 结构合法；「重新生成」（不限次）产出有区分度（尤其 seed_keywords 不雷同）
- [ ] **确认落库开跑** — 点「确认使用」→ persona.persist 成功 → 该账号 persona_config 落库 + 绑定即被唤醒开始自动运营（onBound）；badge 转「已设置」
- [ ] **生成失败硬 fail-closed** — 制造模型不可用/超时，向导诚实提示失败、绝不塞模板人设、账号维持未绑（无草稿卡出现）
- [ ] **重连不双计费** — 生成在途遇断连/重试，云端幂等键去重、不重复调模型（观察 llm 记账 account=真实账号、无重复 ~185s 调用）
- [ ] **stdin 桥与 browser-parking 并存** — 桌面「显示浏览器 / 重置位置」等 parking 命令仍正常，persona 命令不干扰 readline（两条 stdin 消费者按 type 各取、互不抢行）
- [ ] **soul 序列化 round-trip 真机** — 真机生成的中文人设经 JSON→YAML 序列化后能被 loadSoulFromYaml 落库（含引号/#/特殊字符不炸）

**已知接受、后续独立立项的缺口**（本 change 明确不做，见 proposal Deferred/Accepted Risks；按用户 2026-07-08 决策砍配额、暂不补鉴权）：
- [ ] **边缘身份鉴权缺失（头号）** — 边云握手零鉴权、accountId 客户端自报；自助模型把边缘搬到客户机后隐性网络边界失效。付费生成端点在公网不鉴权 = 免费大模型刷（成本敞口无上限）+ 给尚无人设账号抢先写人设。**上任何客户可触达付费/写端点前须补**（enrollment 凭据 / 可验证扫码登录证明 + 按连接/IP 限流）。
- [ ] **限流/配额缺失** — 生成端点不限量（本期按用户明确要求砍掉配额与重生成上限）。
- [ ] **服务端枚举复验缺失** — 客户端封闭枚举是不可信 UI，改造客户端可直接发自由文本 keywordSelections 做 prompt 注入 / 白嫖 chatbot；须云端逐项对枚举白名单复验。
- [ ] **只创建不覆写守护缺失** — 未防越权覆写已有人设（当前仅靠握手绑定 accountId 部分收敛，非充分）。
- [ ] **跨账号语义去重 + 运营侧相似度报表/抽检** — 抗同质化真正承重项，后续独立 change（字面去重拦不住中文语义等价词；当前仅靠生成 prompt 内每账号差异化）。
## 簇 18 — edge-bundled-adspower-cli-runtime 打包 + 真机验收（内嵌指纹浏览器 CLI 免装，登记于 2026-07-08）

**背景**：change `edge-bundled-adspower-cli-runtime` 已归档——运行时启动 + 内核预检 + 进度条 + 设置页重设计 + 白标已实装并合入 edge master（d722f2a）；但**「把 CLI 打进安装包」这组 descope 为后续人工触发**（打包走远程 GitHub + 苹果签名，慢且贵，按「默认不打安装包」约定人工做）。本机（mac arm64，全局装 `adspower-browser` + live runtime）已核实：端点直连 + 内核 148 下载 + `browser/start`→CDP headful Chrome/148 全通、包体 58MB、sqlite 为 N-API。**未打包前 edge 启动走 mode: none/external、内嵌路径不激活、对现网零影响**。签名 change `edge-macos-developer-id-signing` 已 Complete、打包单写者约束已解除。

- [ ] **打包实装（人工触发）** — `adspower-browser` 加入 edge 依赖；electron-builder `extraResources`/`asarUnpack`（asar 外）、native `.node` 随 hardened runtime 签名；主安装包 MUST NOT 含浏览器内核；运行时工作目录/缓存指用户可写位置（`~/.adspowerCli` + 必要时首运复制包内 `cwd/`）。
- [ ] **干净机器起服冒烟** — mac arm64 / mac x64 / win 各打包后起一次：N-API `.node` 在 Electron 自带 Node 下加载、`ads start` 起服、`/api/v1/browser/start` 直连、CDP headful。
- [ ] **mac 签名/公证首启 Gatekeeper** — 对运行时下载到 `~/.adspowerCli` 的内核/chromedriver 首启是否弹阻。
- [ ] **首启内核下载全程 + 中断/重试** — 进度条门控 startEdge、断网诚实停「准备失败+重试」、`download-kernel` 续传 vs 重来行为。
- [ ] **单账号完整 cloud 闭环灰度** — `AIDCP_BROWSER_PROVIDER=adspower` 内嵌形态跑一遍完整云端浏览闭环（对应旧 backlog `adspower-browser 8.2`）。
- [ ] **运行时中途死亡有界重起** — 内嵌 runtime daemon 中途死：现靠核心 CDP 断→recycle→重起→再探→重拉；确认该链在真机成立，或补健康轮询。
- [ ] **文档** — OPERATOR/README 新机装机路径（内嵌运行时 + 首启下内核，self 与外部 `AIDCP_ADS_API_BASE` 逃生阀保留）；`docs/anti-detection.md` 补内嵌 CLI 形态。

## 簇 19 — 洗稿配图张数对齐 + 待审配图删除（2026-07-08 部署 dev，登记真机项）

**背景**：两 change 已实装 + 全绿 + 部署 dev：`rewrite-image-count-parity`（洗稿配图张数=源稿有效图数≤9、默认上限 3→9，cloud b1fbcec）+ `pending-draft-image-delete`（待审草稿逐张删配图，cloud 0be613f / console 8ce490f）。桩层已证决策/交互；下列须真机核（发一篇真洗稿 + 后台操作）。

- [ ] **洗稿张数对齐** — 挑一篇源笔记 N 张图（N≤9）的精选做洗稿发布，验证产出正好 N 张（图 0 文字卡/钩子、其余生成式）；源 >9 张验证夹到 9；源 0 有效图（纯文字源）验证回落内容驱动而非报错。
- [ ] **默认上限 9 生效** — 确认 dev 未设 `AIDCP_PUBLISH_MAX_IMAGES` 时上限为 9（非旧 3）；出图串行（IMAGE_CONCURRENCY=1）下 9 张的总耗时/超时可接受，无整篇因某张超时被拖垮。
- [ ] **文字卡只封面** — 复核多图洗稿：仅图 0 可能是文字卡（源封面被判 text_card 时），图 1..N 恒生成式插画，符合设计、非 bug。
- [ ] **待审删一张后照发** — 后台「内容→待审」删掉某张配图 → 批准发布 → 平台真帖少那张、其余顺序不乱、封面重算正确。
- [ ] **删空发纯文字帖** — 删光配图 → 二次确认 → 批准 → 平台发出纯文字帖（M=0 降级路径真机成立、不报错不塞回旧图）。
- [ ] **删配图版本闸** — 删配图后 content_version+1、原飞书审核卡失效（改后走后台审批）；并发下 version_conflict 如实提示、无丢更新。
- [ ] **防注入真机** — 正常 UI 只发子集不触发；确认后端对非成员 URL 拒 invalid_field（构造篡改请求验证，绝不把外部 URL 写进待发帖）。
- [ ] **OSS 孤儿** — 删配图只移除记录引用、不删 OSS 实体（接受）；观察是否需后续存储 GC（属 cloud-oss-storage 议题）。

## 簇 20 — 飞书通知按团队分发（单应用 + 外部群，2026-07-09 部署 dev，登记真机项）

**背景**：change `feishu-per-team-notification-routing` 已实装 + 全绿 + 部署 dev（cloud 25f765d / console b3970cc）。桩层已证解析兜底 / 存储 / 入站闸 / 面板契约；`group_route` 表已随 init 在 dev 自建。下列须真机核（涉及飞书对外共享 + 真外部群，桩验不了）。

- [ ] **对外共享认证前置** — 在飞书开发者后台为机器人开启「允许被添加到外部群中使用」（需一次性企业/团队/实名认证）；确认认证前无法开、认证后可开。
- [ ] **建外部群 + 拉客户 + 加机器人** — 由运营方成员建外部群、邀请一个外部（跨租户）成员进群、把机器人加入（指定自然人当群主）；确认外部成员需确认、且须在应用可用范围内。
- [ ] **按账号路由真机** — 给某账号设 `group_label`=teamX，在后台「通知路由」把 teamX 映射到该外部群；触发该账号一条真「评论/@」通知，验证落到该外部群、不落默认群。
- [ ] **未绑定落默认 + config-gap** — 另一账号不绑或 group_label 打错，验证其通知落默认（管理）群、不丢，云端日志出现 config-gap。
- [ ] **错映射防线** — 后台目标只能从「机器人所在群」下拉选；把机器人退出某群后，该群在下拉消失、原映射显式标「未知群」可清除（防映射错群 → 跨客户 PII 泄漏）。
- [ ] **面向运营方流量不外泄** — 验证审批卡 / persona / 验证码 / 排期回执 / 命令结果卡仍落默认（管理）群，MUST NOT 进客户外部群（外部客户不应看到内部运维/审批）。
- [ ] **入站作用域** — 设 `FEISHU_MANAGEMENT_CHAT_IDS`=管理群；在外部客户群 @ 机器人发 `/publish`/`/pause` → 诚实拒「本群无权」、不执行；管理群下同命令正常执行；`/help` 任意群放行。
- [ ] **外部群 API 支持核对** — 确认外部群里 `im/v1/messages`（text + interactive card）+ reaction 均可发（对照飞书 43 支持 / 11 不支持清单），无因不支持 API 静默失败。
- [ ] **零回归确认** — 未配 `FEISHU_MANAGEMENT_CHAT_IDS` 且 `group_route` 空时，命令与通知行为与改动前一字不差（现 dev 即此态）。
- [ ] **群名显示（加权限后）** — 在飞书开发者后台给应用加 `im:chat:readonly` 权限后，后台「通知路由」的目标群下拉与已映射行显示**真实群名**（而非 oc_ 开头的 id），`source=feishu`。
- [ ] **缺权限降级提示** — 未加 `im:chat:readonly` 时，后台顶部出现黄条「暂时无法获取真实群名，正显示群 ID」，目标仍显示 chat_id、可正常配置（`source=store`，不崩不空）。
- [ ] **默认群一眼可见** — 「通知路由」页顶部提示条正确显示「未映射 → 默认群：<群名 / id>」，与 dev 上 is_default 群一致。

## 簇 21 — persona-wizard-onboarding-fixes 真机验收（建号人设向导反馈修复，登记于 2026-07-09）

**前置**：cloud 部署含 master `8160d0e`（ui.snapshot 下发 personaBound + handler 输入校验）；edge 本地重建含 `b37f491`（三态 onboarding + 垂类/兴趣自由文本 + 删互动组）。逻辑单测已锁（AC-PROTO-10 两仓 + 两仓全量绿），此处验真机端到端。

- [ ] **已绑老号显示已设置跳过向导** — 一个此前已绑人设的账号在客户端选环境、启动、扫码登录、连云后：设置抽屉「账号人设」区徽标显示「已设置」、向导体隐藏、不再要求配置（修「已绑仍显示未设置」bug）。核 ui.snapshot 确带 `personaBound=true`。
- [ ] **未登录/未连云分态引导** — 选环境未启动/未登录时「生成人设」灰置且提示「请先点启动、扫码登录」；已登录未连云时提示「正在连接云端」（两态文案不同、非笼统灰置）。gate 判据未放宽（点了发不出仍不可点）。
- [ ] **确认后即折叠为已设置** — 新号生成→确认成功后，向导立即折叠为「已设置」（不等下次 hello；personaLocallyBound 生效）。
- [ ] **垂类自定义 + 兴趣自由文本进 seed_keywords** — 填自定义垂类（如「宠物」）+ 自由文本兴趣（逗号分隔）生成，产出的 soul 的 role/interests/seed_keywords 体现这些长尾输入、更具体有区分度。
- [ ] **删互动组后生成正常** — 界面无「互动偏好」四开关；生成/确认闭环正常。
- [ ] **输入超限诚实拒绝** — 自由文本堆超长/超量（>24 条 or 单项>40 字）时云端诚实回失败、不把超量文本喂 prompt。

## 簇 22 — env-switch-last-publish-reset 真机验收（切环境发布卡不串显旧账号，登记于 2026-07-09）

**前置**：edge 本地重建到 master `9c5991e`（含 `ui-state.cjs` 环境归属键 + `main.cjs` 三处接线）；至少两个 AdsPower 环境（一个有发布记录、一个从未发布）。
**背景**：「上次发布」历史态曾全局单文件持久化、不分账号，切环境重启核心时有意不清、且云端快照对无发布记录的账号宁缺毋假不发覆盖 → 切到没发过帖的账号后旧账号内容永久滞留。修复：历史态带环境归属键（`self` | `ads:<分身id>`）落盘，异键/缺键（旧版文件）不采纳，核心以不同环境启动时清出展示回落空态占位；云端快照仍是权威覆盖源、同环境重启行为不变。

- [ ] **切到无发布记录环境回空态（核心症状）** — 在 A 账号发过帖后，设置抽屉切到从未发布的 B 环境并「按新设置重启」：发布卡随核心启动回落「还没有发布过内容」空态，不再显示 A 的笔记标题 <!-- 2026-07-09 部分证据：14:35 升级首启切到 k1eg3se5（未登录、身份确立失败停手）窗口内卡为空态（经缺键不采纳路径）；envKey 异键清出展示路径（文件已带键后再切环境）尚未跑到，留验 -->
- [x] **切回有记录环境被快照回填** — 再切回 A 环境重启：hello 快照到位后发布卡回填 A 的「上次发布」（标题正确），`ui-state.json` 里 `envKey` 为 `ads:<A的分身id>` <!-- ✓ 2026-07-09 14:43 真机：切回 k1e0ero8（大白）连 dev 云，14:43:51 快照行 kind=lastPublish「首例AI Agent勒索攻击避坑指南」回填，14:44:29 ui-state.json 重写为 {envKey:"ads:k1e0ero8",…} -->
- [ ] **同环境重启历史态保留** — 不换环境、点「按新设置重启」或暂停/恢复：「上次发布」保留展示，与改动前行为一致
- [x] **升级路径一次性空态自愈** — 带旧版无 `envKey` 的 `ui-state.json` 升级后首启：发布卡先空态；启动核心、快照带回真实记录后自愈且新文件带键 <!-- ✓ 2026-07-09 14:35 真机：升级后首启读到 07-06 旧格式缺键文件未采纳（卡空态），14:43 快照回填后文件带 envKey 自愈 -->


## 簇 23 — textcard-carousel-form-parity 阶段0 影子真机验收（帖级形态档只判不渲，2026-07-09 部署 dev + 开 `AIDCP_POST_FORM_PROFILE`）

**前置**：dev 已部署 cloud `1b202d2` 且 `.env` 三旗标均 true（`AIDCP_COVER_FORM_SENSING` / `AIDCP_PUBLISH_TEXTCARD_COVER` / `AIDCP_POST_FORM_PROFILE`）；需真机发若干**带参照图**的洗稿帖（含纯文字卡源稿、卡封面+照片内页混合源、普通照片封面源各若干）。
**背景**：洗稿「文字卡」判定/渲染此前仅封面独占，纯文字卡源稿→只封面是卡、内页全 AI 图（帧内形态自相矛盾）。阶段0 影子只**判定 + 记录**帖级形态档（封面先行 + 内页有界并发判形 → `generative`/`card_cover`/`all_text_card`），**不改任何渲染**；据此攒 go/no-go 数据决定是否建阶段1（真整帖渲卡）。查 `publish_metadata->'coverFormAudit'` 的 `formProfile` / `formProfileGate` / `perImageForms`。**评审属 GATE §3.1**：达标（纯卡源稿够常见 + 内页判定够准）才进阶段1；否则本 change 作诚实信号收尾。

- [ ] **纯文字卡源稿归 all_text_card** — 洗一篇源图整帧全是排版文字卡的稿，查 `formProfile='all_text_card'`、`formProfileGate='all_text_card'`，`perImageForms` 每张 `form='text_card'`；此帖当前产物仍是「封面卡 + 内页 AI 图」（阶段0 不改渲染），确认形态档记录与产物不一致是**预期**（信号先行）
- [ ] **内页（非封面）判定准确率** — 抽 ≥5 篇 `formProfile` 非 generative 的帖，人工核对 `perImageForms` 各张 `form` 与真实源图形态是否吻合（该视觉模型此前只在封面上验证过，内页准确率是阶段1 前置未知项）；记录误判类型（如照片被误判 text_card / 反之）
- [ ] **混合源不误判全卡** — 洗一篇「文字卡封面 + 真实照片内页」的稿，查 `formProfile='card_cover'`、`formProfileGate` 为 `downgrade_inner_not_unanimous`（内页明确异形）或 `downgrade_unknown_or_error`（内页不确定），绝不 `all_text_card`
- [ ] **封面先行零额外成本** — 洗一篇普通照片封面稿，查 `formProfile='generative'`、`formProfileGate='generative_cover_not_card'`，且该帖**未对内页发起额外视觉调用**（对照 token 用量/日志，普通帖不多花）
- [ ] **零回归：既有封面文字卡链路不变** — 对照开影子旗标前后，同类源稿的 `coverForm`/`renderStatus`/封面产物一致（阶段0 只并列加 formProfile 字段、不改任何既有决策与渲染）
- [ ] **纯卡源稿频率统计** — 累计一段时间后统计 `formProfile='all_text_card'` 占带参照图洗稿帖的比例（GATE §3.1 决策依据：够常见才值得建阶段1 真渲染）

### 阶段1 真渲染（2026-07-09 部署 dev + 开 `AIDCP_PUBLISH_TEXTCARD_CAROUSEL`；用户令跳过影子灰度门直接真渲）

**前置**：dev 四旗标均 true（SENSING/TEXTCARD_COVER/POST_FORM_PROFILE/TEXTCARD_CAROUSEL）；cloud `09eef52`。核心诉求：纯文字卡源稿洗稿 → **产物真变化**（整篇每张都是文字卡，不再只封面是卡、内页 AI 图）。旗标秒回滚（删 `.env` 那行 + 重启）。
**背景**：阶段1 在 all_text_card 档一次多卡文案 → 每槽渲文字卡（cardSet）。卡面是**洗稿产物重排**、非源卡复刻（防搬运，能对齐形态非内容）。内页判定准确率未经真机验证是最大未知项。

- [ ] **纯卡源稿 → 整帖文字卡轮播（核心诉求）** — 洗一篇源图整帧全是文字卡的稿（如「把 AI 记忆从云端搬去本地教程」），产物**每一张**都是排版文字卡（查 `coverFormAudit.cardRenderStatuses` 全 `rendered`、`imageUrls` 每张为 `${seq}.png`），封面+内页形态一致
- [ ] **卡面内容合理 + 不搬运** — 人审轮播每张卡：文案通顺、覆盖正文主线、各卡不重复；与原稿无 ≥12 字逐字重叠（防搬运）；无联系方式/促销/作者名
- [ ] **轮播视觉连贯** — 各卡同色板版式族（账号种子）、同 1728×2304 尺寸（帧内一致），逐 seq 装饰有别不单调
- [ ] **内页判定误判的兜底** — 若某内页被误判非文字卡 → 该篇退 `card_cover`（卡封面+AI 内页），**不**在照片位捏卡、**不**假全卡；确认误判时产物仍诚实（配 backlog 阶段0「内页判定准确率」项一起核）
- [ ] **多卡文案失败兜底** — 若某张卡违规/LLM 失败 → 整帖回落生成式（`coverFormAudit.formProfileGate='carousel_copy_failed'`），绝不半套卡+半套图
- [ ] **零回归：非纯卡帖不受影响** — 普通照片封面帖仍全生成式、卡封面+照片混合帖仍 `card_cover`（单封面卡+AI 内页），与开轮播旗标前一致

## 簇 24 — edge-multi-environment-fleet 真机验收（一台客户端并行托管 N 个环境 + 舰队控制台，登记于 2026-07-09）

**前置**：edge 本地重建到 master `c6292d8`（含 `fleet.cjs` + `main.cjs` 多环境重写 + 环境栏/引导流 renderer + 配图临时目录按 edgeId 隔离 + `browser/active` 对账）；打新安装包（当前 `../aidcp-edge/dist-electron`，版本仍 0.2.7）；≥2 个已登录目标平台的 AdsPower 分身（内存足够 ~1GB/环境）。云端与 console 本 change **零改动**（edges 已按 edgeId 独立路由）。
**背景**：桌面端此前单账号（一个 `edgeProcess`、一个分身）。本 change 把外壳升级为「按环境 id 索引的一组受监督子进程」（每环境 = 一分身 = 一子进程 = 一云端连接，edgeId=`ads-<分身id>`），加舰队控制台（默认收起环境栏 + 状态色环 + 引导式登录/验证码流 + 主区域按选中环境路由既有陪伴视图）。桩层已锁大量逻辑（789 test，含多环境不串号 / 身份闸 / 错峰 / 内存预检 / 引导不误退休 / persona 不跨账号 / 串扫隔离 / decideRespawn+temp parity）；下列须真机核（多进程/内存/限频/窗口/孤儿桩验不了）。经两轮多 agent 对抗性评审修 14 项 + 3 加固，红线均验证 closes+noRegression。

- [ ] **2–4 环境并行内存实测（Phase 0.1 补）** — 花名册加 2–4 个分身、「全部启动」，实测每 headful 环境内存占用（校准 `fleet.cjs` `PER_ENV_BYTES_DEFAULT` ~1GB 估值）+ 本机余量；确认各环境两条独立 headful 窗口、云端各成一套隔离运行时（按 edgeId）
- [ ] **AdsPower 限频错峰实测（Phase 0.2 补）** — 「全部启动」时看外壳错峰队列是否把相邻 `browser/start` 拉开 ≥1.1s（日志/网络）、避开 AdsPower ~1req/s；单环境启动失败（如某分身未登录）不阻塞队列其余环境如实各自起
- [ ] **配图临时目录串扫不再发生（Phase 0.3 补真机）** — 两环境并行发帖，一环境写 `aidcp-img-<edgeId>-*` 在途、另一环境（重）启动清扫，确认只清自己命名空间、绝不误删兄弟在途上传（发布不半截）
- [ ] **双 headful 窗口人工登录/验证码引导流** — 两个需登录/验证码的环境点「引导处理」：一次引导一个（聚焦其窗口 → 人工完成 → 完成·重检 → 真恢复后自动前进下一个）；确认**绝不**在 relogin 重启瞬态误判已恢复而把未完成登录的环境永久踢出队列；新到待处理项实时并入
- [ ] **验证码阻断浮层浮顶为需处理（红线）** — 某在跑环境遇验证码/登录墙（核心本地暂停但 edge 仍 running），确认环境栏该行浮顶为「需人工处理」琥珀脉冲、计入待处理计数、进引导队列——绝不呈现为绿色在线（多环境跨窗盯验证码是控制台核心目的）；验证码处理后（核心发「阻断弹窗已清除/已消失，恢复浏览」）该态即时撤下
- [ ] **退出无孤儿** — 有环境在跑时关闭应用：确认外壳先对全部在跑环境有序 SIGTERM + 确认浏览器关闭再退出，不留孤儿 Chrome/AdsPower 进程（`ps` 核）；子进程非 detached 随外壳终止
- [ ] **重启对账无双拉** — 某分身在上次异常退出后仍被 AdsPower 标记运行中，重开外壳：确认经 `browser/active` 对账后接管/不重复 spawn 该分身（该行提示「已在运行，接管」），绝不造成同 edgeId 第二条连接被云端互踢
- [ ] **每环境失败诚实呈现不被掩盖** — N 环境某一个连续失败达重起上限：确认其行如实呈现「错误·已放弃重启」终态 + 系统通知 + 人工重试入口，其余健康环境不受牵连、整体呈现不因多数健康而掩盖这一个失败
- [ ] **同账号铺多环境告警** — 两个环境登录/解析到同一账号：确认外壳如实告警「同一账号、风控与配额会合并、发布只发最早那条」，引导改为不同账号；移出其一后告警随即撤下（不留幽灵需处理项）
- [ ] **切换环境陪伴视图整体切换不串号** — 多环境同时在跑各产活动/计数/发布，点选切换：确认标题带身份/活动流/计数/发布卡/限额窗全部切为选中环境投影，绝不残留或混入别环境数据；开发者原始日志亦按环境隔离
- [ ] **持久 UI 态按环境隔离** — 各环境「上次发布」等历史态按 envId 分桶落 `ui-state.json`（`byEnv`），切环境不串显旧账号内容（与簇 22 env-switch-last-publish 同族，此处验多环境并存形态）
- [ ] **安装包冒烟** — 新安装包在运营机装（先清单实例锁/旧版本）：单实例锁文案已改「一台机一个监督者、其下并行托管 N 个环境」；空花名册引导加入；旧单值 `adsProfileId` 设置向后兼容加载为单元素花名册（升级不丢配置）
- [ ] **左栏环境管理 UI（edge master `2f68469` `edge-fleet-rail-env-management`）** — 环境管理已搬进左栏（对齐 v2.3 设计稿），真机视觉 + 交互核：① 左栏「＋ 添加环境」拉起独立浮层，「加入现有环境」多选 AdsPower 环境、加入即出现在左栏离线行（根治旧「点了显示已加入但左栏看不到」）；「新建环境」建指纹环境亦即时入栏；② 每行昵称后人设图标（未设置淡描边/已设置品牌色），点击选中该环境并弹独立人设浮层做人设（envId 路由 persist，绝不跨账号）；③ 设置抽屉已精简为「浏览器引擎（AdsPower API Key/地址收进其高级折叠）+ 窗口停放 + 开发者开关」；④ 左栏分组（需处理/运行中/暂停·离线）+ 汇总 chip + 待处理徽标视觉与设计稿一致。桩层 791 test 锁结构/逻辑，视觉与真实 AdsPower 列举/建号需真机核。

## 簇 25 — persona-badge-preconnect-neutral 真机验收（人设徽标未连云中立态，登记于 2026-07-09）

**前置**：edge 本地重建含 master `e4f8bfa`（纯 edge 渲染层，cloud/协议不动）。多环境模型下 status 已 per-handle（`personaBound` 每环境 init false）。

- [ ] **未启动/未连云显示「待启动」** — 设置页选 / 切换环境但未启动（或未登录/未连云）时，「账号人设」徽标显示中立「待启动」而非「未设置」；hint 提示「连上云端后会显示该账号是否已设置人设」。
- [ ] **连云后翻正确态** — 启动扫码登录连云后：已绑账号 hello 带 `personaBound=true`→徽标「已设置」跳过向导；未绑→「未设置」+ 启用向导。
- [ ] **切环境不残留旧态** — 从已绑环境 A 切到未绑环境 B（多环境并存 / 换 handle）：B 不因 A 的已绑态误显示「已设置」（per-handle status + resetPersonaDraft 双保险）。
- [ ] **确认后即已设置** — 新号生成→确认成功后，当前环境徽标立即「已设置」（personaLocallyBound，不等下次 hello）；切到别的环境不带走该态。
- [ ] **同环境重启不残留 stale 已绑** — 某环境曾已绑、后台解绑、重启该环境：startEdge 清 `handle.status.personaBound`→连云后据真实（无 personaBound）显示「未设置」，不残留「已设置」。

## 簇 26 — generalize-contact-info 真机验收（群聊引流码→联系方式泛化，登记于 2026-07-09；代码已 land 三仓 master、**尚未部署 dev**）

**前置**：cloud `2f0ef2a` + console `49d4203` 部署 dev（**含手动跑 `migrations/0036`**：物理列/表改名 group_chat_info→contact_info、group_comment_*→contact_comment_*）；edge `7699be8`（wire 键未改、旧 edge 兼容，非阻塞）。wire 采 Method A（`groupChatCode` 保留）。

- [ ] **迁移保数据** — 跑 0036 后，既有账号后台「联系方式」列仍显示原值（列/表改名不丢数据）；`accounts.contact_info` 有数据、无空 `group_chat_info` 僵尸列。
- [ ] **命令 `--contact` 真发** — 飞书 `/comment <昵称> --contact`：已配联系方式账号 → 人审卡展示「正文+联系方式」合并终稿、通过后边缘真发带联系方式的评论（verbatim、含 emoji/换行）。
- [ ] **旧写法不再识别** — `/comment <昵称> group:on`：`group:on` 被并入昵称、走「找不到账号」诚实失败，绝不静默注入。
- [ ] **缺配 fail-closed** — 对未配联系方式账号 `--contact` → 告警回执「未配置联系方式」、本次不发，不静默发无联系方式评论。
- [ ] **后台编辑回真态** — 后台「联系方式」列就地编辑保存 → 走 `/api/accounts/:id/contact-info`、回读真态（verbatim）；旧路由 `/group-chat-info` 过渡期仍受理。
- [ ] **自动带联系方式评论 + 一码一号放松** — 内容排期开「自动带联系方式评论」：无联系方式 → `no_contact_info` 硬拒；联系方式与他号共用 → 放行 + `sharedContactInfoWarning` 风险提示（**放松未被本 change 回退**）。

## 簇 27 — parallel-rewrite-drafts 真机验收（同账号并行洗稿+多草稿挑选发布，登记于 2026-07-09；cloud e292493..7c3d1a2 + console f5999e0 已部署 dev）

- [ ] 27.1 同账号并行洗两篇不同精选笔记：两轮同时生成（console 发布队列卡按轮列出、Segmented 可切换查看每轮详情、账号显昵称——07-09 用户反馈跟进 console 75677ec 已部署 dev）、各落各的待审草稿、各发各的审批卡；同一篇笔记双击触发第二次同步拒 `duplicate_source`
- [ ] 27.2 挑选发布端到端：批一驳一→批的真发、驳的落 needs_review；批准后台账（llm_token_usage）按账号各归各账（含去 AI 味重写调用）
- [ ] 27.3 下发韧性：批准时恰逢边缘离线→草稿退回待审+飞书「请重批」通知实收；同账号连续 2 次下发失败→熔断告警实收、第三份授权保留不烧；重新批准任一草稿→熔断解除通知+恢复下发
- [ ] 27.4 容量帽：同账号在途待审达 3 → 洗稿触发回 `publish_capacity` 中文提示；全局并发 2 轮时第三轮回「生成并发已满」
- [ ] 27.5 排期口径：有洗稿候选在途时排期发帖不被堵（日上限只数自主）；账号自主轮在跑时排期顺延

**已知缺口（design.md D8，如实登记不修）**：① 同窗批准多张=背靠背连发（每篇 1-3 分钟）**无间隔节流**（用户 2026-07-09 定案本期不做）——运营请错峰批准控节奏，后续按需补间隔机制；② 重启时在途下发是 at-least-once 重复发帖窗口（既存）；③ 风控 `record('publish')` 死数字、封号/限流信号驱动状态迁移缺失（全系统既存）；④ 跨账号草稿同质（素材层无账号隔离，仅自主路径）；⑤ 陪伴端单槽只显示最新一份待审（协议不动的已知降级）；⑥ 飞书僵尸卡随并行数放大（误发已被版本闸+status 闸拦住）。

## 簇 28 — feed-hot-lead-auto-group-comment 真机验收 + fast-follow（浏览热帖自动联系评论,登记于 2026-07-09）

**已实装+dev部署（cloud origin/master `1bb0406`）**：浏览闭环命中热帖 + 账号 `contactCommentEnabled` + 过共用评论安全闸（`canDo('comment')` 时/日 + 单场评论预算 + 子上限 `contactCommentDailyCap`）→ `triggerTargeted(injectContact)` → 飞书人审=发；helper 触发 ok 显式 `record('comment')` 消费共用配额 + 记 `contact_comment_attempts`（含审计列）。默认关＝零回归。1678 云端测试过。**未归档时的 fast-follow 已随 change 移出、留此跟踪。**

### 真机验收（灰度启用后）
- [x] **灰度启用 → 端到端真发成功** — ✅ 2026-07-09 真机：测试号配联系方式 + 开关 + cap 后，刷到热帖 → 触发 → 飞书审批卡 → 点通过 → **联系评论真发出成功**。核心链路（发现→过闸→触发→人审→发）端到端跑通。
- [ ] **共用配额真消费**：发一条联系评论后，该账号 `canDo('comment')` 余额 -1（与普通评论同池）+ `contact_comment_attempts` 当日 +1（source='hot_lead' + note_id 快照）。
- [ ] **子上限真拦**：cap=N，触发 N 次后第 N+1 次命中被 `countContactAttemptsToday>=cap` 拦、不发。
- [ ] **零回归**：账号不开 `contactCommentEnabled` → 命中仅日志、不发。
- [ ] **缺联系方式 fail-closed**：开了但未配联系方式 → 不发。
- [ ] **note_not_found 率**：triggerTargeted 按标题重搜定位可能在最热帖上落空——盯该路径落空率（若显著，follow-up 让触发吃「已打开 noteId」跳过重搜）。
- [ ] **短时去重**：人审拒/超时后重刷同一 note，45min 窗口内不重复推审。

### Fast-follow（本 change 未做，另案实装）
- [ ] **排期评论/排期群评纳入统一账本**：让现有排期路径也经同一 helper `record('comment')` 消费共用配额（改线上现行为，单独灰度）。当前只有浏览路径记账；排期路径维持原样（过 canDo 但不 record）。
- [ ] **审批卡标注**：「本账号今日 x/cap（排期+浏览合计）+ 风控态 + 本联系方式被 N 账号共用」——供人审对频率与跨账号同码集中把关（用户定：只按账号上限 + 卡面标注）。
- [ ] **发出前复检**：post 步骤前再查一次 `canDo + 子上限`，闭「检测→人审延迟→发出时已超」的 TOCTOU。
