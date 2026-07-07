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
