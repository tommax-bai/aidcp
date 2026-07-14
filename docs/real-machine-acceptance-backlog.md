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

> **2026-07-11 清账批**（第二次 openspec 分诊清账）：本批归档 **31 个** landed+deployed change，真机验收项按既有簇归并——发布链路 → 簇 3（`publish-select-mode-layout-robust` 5.3）、textcard → 簇 23（`textcard-carousel-form-parity` 6.3）、FB 加群评论 → 簇 32（新增 `facebook-group-join-observe-i18n` / `fb-group-join-wait-render` 两项 i18n + 就绪修复复核，见簇 32 补登）、`/comment` 搜索闭环 → 簇 34/55（`comment-search-command` 12.1，多次已跑通）、FB 评论人审 → 簇 48（`facebook-comment-review-and-targeted-join`）、**FB 公开组放量 → 新簇 59**（`facebook-group-join-and-commenting` 9.1-9.5）。归档后全库 `openspec validate --specs --all --strict` 106 项全绿。**本批刻意未归档（5 个仍活跃，另有门槛）**：① `publish-trigger-and-apply`（§11 统一部署待核）；② `edge-environment-platform-select`（tasks 3.3 明确 gate 在 FB edge driver `facebook-browser-env-and-login` 落 master，当前仅 probes 落地）；③ `humanize-interaction-prompts`（代码已部署 dev，但 tasks 9.4 spec 交织须待 `category-adaptive-images-and-judgment` 先归档）；④ `estimate-token-cost-column` + ⑤ `manual-billing-price-refresh`（代码已 shipped，但 `llm-token-usage-stats` spec delta 应用失败——前者用英文 header MODIFY 中文「console 提供…」需求、后者 MODIFY 一个无人创建的 `Token Usage Cost Estimates` 需求；两者对 cost/billing 需求建模不一致，须 owner 理顺 delta header / 重建模型后再归档）。**已废弃删除（1 个）**：`facebook-scheduled-comment`（2026-07-11 用户决定关为 superseded）——其 target-URL 定向评论设计已被 keyword-in-container 版取代（见归档 `2026-07-09-facebook-scheduled-comment` + `facebook-group-join-and-commenting`）；34/35 核心任务空，change 目录已 `git rm` 删除（内容存 git 历史）。**注**：唯一落地的 task 2.9（云端在握手时持久化 FB 昵称）代码仍在线；其需求已由后续小 change `facebook-nickname-handshake-persist`（2026-07-11 归档）正式补登进 `facebook-identity` capability——剔除了已被 `facebook-nickname-inplace-read`（簇 42）取代的 `/me` 探针描述、按现网「就地读取 → hello 附带 → 云端仅库内空时写、既有不覆盖」校订。至此该行为「代码在线 + 主 spec 有据」齐全。另 `category-adaptive-images-and-judgment`（高风险图产后校验待选视觉模型）、`self-contained-ads-runtime`（dev CLI 解析等代码活 + baked-key 决策）、及 4 个纯提案（`transcribe-textcard-image-text` / `facebook-consent-structural-detect` / `facebook-join-actuation-decouple` / `edge-installer-oss-distribution`）本就在研、非本批对象。

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

## 簇 29 — edge-client-proxy-platform-persona-ux 真机验收（客户端代理配置 + FB 平台识别/上色 + 人设闸修复 + 人设浮层重设计，登记于 2026-07-09；edge master `9f5e0b8` 已 land，edge-only 无 ECS 部署，运营机重建/pull 后生效）

**判据交接**：人设徽标四态语义（待启动/未设置/待确认/已设置）与向导折叠行为未变，簇 17/21 的这部分判据仍有效；但旧「hint 一行文案」判据被空态面板取代、草稿 YAML 收进折叠——涉及 UI 文案/布局的旧判据以本簇为准。

- [ ] **人设闸修复（问题 4/5 根因）** — AdsPower 环境启动→浏览器内登录→核心打出「账号身份已确立」→连云后：人设浮层徽标数秒内离开「待启动」（已绑显「已设置」、未绑显「未设置」），生成按钮自然可点（不再永久灰）；停止该环境后徽标诚实回「待启动」。
- [ ] **代理 update 真机语义** — 对已有环境「代理」编辑保存：① 环境**已打开**时 AdsPower 是拒绝还是接受（当前 UI 按「下次启动生效」保守口径，按实测修文案）；② `user/list` 对 `proxy_port`/`proxy_user` 的回传完整度（决定编辑预填完整度，当前容忍空预填）；③ 密码留空保存带鉴权代理的实际行为（当前按「整体替换需重填」口径）。
- [ ] **新建带代理** — 创建表单选 socks5/http 填合法代理 → 建成后 AdsPower 侧该分身 `user_proxy_config` 为所填值、列表摘要如实显示；配真代理后浏览器出口 IP / 时区随代理（指纹 webrtc/时区 based-on-IP 自洽）。
- [ ] **FB 平台识别（问题 3）** — 手工在 AdsPower 建的 FB 环境（remark 无 plat、domain_name=facebook.com）：加入面板平台签显示「Facebook?」（推断标注）、rail 行头像 FB 蓝、选中后顶栏头像/徽标变蓝且健康浮层显示「Facebook 登录」；启动注入 `AIDCP_PLATFORM=facebook` 打开 facebook.com。误推断环境点「改平台」纠正后持久生效、刷新列表不被改回。
- [ ] **人设浮层重设计视觉项（问题 6）** — 560px 三段式浮层：未启动环境显空态面板+「去启动」；生成中出骨架、遮罩误点不关层；结果 identitySummary 为标题、YAML 在「查看完整人设定义」折叠内；确认后绿卡「已设置」。矮窗口下底部 CTA 始终可见（不沉折叠线下）。
- [ ] **rail 字形（问题 7/8）** — 添加按钮加号居中、收起/展开箭头尺寸合适且方向正确（收起时指右）。

## 簇 30 — 打包客户端启动浏览器修复（spawn ENOTDIR / cwd 落进 app.asar，登记于 2026-07-10；edge master `3f578b9`/`4c27e85`/`34d668e` 已 land，edge-only 无 ECS 部署，本机已打 0.3.6 dmg，运营机装新包后生效）

> 复发 bug：打包态核心子进程 spawn 的工作目录被设成 `app.getAppPath()`（asar 包内是 `app.asar` **文件**、非目录）→ macOS `spawn ENOTDIR` → 核心起不来、浏览器无法启动。本地 dev / typecheck / 单测全抓不到，只在打包版暴露。曾修于签名分支 `20d3784` 未合回 master、`0.3.5` 又发出。已在本机验证：ENOTDIR 复现 + `dirname` 守卫修复 + 两份 0.3.6 dmg 的 asar 内容确认含 `cwd: edgeCwd`（非 `cwd: appRoot`）；源码级回归断言（`test/electron/lifecycle-contract.test.ts`）+ 发版 smoke 步（`docs/release-desktop.md` §2C）已加。**下面为真机 live 项**（本机无法在不驱动真实自动化的前提下确认浏览器真弹出）。

- [ ] **装 0.3.6 后能启动浏览器** — 运营机装 `AIDCP-0.3.6-arm64.dmg`（或 Intel `AIDCP-0.3.6.dmg`）覆盖 0.3.5，点「启动」：核心子进程正常起来（**不再** `spawn ENOTDIR`）、走到「正在启动指纹浏览器」并真的弹出浏览器、连上云端开始浏览。
- [ ] **app.log spawn 行 cwd 正确** — `~/Library/Application Support/aidcp-edge/logs/app.log`（或对应 userData）里 `[edge-process] spawning … cwd=` 应为 `.../Contents/Resources`，**绝不**再是 `.../Contents/Resources/app.asar`。
- [ ] **多环境并行启动均正常** — 环境栏加入多个环境并行启动，每个环境的核心子进程都成功拉起（不因某一 spawn 失败拖累其它）。

## 簇 31 — edge 人设弹窗时机 + 主屏停放 + 环境头像三态（登记于 2026-07-10；edge master `90bcb14` 已 land，edge-only 无 ECS 部署，运营机重建/pull 后生效）

> 桩测覆盖了逻辑（宽限抑制/到点弹、停放 bounds、三态切换含 attention 环境与键盘豁免），但真机层要看：窗口是否真按主屏可见位停放、头像点击是否真把浏览器抬到前台、已设置账号是否真的不再被弹。

- [ ] **已设置账号不再被误弹** — 已绑人设的账号启动+登录+连云：客户端**不**自动弹人设浮层、**不**发系统通知、小红书页顶**不**出现「账号人设尚未设置」横幅（此前刚连云的空窗会误弹一下）。
- [ ] **未设置账号仍会被引导** — 真未绑人设的账号：登录+连云约 6s 宽限后，仍自动弹人设浮层 + 发一次通知 + 页顶横幅；手动点 ✦ 图标随时可开。
- [ ] **主屏停放真生效（单显示器）** — 默认「主屏停放」下启动环境：浏览器窗口停在主屏可见处（不再像旧「边缘/完全移出」那样被系统拽回、看着没停好）、保持渲染、不抢焦点。
- [ ] **头像三态（单显示器）** — 点环境头像①选中（红高亮明显）②再点浏览器抬到主屏前台并聚焦③再点归位到背景位；浏览器未就绪时点击诚实提示、不推进相位。
- [ ] **验证码环境三态可用** — 出验证码浮层（attention，核心仍在跑）的环境仍保留「已显示」红态、第三次点击能归位（不是又一次抬前）。
- [ ] **多环境/多屏** — 多个环境并行时主屏停放的层叠可接受（靠头像逐个抬前访问）；有第二显示器时「副屏停放」仍把窗口放副屏、无副屏时降级到主屏停放且不报错。

## 簇 32 — facebook-manual-join-comment 真机验收（`/comment --join` 加群+评论 + 后台自动加群真开，登记于 2026-07-10；cloud master `1037fe4` 已部署 dev + `AIDCP_FB_GROUP_JOIN_AUTO=true` 已开）

> `/comment <昵称> --join [--contact]`：先复用云端加群调度器加入**一个新群**（观察→判定 fail-closed→点加入→服务器确认→写账本），确认加入后在该新群里发一条评论。`--join --contact` 走飞书人审的联系评论。本次同时把后台自动加群循环真开（`AIDCP_FB_GROUP_JOIN_AUTO=true`，shadow 关）。前置：目标群已导入目录、FB 账号在线且配了评论关键词、在管理群下命令。**下面为真机 live 项**（本机/单测无法确认真实浏览器加群+评论）。

- [ ] **`/comment <昵称> --join`** — 管理群下命令：该 FB 账号真加入一个新目标群，加入成功后在群内发一条自动情境评论（服务器确认上墙），飞书回「加群 + 评论成功」绿卡；结果卡显群名或中性占位、**绝不显裸群 id/URL**。
- [ ] **`/comment <昵称> --join --contact`** — 加群 + 联系评论走飞书人审：正文先过无人值守硬校验，审批通过后才带「联系方式」提交；账号未配联系方式 → 加群前 fail-closed 黄卡、不加群不评论。
- [ ] **诚实非成功卡** — 审批制群（gated_skip，判定门→不点、无悬挂请求）/ 待审（pending）/ 无可加群（no_targets）/ 加群未开（disabled）/ 边端离线 → 均**不评论** + 说清原因的卡；加了群但评论未发（含评论阶段异常）→「已加群，但未评论」黄卡（部分成功绝不染绿）。
- [ ] **后台自动加群循环** — `AIDCP_FB_GROUP_JOIN_AUTO=true` + `AIDCP_CONTENT_SCHEDULE_AUTO=true`：在线 FB 账号按排期错峰 + 风控日/时/分配额 + 单场会话额度自主加入目标群（先导入 2000–5000 目标群、账号在线、排期活跃时段）；加群判定角色准确率符合预期（沿簇 group-join 判据）。
- [ ] **跨调度器不抢边端** — 手动 `/comment --join` 进行中，后台自动加群/评论不对同账号并发触发（ContentScheduler 见 isCommentBusy/isJoinBusy 即本 tick 跳过）；反之亦然。
- [ ] **回滚开关** — `AIDCP_FB_GROUP_JOIN_AUTO=false` 重启后：后台自动加群立停，手动 `/comment --join` 随之诚实回「自动加群功能未开启」（不真加群）。

> **补登（2026-07-11 清账批）**：两处加群健壮性修复随本批归档，须在同一 `/comment --join` 真机 session 一并复核——① `facebook-group-join-observe-i18n`（edge `a6f0f3f`：Join 按钮跨语言识别，靠「composer 点前无→点后有」结构跃迁承重，修「非成员被误判 + observe 期误 markJoined 污染账本」）；② `fb-group-join-wait-render`（edge `a6f0f3f`：群页 ~7s 才渲染加入按钮，改就绪轮询等决定性信号或 12s 兜底，治「死等 2.5s 看空页 fail-closed 空跳」）。**验收点**：非 EN/ZH 群 `/comment <昵称> --join` 能越过 observation 真点 Join（服务器确认）或给诚实 gated/pending，不再 `ambiguous_skip`。

> **补登（2026-07-12）**：`facebook-join-pending-label-audit` 修中文已 pending 群按钮「取消请求」漏识别。edge `c06fa2c`（需运营机 pull master + 重建安装包后生效）把「取消请求 / 取消加入请求 / 取消申请 / 已发送请求」纳入 pending CTA，cloud `19b83b4` 已部署 dev（备份 `cloud.bak.20260712-152112`、healthcheck 全绿：active/8787/8090/PG/Feishu onReady）同步判官 pre/post-click 兜底。**验收点**：中文界面、账号已申请待审的群（真机证据群 `groups/311384382278852` 或同类 pending 群）观测腿报 `pendingRequest=true`、云端 pre-click 判 `gated_skip`，不再误报未申请/可加入；页面普通裸「取消」按钮不触发 pending。

## 簇 33 — feed-refresh-on-depth 真机验收（feed 浏览深度到阈值改点右下「刷新」回顶换新批，登记于 2026-07-10；cloud master `c4545f0` 已 land + **已部署 dev**、edge master `60088d7` 已 land，edge 需运营机 pull/重建后生效）

> 探针 `aidcp-edge/scripts/feed-refresh-button-probe.ts` 已真机确认按钮结构（右下 `div.floating-btn-sets` 内 `div.reload`，宽窄同构）与行为（点 reload = 回顶 + 换全新一批，前 6 卡 0 重叠）。下面为 live 端到端 + 阈值校准项。默认阈值 60 张、默认开启（env `AIDCP_FEED_REFRESH_AFTER` / `AIDCP_FEED_REFRESH` 可调 / kill-switch）。

- [x] **端到端真机触发** — ✅ 2026-07-10 已现场证（tom 工程师大白连 dev，临时阈值 8）：一场会话内 `feed.refresh` 触发**两次**，每次云端 `sendCommand action=refresh` → 边缘 `[browse] 命令: feed.refresh` → `refresh 成功：回顶 + 换出全新一批` → 云端 `action.completed: refresh ok=true` → 立即上报全新一批卡片（两次的新批内容互不相同，证明换新批 + 计数复位后周期性重复）。change 已 archive。
- [ ] **阈值可达性校准** — 观测并记录「每会话实际浏览的不重复 feed 卡数」，据此确认 60 是否合适（对抗评审提示 10min/60 动作会话下 200 常达不到，故默认降到 60）；必要时 env 调整。可临时把阈值调小（如 `AIDCP_FEED_REFRESH_AFTER=8`）在一场内快速验证触发链，验完调回。
- [ ] **诚实失败不误判** — 构造非 feed 页 / 按钮未浮出 / 点后未换新批等，边缘如实回 `action.completed{refresh, ok:false}`（wrong_context / no_floating_btn / not_reloaded 等），云端失败兜底发一次恢复滚动、浏览闭环不死锁；**绝不**把纯回到顶部（内容未换）当刷新成功。
- [ ] **kill-switch 秒级回滚** — dev `.env` 设 `AIDCP_FEED_REFRESH=false` + `systemctl restart` 后，无论浏览多深都不再触发刷新、行为回退到本 change 前（一直向下滚）。
- [ ] **宽窄双布局** — 宽窗（侧栏）与窄窗（底部栏）各验一次刷新按钮定位与点击均命中（探针已证结构同构，真机复核点击链）。

## 簇 34 — comment-search-nav-confirm 真机验收（`/comment` 搜索未导航到结果页不再把 feed 当结果、失败诚实归因，登记于 2026-07-10；cloud master `8a35cbe` 已 land + **已部署 dev**、edge master `0274cf2` 已 land，edge 需运营机 pull/重建后生效）

**前置**：tom 分组 headful 真机（工程师大白 `k1e0ero8` / Tmax `k1e0awu5`），飞书 `/comment` 可触发。

> 事故根因（2026-07-10 dev 黑匣子）：`/comment` 搜索词「Claude Code实测」首次搜索小红书 AI 搜索框回车未提交、仍停在首页 feed，边端却把 feed 当搜索结果上报 → 云端选中无关的《GPT5.6上线》幻影候选 → 复检找不到 → `read_failed`，对运营误报「已选中，但开笔记/读正文失败（边端超时或离线）」（边端全程在线）。本 change：边端采卡前以**实时 URL** 确认到达搜索结果页，未到不采不报 + 发 `action.completed{search,ok:false,not_on_search_page}`；云端竞速消费该诚实回执 → 快速空候选 + 独立真实归因，read_failed 回执带真实原因。本 change **只保证失败诚实、不修 XHS AI 搜索提交本身的 flakiness**。

- [ ] **AI 搜索是否真跳结果页** — 真机跑 `/comment`，观察小红书 AI 搜索框回车 / 点提交按钮（`.bottom-box-right-submit-button`）后**是否真导航到 `search_result_ai`**；记录真实提交机制与结果页 URL 形态（`search_result_ai` vs 裸 `/search`），确认 `SEARCH_LIST_RE`（已放宽为 `/\/search(?:_result\w*)?(?:[/?#]|$)/`）覆盖真 URL。
- [ ] **未导航诚实回失败（核心）** — 构造 / 遇到「搜索没跳结果页仍在 feed」时：边端**不再上报 feed 卡**、发 `action.completed{search,ok:false,not_on_search_page}`；云端日志出现「搜索未导航到结果页（nav 未确认）→ 空候选」、**不再**出现幻影候选被选中、**不再**误报「边端超时或离线」；`/comment` 换下一个搜索词或诚实结束，不再干等 maxTerms×28s。
- [ ] **happy-path 不回归** — 搜索真跳到 `search_result_ai` 时，照常应用「最多收藏/一天内」筛选、正常采卡、择优、开笔记、评论（人审通过后真发）；确认诚实闸未误伤正常路径。
- [ ] **自治搜索不破** — 非命令的自治搜索（`search_evaluator`/`search.approved`）在 nav-fail 时也走同一诚实闸（不把 feed 当搜索结果），云端一次恢复滚动、浏览闭环不死锁、无幻影开笔记。
- [ ] **read_failed 回执文案** — 若仍发生 read_failed，飞书卡片显示**真实原因**（如「复检时目标已不在搜索结果中（页面重排/未导航到结果页）」），**绝不**再显示「（边端超时或离线）」。

## 簇 35 — captcha-assist-live-snapshot 真机验收（验证码远程协助改「近实时活体帧 + 选点期冻结」，登记于 2026-07-10；cloud master `210183a` 已 land + **已部署 dev（旗标默认关）**、console master `e63568c` 已 land + **已部署 dev**、edge master `e73dd3e` 已 land，edge 需运营机 pull/重建后生效）

**前置（关键）**：本功能 **env 旗标默认关**，零回归。真机验收前须在 dev ECS `.env` 设 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED=true`（可选 `AIDCP_CAPTCHA_ASSIST_LIVE_INTERVAL_MS` / `_MAX_DURATION_MS` / `_MAX_FRAMES` 调 hint）+ `systemctl restart aidcp-cloud.service`，并让运营机 edge pull/重建。范围仅**自刷新 / 多步换图的点选类**验证码；滑块/拖拽不在内。

> 设计经两轮多 agent 对抗评审，红队揪出并已修：① 云端 `submitClick` 陈旧守卫放宽为「最近 N 帧集」（否则边缘帧环死代码、白跑反增）；② 自主判清除须连续 K=3 次无遮罩确认才发 `risk.captcha_cleared`（防多步验证码瞬时无遮罩窗口误清 = 自残）；③ 内容去重 + 最小推帧间隔地板（防动画页去重失效成本爆炸）；④ 实时窗口绑运营在场（console 轮询 re-arm）；⑤ 迟到帧不复活已清除态。

- [ ] **活体帧更新** — 开旗标后真机触发一次点选类验证码：处理页出现「实时」标；验证码画面自刷新 / 一点换新题时，处理页在约 1s 内看到新帧（内容变才推、不变静默），非陈旧快照。
- [ ] **选点期冻结** — 放下第 1 个点后，后台来新帧**不冲掉已选点、不换显示画面**；提交发的是被冻结那帧的 `snapshotId`（云端按近期集放行、边缘按该帧 crop 落点），落点不错位。
- [ ] **换题提示不静默** — 冻结中挑战真换新题（新 snapshotId）→ 处理页出「画面已更新，挑战可能已变」提示 + 「看最新画面」可解冻重选；**绝不**静默让运营在旧题上点。
- [ ] **自主不误清除（风控红线）** — 多步验证码旧挑战消失、新挑战未绘出的瞬时无遮罩窗口下，实时循环**不**提前发 `risk.captcha_cleared`、账号**不**被提前解 `restricted`（须连续 K 次确认）；只有真实清除才恢复。
- [ ] **成本有界** — 带倒计时/动画的验证码页下，推帧速率受最小间隔地板约束、不全速推大图；CDP 无明显争用（不拖垮身份监测/看门狗/浏览会话）。
- [ ] **在场 re-arm** — 运营开着处理页时实时循环随轮询续期（窗口到期后下一次轮询重新武装）；关闭处理页后循环随窗口自终止、不留孤儿抓帧。
- [ ] **kill-switch 秒级回滚** — dev `.env` 设 `AIDCP_CAPTCHA_ASSIST_LIVE_ENABLED=false` + 重启后：capture 不再带 live、边缘回单次抓帧、处理页回今天行为（无「实时」标、无冻结/新帧提示），零回归。

## 簇 36 — pacing-fallback-hardening 真机验收（中途风控档位实时传播 + 停留兜底叠档位 + 清死通道，登记于 2026-07-10；cloud master `7381c3f` 已 land + **已部署 dev**、edge master `10f5f9b` 已 land，edge 需运营机 pull/重建后生效）

- [ ] **中途升档实时到边缘（latent，难触发）** — 「风控状态迁移接真实平台信号」尚未实装，状态平时恒 `normal`、tempo 恒 1.0，故 `pacing.update` 平时不触发。诱发法：真机用配额阈值（`quota_exceeded`）或验证码 / 风控浮层信号把某账号推到 `warned`/`restricted`，观察云端是否发出 `pacing.update`、边缘日志 `[browse] 应用中途档位刷新：tempo=…` 是否出现、其后动作最小间隔与详情页缺 `dwellMs` 的兜底停留是否随档位放慢。
- [ ] **停机窗口收档位不复活（自残红线）** — 会话 `session.end` 后、或独占任务（发布 / 评论 / 验证码恢复）窗口内恰有 `pacing.update` 到达时，确认边缘只更新 tempo、**不**重启浏览循环（无「唤醒重启」日志、无异常续场）。桩测已锁，真机顺带观察。
- [ ] **死通道移除无回归** — 确认 `session.budget` 回执仍正常（预算 + `viewOnly`）、welcome 快照兜底照常，无因移除 `session.budget.pacing` 引发的异常。

## 簇 37 — facebook-consent-overlay-auto-accept 真机验收（Facebook「允许 Cookie」同意浮层边缘拟人自动接受，登记于 2026-07-10；edge master `d8a83ca` 已 land，edge-only 无 ECS 部署，运营机重建/pull 后生效）

**前置**：edge 本地/运营机重建到 master `d8a83ca`；一个可用 Facebook 环境（AdsPower 指纹浏览器，已嵌入 FB 账号资料）；首次打开 `facebook.com`（或清 cookie 后）会弹「允许 Facebook 使用 Cookie」同意浮层。默认策略 `accept_all`（env `AIDCP_FB_COOKIE_CONSENT`，可切 `necessary_only`）。
**背景**：FB 评论/加群动作前都会跑浮层探针、浮层≠none 即中止；同意浮层此前无人识别——正文含「登录 Facebook」字样可能被误判成 login（误报「需要登录」中止，账号其实已登录），或判 none 而模态挡住点击（`no_target`），导致每次新环境/清 cookie 后 FB 评论/加群必然卡住。修复=专门探测器 + 动作前拟人自动接受 + 后置校验 + 有界重试 + 诚实回执，零改 4 类分类器（`overlay.test.ts` 零回归）。逻辑单测已锁（907 绿），此处验真机页面行为。

- [ ] **同意浮层被识别并自动接受** — 新环境首开 FB 触发同意浮层时，边缘拟人点掉「允许所有 Cookie」、浮层消失、页面可交互（后置复探判 clear）
- [ ] **含「登录 Facebook」字样不误判 login** — 同意浮层正文的「…应用到你登录 Facebook 的任何地方」不再让动作被误报 `login_required`/`blocked_by_login`（账号实际已登录）
- [ ] **接受后 FB 评论/加群不再卡** — 同意浮层清掉后，`/comment` 定向评论、`--join` 加群的整链路继续跑通、不再首屏卡死
- [ ] **真验证码/登录门不被误点** — 真 `/checkpoint`、验证码浮层、真登录门（无 cookie 接受按钮）仍走既有 fail-closed（`blocked_by_captcha` / 远程协助 / `login_required`），绝不被同意自动接受误点穿
- [ ] **按钮漂移诚实失败** — Facebook 改文案/布局致接受按钮定位失败时，回报 `no_target`/`blocked_by_consent`、不乱点其他按钮、不假成功
- [ ] **accept_all 生效 + necessary_only 可切** — 默认接受全部 cookie；设 `AIDCP_FB_COOKIE_CONSENT=necessary_only` 时改点「仅允许必要 Cookie」
- [ ] **cookie 持久化一次性** — 接受后写入 AdsPower 持久 profile，同环境后续会话不再反复弹同意浮层

## 簇 38 — browser-permission-prompt-defaults 真机验收（指纹浏览器权限弹窗抑制 + Electron 客户端通知恢复，登记于 2026-07-10；edge master `381bc4a` 已 land，edge-only 无 ECS 部署，运营机重建/pull 后生效）

**前置**：edge 本地/运营机重建到 master `381bc4a`；一个可用 AdsPower 指纹浏览器环境（`tom` 分组，`k1e0ero8`=大白 / `k1e0awu5`=Tmax），首开小红书时以往会弹「是否允许通知」权限浮层。
**背景**：客户端有两个浏览器——Electron 操作界面窗口 + AdsPower 起的指纹浏览器（真正刷小红书）。此前唯一的权限拦截（`installPermissionPolicy`，为拦地理位置加）只装在 Electron 窗口，管不到独立进程的指纹浏览器 → 小红书的通知权限弹窗照弹；且那套策略顺带把 Electron 客户端自身通知也拦了。修复=指纹浏览器两条启动路径加 `--deny-permission-prompts` + attach/重连经 CDP `Browser.setPermission=denied` 兜底（覆盖复用实例）+ self 模式反检测 query 映射改忠实（default→prompt、denied 照实，防新破绽）+ Electron allowlist 放行 notifications。逻辑单测已锁（914 绿），此处验真机页面行为。

- [ ] **指纹浏览器不再弹通知权限浮层** — 新环境首开/刷小红书时不再出现「是否允许通知」弹窗（`--deny-permission-prompts` 生效；顺带确认 AdsPower 确实透传该 flag）
- [ ] **复用实例也被抑制** — 复用一个已在跑的 AdsPower profile（未拿到本次 flag）时，attach 后 CDP `Browser.setPermission=denied` 兜底仍把弹窗压住
- [ ] **地理位置/摄像头/麦克风弹窗一并消失** — 指纹浏览器不再弹这几类权限浮层（`--deny-permission-prompts` 覆盖全部权限类型）
- [ ] **Electron 客户端自身通知恢复** — 客户端的状态提醒（拦截提示/运营通知等）仍能正常弹出，未被 allowlist 误拦
- [ ] **反检测无新破绽（self 模式）** — self provider 下 `navigator.permissions.query({name:'notifications'}).state` 与 `Notification.permission` 一致（均为 denied），不再出现 query 报 prompt 而 Notification.permission 报 denied 的矛盾
- [ ] **浏览/互动闭环零回归** — 权限抑制不影响小红书正常浏览/点赞/评论/发布链路（弹窗消失≠页面功能受损）

## 簇 39 — pacing-tempo-follows-quota-level 真机验收（配额档接进节奏快慢，登记于 2026-07-10；cloud master `870be7b` 已 land + **已部署 dev**，纯云端、边缘无改）

- [ ] **保守账号又少又慢** — 后台管理台把某测试号配额档由「正常」改「保守」，观察其后：动作前停顿 / 详情页停留 / feed 翻页停留明显变慢（约 ×1.3），且边缘日志出现 `[browse] 应用中途档位刷新：tempo=1.3`（**当场生效、无需断连重连**——这条现在真可人为触发，非 latent）。
- [ ] **激进只多做不提速** — 配「激进」的号动作停顿与「正常」号一致（不提速到人类基线以下），只是互动配额更宽。
- [ ] **握手即带档** — 保守账号新会话握手时 welcome 快照 tempo 即为 1.3（不用等中途推送）。

## 簇 40 — captcha-assist-humanize-click 真机验收（验证码协助注入点击提到不低于日常拟人度，登记于 2026-07-10；edge master `1d73797` 已 land，edge-only 无 ECS 部署，运营机 pull/重建后生效）

> 现状：协助注入曾用 `{jitter:0, overshoot:false, moveDelayMs:6}`（比日常点击还机械）。本 change 改为连续光标（下点从上点真实落点起步）+ 恢复 overshoot/小幅 jitter + 逐帧 dt 抖动 + 落点前读图停顿 + 点间对数正态停顿，节奏按 edgeId 派生偏置防车队指纹。无协议/无旗标，纯 edge 执行细节。

- [ ] **注入拟人度肉眼观察** — 真机触发点选验证码人工协助，观察注入不再是快直线单击：有曲线移动、落点前有停顿、多点之间光标连续（不各自瞬移冒出）。
- [ ] **落点仍精准** — 小幅 jitter（±2px）不致脱靶；贴边目标必要时点中心；脱靶时诚实 reprobe 回 still_blocked 让运营重试（绝不静默假成功）。
- [ ] **是否降低复现/被拒** — 对比启用前后，验证码协助后二次触发风控 / 验证码复现是否下降（与簇 41 轨迹回放合并观察）。

## 簇 41 — captcha-assist-trajectory-replay 真机验收（采运营真实鼠标轨迹回放到原浏览器，登记于 2026-07-10；edge master `b8dccf7` 已 land、cloud `55de0a4` + console `685e3c1` 已部署 dev，edge 需运营机 pull/重建后生效）

**前置**：无 env 旗标——靠 edge pull 门控（旧 edge 忽略 trajectory 字段、走合成路径）。console 采集轨迹、cloud sanitize 后透传、edge 回放；无/无效/过短轨迹一律回落合成拟人路径（change captcha-assist-humanize-click），落点始终取 points 权威。

> 设计经对抗评审，红队 must-fix 已折入：① **每次 press 前补一帧 move 到权威落点**（消 mousedown 无前驱 move 的瞬移伪影，否则比合成更可检测）；② 缩时只裁剪长停顿不等比压缩（防超人速度）；③ clicks 长度/越界校验、非单调按样本下标建表；④ panel 三处透传 + 丢弃可观测；⑤ click_result 带 replayMode 供度量；⑥ 过短轨迹（<5 样本）console 不上送。

- [ ] **轨迹真被采集+回放** — 运营在处理页移动+点击后提交：飞书/日志或 click_result 显示 `replayMode:'trajectory'`（有足够移动时）；原浏览器回放呈现曲线移动而非合成路径。
- [ ] **落点权威不错位** — 无论轨迹样本如何，press 落在 points 权威坐标（按被点帧 crop 缩放）；press 前有补 move 到该点（无瞬移伪影）。
- [ ] **诚实回落** — 秒点无移动（<5 样本）/ 畸形轨迹时不上送或被 sanitize 丢弃，edge 走合成路径、`replayMode:'synthetic'`，日志可观测（绝不谎称用了轨迹）。
- [ ] **通过率/二次触发** — 按 `replayMode` 分组对比：真实轨迹回放相较合成路径是否提升人工协助通过率、降低协助后二次触发风控。
- [ ] **成本/时长有界** — 回放时长受样本上限(250)+单帧停顿裁剪(≤120ms)约束，不超 system_recovery 60s 租约；大轨迹被降级/丢弃。

## 簇 42 — facebook-nickname-inplace-read 真机验收（FB 昵称改就地 id 锚定读取、删 /me 跳转，登记于 2026-07-10；edge master `ae86cc9` 已 land，edge-only 无 ECS 部署，运营机重建/重跑 edge 后生效；云端"握手 hello 昵称仅库内为空时落库"已在 dev live）

- [ ] **昵称就地读到并落库** — 现有 FB 测试号（如 `61591701813509` / `100064789146508`，当前 dev `accounts.nickname` 为空）重建 edge 后启动：昵称从顶栏头像锚点 `aria-label`（`<昵称>的头像`）就地读到，经 hello 落 dev `accounts.nickname` 非空、控制台显示真名而非数字 id。
- [ ] **不再跳 /me / 不再卡超时** — 启动日志不再出现 `/me nickname probe`；无 `CDP 命令超时: Page.navigate`（取昵称路径）；FB 活标签页不被导航走。
- [ ] **不写垃圾名** — 昵称不再出现 `(4) Facebook` 等标签栏标题、也不再把关联主页名（如 `việc làm hà nam`）当本人昵称。
- [ ] **vanity 头像限制观察** — 采用 vanity 用户名头像链接（非 `profile.php?id=`/`/me`）的账号本轮仍可能就地读空（诚实留空、无回归）；若量大再扩 id 锚定判据。

## 簇 43 — manual-comment-bypass-quota 真机验收（手动 /comment 命令绕节奏/风控配额，登记于 2026-07-10；cloud master `cb0889a` 已 land + **已部署 dev**，纯云端、边缘无改；openspec change manual-comment-bypass-quota 于 main `f6100a8`）

- **背景**：飞书手动 `/comment <昵称> [--join]` 曾复用自动巡回的节奏/风控配额闸——操作员命令被「本场会话加群额度已用尽；未加群也未评论」挡下；加群成功后群内评论还会再撞评论配额/日上限。用户定案（2026-07-10）：手动命令 = 操作员全权，绕全部配额（会话加群额度 + 加群速率 + 评论速率 + 评论日上限）与硬风控状态（restricted/frozen）；自动排期路径不受影响、配额照旧；只守物理正确性闸（边端在线/单飞/无目标/无关键词/kill switch/影子/仅 FB）。
- **验收项**：
  1. 取一个加群会话额度已耗尽（或风控速率被拒）的真实 FB 账号，跑 `/comment <昵称> --join`：应真加入一个新群并在群内发一条评论，**不再**回「本场会话加群额度已用尽」；结果卡为「加群 + 评论成功」（评上=绿）或诚实黄卡（加了群没评上），绝不假绿。
  2. 该账号评论日上限已满时跑手动 `/comment`：应照发（不回 quota_denied / daily_cap）。
  3. 回归：自动排期评论 / 后台自动加群在同账号配额耗尽时**仍**被诚实挡下（quota_denied / session_budget），不因本 change 误放。
  4. 账本诚实：手动加群成功后仍消费一格会话加群额度（recordSessionJoin），不因绕闸而漏计。
- **回滚**：外科回滚 dev 上 3 文件 `.predeploy.20260710-214949.bak`（comment-scheduler / facebook-group-join-scheduler / server），或整包 `cloud.bak.20260710-214949.tar.gz`；restart 即回旧行为。

## 簇 44 — facebook-join-comment-resilience 真机验收（FB 加群/评论健壮性 P0+P1，登记于 2026-07-10）

**前置**：cloud 部署含 `09dc642`（judge 多语确认+词表对齐、markTransientRetry 分层退避、覆盖不即时驱逐、评论长度感知超时）；edge 运营机 pull master `0d3e39f`（多语确认/待审/问卷、not_ready/post_not_confirmed_slow、不盲 Esc）后才生效。用 tom 分组（大白 `k1e0ero8` / Tmax `k1e0awu5`）或 FB 测试账号。逻辑单测已全绿（edge 938 / cloud 1778），此处验真机页面行为。

- [ ] **非中英群加成功被正确识别** — 加入界面语言非中英（越南语/西语/泰语等）的公开组，加成功后按钮翻本地语「已加入/退出小组」→ 边缘判 `already_member`/joined、云端记 joined，**不再误报 join_failed**、不重复发起加入。
- [ ] **慢网长评论不重复发** — 慢网络下对一条帖发较长评论（>150 字），确认云端按长度放大提交步超时、等到真回执打去重标记，下一轮**不再对同帖发第二条**（平台无重复评论）。
- [ ] **覆盖 nav_error 不即时驱逐** — 已加入群覆盖评论阶段偶发一次导航失败，成员身份**仍 joined**（left_confirmations+1），需达 `AIDCP_FB_GROUP_LEFT_CONFIRMATIONS`（默认 3）次才降 `left`；一次抖动不永久丢群。
- [ ] **慢渲染不落永久失败** — 群页加载慢/网络抖时加群走 `not_ready`/短退避重试（分钟级），**不喂 LLM、不永久 failed、不消耗尝试上限**；网络恢复后能成功加入（audit `*:transient_retry` + `attempts` 不累积到 cap）。
- [ ] **待审/问卷浮层不被误关** — 点击加入后弹出的入群问卷/待审浮层（含词表未覆盖语种）不被边缘 Esc 关掉，诚实上报 `questionnaire_required`/`pending`。
- [ ] **裁判多语 instant_join 不误判** — 非中英群清晰「加入」按钮走确定性 instant_join（不问 LLM）；本地语「已加入」不被误判成 instant_join 空点。

> **说明**：本 change 归档时 P0-1 的「重发前重观察本人是否已评」幂等仲裁（治边端硬断线永无回执的残留场景）已 descope 到后续 change，不在本簇验收范围；本簇「慢网长评论不重复发」验的是已交付的长度感知超时。归档目录 `openspec/changes/archive/2026-07-10-facebook-join-comment-resilience`。

## 簇 45 — adspower-first-login-wait-gate 真机验收（新建环境扫码登录后卡住修复：核心内有界等登录门 + 诚实停手真退出，登记于 2026-07-10；edge master `a758fc7` 已 land，edge-only 无 ECS 部署，运营机重建/pull 后生效）

**前置**：edge 运营机 pull master `a758fc7` 后才生效（含等待门 + 真退出 + adspower 首读 allowNavigate=false）。用 tom 分组（大白 `k1e0ero8` / Tmax `k1e0awu5`）或新建一个全新未登录分身。逻辑单测已全绿（edge 952，新增 14 条 login-wait-gate）；此处验真机页面行为与两个已知风险。

- [ ] **新建环境首登不卡死** — 新建一个全新未登录分身、点启动，浏览器开出小红书未登录态；核心进入「请扫码登录」等待（不即刻停手），扫码登录后**无缝续上握手**、正常进浏览闭环。
- [ ] **慢速扫码可续** — 故意慢扫码（>20s，找手机/开 App/确认/跳转），确认仍在等待窗内、登录完成后能续握手（旧行为此时早已 halt 挂僵尸）。
- [ ] **始终不登录 → 诚实干净停止、不无限重起** — 启动后一直不登录，到 `AIDCP_ADSPOWER_LOGIN_WAIT_MS`（默认 5min，验收可设短如 30000）超时；确认核心**真退出**（无残留僵尸进程）、外壳标 stopped、「启动」可用、且**不无限重起**（不每 5min 空起一次浏览器）。
- [ ] **等待期暂停/关闭即时响应** — 等待登录期间点「暂停/关闭」，确认核心即时干净停止退出（非等满超时），且不被看护重起后再次进入等待。
- [ ] **已登录老号零回归（头号风险）** — 一个已登录的老号（尤其历史布局仅靠 navigate 兜底才读出 id 的）启动后，`allowNavigate=false` 就地即能读出稳定 id、秒级续握手，**不进等待、不空等到超时**。
- [ ] **登录落点 tab 一致性（头号风险）** — 扫码登录完成后落点 tab 若与 `attachToPage` 选中 tab 不一致，就地重读永远读不到、白等到超时且 UI 仍显示「在等」＝静默假成功；须验证登录后落点 tab 与附着 tab 一致（覆盖「同 tab 内重定向」与「登录落新 tab」），不一致则记录、需后续外科处置（换附着目标/诚实提示）。

> **说明**：edge-only、无 ECS 部署；`process.exit` 真退出破僵尸的「进程确实终止」由逻辑层 terminate action 断言 + 结构保证（`terminateNow` 用 `process.exit`），真机复核「不留僵尸 / 看护重起 / 启动可用」。同源姊妹僵尸 `main.ts:605-609`（身份重检刻意 stay-alive）经审计**保留原样**、不在本簇。openspec change 仍活跃，待本簇验收后归档。

## 簇 46 — edge-multi-instance-userdata-isolation 真机验收（同机并行两 GUI，登记于 2026-07-11）

**前置**：edge 本地重建到 master `cdb7115`（含 `AIDCP_USER_DATA_DIR` userData 隔离）；准备**两个不重叠**的 AdsPower 分身（tom 分组，如大白 `k1e0ero8` / Tmax `k1e0awu5`）。
**背景**：桌面客户端默认「一台机一个监督者」（单实例锁按 userData 分）。本 change 让第二个 GUI 设不同 `AIDCP_USER_DATA_DIR` 即整体隔离锁/设置名册/界面状态/日志/内置运行时落地；用户诉求=同机一 GUI 连 dev、一 GUI 连 ol、各操作不同账号。本地代码验证已过（`npm test` 964/0 + typecheck），此处验真机并存互不干扰。**红线**：同一分身绝不出现在两实例名册（否则两套操纵系上同一浏览器、连不同云还不报错、静默互扰）。

- [ ] **两 GUI 并存启动** — 实例甲设默认目录 + `AIDCP_CLOUD_URL=dev`，实例乙设 `AIDCP_USER_DATA_DIR=<独立目录>` + `AIDCP_CLOUD_URL=ol`；两者**均成功启动**，第二个**不被单实例锁弹「已在运行」退出**。
- [ ] **本机状态各自独立** — 两实例的设置/名册（settings.json）、界面状态（ui-state.json）、日志（logs/edge.log）落在各自 userData、互不覆盖。
- [ ] **分身不重叠、浏览器互不干扰** — 两实例各用不同分身，各自浏览器会话独立，无「同一窗口被两边驱动」；一边停浏览器不影响另一边。
- [ ] **错峰启动复用守护进程** — 先起甲、待本机 AdsPower 服务（50325，机器全局）稳定后再起乙；乙**复用**已在跑的守护进程、不抢杀（无守护进程 SIGKILL 战、无 launch 大面积「Too many request per second」）。
- [ ] **未设 `AIDCP_USER_DATA_DIR` 零回归** — 旧的单实例启动方式（不设该变量）行为逐字不变、用默认目录，现役 dev GUI 不受影响。

> **说明**：edge-only、无 ECS 部署；源码契约测试已锁「覆盖存在 / 受守卫 / 在单实例锁与任何 `getPath('userData')` 之前生效」三不变量（`test/electron/instance-userdata-isolation.test.ts`，964/0）。真机核并存互不干扰 + 错峰复用守护进程 + 零回归。生效需运营机重建 edge checkout 并 pull master `cdb7115`。

## 簇 47 — edge-env-name-live-sync 真机验收（客户端环境展示名保真于 AdsPower 实时名，登记于 2026-07-11；edge master `1d2620a` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

**前置**：edge 运营机 pull master `1d2620a` 后才生效（创建回执带回环境名 + 拉列表回填花名册名）。用 tom 分组分身或在客户端「创建环境」新建。全量单测已绿（edge 968 + acceptance 16 + typecheck 干净）；此处验真机左栏展示名与「添加环境」面板是否一致。
**背景**：修复前左侧环境列表用「加入那刻拍下、之后不更新」的花名册名，添加面板用实时 AdsPower `user/list` 名 → 新建环境（花名册被写空名）时左栏回落「环境 …末4位」/账号昵称、与面板显示的真名不一致。

- [ ] **新建环境即一致** — 在客户端「创建环境」建一个（非 FB，用模板），左侧列表对它显示的名字 = 「添加环境」面板对它显示的名字（即模板名），**不再是「环境 …末4位」占位**。
- [ ] **FB 单账号导入即一致** — FB 平台单账号导入建环境，自动选中后左栏显示的名字与面板一致（导入标签名）。
- [ ] **AdsPower 端改名后刷新同步** — 某已加入环境在 AdsPower 端改名，回客户端点「刷新」，左栏名字随即更新为新名、与面板一致。
- [ ] **登录后不被账号昵称顶掉** — 环境登录账号后，左栏仍显示 AdsPower 环境名（花名册名已有值时不回落到平台昵称）。
- [ ] **缺数据不误改（红线）** — 环境较多致列表被截断、或拉取失败/空列表时，在用环境的左栏名字**保持不变**、绝不被清空或改错。

> **说明**：edge-only、无 ECS 部署；源码契约测试已锁「创建带回真名入册 / 拉列表回填空名 / 截断不回填」（`renderer-smoke.test.ts` + `ads-create-flow.test.ts`，968/0）。生效需运营机重建 edge checkout 并 pull master `1d2620a`。落地经 session scratchpad 全新 origin clone（基线 `cdb7115`）验证后 push，未触碰本机被外部清空的 edge worktree 群。

## 簇 48 — facebook-comment-review-and-targeted-join 真机验收（FB 评论全量人审 + /comment --join=<url>，登记于 2026-07-11；cloud master `8062dd5` 已 land + 部署 dev）

**前置**：cloud 已部署 dev（`8062dd5`）。dev 上 `AIDCP_FB_COMMENT_AUTO` / `AIDCP_CONTENT_SCHEDULE_AUTO` / `AIDCP_FB_GROUP_JOIN_AUTO` 均已 `=true`；`AIDCP_FB_COMMENT_REVIEW_ALL` 缺省（=默认开）。用 FB 测试账号（tom 分组，如 `61591458584142` / env `k1ehveal`）。全量单测已绿（cloud 1797/0 + acceptance 47/0 + typecheck 干净）；此处验真机人审卡与指定群加入行为。
**背景**：改前 FB 不带联系方式的评论校验后**直发、无人审**；本 change 让**所有 FB 评论**（带/不带联系方式）默认走飞书人审（`AIDCP_FB_COMMENT_REVIEW_ALL`，可 env 关）。并给 `/comment --join` 加 URL 形式 `--join=<群链接>`：加入**指定群**（只归该账号，target `enabled=false` 不外泄）、已是成员则直接评论。**红线**：人审未过/未接线绝不裸发；`manualOverride` 只绕配额、不绕人审；`--join=<url>` 未接线/非法 URL 绝不回落「下一个库内群」、群被别账号占则诚实拒不冒充成员。

- [ ] **非联系评论出人审卡** — 触发一次不带联系方式的 FB 自动/手动评论：飞书出**人审卡**、卡文本=纯正文（无尾部换行/联系方式），**审批通过后才真发**、拒/超时则不发。
- [ ] **联系评论仍必审（零回归）** — `/comment <昵称> --contact`：人审卡文本=正文+换行+联系方式，通过后带联系方式真发。
- [ ] **逃生门可关** — 临时设 `AIDCP_FB_COMMENT_REVIEW_ALL=false` 重启：不带联系方式评论恢复「校验后直发、无人审」；验完改回缺省（默认开）。
- [ ] **`/comment <昵称> --join=<群链接>` 加入指定群再评论** — 传一个该账号未加入的公开群 URL：客户端**加入这个群**、加入成功后在**该群内**发一条评论（走人审）；结果卡显「加群 + 评论成功」。
- [ ] **已是成员快路** — 对一个该账号**已加入**的群 URL 再发 `--join=<url>`：**跳过加群**、直接在该群评论（无多余加群回合）。
- [ ] **诚实失败** — 非法 URL → 「群链接不是有效的 Facebook 群地址」黄卡不加不评；群已归属别的账号 → 「已归属其他账号」黄卡不冒充成员评论；`--join=<url>` 用在非 FB 账号 → 「仅支持 Facebook」诚实拒。

> **说明**：cloud-only、无协议/边端改动；源码契约测试已锁「人审全量默认开 + 未接线不裸发 + manualOverride 不绕人审 + shadow 不审不发」「`--join=<url>` 路由指定群 + 已成员快路 + 未接线不回落 + 群 UNIQUE 归属诚实」（`comment-scheduler.test.ts` / `facebook-group-join-scheduler.test.ts` / `feishu-commands.test.ts`，1797/0）。生效即用（cloud dev 已部署）；真机核人审卡文本与指定群加入判定准确率。

## 簇 49 — facebook-locale-pin-en-us 真机验收（FB 互动号界面语言钉死 en-US，登记于 2026-07-11；edge master `af83f38` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

**前置**：edge 运营机 pull master `af83f38` + 重建安装包后才生效（新建的 FB 环境指纹语言才带 en-US）。用 tom 分组分身。全量单测已绿（edge 973 + acceptance 16 + typecheck 干净）+ 对抗评审 0 确认缺陷。此处验真机「界面英文 + 内容不塌 + 无检测破绽」。
**背景**：FB 按钮/状态识别本质按可见文字关键词匹配，界面语言随代理 IP 漂（中国代理号显中文 UI）→ 跨国家/跨语言群组时词表漏判 fail-closed 跳过。本 change 在建号源头把界面 chrome 语言钉成 en-US（指纹 `language_switch:'0'`+`language:['en-US']` + 启动 `--lang=en-US` + 导入 cookie `locale=en_US`），与内容语言解耦。登出态已探针实证界面渲染英文（2026-07-11 chrome_149）；登录态与内容侧待真机核。**红线**：内容（帖文/群名/人名）语言绝不塌、只塌界面 chrome；不触发指纹一致性拒建。

- [ ] **新号登录态界面英文** — 新建一个 FB 互动号（指纹带 en-US），登录后 Join / Pending / Joined / Write a comment / 菜单等界面 chrome **全英文**（非随 IP 的中文）。
- [ ] **浏览非英文群内容不塌（红线）** — 用该英文界面账号浏览/加入一个越南语（或任一非英文）群：**界面按钮/系统文案英文**，而帖文正文 / 群名 / 评论内容 / 作者人名**仍为原语言**、未被翻译或塌为英文。
- [ ] **Intl/ICU locale seam 一致（防语言伪造破绽，评审 finding #1）** — 在该环境页面控制台核 `navigator.language` === `Intl.DateTimeFormat().resolvedOptions().locale`（并 NumberFormat/Collator）；预期两者一致为 en-US（`--lang=en-US` 同步驱动 ICU 默认 locale）。若 navigator=en-US 但 Intl.resolvedOptions 随时区/IP 漂成他值 = 经典语言伪造 tell，需补 `--accept-lang` 或 ICU 参数。
- [ ] **指纹一致性不被拒建 + 非红旗** — 建号未因语言 pin 触发四者一致断言拒建（`language` 不在断言集，码级已证）；「英文界面 + 本地时区（Asia/Shanghai）+ 本地 IP」为可接受真实用户形态、非一眼假。
- [ ] **存量号归一 runbook（task 3.2，设置页导航路径待真机核）** — 存量登录号指纹语言经受限写客户端**改不动**（结构性两键，码级已证），唯一路 = 一次性登入 FB → 账号设置改语言为 **English (US)** → 跨代理/会话验证界面稳定英文。**真实设置页导航路径待真机核实**（Settings & privacy → Language，具体层级/入口跨版本可能漂）；核出后补入本条与运维手册。启动参数 `--lang` / cookie `locale` **只兜登出 chrome、改不了登录态群面**，勿据此判存量号已归一。
- [ ] **登录态英文串对表（补 button-probe 缺口）** — 登出态探针够不着的关键业务串：登录态英文实测 Join / Pending / Joined / 评论框 label 与 edge 词表英文项一致；cookie 同意条需 GDPR 触发会话（EU 代理/首访）才弹、届时核 consent 正则（此项与 C3 consent 结构化重叠、可并轨核）。

> **说明**：edge-only、无 ECS 部署；源码契约测试已锁「指纹产物 language=[en-US]+language_switch 关闭+时区仍随 IP」「language 不进四者一致断言、pin 不拒建」「launch_args 含 --lang=en-US」「cookie 缺 locale 注入 en_US / 已有不覆盖」「存量号 user/update 硬塞 fingerprint_config 进不了 body」（`ads-fingerprint.test.ts` / `browser-provider.test.ts` / `facebook-account-import.test.ts` / `ads-write-api.test.ts`，973/0）。对抗评审 6 raw findings 全被证伪（Intl seam=探针覆盖缺口非码缺陷已收本簇；fleet 语言熵下降=设计目标；stealth zh-CN 回退=empty-guard 惰性不触发；结构化 cookie 豁免=设计 belt）。C1 necessary-not-sufficient，语言无关 bug 归后续 C2（加群动作解耦+结构后置校验）/C3（同意浮层结构化）。

## 簇 50 — edge-cloud-env-selector 真机验收（客户端设置内切换云端环境 dev/ol/自定义，登记于 2026-07-11；edge master `4e69690` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

**前置**：edge 运营机 pull master `4e69690` + 重建安装包后生效。用 tom 分组分身。全量单测已绿（edge 980 + acceptance 16 + typecheck 干净）。此处验真机「界面选云端 + 重启生效 + 当前云端显示与实际一致 + ol 确认 + 并行两 GUI 各自独立」。
**背景**：改前客户端连哪个云端只能靠启动环境变量 `AIDCP_CLOUD_URL`，界面无入口、顶部只显示「连没连上」不显示「连的哪个云」。本 change 在设置抽屉加「云端环境」卡（dev/ol/自定义），界面选择优先解析（合并之后覆盖继承的 `AIDCP_CLOUD_URL`，留空零回归），标题带常驻「当前云端」chip。**红线**：显示的云端=核心实际连接的云端，已切未重启显示「待重启生效」、绝不显示成已生效；切 ol 需确认。

- [ ] **界面选 dev/ol 生效** — 设置里「云端环境」选 dev，点「全部重启并连接新云端」，环境重启后连的是 dev 云端（8787，dev IP）；再切 ol、确认、重启，连的是 ol。用 `logs/edge.log` 或云端在线列表核实际连的是哪个。
- [ ] **自定义地址** — 选「自定义」填一个 `ws://` 地址，保存后重启，核心连该地址；填非 `ws(s)://` 的串 → 诚实回错、不保存、不注入垃圾。
- [ ] **当前云端显示与实际一致（红线）** — 切换云端但**先不重启**：标题带 chip + 抽屉「当前连接」显示「<在跑的旧云> · 待重启生效」，**不**显示成已切到新云；点「全部重启」后 chip 变新云、pending 消失。
- [ ] **ol 二次确认** — 界面把云端切到 ol 时弹确认「将连接线上生产云端」；取消则保持原选择不变；chip/徽标对 ol 有醒目标注。
- [ ] **留空零回归** — 不在界面选任何云端（cloudEnvKey 空），以 `AIDCP_CLOUD_URL=<某地址>` 启动：核心连该继承地址，行为与本 change 前逐字一致。
- [ ] **并行两 GUI 各自独立** — 配合 `edge-multi-instance-isolation`：两个 GUI 各设不同 `AIDCP_USER_DATA_DIR`，各自在界面选不同云端（甲 dev、乙 ol），两者的云端选择互不影响（各自 settings.json）。

> **说明**：edge-only、无 ECS 部署；源码契约测试已锁「映射两地址 / 受 fromSelection 守卫的覆盖 / **覆盖在 env 合并之后** / 留空零注入 / custom 非法降级 / snapshot 带 cloudEnv / restart-all IPC」（`test/electron/cloud-env-selector.test.ts`，980/0）。生效需运营机 pull master `4e69690` + 重建安装包。与 `edge-multi-instance-isolation`（簇 46）正交互补：多实例并行仍靠两 GUI + 独立数据目录，本 change 省去手敲 `AIDCP_CLOUD_URL`。

## 簇 51 — facebook-coverage-relax-and-keyword-space 真机验收（覆盖模式全局开关 + 放开时限兜底 + 搜索词保留空格，登记于 2026-07-11；cloud master `7655b00` + console master `6704e99` 已部署 dev）

**前置**：覆盖模式现由**全局开关** `AIDCP_FB_GROUP_COVERAGE_ALL` 门控——**dev 上已 = true（所有 FB 账号都走加入群覆盖评论，2026-07-11 用户令开）**，不再需要 per-account 白名单。dev 现状 4 个 FB 账号里只有 `61591753702668` 有加入群（6 个）+ 1 关键词、会真跑覆盖评论；其余账号无加入群/无关键词 → 诚实 no-op。核放开时限兜底那几组，需让该账号的加入群全部落在冷却/预热窗内（或临时调低 `AIDCP_FB_GROUP_COVERAGE_WARMUP_HOURS`/`_COOLDOWN_HOURS` 造窗）。搜索词第 2 组与覆盖模式无关、任何 FB 账号可核。用 tom 分组分身。全量单测已绿（cloud 1802 + acceptance 47 + typecheck；console 91 + typecheck）。
**背景**：① 覆盖模式选群原本要求加入群满 24h 预热 + 距上次评论满 72h 冷却，全落空则这轮不评（账号闲置）。既然 FB 评论现已一律走飞书人审，本 change 把时限从「硬跳过」降级为「无合规群时放开时限兜底选一个（最久没评优先）+ 审核卡标注」，由人把关；`AIDCP_FB_GROUP_COVERAGE_RELAX=false` 可退回严格。② 管理后台搜索词输入原本按空格把「手冲 咖啡」切成两个词（AntD tags tokenSeparators 含空格），本 change 去掉空格分隔、多词短语算一个搜索词（后端本就保留内部空格）。**红线**：放开时限只放开单群时限、不放开账号日上限、不绕人审；relaxed pick 是真实、诚实标注、经人审的评论，绝不静默假成功；账号零加入群仍诚实 no-op。

- [ ] **全局开关生效——所有账号走覆盖（红线）** — `AIDCP_FB_GROUP_COVERAGE_ALL=true` 下，有加入群 + 有关键词的账号（如 `61591753702668`）的排期评论走「加入群」而非配置容器；无需把账号加进 `AIDCP_FB_GROUP_COVERAGE_ACCOUNTS`。设回 `=false`（或删）后恢复：仅白名单账号走覆盖、其余回落配置容器。核审计/回执里容器确为加入群 URL。
- [ ] **放开时限兜底触发 + 审核卡标注（红线）** — 覆盖账号的所有加入群都在冷却/预热窗内时，排期评论仍选出一个「最久没评」的加入群，飞书审核卡标题带「⚠️ 未满足冷却/预热期，已放开时限选群，请人工确认」；人点通过后正常真发、人点不发则不发。核卡标题文案 + 选中的群确为最久没评的那个。
- [ ] **正常约束优先（非 relaxed 不标注）** — 存在至少一个满足 24h 预热 + 72h 冷却的加入群时，走正常选群、审核卡标题**不带**放开时限警示（零回归）。
- [ ] **日上限仍生效** — relaxed 兜底下账号当日已达 FB 评论日上限（默认 2）→ 不再发（quota_denied），放开时限绝不抬高账号日发量。
- [ ] **kill switch 退回严格** — 设 `AIDCP_FB_GROUP_COVERAGE_RELAX=false` 后，所有加入群都在窗内 → 这轮诚实 no_targets、不评（恢复本 change 前行为）。
- [ ] **零加入群仍诚实 no-op** — 覆盖账号无任何 `status='joined'` 群 → 正常与 relaxed 两级都空、诚实 no-op，绝不伪造目标或盲发。
- [ ] **搜索词保留内部空格（console→edge 端到端）** — 管理后台「FB配置」关键词框输入「手冲 咖啡」回车 → 存为**一个**关键词（不被切成「手冲」「咖啡」两个）；保存后云端 `account_facebook_comment_config.keywords` 该项含空格；FB 评论时边缘按该整串（含空格）站内搜索、非拆词。逗号仍分隔多个关键词。

> **说明**：cloud（覆盖选群 + 审核卡标注）+ console（关键词输入）双仓、已部署 dev；无协议 / 边端 / DB schema 改动。源码契约测试已锁「coverageCandidates relaxed 去三时限闸留 status=joined+LRU 排序」「两级选群 + relaxed 标记」「审核卡标题按 relaxed 分支」「relaxed 仍受日上限」（cloud `facebook-group-store.test.ts` / `comment-scheduler.test.ts`，1802/0）与「关键词框 tokenSeparators 去空格」（console，91/0）。搜索词多词行为本身未做单测——AntD tags 的 CJK 分词在 jsdom 下靠 fireEvent 无法稳定复现，故转本簇真机核。覆盖白名单空时本 change 全程 latent。

## 簇 52 — edge-adspower-close-real-teardown 真机验收（客户端「暂停→关闭」真关指纹浏览器 + 诚实收尾，登记于 2026-07-11；edge master `0e569f4` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

**前置**：关闭按钮只在「已暂停」态出现，是关浏览器的唯一入口。用 tom 分组分身：启动一个 adspower 环境（指纹浏览器打开）→ 点暂停（浏览器应保持打开）→ 点关闭。edge-only、全量 987 + acceptance 16 + typecheck 已绿；生效需运营机 pull master `0e569f4` + 重建安装包。**背景**：旧关闭完全托付软性 `browser/stop` + 「查不动就当已关」的 confirmClosed（静默假成功红线）、无 OS 级实杀，故 `browser/stop` 没真杀内核时浏览器留着而界面报「已关闭」。本 change：关闭以**该分身 CDP 调试端点是否变暗**为权威判据（独立于 AdsPower 自报）、软停止未生效则升级（重发 + `AIDCP_ADS_CLOSE_OS_KILL` 默认开的 OS 级强杀）、无法确认如实报未关；外壳 no-child 分支经只读 local-active 实证后才判已关。

- [ ] **暂停→关闭真关（核心，红线）** — 启动 adspower 环境后暂停（浏览器仍开）再关闭：指纹浏览器窗口**真的关掉**，界面显示「浏览器已关闭」。反例（本 change 前）：窗口留着但界面报已关。
- [ ] **软停止失败态如实呈现** — 构造 `browser/stop` 不生效（如手动让 AdsPower 拒/无响应，或临时 `AIDCP_ADS_CLOSE_OS_KILL=false` 且软停止无效）：界面**不**假报「已关闭」，而是保持暂停 + 「关闭状态未能确认，可重试关闭」；浏览器仍开着与界面一致。
- [ ] **OS 级强杀兜底是否触达** — 软停止确实没杀掉内核时，`AIDCP_ADS_CLOSE_OS_KILL=true`（默认）下核心日志出现「OS 级强杀调试端口 <port> 监听进程 pid=…」且随后端点变暗、真关；`=false` 时退回「仅软停止 + 诚实未确认」。核 mac 上 `lsof -iTCP@127.0.0.1:<debug_port> -sTCP:LISTEN` 命中的确是该分身内核进程、不误伤他者。
- [ ] **no-child 分支不假关** — 若驻留核心在暂停与关闭之间已死（浏览器由 AdsPower 运行时托管仍在跑）：点关闭后界面**不**零回收直接报已关；经 local-active 实证仍在跑 → 报「浏览器仍在运行，请点恢复接管后再关闭」；点恢复能接管已开浏览器、再关闭走正常权威路径真关。
- [ ] **暂停期拆 CDP 后仍收敛（领先假设核实）** — 复现「暂停→关闭」路径，用 CDP 连本地浏览器 + 核心日志观察：确认暂停 `session.close→cdp.close` 后 `browser/stop` 是否空转（AdsPower 是否把该驻留分身判非活跃）；无论是否属实，本 change 的「重发 stop + 端点实证 + 升级实杀」应都能真关。若属实，评估是否值得后续把「会 detach 的 CDP 拆除」推迟到真关闭（改暂停时序，本 change 未做）。
- [ ] **退出期不留孤儿（时序）** — 关整个客户端（app quit）时，各环境浏览器随之关闭、不留孤儿；最坏（端口挂着一直超时）关闭确认仍落在 `gracefulStopAllAndQuit` 的 ~10s 有界等待内、不被截断致孤儿。

> **说明**：edge-only、无协议 / 云端 / DB 改动。修改 `src/cdp/browser-provider.ts`（权威端点实证 + K=2 连读闸 + 三阶段升级 + OS 级强杀）、`src/electron/main.cjs`（no-child 诚实收尾 + 防 start/resume 竞态）、`src/electron/ads-local-api.cjs`（`listWellFormed` 区分确认为空 vs 响应不完整）。源码契约测试已锁假成功分支（`test/cdp/browser-provider.test.ts` 23/0：端点变暗判关 / OS 杀升级 / 禁用诚实 false / stop 失败端点权威 / 不可达仍活 false / K=2 瞬态不误判 / 默认探测被拒判死）。OS 级强杀与「暂停拆 CDP」这两项桩验不了、须真机核（本簇 3、5 项）。多 agent 对抗评审 5 findings（探测无超时会挂过 10s 预算、单次瞬态误判、lsof 未限地址、no-child 竞态、不完整列表当已关）均已修。

## 簇 53 — facebook-comment-inplace-ack-verify 真机验收（FB 评论发布判定改就地 ack 门控 + 刷新有界轮询，登记于 2026-07-11；edge master `1e7e6d9` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

- [ ] 53.1 就地快确认：目标帖上本人发一条评论，服务器点头后（~3.5s）应**不刷新**即判成功（`serverConfirmed`），比旧「刷新+死等 5s」明显更快。
- [ ] 53.2 绝不 over-confirm：乐观阶段（回车后 <3s、只有客户端占位 `comment_id=client…`、无点赞/回复）绝不误判成功。
- [ ] 53.3 慢渲染不再假阴性：网络/渲染慢时评论已在服务器 → 刷新兜底有界轮询应命中判成功，而非旧的单次落空误报 `verification_ambiguous`（P2②）。
- [ ] 53.4 真失败仍诚实：评论确实被拒（无权限/被删）→ 两条路径都确认不了 → 诚实 `verification_ambiguous`（提交过、打去重、不重发）。
- [ ] 53.5 误导性报错浮层：出现「无权限添加此评论」等浮层但评论实际成功时（真机探针已实证会发生）→ 最终按确认信号判成功、不被浮层带成失败。

> **说明**：edge-only、无协议 / 云端 / console / DB 改动，只改 `src/facebook/comment-executor.ts` 提交后确认路径。判据源自真机探针 `scripts/fb-comment-verify-probe.ts`（本会话实测）：FB 评论回车后 ~68ms 乐观渲染带**客户端占位** `comment_id=client…`、0 个点赞/回复；服务器写入响应 ~3.5s 才到、之后 id 升级为**服务器正式**（base64 "comment:"）且点赞/回复才出现。故成功只认「本人+文本」评论行上服务器正式 id 或点赞/回复交互控件（皆 ack-gated），绝不认乐观渲染/占位 id。源码契约测试已锁就地命中不刷新 / 慢渲染有界轮询命中 / `isServerFacebookCommentId` 纯函数（990/0）；乐观占位 id 与点赞/回复计数的页内 JS 判别是 FakeCdp 桩测盲区、由真机探针坐实，本簇复核。生效需运营机 pull master `1e7e6d9` + 重建安装包。

## 簇 54 — edge-adspower-env-in-use-terminal-stop 真机验收（启动撞「分身被同账号在别处占用」判为不可重起终局：直接停 +「环境被占用」提示、不空转重起、不关别处浏览器，登记于 2026-07-11；edge master `7d7d758` 已 land，edge-only 无 ECS 部署，运营机 pull master + 重建安装包后生效）

**前置**：制造并发占用——用同一 AdsPower 账号在 A 处（另一台机 / 另一个 GUI 实例 / AdsPower 桌面端）打开某分身（tom 分组），再在本客户端选同一分身点「启动」。edge-only、全量 993 + acceptance 16 + typecheck 已绿；生效需运营机 pull master `7d7d758` + 重建安装包。**背景**：此前外壳把 `browser/start` 的 `code=-1 … is being used by … not allowed to open` 当普通崩溃喂进有界重起，空转 6 次（1 初始 + 5 重起、退避 1+2+4+8+16s、约 45–60s）后落到通用「本机引擎已停止」+ 生英文详情。本 change 把该拒启识别为不可重起终局：即刻停、不重起、换「环境被其它端占用…请先关闭后重试」提示；护栏 `AIDCP_EDGE_ENV_IN_USE_TERMINAL` 默认开可退回旧行为。

- [ ] 54.1 直接停不空转（核心，红线）— 选中已被同账号在别处打开的分身点启动：**不再**反复 6 次重发 browser/start、约 45–60s 空转；一次失败后即停，失败详情/健康详情/系统通知显示「环境被其它设备或窗口占用（AdsPower 账号 …）；请在占用它的一端关闭后再点『启动』重试」。核 edge.log 里 `browser/start … is being used` 只出现 1 次、无后续退避重起行。
- [ ] 54.2 不关别处浏览器（红线）— 本客户端这次失败启动**绝不**关闭 / 杀掉 A 处那个正在用的浏览器；A 处会话全程不受影响。
- [ ] 54.3 账号解析 — 提示里带出占用账号（从拒启 msg 的 `is being used by [<account>]` 解析）；解析不到时提示不带账号但仍成立。
- [ ] 54.4 护栏回退 — 设 `AIDCP_EDGE_ENV_IN_USE_TERMINAL=false` 后重来：退回旧的「按崩溃有界重起」行为（识别误伤时应急）。
- [ ] 54.5（待评估，非本 change）确认 AdsPower 同账号并发到底返 `code=-1` 拒启还是 `code=0` 复用既有端口。若存在 `code=0` 复用，核心会 attach 到别处那个浏览器、正常收尾会关掉它——那是另一条危险路径，需单独加「attach 前校验非外部实例」防护。本 change 只处理明确拒启的 `code=-1`。

> **说明**：edge-only、无协议 / 云端 / console / DB 改动，只改 `src/electron/fleet.cjs`（新增纯函数 `classifyAdsInUse`）+ `src/electron/main.cjs`（`handleEdgeLogLine` 置 `envInUseThisRun`、`child.on('close')` 据标志强制 `decision=stop` + 换友好文案 + 专门通知；护栏 env）。源码契约测试已锁 `classifyAdsInUse`（双闸识别拒启 + 解析账号 + 缺内核/连云失败/无关串/空 皆判否，993/0）；「命中即 stop 不重起 + 别处浏览器不被关」是 electron 外壳退出路径行为、桩验不了，由本簇真机坐实。生效需运营机 pull master `7d7d758` + 重建安装包。

## 簇 55 — comment-keep-open-through-approval 真机验收（按需评论 keep-open：搜到一篇合适笔记就攥住详情页贯穿人审、原地发布，不再为它复搜；根治 target_not_found_on_commit / read_failed，登记于 2026-07-11；cloud master `1fd65c9` 已 land + 部署 dev，edge master `4576a2a` 已 land、需运营机 pull + 重建生效）

**前置**：dev 对 Tmax（cloud accountId `66cd1d4f000000001d0314ee`，AdsPower env `ads-k1e0awu5`，tom 分组）跑排期自动评论（`ContentScheduler` 心跳命中）与手动 `/comment`。**背景**：原设计对同一搜索词做三次独立全量搜索（发现 / 读正文前复搜 / 发评论前复搜），每次骑在小红书 AI 搜索「提交→到结果页」这个不稳定入口上，成功率≈p³；自动路径送审时放掉浏览器→自治浏览闭环抢回把页面带走→commit 复搜必然找不回（2026-07-11 Tmax《AI自己改自己》已人审授权仍在 commit 复搜掉链、《GPT-5.6三档》prepare 复搜掉链）。本 change 改 keep-open：只搜一次，搜到合格候选后在同一持有租约内 pick→读正文→人审→原地发布，审批期不释放边端。

- [ ] 55.1 审批期浏览器停在详情页不漂走（核心）— 触发一次评论、飞书出审批卡后，观察边端（CDP 连本地浏览器看真 DOM 或 edge.log）：整个人审等待窗口浏览器**停在目标笔记详情页**，不被自治浏览带去别的笔记 / feed；`edge-task acquired kind=comment_prepare` 后到发布前**只有一次** `search.execute`（无 prepare / commit 复搜）。
- [ ] 55.2 通过后原地发成（核心）— 飞书点授权→评论在**当前详情页**原地发出，`[comment-edge] 发评论 … ok`，飞书终态卡绿；不再出现 `target_not_found_on_commit`。
- [ ] 55.3 超时 / 被拒诚实结束 — 人审超时（90s）或点拒绝→任务结束、释放浏览器、恢复自治浏览；回执诚实（compose_skipped），不复搜、不换词、不评他篇。
- [ ] 55.4 发现搜索不再被旧页假成功（Bug C 关）— 制造浏览器停在上一次某关键词结果页，再触发新词搜索：若提交没真导航，边端**不**把旧关键词结果页当本次成功（`未导航到结果页`）；日志 `搜索导航成功` 的 URL keyword 参数须与本次词一致才认。
- [ ] 55.5 发前就地核对（取舍2）— 人审期间若详情页被弹层顶掉 / 被导航离开（极端），发布前就地读 noteId 不符→诚实 `note_page_mismatch` 不发（keep-open 持锁已是主保护，此为二次闸；正常流程不应触发）。
- [ ] 55.6 空闲看门狗不误杀（观察）— 审批攥住浏览器停详情页最长约 90s，确认边端空闲看门狗（≈240s 阈值）不在持锁期误杀会话；若观察到误杀，需给人审期加轻 dwell（复用 `ensureDetailDwell`）。
- [ ] 55.7 回执区分来源 — 自动排期评论终态卡标「排期评论（自动）」、人工 `/comment` 标人工，可区分。

> **说明**：cloud `1fd65c9`（`comment-scheduler.ts` runTask 单持有租约 + `edge-steps.ts` 措辞 + `server.ts` 回执来源）已部署 dev（备份 `cloud.bak.20260711-155913`、healthcheck 全绿）；edge `4576a2a`（`browse-session.ts` 就地核对 + `search-handler.ts` nav 判据 / keyword 一致）需运营机 pull master + 重建安装包后生效。无协议消息类型改动。全量 cloud 1803 + edge 997 + 两端 acceptance + typecheck 已绿；「持锁贯穿人审浏览器不漂走」「原地发成」是 edge 运行时行为、桩验不了，由本簇真机坐实。真机测试账号只用 tom 分组（见 memory real-machine-test-accounts）。

## 簇 56 — facebook-join-structural-verify（L3）真机验收（加群成败补语言无关结构真值：承重=「跃迁」composer 点前无→点后有；消灭「本地语已加入→误判 join_failed→重复加群」，登记于 2026-07-11；edge master `1442783` 已 land、需运营机 pull + 重建生效，cloud master `6ce347e` 已 land + 部署 dev）

**前置**：dev 对 FB 互动号（tom 分组测试环境，见 memory real-machine-test-accounts / fb-integration-test-flow）跑加群——重点选**非英中语种群**（越南语 / 西语 / 日语 / 土耳其语等，Join/已加入按钮文案不在词表内）。**背景**：加群成败原靠多语词表判「已加入」，词表漏某语种→加成功但按钮翻本地语「已加入」未命中→边缘诚实但错误报 `join_failed`→云端重复加群（真机事故）。L3 给成败校验补语言无关结构真值。**对抗评审关键修正**：承重判据从「点后无可见 Join CTA」（`joinCtaPresent` 词表派生、未覆盖语种 fail-open→非成员误判 joined）改为**语言无关「跃迁」**（群主体可聚焦发帖/评论 composer 点前无、点后有），并**删除 observe/pre-click 结构判定**（无点击不 markJoined）。零协议改动。edge 全量 1000 + cloud 1807 + 两端 acceptance + typecheck 已绿；结构判定是真机 DOM 行为、桩验不了，由本簇坐实。

- [ ] 56.1 消灭重复加群（核心）— 对未覆盖语种群加群：加成功后按钮翻本地语「已加入」（词表未命中）时，靠 composer 跃迁判 `joined`（云端 `structural_join_transition`），**不再** `join_failed`→重复加群。核 cloud 审计 outcome=joined、边缘 ok=true clicked=true；同群不被重复加。
- [ ] 56.2 非成员不假成功（红线）— 对**未真加入**的群（审批门 / 点击没生效 / 公开组对非成员渲染 composer）：绝不误判 joined/already_member。尤其核「公开组点前已渲染发帖框」——点前已有 composer→无跃迁→诚实 `join_failed`（靠 LLM 层兜是否 joined，见 56.4），不据 fail-open 的 joinCtaPresent 假成功。
- [ ] 56.3 composer 子树判别精度（校准）— 用 CDP 连本地浏览器看真 DOM：确认「群主体内可聚焦发帖/评论 composer」选择器（`[role=main]` 内 `[contenteditable]`/`[role=textbox]`、排除顶栏/群内搜索框）在成员态命中、非成员态（登录墙/纯浏览）不命中；记录各版式群页真实 DOM 结构以细化选择器（源码注释已标「选择器精度留真机取证细化」）。
- [ ] 56.4 公开组点前 composer 靠 LLM 兜（观察）— 对「公开组对非成员也渲染 composer」的群，加成功后无跃迁→落云端 LLM（prompt 已喂 composerPresent/joinCtaPresent 信号 + 规则）：确认 LLM 能据结构信号正确判 joined，不误 failed→重复加群、也不误 joined 非成员。
- [ ] 56.5 渲染时序残留（观察，理论级）— pre 观测的 composer 在就绪帧读取（早于 preClickSettleMs），懒渲染 composer 可能造成 skew。评审论证 edge 侧不可达（点击需 join 按钮词表命中=覆盖语种，覆盖语种下非成员点后 join 按钮仍在→joinCtaPresent=true 挡住跃迁）。真机若观察到覆盖语种群出现「点前无 composer→点后有 composer 但实际没加入」的假 joined，需把 pre composer 读取移到 preClickSettleMs 之后同一帧。
- [ ] 56.6 pending/问卷先于结构（回归）— 审批门群：Join→Pending 即便渲染了 composer，判 pending 不判 joined。

> **说明**：edge `1442783`（`join-executor.ts` composerPresent/joinCtaPresent 观测 + `structuralJoinConfirmed` 跃迁 + 删 observe/pre-click 结构 + isDecisiveObservation）需运营机 pull master + 重建安装包后生效；cloud `6ce347e`（`facebook-group-join-judge.ts` 跃迁主判 + 删 pre-click 结构 + LLM 提示 / `facebook-group-join-scheduler.ts` 透传 pre 观测）已部署 dev（备份 `cloud.bak.20260711-162224`、外科 rsync 2 文件 md5 核对、healthcheck 全绿：active/8787/飞书长连）。两轮对抗评审：首轮揪出 fail-open false-positive（初版 `composerPresent && !joinCtaPresent` 未覆盖语种非成员误判 + observe 期无点击 markJoined 污染账本），已改跃迁 + 删 observe/pre-click 结构；二轮复验 gapClosed=true。真机测试账号只用 tom 分组。

## 簇 57 — edge-adspower-name-follows-nickname 真机验收（客户端左栏环境名跟随真实账号昵称：建号不写死模板名 + 登录后渐进改名 + 显示层优先昵称，登记于 2026-07-11；edge master `7b3cea4` 已 land、需运营机 pull + 重建生效，edge-only 无 ECS 部署）

**背景**：`edge-env-name-live-sync`（`1d2620a`）新增的 reconcileRosterNames 把左栏花名册名回填成 AdsPower live 名（= 客户端自建 profile 一直用的设备模板 key），而左栏取名优先级里花名册名排在真实登录昵称之前 → 昵称被模板名遮蔽（左栏全变 `win11-intel` 之类）。本 change 让 AdsPower 环境名本身跟随昵称（单一真源）+ 显示层兜底。edge-only、无协议 / 云端 / DB 改动。改 `ads-write-api.cjs`（新增 renameProfile 两键封装）、`ads-create-flow.cjs`（建号不下发模板名）、`main.cjs`（身份事件渐进改名 maybeRenameEnvToNickname）、`ui-logic.js`/`renderer.js`（显示优先昵称）。源码契约测试已锁两键改名 body / 建号空名不带模板名 / 显示优先级三态（全量 edge 1009 + acceptance 16 + typecheck 绿）。两项外部 AdsPower API 假设桩验不了、须真机核（本簇 57.1 / 57.2）。

- [ ] 57.1 AdsPower `user/update` 带 name 改名生效（核心外部假设）— 对 tom 分组一个环境，登录读出真实昵称后核 AdsPower 客户端里该环境名变昵称、下次 `user/list` 读回也为昵称；确认 `user/update` 的 name 字段确被 AdsPower 接受生效（保守假设字段名为 `name`，若不生效看本簇诚实降级是否兜住）。
- [ ] 57.2 建号不传 name 时 AdsPower 默认命名形态（核心外部假设）— 新建一个环境（不走 FB 导入），核 AdsPower 给它自动起的默认名形态（不再是 `win11-intel` 模板名）；确认左栏该环境登录前显示不呈现设备模板名（由末4位/默认名兜底）。
- [ ] 57.3 存量环境渐进改名到位 — 一批既有环境名仍是模板名，各自下次登录读出昵称后左栏 + AdsPower 名逐个变昵称；确认是渐进（随运营）而非一次性批量，且不依赖云端。
- [ ] 57.4 改名失败诚实降级不阻塞（红线）— 制造改名写失败（如临时断 AdsPower 服务 / 环境正被占用 `user/update` 被拒）：该环境保持原名、不假成功、浏览闭环不中断、不重试风暴；下次身份事件再试。
- [ ] 57.5 幂等去抖不重复写 — 名已等于昵称的环境反复触发身份事件，确认不再发 `user/update`（日志无重复改名）。
- [ ] 57.6 显示层兜底（空窗 + 写失败）— 刚建好未改名 / 改名写失败期间，左栏仍显示真实昵称（已读到时）而非模板名；实时名回填把花名册名刷成模板名也不遮蔽已知昵称。

> **说明**：edge `7b3cea4`（renameProfile 两键封装 + 建号不写死模板名 + 身份事件 `maybeRenameEnvToNickname` 渐进改名 + `railDisplayName` 纯函数优先真实昵称）需运营机 pull master + 重建安装包后生效；edge-only 无 ECS 部署。写客户端 M7 红线由「`user/update` 仅改代理」放宽为「改代理或改名两个各两键封装」，回归断言分别锁两个封装的 body 键集（放行 update ≠ 打开整张写面）。真机测试账号只用 tom 分组（见 memory real-machine-test-accounts）。

## 簇 58 — manual-comment-force-flag 真机验收（飞书 `/comment <昵称> --force` 放开「相关性 + 每笔记去重」两道软筛选：没强相关目标也评、已评过的也能再评；仅手动路径，仍守人审 / 内容安全校验 / 边端诚实闸，登记于 2026-07-11；cloud master `3177735` 已 land + **已部署 dev**，纯云端、边缘无改）

**背景**：手动 `/comment` 此前被两道软筛选挡下——小红书「人设强相关」甄选（一篇都不强相关就换词、用尽则本次不评）、Facebook「零重叠相关性」`weak_relevance`，外加两侧「每笔记/每帖去重」。运营刻意补评 / 没强相关目标也想发 / 想再评已评过的目标时无法表达意图。本 change 加尾部开关 `--force`（复用 `--contact`/`--join` 尾部解析，任意顺序可组合）：小红书无强相关时兜底选**收藏最高的一篇**、Facebook 传空关键词让 `weak_relevance` 分支 no-op、两侧放开去重（发布成功后仍照记）。**红线不动**：飞书人审、FB 内容安全校验（链接/联系方式/@提及/刷屏/长度）、边端诚实闸、账号隔离；`--force` 只从飞书手动入口置位，自动/排期/面板路径绝不带（零回归）。桩测已锁解析组合、XHS 兜底选 top-collect、XHS/FB 去重放开、FB 跳 `weak_relevance` 但 url 仍拦、人审在 force 下仍拦（全量 cloud 1824 + acceptance 47 + typecheck 绿）。以下须真机核（桩验不了平台真实发布 / 人审闭环）。真机测试账号只用 tom 分组（见 memory real-machine-test-accounts）。

- [ ] 58.1 XHS `--force` 无强相关兜底真发 — tom 分组小红书账号，选一个人设强相关笔记稀少的时段跑 `/comment <昵称> --force`：确认在「本轮无强相关候选」时兜底选**收藏最高的一篇**、开帖→撰写→飞书人审→批准后**真发**（而非回「本次不评」黄卡）；触发回执与结果卡标注 `--force`。
- [ ] 58.2 XHS `--force` 再评已评过的笔记 — 对该账号**已评论过**的一篇笔记（去重账本命中），`/comment <昵称> --force` 能再评一条（去重放开）；发布成功后仍记一笔去重（后续不带 force 的任务对其仍去重）。
- [ ] 58.3 FB `--force` 跳过 `weak_relevance` 真发 — tom 分组 FB 账号 `/comment <昵称> --force`：确认零重叠草稿也过相关性闸、经飞书人审后真发（对比不带 force 时零重叠被判 `weak_relevance`/compose_skipped）。
- [ ] 58.4 FB `--force` 内容安全校验仍拦（红线）— force 下若草稿含链接 / 联系方式 / @提及 / 刷屏短语，仍 `compose_skipped`（对应 reason）、绝不发；force 只放开相关性、不放开安全校验。
- [ ] 58.5 人审红线：`--force` 绝不绕人审 — XHS 与 FB 两侧，force 下在飞书审批卡**不点同意 / 超时**，确认不发、诚实回执（人是刹车）；force 只绕相关性/去重。
- [ ] 58.6 组合开关按预期 — `/comment <昵称> --force --contact`（放开相关性/去重 + 注入联系方式，联系评论仍走人审）、`/comment <昵称> --join --force`（FB 加群 + 群内评论 + 放开相关性/去重）任意顺序均生效、昵称解析正确。
- [ ] 58.7 零回归：不带 `--force` 的普通 `/comment` 行为不变 — 无强相关仍「本次不评」、已评过仍被去重挡下；自动排期 / 面板定向评论路径相关性 + 去重照旧（force 信号不出现在这些路径）。
- [ ] 58.8 透明标注 — 触发回执（XHS「已启动…--force：跳过强相关甄选与已评过去重」/ FB「…· --force（跳过相关性/去重）」）与加群评论合并卡的 `--force` 标注对运营可见。

> **说明**：cloud `3177735`（`comment-scheduler.ts` XHS `runTask` 兜底 top-collect + 放开两处去重、FB `runFacebookTargetedTaskBody` 取首候选 + 空 `targetKeywords`、`triggerManual`/`runFacebookTargetedTask(Body)`/`runFacebookJoinThenComment` 透传 `force`；`server.ts` `actions.comment` 与 `manualOverride` 分开传 `force`；`feishu/commands.ts` 尾部 `--force` 解析 + 透传 + HELP）已 land origin/master + 部署 dev（备份 `cloud.bak.20260711-175101.tar.gz` + `.env.bak`、外科 rsync src 3 文件、healthcheck 全绿：active/8787/飞书长连接/PG 就绪）。纯云端、无协议 / 边端 / DB 改动。`force` 与既有 `manualOverride`（只绕配额）独立：manualOverride 绕风控/配额闸、force 绕相关性/去重软筛选，二者语义不合并。openspec change 修订 `manual-command-override`（ADDED `--force` 覆盖 requirement）+ `comment-search-command`（MODIFIED 强相关择优 / 命令去重两条开例外）+ `facebook-scheduled-comment`（MODIFIED 硬校验器：force 跳 `weak_relevance` 但保安全校验）。

## 簇 59 — facebook-group-join-and-commenting Phase 0-4 放量 真机验收（公开组批量加入 + 按账号群评覆盖，登记于 2026-07-11；cloud master `0a0f1ae` + console `8e596f4` 已 land、部署 dev）

**前置**：≥1 在线 FB 账号、目标群目录已导入（2000–5000 目标）、管理群下命令；真机账号只用 tom 分组（见 memory `real-machine-test-accounts`）。

> FB 公开组闭环：批量导入目标 → 原子惰性认领（`ON CONFLICT (group_url) DO NOTHING`）→ 加群判定门 → 加入 → 服务器确认 → `facebook_group_membership` / `facebook_group_join_audit` 账本闭环；加入后按账号做情境群评覆盖，**两回路反同质化铁律**：自动情境评论禁带联系方式、联系评论必走飞书人审。风控加 `join_group` 配额（日/时/分三闸 + 单场会话额度）、判定角色 shadow 先行。整套按 Phase 0-4 灰度放量，只能真机分阶段验（对应 change tasks 9.1-9.5）。

- [ ] 59.1 Phase 0（无加群 / 评论）— dev 导入 2000–5000 目标群，核去重 + 原子惰性认领 + 加群限频配置在「安全」页正确呈现；无任何真实加群 / 评论动作。
- [ ] 59.2 Phase 1 shadow — 判定角色对数百真实目标跑影子，测「加群判定门」分类准确率（带分母的数字门）；达标才放 Phase 2。
- [ ] 59.3 Phase 2 单弃用账号（`join_group` 日上限 1–3）— 诚实回执→账本闭环，无假 ok、无悬挂 pending、判定学习集排除 fleet 自身。
- [ ] 59.4 Phase 3 单账号 — 自动情境覆盖（按账号门）+ 选定群的飞书人审联系评论回路。
- [ ] 59.5 Phase 4 fleet — 逐步抬 caps，观察分区均衡、共享预算钳制、跨账号抖动。

> **说明**：change tasks 9.5 明确要求把放量项登记本文件。代码全落地（cloud `0a0f1ae`：目标 / 成员 / 账本 store + 惰性认领 + 面板 API + `join_group` 风控三闸；console `8e596f4`：风控枚举镜像）+ 部署 dev。源 change 已归档，完整上下文见 `openspec/changes/archive/<date>-facebook-group-join-and-commenting/tasks.md` §9。

## 簇 60 — 桌面客户端 mac 签名+公证包（默认 ol 环境）真机验收（GitHub CI Developer ID 签名 + Apple notarytool 公证 + staple，装完默认连 ol；edge master `f41d94c` 已 land、CI 出包 0.3.18 已上架 dev 下载页，console master `0c8db0c`，登记于 2026-07-11）

**背景**：此前分发包不签名（`mac.identity=null`），用户下载安装被 macOS Gatekeeper 拦成「非法软件/无法验证开发者」。本次把签名分支（`codex/edge-macos-developer-id-signing`，基于 0.2.9、从未合回）的 Developer ID 签名 + notarytool 公证 + staple 基建移植到当前 master，并补齐**自包含运行时进 CI**（`build:ads-runtime` staging + 从 `ADS_RUNTIME_JSON_BASE64` secret 还原 gitignored 的 `resources/ads-runtime.json` baked key），出**签名+公证**包；构建期经 `-c.extraMetadata.aidcpCloudDefaultEnv=ol` 烘焙默认云端（装完无界面选择/无启动环境变量时默认连线上，界面可切；master 源码仍默认 dev、零回归）。本机已核（静态 + 干净 userData 启动）：`spctl --assess` = `accepted, source=Notarized Developer ID`、codesign 有效、dmg+app 均 staple、hardened runtime(flags=runtime) + 3 entitlements(allow-jit/allow-unsigned-executable-memory/disable-library-validation)、asar cwd 守卫、烘焙 `aidcpCloudDefaultEnv=ol` 落包、自包含运行时 42M + key 进包、干净 userData 下完整进程树启动 + 运行时工作目录 `ads-runtime/` 初始化。以下须真机核（桩验/本机静态验不了的运行时闭环 + 真实下载体验）。真机测试账号只用 tom 分组（见 memory `real-machine-test-accounts`）。

- [ ] 60.1 真实下载安装不被 Gatekeeper 拦（核心诉求）— 从后台下载页（dev `:8088` `/downloads/AIDCP-0.3.18-arm64.dmg`）在一台**干净 Mac**（带 com.apple.quarantine）下载 → 双击 dmg → 拖入 Applications → 首次启动：确认全程无「非法软件/无法验证开发者/已损坏」拦截、正常打开。Apple 芯片（arm64）+ Intel（x64）各核一台。本机 `spctl` 已判 accepted，但真实下载-开封是终极证明。
- [ ] 60.2 装完默认连 ol（烘焙生效 + 显示=实连红线）— 全新安装（无 in-app 选择、无 `AIDCP_CLOUD_URL`）：配好 AdsPower 环境点启动后，核心实连 `ws://123.56.253.183:8787`（ol），界面「当前云端」显示 ol、与实连一致（**绝不得显 ol 实连 dev**——烘焙缺省以 fromSelection:true 显式下发 spawnEnv 正为治此）；界面切 dev/custom 后能改连。
- [ ] 60.3 hardened runtime 下能真起指纹浏览器（未测组合，重点）— 签名 + hardened-runtime 的 app spawn 核心（ELECTRON_RUN_AS_NODE，签名 Electron 自身）+ 拉起内置 `adspower-browser` CLI + SunBrowser 内核：确认浏览器真弹出、能登录跑浏览闭环，不被 hardened runtime / Gatekeeper 拦下嵌套未签名可执行文件（entitlements 已带三项，但本机静态验不了真实内核启动这一层）。
- [ ] 60.4 旧 userData 陈旧单实例锁不卡启动（既有隐患，观察）— 本次冒烟发现：用旧 `aidcp-edge` userData（含早前会话残留 SingletonCookie/Socket）启动新包会**卡在主进程早期 JS**（无子进程、无 window、0 CPU），换干净 userData（`AIDCP_USER_DATA_DIR` 指新目录）即完整启动。这是既有行为、非本次引入、非签名问题，但**运营机原地升级时旧 userData 仍在**→可能复现。真机核：从旧版升级到 0.3.18 后首次启动是否卡；若卡，考虑启动早期清陈旧 singleton（SingletonLock/Socket/Cookie）或诊断具体阻塞点。
- [ ] 60.5 CI 复跑与产物交付稳定 — 再触发 `gh workflow run build-desktop.yml --ref master -f cloud_default_env=ol`：确认签名+公证稳定过；dmg 经 GitHub prerelease `desktop-v<版本>` 交付（Actions **产物存储配额 6-12h 滞后重算、删旧产物短期不解封**，故改走 release 存储——独立不受该配额限，见工作流 `Publish dmgs to GitHub prerelease` 步）；`Upload macOS artifacts` 为 best-effort（continue-on-error）。复核 asar cwd 红线两 arch + 烘焙 ol + 运行时进包。

> **说明**：edge `f41d94c`（`.github/workflows/build-desktop.yml` 签名 job + cloud_default_env/include_windows 输入 + 运行时 key 还原步 + release 交付；`scripts/build-desktop-macos.sh` 补 `build:ads-runtime` + 缺 key 硬失败 + 烘焙注入 + CI 专属 `forceCodeSigning`；`scripts/notarize-and-staple.sh`；`build/entitlements.mac.*.plist` 纳管；`package.json` build.mac 签名配置 + 版本 0.3.18；`stage-ads-runtime.mjs` 剥离绝对/逃逸符号链接；`main.cjs` 烘焙缺省环境读取 + 显式下发）需运营机 pull master + 重建/或直接下载页取 0.3.18 安装包生效。CI 实测踩三坑均已修：① codesign `--deep --strict` 拒 `node_modules/.bin/*` 绝对符号链接（stage 剥离）；② dmg 无主签名致 `spctl --context primary-signature` 误判 rejected（electron-builder 有意不签 dmg 容器，改用 `stapler validate` 权威公证检查）；③ Actions 产物配额爆 + 6-12h 滞后（改 release 交付 + 精简只传 dmg）。本机打包能力零回归（`forceCodeSigning` 只在 CI 脚本、不进 package.json → 本机无证书照出 unsigned 自测包）。win 仍 0.3.5（Windows 自包含 CI 未接，`include_windows` 默认关）。签名/公证凭据 6 secret + `ADS_RUNTIME_JSON_BASE64` 均在 GitHub 仓库 secret（baked key 本就 bake 进每个分发 .app、放 secret 更安全非新暴露）。见 memory `edge-mac-signed-notarized-release`。

## 簇 61 — edge-client-customer-auth 真机验收（对外客户端 name+key 登录门 + 按客户隔离环境可见性，登记于 2026-07-12；cloud master `0b6ef42` 已 land + **部署 dev 并启用（8091，真库端到端冒烟绿：登录/my-environments/错误 key/停用即时失效）**；console master `ef8e356` 已 land + 部署 dev；edge master `85d0528` 已 land，edge-only 登录门属客户端行为变更、需运营/客户机重建安装包后核）

**背景**：给 edge 桌面客户端加一层对外客户鉴权（与内部运营 console 登录物理隔离）。云端独立小 HTTP 服务（独立 JWT 密钥、启动断言 ≠ 面板密钥）+ 新表 `client_users` / `client_env_scope`（scrypt key、显式归属 fail-closed）+ 面板 `/api/client-users*` 管理端点；edge 独立登录窗口门控（未登录不连云不起环境）+ 环境栏按云端权威 `/my-environments` 过滤（env_key = profileId）+ 新建环境自动归属；console 新增「客户端用户」管理页。**协议零改、不碰 accounts 热点表**。登录门 opt-in（配了客户鉴权地址才启用，零回归）。三条隔离不变量（N1 密钥即边界 / N2 结构性无泄漏 scoped-only 读 / N3 每请求回库复核 status）已单测锁死（cloud 13 用例）+ 全量 cloud 1862 / edge 1050 / console 94 绿。桩验不了的真机项：

- [ ] 61.1 edge GUI 登录流（重点）— 客户机配 `AIDCP_CLIENT_AUTH_URL`（或 `AIDCP_CLIENT_AUTH_ENABLE=1` + 云端选择）后启动客户端：出现蓝灰登录门 → name+key 登录成功进主界面 → 环境栏只显示归属环境 → 托盘「退出登录」回登录门 → 关登录窗后 dock 点击能拉回登录门。桩验不了 Electron GUI。
- [ ] 61.2 跨客户隔离（重点，安全）— 两个客户各自登录（同机切换或异机）：各只见自己归属环境、拿不到对方环境清单；运营在后台移除某客户对某环境的归属后，该客户 ≤4min（会话维护周期）内环境栏剔除该环境；停用某客户 → 其在途客户端 ≤4min 内被踢回登录门。
- [ ] 61.3 新建环境自动归属 — 登录态下客户端「添加/创建环境」→ 该 profileId 自动归当前客户、即时出现在环境栏，且后台该客户 scope 里可见（source=client）、可被运营调整。
- [ ] 61.4 console 管理流 — 后台创建客户 → 一次性密钥 Modal 展示 + 复制 → 用该 key 在客户端登录成功；轮换 key 后旧 key 立即登录失败、新 key 可登录；停用后无法登录。console 页 AntD portal 交互（create→key-reveal→copy）桩验 flaky、须真机/手动核。**复制修复（2026-07-12，console master `efd1ea4` 已部署 dev）**：明文 HTTP（`http://<ip>:8088`）非安全上下文下 `navigator.clipboard` 为 undefined，一次性密钥复制曾恒报「复制失败，请手动选中复制」；已加 `copyToClipboard()` 兜底（async API 优先，不可用/失败退回 `textarea + execCommand('copy')` 同步选区复制），兜底不变量单测锁死（7 用例绿）。**真机核**：dev console 页点「复制密钥」实际落入剪贴板（execCommand 真写只能浏览器核）。
- [x] 61.5 reachability 接线（dev 已完成）— dev 已在 `aidcp-console.conf`（8088 + 80/`aidcp.tommax.cc`）加 `location /capi/ → 127.0.0.1:8091/`（带 X-Forwarded-For），公网完整登录往返已验证；客户端可达 `http://121.89.85.150:8088/capi`。**剩**：真客户机上 edge 配 `AIDCP_CLIENT_AUTH_URL=http://121.89.85.150:8088/capi` 后实连（并入 61.1 GUI 流）；**ol 上线**须独立 TLS 子域 + 独立 ol 密钥（不复用 dev）。
- [ ] 61.6 打包态门控（asar 红线）— 打包版 edge 起独立 login 窗口 + 启动门控不被 asar/cwd 坑（login.html 走 loadFile、preload 路径正确）；发版前本机跑打包产物确认登录窗弹出 + 登录后主窗与环境启动正常。edge-only、需重建安装包。

### 61 增补：端用户环境选择列表（change client-user-env-picker，2026-07-12 已 land + 部署 dev；cloud master `05bd239` / console master `6a6fe92`）

后台「客户端用户」页改名「端用户」；环境归属抽屉从手填 profileId 升级为「从全局环境注册表勾选加入 + 待分配/已分配筛选 + 一环境多分 + 多人标识」。cloud 新增 `GET /api/client-environments`（内部 JWT，跨用户聚合、绝不接客户服务=守 N2）。**已真机验证**：dev PG 用 ROLLBACK 事务跑真 `listAllEnvironments` SQL——多分环境返 2 assignees（多人）、独占返 1、label/platform 取非空代表值、`{userId,name}` 形状对、0 残留。GUI/交互项桩验 flaky（AntD portal + TanStack 时序）→ 真机核：

- [ ] 61.7 后台勾选加入流 — 端用户页开「环境归属」抽屉：默认「待分配」列出全局注册表里未归属该端用户的环境；勾选多个 → 「加入选中（N）」→ 切「已分配」见新增；保存后该端用户 `/my-environments` 与客户端环境栏出现这些环境。
- [ ] 61.8 一环境多分 + 多人标识 — 同一环境加入端用户 A 与 B 都成功；两侧客户端都能见到该环境；后台抽屉里该环境显示「多人（2）」、Tooltip 列出 A/B 名。**关键**：给 A 加入 B 已有的 env 并保存后，B 的归属集合不变（`setScope` 只 DELETE 当前 user_id）——真机核 B 不掉环境。
- [ ] 61.9 暖缓存重开回归（评审揪出的 critical，已结构性修复）— 打开某端用户环境归属抽屉（有已归属环境）→ 关闭 → 5 分钟内重开同一端用户：「已分配」必须仍显示原有环境（**不得**变 0、原环境**不得**跑到「待分配」）；此时点保存**不得**清空该端用户归属。修法=rows 由 `scope.data` 单一 effect 驱动（原双 effect 竞态清空草稿）。桩测 portal 重、以真机点击 open→close→reopen 核。
- [ ] 61.10 复制密钥（并入 61.4）— HTTP 后台点「复制密钥」实际落入剪贴板（execCommand 兜底真写只能浏览器核）。
- [ ] 61.11 存量环境导入 + 待分配呈现（change `client-user-env-registry`，cloud master `843a0a9` land + 部署 dev + 归档）— 后台打开任一端用户环境归属抽屉：11 个已导入的存量环境出现在「待分配」（`assigneeCount=0`、「已分配给」列显示「—」）、可勾选「加入选中」→ 保存后转「已分配」。dev 真库已直查核（11 个 count 全 0 + 已归属 k1ejvb06 并入 count 1）；GUI 呈现与勾选加入需浏览器核。导入只取 env_key/名字/平台，凭据不入库。
- [ ] 61.12 边缘自动登记自维护（`onEdgeRegistered`）— 新 AdsPower 环境连上 dev 云端后，自动出现在后台「待分配」（source=auto），env_key=裸分身 id（无 `ads-` 前缀），且**未被误归属任何客户**（归属表无其行、assigneeCount 保持 0）。self-/host- 兜底 edge 不应出现。需真机连一个新环境核。
- [ ] 61.13 并集读不丢已归属环境 — 某 env 只在归属表（客户端自建 attach）、注册表无：后台仍列出并带真实归属客户与人数（dev 已见 k1ejvb06 count 1 验证；GUI 核）。

### change `edge-client-env-scope-and-logout`（edge master `36144c2` 已 land，edge-only 无 ECS 部署，运营/客户机 pull master + 重建安装包后生效，登记于 2026-07-12）
- [ ] 61.14 加入列表按客户收窄（重点，安全）— 登录客户 A，开「添加环境 → 加入现有环境」：**只列 A 归属的环境**（他客户/未归属环境的名字/分组/代理/分身 id 均不出现）；后台给 A 新分配一个环境后点「刷新」即时出现；令牌到期但主窗仍开时点刷新 → 登出回登录门（**绝不**回落全量）；未启用鉴权的内部构建仍列本机全部环境（零回归）。
- [ ] 61.15 降范围环境不被误剔 — A 归属并在册环境 C（本机物理仍在），后台把 C 移出 A 的可见集后 A 刷新加入列表：C 不显示，但其花名册项**不被删**（不弹「已清理云端已删除的残留环境」）；后台再把 C 授权回 A → C 能自动恢复运行。
- [ ] 61.16 设置「退出登录」（取代「重新登录」）— 设置抽屉底部为「退出登录」（显示「当前客户：<名>」）、无 per-环境「重新登录」；二次确认后清会话、停全部环境、回 name+key 登录门、可重登账号；未启用鉴权时该入口不出现；**回归**：通知巡视引导流的「重检」仍能重启单环境（`auth:relogin` 未被误删）。打包态同样生效（asar 红线，需重建安装包）。
- [ ] 61.17 **【高优先级专项安全 change，非本 change 修复】** 写侧租户隔离缺口（三轮对抗评审 critical 结论，2026-07-12）— 现状：① `ads:deleteEnv` / `ads:updateEnvProxy` 按 `userId` 改/删既有环境**未按归属设闸**；② `settings:save` 乐观自动归属对渲染层提交的任意新 `profileId` **无条件** `allowedProfileIds.add(...)`（云端 attach 结果被忽略）→ 恶意渲染层/DevTools 可先注入他客户环境 id 污染本地归属集、再删/改他客户环境；③ `settings.environments` 花名册**跨客户登录共享**（`settings:get` 会把上一客户的 id 暴露给下一客户）。**正确修需**：云端 attach 权威化（拒绝认领他客户已归属环境 + attach 结果为准）+ 边缘写请求 fail-closed 的每请求权威复核 + 花名册按客户隔离。**曾在本 change 试加边缘写闸但确证=假安全（同一污染面可绕）已移除**。→ **须开专项 change（edge+cloud），独立评审**。

## 簇 62

### change `edge-rail-fixed-height-scroll`（edge master `f34af1b` 已 land，edge-only 无 ECS 部署，运营/客户机 pull master + 重建安装包后生效，登记于 2026-07-14）

环境栏改为定高（视口减标题带）+ sticky，环境超出只在列表区内滚；栏头 / 汇总 / 栏尾常驻。以下为 jsdom 无布局、桩测诚实验不了的项，须真机（多环境实景，建议 ≥15 个环境）核：

- [ ] 62.1 栏内滚动 + 栏尾常驻（主项）— 环境数超出一屏时：滚轮在左栏内滚动列表，栏头「环境 N / ＋ / 收起钮」与栏尾「引导处理 / 全部启动 / 提示」始终可见、无需滚整页即可点到；右侧主区域滚动时左栏钉住不动。
- [ ] 62.2 滚动链隔离 — 列表滚到顶 / 底后继续滚轮，**不得**把整页一起带滚（`overscroll-behavior: contain`）。副作用已知：环境很少（列表不溢出）时在左栏上滚轮将不再滚动页面，属预期。
- [ ] 62.3 收起态窄条同样能滚且状态色环不被裁 — 默认收起的 56px 图标条：环境多时可滚；每行头像外圈状态色环（运行绿 / 留意琥珀 / 错误红…）右侧**不得**被裁掉一截（收起态已刻意不留滚动条槽、行宽收到 42px）。
- [ ] 62.4 分组标题吸顶（展开态）— 长列表滚动时「需要处理 / 运行中 / 暂停·离线」分组头吸在列表顶部、底色不透行；收起态该元素仍是 1px 分隔线、**不得**在列表顶永久钉一条线。
- [ ] 62.5 状态刷新不打断滚动 — 把列表滚到下方停住，等任一环境状态跳变（触发左栏重建）：滚动位置**不得**跳回顶部。
- [ ] 62.6 引导流选中行自动入视野 — 待处理环境多于一屏时点「引导处理」：当前引导目标那一行被滚入可视区（含「目标本就是当前选中项」的情形）。
- [ ] 62.7 小窗口 / 缩放边界 — 把窗口高度拉到最小：栏尾动作区仍在视口内可点（列表可被压得很矮属预期，栏尾**绝不**能被挤到栏底边以下——那片区域滚多少页都够不着）。
- [ ] 62.8 浮层不被新滚动容器裁切 — 人设浮层 ✦ / 添加环境面板 / 代理面板 / 设置抽屉从左栏行上唤起时完整显示、不被列表边界裁掉。

---

## 簇 63

### change `feishu-route-account-cards-by-team`（cloud master `9498092` 已 land + **已部署 dev**，纯云端、边缘 / console 无改，登记于 2026-07-14）

账号维度的业务结果卡（排期发帖 / 评论终态 / 排期评论与联系评论触发回执 / 免审通知 / 参照创作）从硬绑默认群改为按账号 `group_label` 路由到团队群；审批卡与运维告警仍留默认（管理）群。

**部署当日已在 ECS 上用真实 dev 库跑过解析验证**（部署好的代码直连真库）：默认群 = `oc_144e761f…`（AI运营）；工程师大白 / Tmax（`tom`）→ `oc_1c268549…`（Tom.A）；小猫（`YY`）→ `oc_f5c3f6fc…`；阿柚（`ninghao`，其路由即默认群）→ 默认群。**解析层已坐实**，以下为需飞书肉眼确认的投递层：

- [ ] 63.1 排期发帖结果卡落团队群（主项）— 等「工程师大白」下一个排期发帖槽（或手动触发），确认「排期发帖：本槽无新素材 / 草稿已生成」卡出现在 **Tom.A** 群、不再出现在 AI运营群。
- [ ] 63.2 排期评论结果卡落团队群 — 同上，「按需评论未产出」/ 评论终态卡落 Tom.A。
- [ ] 63.3 人工 `/comment <昵称>` 终态卡落团队群（**已知行为变更**）— 从管理群下 `/comment`，其**终态结果卡**会落该账号团队群（受理回执与人审卡仍在管理群）。确认操作员可接受；若碍事，回退面只有该一处出口。
- [ ] 63.4 审批卡 / 运维告警**不外流** — 发布审批卡、评论人审卡、验证码 / 边缘离线 / CDP 不健康 / 熔断告警仍落 **AI运营** 群，MUST NOT 出现在 Tom.A / YY 群。
- [ ] 63.5 未绑定团队的账号 — 其业务结果卡仍落默认群；若该账号 `group_label` 非空却未命中路由，日志应有 `[feishu-routing] config-gap` 一行（这是「配错了」与「没接线」的判别依据）。
- [ ] 63.6 机器人在团队群的发言权限 — 确认机器人在 Tom.A / YY 群确实能发卡（`bot_chats` 标 active 仅表示在群内，未证发言权）。

## 簇 64

### change `persona-bound-tristate-and-standby-drain`（edge master `0e383b3` + `9761448` 已 land；cloud master `707ea76` 已 land + **已部署 dev**，登记于 2026-07-14）

两个真机 bug，共用同一个触发器（冷待机唤醒）：① 冷待机关浏览器时把浏览循环撕断，13s 后抛「浏览会话异常」（`CdpDisconnectedError`）；② 已设置人设的账号（工程师大白）被反复误弹人设向导。桩层已坐实两条因果链（BUG A 的回归用例在修复前的代码上空转 12001ms，与线上 13s 缺口逐帧吻合），以下为只能在真机确认的部分。

**边缘改动需重启桌面客户端才生效**（用户在 canonical `aidcp-edge` 跑 `electron:dev`；云端已部署，旧客户端只读 `personaBound === true`、忽略新下发的 `false`，无回归）。

- [ ] 64.1 冷待机一轮（主项）— 让「工程师大白」跑到配额耗尽进入冷待机（日志「浏览器已关闭进入冷待机」）。确认此后**不再出现**「浏览会话异常: CdpDisconnectedError」，且「[browse] 浏览循环结束」出现在关浏览器**之前**而非之后 13 秒。
- [ ] 64.2 冷待机唤醒后正常复跑 — 唤醒（配额恢复 / 新任务）后核心重启、浏览闭环恢复，不出现停摆。
- [ ] 64.3 工程师大白重启客户端 → **不再弹人设向导**；人设徽标直接显示「已设置」，中途不闪现「未设置」。
- [ ] 64.4 真未设置人设的账号仍照常弹一次向导 + 一条系统通知（防「为了消除误弹把提醒改没了」）。
- [ ] 64.5 客户端内清空人设保存（= 显式解绑）→ 徽标即时翻「未设置」并弹向导，**不必等重启**（云端 `onChanged` 即时重推）。
- [ ] 64.6 退出 / 暂停关浏览器路径同样不再抛断连异常（与 64.1 同根因，改的是同一处排空契约）。

### change `browser-cold-standby-next-action`（cloud master `a564b36` + `5fba9e7` 已 land + **已部署 dev**；edge master `6d4815a` 已 land、需运营机 pull + 重建安装包后生效，登记于 2026-07-14）

上面 64.1–64.6 修的是「冷待机把浏览循环撕断」这个 bug；本 change 是**冷待机特性本身**（云端算出下一个可动作时刻并下发 `browserStandby.eligible/wakeAt/warmupMs`，客户端据此关浏览器、保核心与云连、按时提前唤醒）。共用同一台真机、同一个账号、同一次「跑到配额耗尽 → 关浏览器 → 唤醒」的验收动作，与 64.1/64.2 一次验完。

- [ ] 64.7 冷待机真的进入（本 change 主项）— 让一个账号跑到配额耗尽、云端下发 `browserStandby.eligible=true`，确认客户端日志出现「浏览器已关闭进入冷待机」且 AdsPower 分身的调试端点变暗（浏览器进程真被关掉，不是只标了状态）；同时确认核心进程与云端 WS 连接**仍在线**（左栏该环境不掉线、云端不判边缘离线）。
- [ ] 64.8 按预测时间提前唤醒 — 记录云端下发的 `wakeAt` 与 `warmupMs`，确认客户端在 `wakeAt - warmupMs` 附近（而非配额恢复后才被动重启）重新拉起浏览器并恢复浏览闭环；偏差在分钟级，唤醒后不出现重登陆 / 扫码。
- [ ] 64.9 硬阻塞绝不误关（诚实闸）— 制造验证码 / 掉登录 / 分身被别处占用三种阻塞之一，确认云端**不**发 `eligible=true`（或发 `false` 带明确 reason），客户端**不**关浏览器，原有告警 / 人工介入提示照常出现。
- [ ] 64.10 短等待不触发 — 配额只剩几分钟的短等待场景，客户端不进冷待机、浏览器保持打开（避免高频开关浏览器）。
- [ ] 64.11 本地开关可关停 — 客户端设置里关闭「浏览器冷待机」后，即使云端仍下发 `eligible=true`，浏览器也**不被关闭**（日志可见跳过原因），确认这条 kill switch 在真机上真能兜住。
- [ ] 64.12 手工操作取消自动唤醒 — 冷待机计时器存在期间，操作员手动暂停 / 关闭 / 移除 / 重启该环境，确认旧的自动唤醒定时器被取消，不会在原 `wakeAt` 时刻突然把浏览器拉起来覆盖操作员意图。
- [ ] 64.13 客户端需重建才生效 — edge 侧改动在 master（`6d4815a`），运营机需 pull + 重新出包（或 canonical 跑 `electron:dev` 重启）后上述行为才存在；确认运营机跑的版本确实包含冷待机控制器。

---

## 簇 65

### change `facebook-post-publish`（cloud master `55a3bcf` / `1ab6f51` / `feda1d1` 已 land + **已部署 dev**；console master `7f8627c` / `30f25ed` / `76b528a` 已 land + 已部署 dev；edge master `6587c1d` / `5025eef` / `4e466ca` / `987f91d` 已 land、需运营机 pull + 重建安装包后生效，登记于 2026-07-14）

Facebook 个人主页发帖 + 账号级素材池 + 排期审批链。FB 发帖只在 dev 用 Dennis 账号做过一次门禁真提交（单次取证，非稳定验收），edge 侧改动全部未出安装包。

- [ ] 65.1 发帖全链（主项）— 运营机 pull edge master 并重建安装包后，用 Facebook 互动号跑一次「排期 → 飞书待审 → 批准 → 边缘发帖」：算过 = 帖子真出现在个人主页，云端 `publish_log` 该条最终为 `published` 并带干净的 permalink / post id，全程无刷新页、无自动重试、无静默假成功。
- [ ] 65.2 正文逐字键盘输入（红线）— 真机 CDP 观察到按字符逐次输入、composer 内文本逐渐增长；最终帖子正文与草稿逐字一致、无丢字漏字（一次性整段插入是 FB 的高危信号）。
- [ ] 65.3 `submitted` → `published` 升级链是**自动**完成的 — 算过 = 提交后不刷新页面、边缘在同页捕获 permalink / postId 回传，云端自动把该条从 `submitted` 改写为 `published`。若真机上只能停在 `submitted` 需人工干预，判为缺口、另开 change 做云端对账，**不得靠人工改库掩盖**（已知疑点：此前 dev 那条疑似人工补记）。
- [ ] 65.4 素材池不足与 quarantine 闭环 — 素材池清空后 FB 排期槽被诚实跳过并给出「素材不足」原因（不生成空图草稿）；提交后未确认的素材真的落 `quarantine`，且能在控制台「确认」改回 `available` / 编辑备注 / 删除，而 `reserved` / `used` 仍锁定不可动。
- [ ] 65.5 飞书审批卡的 Facebook 形态 — 待审卡正确显示平台=Facebook、账号名、本次锁定的素材缩略图与张数；批准后发帖用的就是卡上那组图（顺序一致），拒绝后这组素材被释放回 `available`。

---

## 簇 66

### change `compress-admin-upload-images`（console master `29d8e9f` + `2d43980` 已 land + **已部署 dev**；纯前端，cloud / edge 无改，登记于 2026-07-14）

管理后台 FB 发帖图片上传前统一转 JPEG 压缩。console 单测把浏览器成像栈全打了桩（`createImageBitmap` / canvas / `toBlob`），只证了控制流与请求装配——**真实解码、真实 JPEG 编码质量、真实字节缩减、画面保真、拒绝路径**全是桩测盲区，必须在真浏览器上对 dev 后台（`http://121.89.85.150:8088` → Facebook 账号「FB配置」→「发帖图片」）核。

- [ ] 66.1 手机原图压缩入队（主项）— 上传一张手机/微信原图（≥3MB，如 3024×4032）：被接受入队，队列标签显示「原始大小 → 压缩后大小」，压缩后接近或低于 600KB，上传请求 `contentType=image/jpeg`、`filename` 以 `.jpg` 结尾。
- [ ] 66.2 画面不被裁切（承重项）— 把 66.1 的图从素材池取回与源图逐眼比对：画面范围完整、宽高比不变，**不得**只剩中间裁剪区或被拉伸补边（长边等比缩到 ≤2048px 属预期，不算裁切）。
- [ ] 66.3 PNG 透明图白底合成 — 上传带透明背景的 PNG：入队显示 `.jpg`，成品透明区是白底而非黑底 / 花屏。
- [ ] 66.4 已优化小图被拒的可接受性（**已知行为变更**）— 上传一张本身已高度压缩的小 JPEG（50–100KB）：代码在无法生成更小 JPEG 时判 `not_smaller` 并**拒绝入队**。确认运营能理解该提示、这类图在实际素材里不常见；若运营常被挡住，说明「必须更小」这条策略需放宽（回退面只有该一处判定）。
- [ ] 66.5 动图 GIF 只保留首帧 — 上传动画 GIF：入队为静态 JPEG（首帧），运营知情该图不再是动图；若产品上不可接受，应改为直接拒绝而非静默变静态。
- [ ] 66.6 无法解码的文件被诚实拒绝 — 上传改了扩展名的假图片（.txt 改成 .jpg）或损坏图：前端显示「无法转换压缩」错误，该文件**不得**进入待上传队列、也不得以原文件形式被上传。
- [ ] 66.7 端到端发帖提速（本 change 初衷）— 用 66.1 压缩后的素材真发一条 FB 帖：边缘上传 / 提交阶段不再长时间卡「发布中」，配图正常显示、清晰度可接受。

---

## 簇 67

### change `edge-cdp-health-recovery`（edge master `1b636df` 已 land、需运营机 pull + 重建安装包后生效；cloud master `e668476` 已 land + **已部署 dev**，登记于 2026-07-14）

治「边缘与云端还连着、但浏览器已经驱不动」这个哑状态：边缘对输入类命令做时延分级与超时判定，不健康时在安全边界停手、走一次有界软恢复；人审通过的发布来要浏览器时立刻明确拒收（`cdp_unhealthy`）而非干等 45 秒 acquire 超时；云端把拒收翻译成「客户端在线但浏览器控制不可用、未下发任何发布命令」，把稿件退回待审、作废本次授权。

- [ ] 67.1 输入超时被识别并停手（主项）— 人为制造 CDP 输入停顿（挂起页面 / 断开渲染进程），确认边缘日志出现输入超时诊断（触发方法名、观测时延、分类原因、恢复关联 id），浏览器控制被标不可用，此后**不再发起新的普通浏览动作**；绝不出现「点不动却回 ok」的假成功。
- [ ] 67.2 慢输入连续命中触发有界软恢复 — 输入命令连续多次「成功但很慢」（超慢输入阈值）后，边缘进入恢复态、**只发起一次**有界恢复（重连 + 重新发现页面目标 + 重新注入反检测），恢复后向云端**重新上报一次页面状态**，浏览闭环续跑；被打断的那条命令**不得被重放**。
- [ ] 67.3 人审发布撞上不健康（核心价值项）— 在 67.1 的不健康窗口内从飞书批准一条发布：飞书**当场**（秒级，而非 45 秒后）收到「客户端可能仍在线，但浏览器控制不可用，未下发任何发布命令」；草稿退回待审；本次授权作废。通知文案**不得**说成「边缘离线」「acquire 超时」或「发布序列失败」。
- [ ] 67.4 拒收不留残留租约 — 67.3 之后边缘侧无遗留排队中 / 活跃租约；浏览闭环在浏览器恢复后自行续跑、不需重启核心；云端补发的 release 被幂等吞掉，**不得**因重复 release 把浏览冻住或误唤醒。
- [ ] 67.5 外部 / 复用浏览器所有权边界（红线）— 用「复用一个非边缘启动的浏览器」复现输入超时：边缘**绝不**强杀 / 关闭这个非自有浏览器，只如实停在不可用态并提示需人工重启 / 重连；自有浏览器在恢复次数耗尽时才走既有的回收重起链路。
- [ ] 67.6 客户端需重建才生效 — 运营机装上含 edge `1b636df` 的新包后重跑 67.1 与 67.3（边缘侧保护只随新客户端生效，云端部署单独改变不了已装客户端行为）。

---

## 簇 68

### change `edge-task-acquire-timeout-recovery`（edge master `c29f8ac` 已 land、需运营机 pull + 重建安装包后生效；cloud master `b2de46b` 已 land + **已部署 dev**，登记于 2026-07-14）

云端 acquire 超时后主动撤销租约、边缘在本地等待上限届满后取消排队申请、排期评论在接管失败时诚实回「未开始」。真机建议用 dev + tom 分组账号（如 Tmax）。

- [ ] 68.1 等待上限届满不再授予陈旧任务（主项）— 边缘正处于长动作（详情页深读 / 长停留）中时云端下发一次排期评论 acquire；上限届满后观察边缘日志：该 taskId 被移除、**绝不**在上限之后再发 acquired、浏览闭环继续收敛不冻结。
- [ ] 68.2 云端超时即主动 release — 超时后日志有对该 taskId 的主动 release；此后浏览器仍可继续自治浏览（不出现「边缘在线但页面不动」直到租约自然到期）。
- [ ] 68.3 迟到 acquired 二次撤销 — 制造边缘在云端超时之后才回 acquired 的时序：云端**零条业务命令**下发、并再次发出 release，边缘随即释放租约、恢复浏览。
- [ ] 68.4 排期评论回执诚实为「未开始」— 超时发生在准备阶段时，飞书结果卡明确「本次未搜索、未选中笔记、未发布评论」并带可审计的接管失败原因；**绝不**出现「已选中笔记」「发布未确认」等措辞；该次不被记为已评论 / 已发布 / 候选已选中。
- [ ] 68.5 已进入流程后的失败保持原阶段语义（防过度改写）— 已取得租约后在候选选择 / 撰写 / 提交阶段失败的，回执仍显示对应阶段的真实失败，**不得**被改写成「未开始」。
- [ ] 68.6 正常路径零回归 — 边缘空闲时下发排期评论：仍在上限内正常 acquired → 搜索 → 选中 → 人审 → 发布，全链无回归、无多余 release。

---

## 簇 69

### change `facebook-humanized-scroll`（edge master `6576a49` 已 land，edge-only 无 ECS 部署，运营 / 客户机 pull master + 重建安装包后生效，登记于 2026-07-14）

FB feed / 评论编辑器的滚动从「一次固定 900px 滚轮 + 紧接着又一次 900px JS 兜底」改为惯性拟人手势，并去掉成功手势后叠加的 JS 双倍滚动。

- [ ] 69.1 feed 滚动手势拟人化（主项）— 跑 FB 互动号 feed：单次翻页是**多帧惯性滚轮序列**（连续推进约 0.5s、总位移在 650px 上下抖动），**不得**再出现双倍跳跃。判过 = CDP / 日志观测到每次翻页只有一段连续 wheel 序列、位移落在 ~500–800px 且每次不同。
- [ ] 69.2 成功手势后不再叠加 JS 兜底 — 页面确实被滚轮推动的回合，**不得**再触发 JS 兜底（兜底只允许在「手势后位移为 0」时发生）。判过 = 一轮 feed 浏览中，凡位移 >0 的回合日志里都没有随后的 JS 兜底记录。
- [ ] 69.3 零位移兜底仍有效 — 人为构造滚不动的情形（浮层锁住 / 内容未加载），边缘走一次**有界** JS 兜底把页面推动，而不是静默当作已滚成功（诚实闸）。
- [ ] 69.4 评论框懒加载滚动共用同一手势 — 走一次 `/comment` 或群评：唤起评论编辑器的滚动同样是拟人惯性手势，且「有界探测 + 找不到编辑器就诚实报失败」没退化（不得因换手势把 no_target 变成假成功）。
- [ ] 69.5 与「FB feed 只看顶部就整页重载」的交叉确认 — 已知 FB 会话存在「全程 URL 跳转导致 feed 不往下滚」的独立缺陷（见 memory `fb-feed-never-scrolls-down`）。真机核：本 change 上线后 feed 能否连续滚过 3 个以上帖子而不回顶 / 整页重载；若仍回顶，需确认根因归属那条独立缺陷、而非本手势改动引入的回归。

## 簇 70

### change `fb-publish-fill-deadline`（cloud + edge，登记于 2026-07-14；FB 正文逐字输入 vs 云端常数单步墙）

FB 发帖的正文填写是 O(正文长度) 的逐字输入，却被云端用常数 30s 窗口去等——约 175 字即中位数超时，而内容管线产出 200–500 字。修法：云端按长度下发单步预算、边缘自我掐表并诚实清场；验收闸从「前 20 字前缀」换成全文回读。**边缘改动需运营 / 客户机重建安装包后生效**；真机只能打 dev（OL 已转稳定生产、FB 在其上硬关）。

- [ ] 70.1 **长正文逐字 probe P1（决定方案生死 + 校准常数）** — dev + tom 分组 FB 环境，用**生产的**逐字逻辑打一篇 400–500 字真实形状正文（含标点、两个空行、一个 URL、一个 emoji——URL 最可能触发链接预览重渲染抢光标）。记录：① 总耗时与实测 ms/char；② 单次 `Input.insertText` 往返 p50/p95；③ **回读与源文逐字符 diff**（不是包含，是逐字符）；④ 打字途中有无 typeahead / 链接预览 / 同意浮层弹出；⑤ 提交控件是否仍 enabled。清场、**不提交**，跑 ≥5 次。判过 = 逐字符无差异，且实测 ms/char 落在预算的每字 250ms 之内。若长正文逐字本身就是有损的（被 typeahead 劫持 / 丢字），则预算抬多高都没用——此时才需翻到「分块插入 + 全文回读」并改 spec。
- [ ] 70.2 **清场语义 probe P2** — 挂 1 张图 + 打约 50 字后，同一 CDP session 内：① 全选 + Backspace → 回读文本**并确认图片缩略图是否还在**（清了文字不等于清了附件）；② 按 Escape → dump 确认弹层的按钮与 aria-label（该账号 UI 语言）；③ 带脏 composer 发 `Page.navigate` → 观察是否触发原生 beforeunload 对话框、navigate 是否 resolve。**这条同时排一个今天就存在的隐患**：edge 全仓**零处**处理 `Page.javascriptDialogOpening`——若脏 composer 注册了 beforeunload，下一篇稿的导航会弹原生对话框**把整个 tab 卡死**（边缘看着在线、浏览器驱不动，即 memory `edge-lease-and-cdp-health` 那一类）。
- [ ] 70.3 端到端真发 — 一篇 300–500 字真实洗稿正文在 dev 上从头走通到**真提交**，正文逐字符核对无缺失、无截断、无残稿拼接。判过 = 帖子正文与终稿完全一致。
- [ ] 70.4 预算耗尽路径 — 人为把 `AIDCP_PUBLISH_FILL_MAX_MS` 调到远小于正文所需（或用超长正文），核：边缘**停手清场**、回 `fill_deadline_exceeded`、**不提交**；composer 不留残文；云端记 failed 而**不再**出现「边缘还在打字」的孤儿循环。
- [ ] 70.5 越界诚实闸 — 构造超出上限（默认 880 字）的正文，核：云端诚实 `content_too_long`、**一条指令都不下发**、绝不截断发出。
- [ ] 70.6 小红书零回归 — 跑一次 XHS 正常发布，核：等待窗口与行为与改动前一致（指令不带预算），逐字输入辅助未受影响。

---

## 簇 71

### change `estimate-token-cost-column` + `manual-billing-price-refresh` 真机验收（用量页「估算成本」列 + 手动账单价格刷新，登记于 2026-07-14）

两个 change 共用同一条真机链路（**厂商账单中心 → 价格快照 → `/usage` 成本列**），一次真机 session 一起验完。
- `estimate-token-cost-column`：cloud master `2eddb24` + console master `8633aa8` 已 land + **已部署 dev**。
- `manual-billing-price-refresh`：cloud master `e117071` + console master `12cd65a` 已 land + **已部署 dev**。
- 二者代码早已上线，长期未归档的原因是 spec delta 建模不一致（主 spec 里那条「账单价格刷新」悬空建立在一条从未被创建的地基需求之上）；2026-07-14 理顺：`estimate-token-cost-column` 用 ADDED 建出地基 `Token Usage Cost Estimates`、`manual-billing-price-refresh` 再 MODIFY 它叠加刷新动作，随后按依赖顺序归档。

**前置**：dev 管理后台 `http://121.89.85.150:8088` 可访问 + 有账号在出流量 + ECS 上配了厂商账单凭据。红线：成本必须由厂商账单反算，**任何硬编码公开价目表都是错的**（见 memory `token-cost-from-billing-not-price-table`）。

- [ ] 71.1 手动刷新真拉到账单价（主项）— 在 `/usage` 页点「更新厂商模型定价」：返回 200 且 `written > 0`；ECS 上的价格快照表新增当次写入的 provider/model 行，单价是「账单金额 ÷ 账单 token 数」派生值。算过 = 至少一个真实在用模型（阿里 qwen 系或火山 doubao 系）拿到非零派生单价。
- [ ] 71.2 无账单快照时诚实 pending — 选一个尚无快照的日期/模型行：「估算成本」列**仍然存在**（不隐藏），显示 pending / 空态而非任何金额；页面上**不得**出现任何来自公开价目表的估算数字。
- [ ] 71.3 有快照时出数并暴露来源 — 刷新成功后回到表格：曾经 pending 的行显示出金额，且 UI 能看到估算的来源 / 日期提示（运营不会把它误当实时官方报价）。
- [ ] 71.4 当日无新样本时复用最新历史价 — 确认**当天没有新账单样本的 provider/model 行也照样出数**（走「同 provider/model 的最新可用历史价」回落，而非只认当日快照）。算过 = 同一模型在没有 T-1/T-2 新样本的日期行上仍有成本数字。
- [ ] 71.5 历史 unknown-provider 行被正确归厂 — dev 库里早期 provider 为空 / unknown 的用量行：模型名含 qwen/deepseek 的推断为 dashscope、含 doubao 或 `ep-*` 的推断为 volcengine，刷新后也能匹配到价格出成本。算过 = 这类历史行不再永久 pending。
- [ ] 71.6 跨 provider 不串价（红线）— 同时有阿里与火山调用时，各行的 provider 标注与实际调用方一致，两家的价格快照**不得**互相套用到对方的模型行上（同名模型不得取错价）。
- [ ] 71.7 金额与账单中心量级对得上 — 取一个已有快照的（模型 × 日）行，把「估算成本 = 该行 token 数 × 快照单价」与厂商账单中心当日该模型的实际扣费做量级核对：数量级一致、无明显偏离（验的是「口径没接反」，不追求分毫相等）。
- [ ] 71.8 刷新诊断不泄密 + 缺凭据时诚实 — 刷新响应体只含写入 / 价格 / 跳过 / 缺凭据四类字段，**不含任何 AK/SK/token 明文**；某厂商账单凭据未配置时，它出现在「缺凭据」里并被如实跳过，**绝不写入任何伪造 / 兜底价格**（守「不静默假成功」红线），UI 提示为警告态而非绿色成功态。
- [ ] 71.9 用量页其余能力无回归 — 新增成本列后，日期范围 / 账号 / 角色 / 模型筛选、10 分钟总量曲线、角色中文标签、空区间空态均照旧工作，表格不因新列被挤破版。
- [ ] 71.10 图片生成行不当作 token 计价目标 — 零 token 的图片生成行**不得**被纳入价格刷新目标、也不得为其请求或写入 token 价格快照（主 spec 已有此条，随本批一并核）。

## 簇 72

### change `facebook-feed-scroll-refresh-fix` 真机验收（FB 首页浏览回归修复 + `feed.refresh` 实装，登记于 2026-07-14；edge master `adf10f8` 已 land，edge-only 无 ECS 部署，运营 / 客户机 pull master + 重建安装包后生效）

**背景**：FB 首页「看一两条就整页刷新、永远滚不下去、每屏只报 1 张卡」。三层根因已修（全 edge-only、不改协议）：① `ensureFeed` 改幂等（已在目标列表面且无 dialog 就不再整页 `Page.navigate`，消掉 `7b9b37e` 的滚动重置回归，fail-closed 复检两条路径都跑）；② `settleCards` 以 loading-aware 累积判稳替换两道 existence gate（相邻两轮真卡集合稳 + 无 `role=progressbar`/`aria-busy` + wall-clock 兜底，空壳仍拒）；③ `feed.refresh` 实装为页内点顶栏首页图标 `[role=banner] a[href="/"]` 换批、后置校验「首卡 permalink 变更且非空」、`Page.reload` 带 ≥3min 频率下限兜底；附带修 split-brain（`backToFeed`/`navigateFeedBestEffort` 回 `activeFeedUrl` 而非会话初始首页）。桩测/jsdom 全绿（feed-reader 幂等/判稳/点击 + session split-brain/refresh，1191 全量 + 19 acceptance + typecheck 绿），但下列真机行为桩验不了、须运营机核。

**前置**：运营/客户机 pull edge master 并以带 Facebook 的默认分支重建安装包运行；一个 FB 互动号（headful）、`AIDCP_FB_BROWSE_AUTO=on`、连 dev 云端；用只读 CDP 连活浏览器看 `performance.timeOrigin` 判有无整页重载。

- [ ] 72.1 连续滚动不再整页重载（核心回归项）— FB 首页自动浏览时连续多条 `page.scroll`：`scrollY` 单调增长、能真正往下看多屏；只读 CDP 观察 `performance.timeOrigin` **全程不变**（无整页重载），对比修复前「44s 重载 5 次、scrollY 每次归零」。
- [ ] 72.2 每屏上报多卡而非 1 张 — feed 稳定后每次 `page.cards` 上报的真卡数 > 1（虚拟化空壳仍被正确跳过、绝不臆造），对比修复前每屏 1 张。
- [ ] 72.3 `feed.refresh` 真换批不重载 — 深度到阈值云端下发 `feed.refresh`：边缘点顶栏首页图标后 feed 首卡 permalink 变成新的一批、`timeOrigin` 不变（SPA 换批非整页重载）；首卡未变时诚实回 `not_refreshed`、不报陈旧卡。
- [ ] 72.4 搜索浏览返回不丢结果（split-brain）— 从 FB 全站搜索结果开一篇帖子后返回：落回**原搜索结果页**继续下滑，而非被带回 explore 首页从头重搜。
- [ ] 72.5 fail-closed 未因省导航而漏 — 在首页态弹出验证码/登录浮层时收到 `page.scroll`：边缘诚实回 `blocked_by_captcha`/`login_required` 且**不滚动**（确认幂等放行路径仍复检阻断，未因跳过导航而漏掉前置门）。
