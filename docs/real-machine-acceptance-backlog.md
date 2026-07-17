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
- [ ] **comment-approval-target-hold（landed cloud decd7f1，2026-07-15）** — 浏览闭环触发评论进人审时账号**停在待评论帖上**、不被滚走/换帖，审通过/超时后再继续浏览。真机观察点：① XHS 触发一篇值得评的帖 → 飞书人审卡出现的整段等待里 feed **不滚动**、账号钉在该帖（旧行为会因并行点赞 no_target 重扫或撰写窗 stray 命令滚走）；② 审通过 → 评论真发到该帖；超时/拒绝 → 该帖不评、继续浏览；③ 抓日志佐证：`idle_nudge 落评论支线在途窗内 → 抑制`、`no_target(stale) 落评论支线在途窗 → 不重扫`、`评论支线在途，巡视让位`（若期间来通知）出现，且评论结算后被让位的巡视**补跑**（不丢未读）；④ 审批窗内不因动作数/时长/配额**提前结束会话**废掉在审评论。FB 就地读评论迁移路径（读 feed / 评 detail）同样观察：审通过后 `open_note{navigate}` 按 permalink 回到该帖再发，不落到别帖。

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

代码与部署已就绪并经只读核验：dev 上 `AIDCP_CAPTCHA_ASSIST_ENABLED=true`、就绪门通过（token secret 走 `AIDCP_PANEL_JWT_SECRET` 回退）、`/api/captcha-assist/<id>` 无 token 401、启动无「未启用」告警。剩人机在环走查（需运营机 edge + 真/模拟验证码）：

> **⚠️ 2026-07-16 更正（本条原验收证据已失效）**：上面原记「`AIDCP_CAPTCHA_ASSIST_PUBLIC_BASE_URL=http://aidcp.tommax.cc`、协助页 `http://aidcp.tommax.cc/captcha-assist/<id>` 外网 200」——那是 **2026-07-11 域名割接前**的证据（当时域名指 dev）。割接后该域名只回 **OL**，dev 签发的链接把运营送到 OL，实测报 `captcha_assist_unavailable`（503，在鉴权之前）。**已修**：dev `.env` 基址改为 `http://121.89.85.150:8088`（备份 `.env.bak.20260716-212426`，21:25:15 重启后进程环境已实测生效、无「未启用」告警）。**下面各项验收一律用新签发的链接**——飞书卡里的链接是发出时固化的，旧卡改配置也救不回。**验收口径不是「503 消失」**（503 只是最外层门，让开后还有 404 / `edge_offline` 两堵墙），而是运营真点一下、边缘真动了。

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

> **补登（2026-07-15，`facebook-manual-comment-keepopen-lease`，landed cloud `0bb45f6` + deployed dev）**：修真机事故「`/comment --join` 开帖后没等审批完就返回首页 → `editor_not_found`」。根因=FB 定向评论路径全程不握边端租约，审批阻塞期被同账号并发的自治浏览闭环（无 taskId 的 page.scroll/返回）把页面滚回首页。改法=把「搜索→开帖→撰写→人审→提交」整段包进 `comment_prepare` keep-open 租约（6min，严格覆盖撰写~180s+人审90s）+ 给三条 FB 命令透传 lease taskId（否则边端持租约期把评论自己的命令也挡死）。**验收点（须在有并发自治浏览的在线 FB 账号上验）**：① 运营 `/comment <昵称> --join`（或 `--contact`）→ 边端加群、开帖后**审批等待的整段时间里页面钉在目标帖上、不被滚回首页**（可看边端日志「Facebook 命令被任务租约抑制」= 并发浏览命令被挡）；② 人审通过后在**同一目标帖**上真发成功（不再 `editor_not_found`）；③ 人审超时/拒 → 诚实非提交、不打去重、可重试；④ 拿不到租约（边端占用/无响应）→ 诚实非提交卡、不下发搜索。**与已归档 `comment-approval-target-hold`（浏览闭环内部就地评论）是两个正交洞**。

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

> **2026-07-15 补登 — `xhs-search-submit-gesture`（AI 搜索提交本身的 flakiness 根因 + 修复；edge master `cb9aeba`，簇 34 归属）**：上面「AI 搜索是否真跳结果页」这条的**根因已定位并修复**。真机 CDP 逐项取证（dev「工程师大白」`ads-k1e0ero8`）：AI 搜索框 `textarea[name=aiSearchTextarea]`（结果落 `/search_result_ai`）的回车导航**不认程序化 `el.focus()` + 不带 text 的裸回车**，且兜底提交按钮 `.bottom-box-right-submit-button` 常**不可见(0×0)**——三条路全断 → 大面积 `not_on_search_page`（该账号一天约 30 次搜索失败、几乎评不出）。修法：**真实指针点击聚焦 + 携带 `text:'\r'` 的回车（产生真实 keypress）+ ~700ms 停顿地板 + 未跳转有界重试回车（≤3）**；提交按钮仅在确可见时作附加尝试。用真机 CDP adapter 驱动**仓库实际 `executeSearch`** 验证：warm 页 5/5、cold-navigate 4/5（唯一失手为冷启首搜、经重试与云端换词自愈），对照现状约 0%。`/search_result` 与 `/search_result_ai` 两页型的 URL 判定 / 关键词双重编码归一 / 卡片提取（真机两页各 30 张 `.note-item`）均已支持。剩余真机项：
> - [ ] **全闭环把评论真发出** — dev 工程师大白跑真实排期评论（`ContentScheduler` 心跳命中）：搜索连续命中 `/search_result_ai`、不再 `not_on_search_page`；采卡 → 择优 → 开笔记 → 人审 → 发布走通，飞书出成功回执；日志不再出现该账号搜索大面积失败。
> - [ ] **happy-path 与自治搜索不回归** — 经典 `/search_result` 页型账号（如 Tmax）与自治浏览搜索（`search_evaluator`/`search.approved`）在真实点击聚焦 + 重试新路径下照常命中、不误伤、不多点不可见按钮。

> **2026-07-15 补登 — `comment-readnote-fastfail`（开笔记失败快速失败 + 诚实归因；cloud master `5529c87` **已部署 dev**，簇 34 归属）**：云端按需评论「开笔记/读正文」步原只监听 `note.detail.arrived`、干等满 28s 单步超时，且超时后把原因误记成「（超时/边端离线）」（边端在线且诚实回过失败）。改为竞速消费三路（`note.detail`=成功 / `action.completed{open_note,ok:false}`=诚实失败带真实 reason / 重报 `page.cards`=目标卡被回收 `target_not_on_page`），任一失败即快速返回、措辞如实。纯云端、不改边缘/协议。剩余真机项：
> - [ ] **开笔记失败即时且诚实** — dev 制造/遇到开笔记失败（目标卡滚走、弹层不弹等）时：飞书 read_failed 回执/云端日志**即时**出现（不再等约 28s）、原因**真实**（`modal_timeout`/`target_not_on_page` 等，不再是「超时/边端离线」）；happy-path 正常开笔记读正文不回归。

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

**补登（change `facebook-nickname-capture-timing`，2026-07-15；cloud master `1cd809d` 已 land + 已部署 dev；edge master `9430479` 已 land，edge-only 运营机重建 edge 后生效）——同一 FB 号真机 session 一并验**：把 FB 昵称采集**时机对齐小红书**（放开采集准入闸到 FB + 边端本人采集改就地读、不导航），治「启动后不更新昵称」（原只搭 hello 那一趟车、握手 3s 时机赛跑 / 等登录门丢昵称 / 会话内不再补读）：

- [ ] **首批 feed 后自动补上昵称（不再只靠握手）** — 空昵称 FB 号（含**导入号 / 换语言号**）重建 edge 后启动：即便握手那一下没读到，等**首批 feed 卡片到达**后云端自动武装本人采集、边端就地读顶栏头像 → dev `accounts.nickname` 落非空、控制台显真名。日志见 `[nickname_enricher] 完整启动首批 page.cards … account=<fbid>` + edge `[fb-session] profile.detail direct authorId=<fbid> nickname="…"（就地读、无导航）`。
- [ ] **采集就地读、绝不导航** — 本人采集全程无 `Page.navigate` 到 `profile.php`/`/me`（edge 日志 `就地读、无导航`）；FB 活标签页不被导航走、采集完不整页重载（`back` 经幂等 `ensureFeed` 空操作）。
- [ ] **走过等登录门的号也能补上** — 首启需人工扫码（走等登录门）的 FB 号，登录后首批 feed 到达时仍能补读昵称落库（不再因启动首读失败而整段丢昵称）。
- [ ] **换语言号读法短板确认** — 头像标签仅覆盖中英文 + 时间线后缀（见下两条 07-15 补丁）；仍未覆盖的语种 UI（越/泰/印尼语等）的号可能就地读空（诚实留空、无回归、不写垃圾），单独跟进。

**读法两连修（2026-07-15，就着「Nancy Terry」真机号 CDP 取证做出，edge master `776c0e8` + `600b9de`，edge-only；已 build:dist + CDP live 复核 `readFacebookIdentity → ok+"Nancy Terry"`）——运营重启 edge 后云端首批 feed 采集即写库**：

- [ ] **中文界面「的时间线」自链后缀**（change `facebook-nickname-aria-timeline-suffix`，edge `776c0e8`）— 中文号本人主页锚点 aria 是「<名>的时间线」而非「<名>的头像」；`AVATAR_ARIA_SUFFIX_RE` 已补 `的时间线`/`的時間線`/`'s timeline`。验：中文界面 FB 号启动后昵称就地读出真名。
- [ ] **c_user 权威、feed 他人链接不判冲突**（change `facebook-self-identity-cookie-authoritative`，edge `600b9de`）— 采集时机迁到「首批 feed 卡片」后，feed 上帖子作者/评论者的 `profile.php?id=` 链接曾被误当自我 id 候选 → `candidates conflict` → 读身份失败 → 昵称空（真机 3 次采样稳定复现）。已改 `deriveFacebookIdentity`：c_user 在场即权威自我 id、id 锚定取昵称、忽略他人链接。验：真实 feed（多帖子作者在场）启动后昵称仍就地读出、不再 conflict；无 cookie 多候选仍诚实 conflict。
- [ ] **闭环写库确认** — 运营机重启 edge 后：空昵称中文 FB 号（如 `61591803599213`）在云端首批 `page.cards` 采集回合内，dev `accounts.nickname` 由空落为「Nancy Terry」、控制台/客户端显真名。

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

### change `client-login-credential-persistence`（edge master **`183bf91`** 已 land，edge-only 无 ECS 部署，运营 / 客户机 pull master + 重建安装包后生效，登记于 2026-07-14 归档批）

登录门记住上次成功登录的 name+key（Electron `safeStorage` 加密落 userData，明文绝不落盘），下次开客户端自动回填；手工清空任一字段即忘掉旧值；退出登录 / 会话失效即清除。

**归档时的台账更正**：tasks.md 原先标注的 `7a07a78` **从未推到远端**（只活在本地分支 `codex/client-login-credential-persistence`）；主干上的等价提交是 **`183bf91`**（同标题，含 `test/electron/client-login-prefill.test.ts`、preload IPC、login.html 回填）。按「验收口径是主干上有等价行为 + 测试覆盖」，行为与测试均在 master 上，故照常归档。

- [ ] 61.18 打包态回填（主项，原 tasks 3.1）— 打包版客户端登录成功后关闭再开：登录窗 name+key **已自动回填**，直接点登录即进主界面。**必须在打包产物上核**（`safeStorage` 依赖系统钥匙串，且这条走 asar 红线覆盖的 login 窗）。
- [ ] 61.19 手工清空即忘 — 在登录窗把 name 或 key 任一字段手工删空：下次开窗**不得**把旧的那一对再填回来。
- [ ] 61.20 退出登录即清除 — 托盘 / 设置「退出登录」后回到登录门：表单是**空的**，不带出上一个客户的凭据（跨客户换人登录的安全面，与 61.2 同一红线）。
- [ ] 61.21 系统不支持加密时诚实降级 — 若 `safeStorage` 不可用（个别 Linux / 无钥匙串环境）：**绝不明文落盘**，行为退化为「不记住」，登录仍可正常进行。

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

### change `facebook-note-scoped-targeting`（edge master `cf8cb4c` + `3a4aeec` 已 land，edge-only 无 ECS 部署，需运营 / 客户机 pull master + 重建安装包后生效，登记于 2026-07-14）

FB 的点赞 / 评论过去不按命令的目标帖定位，而是靠「当前页」的隐式假设：信息流态点赞回落到 DOM 序第一个反应按钮（点错卡），评论编辑框 document 级取第一个（评错帖）。本 change 引入规范帖身份 `fb:<postId>` + 三段式解析（作用域 → 顶层非嵌套候选 → 身份匹配），绝不 DOM 序回落。**edge-only、零协议 / 零云端 / 零 console 改动，小红书零影响**。桩层已用真实注入产物（jsdom 跑页内脚本）复现并覆盖两轮对抗性评审的全部真问题（点错卡 / 评错帖 / 整类卡永久失败 / 假成功确认），以下为只能在真机坐实的部分——需 dev 车队 FB 互动号，且只能打 dev（OL 已转生产、FB 硬关）。

- [ ] 64.14 信息流点赞只命中命令指定的那张卡（主项）— FB feed 上让云端对**第 N 张卡**下点赞，CDP / 日志核：只有第 N 张卡的反应按钮翻转，前 N-1 张一动不动；绝不出现「面板说点了、翻转的却是首卡」。修复前正是首卡被误点。
- [ ] 64.15 目标帖不在当前视口 → 先拟人滚进视野再点，绝不瞬移 — 观测到一段连续 wheel 手势把目标卡滚进视口后才点击（点击脚本里无 `scrollIntoView` 瞬移）；滚不出来则诚实 `target_not_visible`、不对当前居中的卡下手。
- [ ] 64.16 同群 multi_permalinks 两帖不撞卡 — 同一个群里两条 `multi_permalinks` 形态的帖同时在页时，点赞 A 绝不落到 B（旧 postKey 会把两帖撞成同键）。
- [ ] 64.17 详情弹层只锁主帖，不误点评论级 react、不点背景 feed 卡 — 在 permalink 详情弹层（主帖 + 每条评论各一个嵌套 article + 背后 feed 还有同群卡）上，点赞只作用于顶层主帖；评论条目的「留下心情」绝不被当成帖级点赞。
- [ ] 64.18 评论绝不发到别人帖子下（红线）— 多编辑框页面（详情页 + 背后 feed 卡各带评论框）上发评论，只落到目标帖的评论框；目标帖作用域内无评论框时诚实 `editor_not_found`、绝不回落到别人帖子的框。**这是本 change 最关键的真机确认**：桩层已复现「弹层里开目标帖 + 背后 feed 有别人的帖」会把评论打进别人框、并已修复，真机需坐实修复生效。
- [ ] 64.19 无自定义用户名账号的卡照常能点赞 — 作者主页链接是 `/people/<slug>/pfbid…/` 形态（越南 / 老账号常见）的帖，点赞照常命中、不再因「作者链接抢了卡身份」而永久 `no_target`。
- [ ] 64.20 评论「服务器确认」不假成功、不假失败 — 真发一条评论：确认信号来自本人评论行上的服务器正式 comment_id 或点赞 / 回复控件（评论真出现在帖子下才算 ok）；帖子原本没有任何评论行时，绝不把编辑器里还没发出去的正文冒充成「已发」。
- [ ] 64.21 客户端需重建才生效 — edge 侧改动在 master（`cf8cb4c`+`3a4aeec`），运营机需 pull + 重新出包（或 canonical 跑 `electron:dev` 重启）后上述行为才存在。

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

## 簇 73

### change `client-preview-image-delete` 真机验收（客户端稿件预览逐张删配图，登记于 2026-07-14；cloud master `d0d8967` 已 land + **已部署 dev**，edge master `f32e8c3` 已 land、需重建安装包 / 从 master 起客户端）

**背景**：客户端稿件预览抽屉此前只读，客户遇到跑偏的一张配图只能带着坏图发或整稿取消。现在每张配图可单独删（协议 74→76 新增一对「删配图请求 / 应答」消息）。云端复用与管理后台**同一条**待审草稿乐观 CAS 单写通道（事务内行锁 + 版本比对 + 只删不注入），并补上后台路径**没有**的账号归属闸；新增「最后一张不可删」红线（下发段对零配图图文帖直接判 failed，spec `publish-image-required`）。桩测全绿（cloud 1946 + edge 1186 + 两侧 acceptance + typecheck），但下列真机行为桩验不了。

**前置**：客户机以 edge master（含 `f32e8c3`）起客户端并连 **dev** 云端（dev 已含 cloud `d0d8967`；两端协议计数须同为 76，旧云端不认新消息）；一个有待审图文稿（≥3 张配图）的账号。

- [ ] 73.1 预览里配图能真显示（非兜底态）— 打开稿件预览抽屉，配图缩略图**真的渲染出图**而不是一片「图片暂不可用」。（配图对象是对象级 public-read，理论上可读；但客户端从未被真机核过，若全是兜底态则删图功能等于瞎点。）
- [ ] 73.2 删一张 → 界面与真态一致 → 照常发布 — 删掉中间某张：该张消失、其余**保序**、「配图 N 张」计数同步减一；随即点「发布」**不弹版本过期**，帖子真发出且只带剩余配图（守「审的就是发的」）。
- [ ] 73.3 删封面（第一张）→ 第二张成为新封面 — 删掉首图后审批发布，实际发出的帖子以**新首图**为封面（封面由云端按保留列表首项重算）。
- [ ] 73.4 最后一张不给删 — 稿件只剩一张配图时，缩略图上**没有删除入口**且明示「至少保留一张配图」（服务端另有 `last_image` 拒绝兜底，端上藏按钮不是唯一防线）。
- [ ] 73.5 删图后原飞书审核卡失效 — 删图会把稿件版本 +1；此时去点**删图之前**发出的那张飞书审核卡，卡片应拒绝签署并提示到控制台审批，**绝不**按旧版本把稿子发出去。
- [ ] 73.6 与管理后台并发改同一稿 — 运营在后台删掉另一张后，客户端（仍持旧版本）再删：应诚实提示「稿件已更新」而**不是**误删或假成功；刷新后界面收敛到真态。
- [ ] 73.7 断连时诚实 — 拔网 / 停核心后点删除：提示「暂时没能连上云端」，该张配图**仍在**界面上（绝不先在本地抹掉再声称成功）。
- [ ] 73.8 删除在途不能审批 — 删除请求在途时，「发布 / 取消」按钮处于禁用态（防客户拿旧版本号去审批、撞版本闸看到莫名其妙的失败）。

## 簇 74

> change `honest-lease-failure-receipts`（cloud `860ff96`，2026-07-14 dev 已部署）。桩验不了的两件事：
> ① 真实的租约接管失败长什么样（要一台真的驱不动浏览器 / 处于冷待机的边缘）；
> ② 受理超时抬到 200s 之后，边缘为停泊账号原地重开浏览器这条路能不能真的走完。
> 触发条件现成：让某账号的日浏览配额打满（view 300/300）→ 冷待机自动收起浏览器 → 等排期评论开火。

- [ ] 74.1 **停泊账号的排期评论能真的唤醒并发出**：账号日浏览配额打满、浏览器进冷待机后，等一次排期评论开火。边缘应重开浏览器、云端在 200s 受理窗内拿到租约、评论真实发出（飞书绿卡）。回归前：云端 45s 就超时判死，浏览器一分钟后才起来、无人认领。
- [ ] 74.2 **控制面真故障时回执诚实**：把某环境的浏览器搞成「边缘在线但驱不动」（例如直接从 AdsPower 侧关掉分身、或让 CDP 输入卡死），再触发排期评论。飞书卡必须是「**按需评论未开始**」＋「未搜索、未选中笔记、未发布评论」＋原因写「浏览器控制面不可用」；**绝不能**出现「已选中」「发布未确认成功」「离线」字样。
- [ ] 74.3 **小时格被归还**：承 74.2，同一小时内应还能再触发一次（回归前该小时名额零动作白烧、不重试）。查 dev 云端日志里该账号的 `onScheduledTaskNotStarted` / `releaseHourCell`。
- [ ] 74.4 **定向评论同口径**：对一台驱不动浏览器的边缘触发一次定向评论（精选笔记行内动作）。终态卡必须是「定向内容评论未开始」，且**不点名任何目标笔记**（回归前它会说「目标笔记 XXX 评论发布未确认成功」，诱导运营去那篇笔记下找一条不存在的评论）。
- [ ] 74.5 **停泊唤不醒时归因可恢复**：若唤醒真的失败（180s 死线内没起来），回执应说「浏览器处于待机、未能在唤醒死线内起来（可恢复，稍后自动重试）」，与 74.2 的「控制面不可用」可辨识区分。

---

> **2026-07-14 编号更正**：本文件曾一度出现两组 `簇 65` / `簇 66`（两个并发 session 同日追加、各自取了同一个号）。原「下载页版本现扫」与「首次连接诚实标签」两簇已改号为 **簇 75** / **簇 76**（内容未变、只改号并移到文末保持单调）。若外部笔记 / memory 里仍写着「簇 66 = honest-first-connect-label」，以本文件为准。

## 簇 75

### change `downloads-manifest-from-host`（cloud master `38f3082` + console master `aa3461d` 已 land + **已部署 dev**，登记于 2026-07-14；原编号 65，2026-07-14 因撞号改为 75）

下载页安装包版本不再写死在 console 源码里，改由云端 `GET /api/downloads` **现扫该机 `/opt/aidcp/downloads` 目录**得出。桩层 + dev 真机已坐实（在 ECS 上对 dev 真实目录跑扫描 → `{version:"0.3.18", items:[mac 0.3.18 ×2, win 0.3.5]}`，`.bak` 与历史版本全部正确忽略）。以下为需在浏览器 / OL 上肉眼确认的部分。

- [ ] 75.1 dev 后台「下载客户端」菜单：显示 **v0.3.18**，三个条目可点、下载得到真实文件（不是 404）。
- [ ] 75.2 OL 后台（需用户明确要求才部署）：**同一份代码**部署过去后，下载页应自动显示 **v0.3.21**（OL 目录里真实存在的包）——这条是本 change 的核心主张「两台机器各说各的真话」的最终验收。
- [ ] 75.3 目录为空 / API 不可达时：菜单显示「暂无可用安装包」，**绝不出现任何下载链接**（红线：宁缺毋假）。
- [ ] 75.4 下一次发版（≥0.3.22）：只把 dmg 传到目标机的 downloads 目录，**不改任何代码、不重新构建 console**，页面即显示新版本 —— 用 `scripts/release-desktop-macos <版本> --yes` 走一遍确认。**注意**：下载页按 semver 取最高版，所以新包版本号必须真的高于该机已有的包，否则会被**静默忽略**（不报错、页面照旧）。

## 簇 76

### change `honest-first-connect-label`（edge master `416ed94` 已 land，登记于 2026-07-14；原编号 66，2026-07-14 因撞号改为 76）

启动窗口不再被讲成「正在重新连接」。桩层已坐实（两条冷启动断言在修复前必失败、两条真断线断言前后都通过），以下是需要在真桌面客户端上肉眼确认的部分。**注意：需重启桌面客户端才带上本修复。**

- [ ] 76.1 关闭某环境 → 点「启动」：从点下去到「运行中」之间**全程只见「启动中」**，绝不出现「正在重新连接」。窗口不短（AdsPower 起分身秒级到数十秒），足够肉眼看清。
- [ ] 76.2 同一窗口内，左侧环境栏该环境是**蓝色 launching**、不带「需处理」角标、**不浮到列表顶部**（回归前它会被染琥珀并挤到真正待人工的环境前面）。
- [ ] 76.3 运行中真断线（停一下 dev 云端服务，或断网几十秒）：仍如实显示「正在重新连接」+ 琥珀 + 需处理 —— 守住「别把真断线也一起吞掉」。
- [ ] 76.4 核心崩溃自动重起（或点「按新设置重启」）：重起的冷启动窗口同样只显示「启动中」，不因为上一轮核心连上过就冒充重连。
- [ ] 76.5 冷待机唤醒：唤醒**不**重新进入首次连接窗口（云端连接全程未断），直接回「运行中」。

## 簇 77

### change `edge-environment-platform-select`（edge master **`a2fac2a`** 已 land，edge-only 无 ECS 部署，运营 / 客户机 pull master + 重建安装包后生效；登记于 2026-07-14 归档批）

建环境时按环境选平台（小红书 / Facebook），落 AdsPower 备注的 `plat` 字段，启动时注入 `AIDCP_PLATFORM` 决定核心开哪个平台首页、握手上报哪个平台。旧环境 / 空值 / 未知值一律回落小红书（零回归）。

**归档时的台账更正**：tasks.md 原先标注的 `f311ec5` 是一个**不在任何分支上的悬空提交**（大概率是 rebase 后遗留的旧对象）；主干上的等价提交是 **`a2fac2a`**（同标题、同 8 文件）。按「验收口径是主干上有等价行为 + 测试覆盖」，行为与测试均在 master 上，故照常归档。

**原 gate 已解除**：tasks 2.3 曾 gate 在「Facebook edge driver 落 master」，该驱动已于 2026-07 落地（FB 建号 / 登录 / 浏览 / 发帖均在 master）。

**前置**：客户机以 edge master 起客户端（`electron:dev` 或重建安装包）；AdsPower 本地 API 可用；连 dev 云端。

- [ ] 77.1 建 Facebook 环境（主项）— 在建环境表单里把平台选成 **Facebook**，建成后左栏该环境显示 Facebook 平台标签；AdsPower 里该分身的备注含 `plat=facebook`。
- [ ] 77.2 启动打对平台 — 选中该环境点启动：核心打开的是 **facebook.com** 而非小红书；云端握手 `hello` 里 `platform=facebook`（查 dev 云端日志）。
- [ ] 77.3 旧环境零回归 — 一个本 change 之前建的老环境（备注里没有 `plat`）：仍被识别为**小红书**、启动仍打开小红书，不因缺字段被误判成 Facebook 或拒启。
- [ ] 77.4 手工在 AdsPower 侧建的环境（备注非本客户端格式）— 同样回落小红书，不报错、不拒启。

## 簇 78

### change `facebook-dev-autobrowse-enable`（edge master `5e23261` / `bce5a1b` / `cebde5d` / `7b9b37e` 已 land、需运营机 pull + 重建安装包后生效；cloud master `25379e6` 已 land + **已部署 dev**；登记于 2026-07-14 归档批）

dev 云端上按平台放开 Facebook 自动浏览，并把 FB 的会话 / 阅读 / 点赞边界如实投影到客户端 UI（失败与影子动作不计数、不与旧口径重复计数），阅读活动附带有界的作者与正文开头。

**建议与簇 69（FB 拟人滚动）/ 簇 72（FB feed 滚动与刷新修复）同一次真机 session 合验** —— 三者共用同一套前置（客户机 pull edge master + FB 互动号 headful + 连 dev + `AIDCP_FB_BROWSE_AUTO=on`）。

- [ ] 78.1 客户端有 FB 活动投影（主项，原 tasks 2.3）— 一个恢复运行的真实 FB 环境跑起来后，客户端右侧确实渲染出 Facebook 的活动 / 在场投影与该账号今日累计数，**不是空白**。回归前：云端「今日浏览」已从 1 涨到 5，客户端却完全没有 FB 活动投影。判过 = 客户端上看到的条数与云端该账号今日口径**对得上**。
- [ ] 78.2 只计已确认的动作 — 失败的点赞 / 影子动作**不进**计数；同一次点赞不被新旧两套口径重复计成 2（对比云端日志与客户端计数）。
- [ ] 78.3 阅读活动带得出内容 — 阅读条目上能看到作者与正文开头；取不到标识时诚实显示「无可用标识」而**不是**编一个。
- [ ] 78.4 平台闸只对 dev 开 — 同一客户端切到 **ol** 云端时，FB 自动浏览**不被启用**（该策略只允许 Facebook + dev）。

## 簇 79

### change `honest-core-log-severity`（edge master `2473b7e` 已 land，edge-only 无 ECS 部署，运营 / 客户机 pull master + 重建安装包（或 `electron:dev`）后生效，登记于 2026-07-14）

**背景**：客户端外壳把「核心日志走了哪根管子」当成了「这行是不是错误」——核心子进程的 stderr 通道被硬认成出错。可 Node 的 `console.warn` / `console.error` 本就写 stderr，核心里 34 个 `console.warn` + 25 个 `console.error` 大多是良性诊断。于是每来一条良性 warn，环境徽标就翻红、界面讲出「异常」/「运行异常」/「引擎已停止，请查看详情或重新启动」，该环境还被加「需处理」角标、浮到环境栏顶部，与真正待人工的登录 / 验证码 / 风控受限混作一谈——而核心根本没停，下一行正常日志一到又翻回绿（运营看到的「发布时闪红、又秒恢复」）。第二个受害面：良性 warn 会覆盖「最近一次失败」，等核心**真出事**时界面给的归因是最后那条**无关**的 warn。

**修法**：徽标只认核心**自己声明**的终态（白名单），不认通道。安全性由既有结构保证——核心里每条致命路径都必然退出进程，外壳退出处才是权威判据。桩层已坐实（两条契约断言在修复前的代码上实测 `pass 20 / fail 2`，修复后 22/22；全量 1296/1296）。以下为桩验不了、须真机肉眼核的部分。

**前置**：客户机以 edge master（含 `2473b7e`）起客户端（`electron:dev` 或重建安装包）；**建议与簇 76（首连诚实标签）、簇 64（人设三态）同一次重启合验**——三者都只需重启一次客户端。

- [ ] 79.1 发布全程不闪红（主项）— 跑一次完整发布（排期 → 人审 → 边缘发布）：该环境徽标**全程不翻红**，健康结论保持「运行中」，不出现「闪红又秒恢复」。回归前：发布路径上租约抑制说明与 `[publish-submit-diag]` 诊断必现，每条都闪一次红。
- [ ] 79.2 槽位排队不再被讲成「引擎已停止」— 让某环境撞上浏览器槽位排队（多环境同时启动、槽位不够）：核心打印「外壳暂时给不出浏览器槽位…环境仍在等槽位队列里」时，该环境**不得**变红、**不得**被加「需处理」角标、**不得**浮到环境栏顶部；在场文案**不得**出现「引擎已停止」。
- [ ] 79.3 真启动失败仍如实翻红（红线：不吞真失败）— 故意制造一次真失败（如断网让连云失败、或让 AdsPower 拒启）：徽标**仍然**翻红，「需处理」角标仍在，失败详情给出**真实**原因。
- [ ] 79.4 「边缘在线但浏览器驱不动」仍报得出来 — 把某环境的浏览器搞成 CDP 输入卡死（复用外部浏览器那条分支，核心不退出）：徽标**仍然**翻红并提示需人工重启浏览器。这条是白名单里唯一「核心不退出」的终态，少了它这个哑状态就没人报——必须专门验。
- [ ] 79.5 真崩时归因是真失败行 — 让核心先打印若干良性 warn（发布诊断 / 排队），随后真崩溃退出：详情里显示的「失败原因」是**真失败行 / 退出码**，**不得**是那几条无关的良性 warn。回归前必错。
- [ ] 79.6 日志文件仍留痕 — 查该环境的日志文件：走 stderr 的行**仍带 `ERR` 标记**（传输事实要如实记录，只是不再被误读成语义）。排障回溯能力不得因本次修复而削弱。

## 簇 80

### change `standby-covers-idle-waits`（cloud master `33934d6` + `d83cb45` 已 land + **dev 已部署**；edge master `5b9b5b9` 已 land，客户端 pull master 重启后生效，登记于 2026-07-14）

**背景**：系统里有两套判断，各干各的、从不说话——一套决定「这账号还要不要接着干活」（周历排期 / 活跃时段窗口 / 每日场数与分钟上限 / 风控状态），另一套决定「要不要关浏览器、让出槽位」，而后者**只看浏览配额有没有耗尽**。于是因「配额用完」停下的账号会关浏览器，因「排期到点」「今天时长跑满」「账号被冻结」停下的账号，浏览器一直开着占 700MB——直到明天，或者永远。**冻结**最讽刺：等待最长（唯一出口是运营手动改状态，状态机的自动恢复函数全仓无人调用、也从不发恢复信号），却被旧判据当成「没有确定恢复时刻的硬阻塞」判成「等待 0 分钟、不用让位」——**越是不该占着浏览器的，占得越牢**。旧单测把这个 bug 写成了断言。

**修法**：判据从「有没有确定的恢复时刻」换成「**解除这个阻塞需不需要浏览器**」（验证码 / 登录 / 人工介入需要；冻结 / 排期外 / 时长满不需要）。门槛 20min → 5min（两端同改——边缘取两者较大值，**只改一端不生效且无任何报错**）。无恢复时刻的阻塞给「回访」`wakeAt`（6h，语义是「多久后回来再问一次」，不是恢复承诺）。加最短持有时长 3min 防抖动。桩层：cloud 2017/2017、edge 1283/1283、typecheck 均 0 错。以下为桩验不了、必须真机核的部分。

**前置**：dev 云端已含 `33934d6` + `d83cb45`；客户机以 edge master（含 `5b9b5b9`）起客户端。**建议与簇 79 / 76 / 64 同一次重启合验**。

**⚠ 补丁 `d83cb45`（验证码安全回归，务必带上）**：`33934d6` 只接了判据的一半——「解除阻塞**不**需要浏览器」那半有证据，「**需要**浏览器」那半**没有任何输入**。后果：边缘上报验证码 → 风控把账号打成 `restricted` → 续场闸判停工 → 待机闸判「可以让位」→ 而界面快照这条链**有意豁免**验证码暂停闸（它是界面数据、不是页面命令）→ 提示照常送达 → **运营正被要求去解验证码的那个浏览器被关掉**。边缘侧的浮层标志不是防线（会被「浏览循环结束」清掉）。`d83cb45` 由云端权威（该边缘是否处于验证码暂停态）填这一半，且压在**所有**来源之前一票否决。**验 80.5 时若客户端跑的是只含 `33934d6` 的云端，那条必然失败——那不是新 bug，是这个已修的回归。**

- [ ] 80.1 **冻结账号让位后，人工解冻能自动醒来（红线，最危险的一条）** — 在后台把某账号风控状态改成 `frozen`：该环境应在 ≤5 分钟内关闭浏览器、让出槽位（客户端左栏显示「浏览器已关闭，云端连接保持中」），而**引擎与云端连接不断**。随后在后台把状态改回 `normal`：该环境应在 **≤60 秒内自动唤醒**、浏览器重开、恢复浏览。**桩测只能证明提示发出，证明不了端到端真的醒来。** 若不醒 = 我们把一个 700MB 的浪费换成了一块砖，必须立即回滚门槛（`AIDCP_BROWSER_COLD_STANDBY=false` 可秒关整个特性）。
- [ ] 80.2 排期外真的让位 — 给某账号配一个窄的活跃时段窗口（如只在未来 10 分钟内活跃），等窗口关闭：该环境应关闭浏览器让出槽位，提示来源为 `session`、`wakeAt` = 下一个窗口开始时刻；到点前 90 秒应自动热身唤醒。
- [ ] 80.3 每日时长跑满真的让位 — 让某账号（尤其 FB，默认每日在线 6h）跑到每日时长上限：应关闭浏览器，`wakeAt` = **下一个服务器本地日界**（不是上海日界——两套日界并存，进程 TZ ≠ Asia/Shanghai 时混用会算错）。**dev 的 TZ 已核实 = `Asia/Shanghai`（`.env` 也未覆盖 `TZ`）**，故两套日界在 dev 上**恰好重合、这个分歧在 dev 上根本显形不了**——在 dev 验过 ≠ 验过。真正要防的是**换机 / 换机房 / 显式设 `TZ`** 时算错恢复时刻。**验法**：要么在别的 TZ 下起一次云端，要么退而求其次读代码确认算续场额度恢复时刻走的是本地日界、不是上海日界。
- [ ] 80.4 **不频繁开关（用户明确要求）** — 观察一整天：统计每个环境的「关闭 / 唤醒」次数。排期外 / 时长满 / 冻结这三类等待都是小时级，**一天应各只关一次、开一次**；配额类可能多几次。若出现某环境一小时内反复开关 = 最短持有时长闸没生效，查 `min_hold` 是否被记录。
- [ ] 80.5 需要浏览器才能解除的阻塞**仍然不让位**（红线：不能把闸开太大；`d83cb45` 修的就是这条）— 让某账号卡在验证码 / 未登录：**MUST NOT** 关闭浏览器（运维要在那个浏览器里操作）。这条防的是「为了腾槽位把运营手指底下的浏览器关掉」。**关键姿势**：必须让验证码停留到风控把账号打成 `restricted` **之后**再观察（那才是回归的真实触发路径）；同时验「验证码解除后能恢复正常让位」——一票否决闸 MUST NOT 永久禁用让位。
- [ ] 80.6 槽位真的轮转起来了（本 change 的目的）— 在一台槽位不足的机器上挂满账号：应能观察到「A 停工让位 → B 从等槽位队列被叫起来」的完整交接。这是「一台机器能挂更多账号」这个能力是否兑现的唯一直接证据。

## 簇 81

### change `presence-terminal-honesty`（edge master `84267f2` 已 land；客户端 pull master 重启后生效，登记于 2026-07-14）

**背景**：客户端「在场感」这一行是**最后一条被识别出的动作旁白**的覆盖式投影——每来一条动作指令顶掉上一句，**没有任何机制在「不再干活」时把它擦掉**。现网实况：运营看到它停在「顺路去作者主页看看…」、标签写「刚刚更新 · 2 分钟前」，而执行端其实一步没在做。三个已修的缺陷：① 取值顺序把「新鲜的中途动作文案」排在「已算得出的终态文案」前，而同屏探索进度卡顺序恰好相反（先判今日是否完成）——同一份数据下两块 UI 互相打脸最长 5 分钟；② 不满 5 分钟的旧文案照带「刚刚更新」+ 呼吸动效，等于宣称**此刻**正在做，实际是执行端已做完、球在云端（进主页后要过一次大模型定夺是否关注，单次上限 180s）；③ 云端断连只翻云端徽标，在场感继续演。

**修法**：终态优先（依据只认云端下发的当日额度窗口，拿不到依据就不出终态——客户端绝不自行推断「今日已完成」）；「新鲜」拆成两段（1 分钟内说「刚刚更新」+ 动效，之后保留文案但停动效、改说「已等待 · N 分钟」）；断连改写在场感。桩层：edge 1339/1339、typecheck 0 错。以下为桩验不了、必须真机核的部分。

**前置**：客户机以 edge master（含 `84267f2`）起客户端。**建议与簇 80 / 79 同一次重启合验。**

- [ ] 81.1 **今日额度跑满时两块 UI 同口径（本 change 的直接目的）** — 让某账号跑到当日浏览额度上限：探索进度卡说「今天先到这里，明天继续」的同时，**在场感行必须也是「今日内容探索已经完成」**，MUST NOT 还挂着「顺路去作者主页看看…」这类中途动作文案。这是用户报的那一屏，桩已锁死判定逻辑，但「云端当日额度窗口真的下发下来了」只能真机证。
- [ ] 81.2 **额度未满时绝不自称今日完成（红线：不静默假成功）** — 额度没满、执行端长时间无新事件时，在场感 MUST NOT 出现任何「今日已完成」的字样。桩测只能证明拿不到额度依据时不出终态；要防的是真机上云端下发了**残缺**的额度窗口而客户端误判成已满。
- [ ] 81.3 「已等待 · N 分钟」如实走字 — 进作者主页后云端要过一次大模型定夺是否关注：观察在场感应在约 1 分钟后**停掉呼吸动效**、标签从「刚刚更新」变为「已等待 · N 分钟」，文案本身保留（运营仍需知道最后推进到哪一步）。动效是「此刻正在做」的视觉承诺，停不掉 = 修复没生效。
- [ ] 81.4 断连时在场感不再演戏 — 把客户端与云端断开（停 dev 云端或断网）：在场感应改写为「与云端连接中断，正在重连…」，MUST NOT 继续显示断连前的中途动作文案；**恢复连接后应翻回**（`云端已重连` 在翻译规则表里没有条目、不会自己被顶掉，靠本次在 `main.cjs` 补的翻回；若卡在「中断」不动 = 翻回没生效）。

## 簇 82

### FB feed 就地读 + 就地赞 灰度真机验收（C2 `facebook-feed-inline-browse` + C3 `platform-vocabulary-and-thresholds`；edge master `bae3ad4` + cloud master `22dede9`/`c04051e`/`695d5f3`/`1cfddb5` 均已 land + 已部署 dev，登记于 2026-07-15；**原编号 66/67/68/69 四处，2026-07-15 因撞号（66-69 已被 compress-admin-upload-images / edge-cdp-health-recovery / edge-task-acquire-timeout-recovery / facebook-humanized-scroll 占用）合并改为本簇 82**）

**背景**：Facebook 浏览闭环从「进详情页才能读 / 赞」改成「首页就地展开读全文 + 就地逐帖点赞」（读=feed / 赞=feed，评论仍 detail ⇒ 回执驱动两步迁移）。云端命令侧已开（对声明 `inline_targeting` 的重打包边缘下发 `surface:'feed'`），但**要不要真点由边缘启动 env `AIDCP_FB_BROWSE_AUTO` 决定**（off / shadow / on），硬闸是「先影子后真开」。这一整套只在真机 + 观测窗才验得了：桩测证了控制流与协议装配，证不了真实 DOM 上的展开 / 锁卡 / 两步点赞 / 独立见证一致率。C3 同批把浏览闭环 prompt 平台化（去「小红书/笔记/收藏」）+ 门槛放宽（FB 现对 300+ 赞正常帖评论、不再只万赞）+ 补语言规则（当地语言、不丢中文评论）+ 空正文诚实提示——这些措辞 / 门槛效果同样只能真机肉眼核。

**修法（已 land 部分）**：edge `bae3ad4`（inline-reader / 两步 feed 点赞 / surface·purpose 路由 / 就地读停留地板 / feed 光标只报新顶层卡 + feed_exhausted / 独立见证）；cloud `22dede9`+`c04051e`（版本偏斜能力闸 `effectiveReadSurface` + 翻 registry read/like=feed + 回执驱动两步评论迁移）；cloud `695d5f3`+`1cfddb5`（C3 词汇平台化 + 门槛平台化修 FB 评论恒关 bug + deep-read 空正文 + 撰写器去硬编码 + 语言规则 + 评论进撰写）。4×N 路对抗评审全 SAFE。以下为桩验不了、必须真机核的部分。

**前置**：dev 云端已含上述 cloud 提交；**客户机以 edge master（含 `bae3ad4`）重建客户端**（就地读 / 两步赞只随重打包边缘声明 `inline_targeting` 才收到 `surface:'feed'`，老包逐位等今天）；用 tom 分组测试号（大白 / Tmax，见 memory `real-machine-test-accounts`）；`AIDCP_FB_BROWSE_AUTO` 分档跑：先 `=shadow` 后 `=on`。**硬前置铁律**：82.3 影子见证 100% 一致 + `no_target(stale)` 率 <10% + 82.1 feed 连续性通过，**才**可切 82.4 真点赞。**真开前**须把 FB like 从 edge 的 `RETRIABLE_INTERACTION_REASONS` 移除（避免对可能已赞的两段 toggle 二次点成撤销）。**回滚不需重发客户端**：cloud registry read/like 改回 `'detail'` 重部署 dev，或边缘 `AIDCP_FB_BROWSE_AUTO≠on`。

> **⚠ 首跑真机结论（2026-07-15，dev，FB 号 Tianxing Bai `ads-k1ei3dbi`，客户端 GUI mode=on）：82.1 feed 连续性直接不达标，把下游全饿死。** 观测法：客户端 GUI 车队日志 `~/Library/Application Support/aidcp-edge/logs/edge.log` + dev 云端 journal。硬数据（约 14h 断续活跃窗口）：FB 号每次 `page.cards` **恒为 1 张**（3 次全 `上报 1 张`）、每次都 `scroll settle degraded`（3 次）、就地读全文**仅 1 次**（越南语群帖 👍0、正文 1408 字，证明就地读机制本身没坏）、点赞执行器 `fb-like` **调用 0 次**、`like` 计数**恒 0**、`view` 仅 1。云端 journal 侧对应：15+ 分钟**每一条命令都是 `action=scroll`**，零 `note.open`/零 `like` —— 即 memory `note-open-miss-livelock` 的「只刷不点」活锁。**同一客户端上的小红书号（`ads-k1e0ero8`）闭环完全正常**（每次报 10-11 张、note.open/scroll_comments/browse_images/feed.refresh 齐全），故非通用回归、是 **FB feed 扫卡专属缺陷**。
>
> **根因定位**：`settleCards`（edge `src/facebook/feed-reader.ts:348-376`）稳定判据＝「连续两轮 `scanCards` 的 noteId 集合完全相等 ∧ 无 loading 信号 ∧ ≥minCards 真卡」；`scanCards`（`:300-320`）只收「`hydrated===true` ∧ 有 permalink」的卡。FB 此 feed 每轮只提取到 **1 张合格卡且轮间还在变** → 永达不到「连续两轮相等」→ 耗尽 wall-clock 走 `degraded=true` 的 1 张真抽兜底（`:373`）。**待定谳**：是该账号 feed 真稀疏（群组页 / 越南语 / 冷号），还是 `scanCards` 的选择器 / permalink 提取在此 feed 布局上漏掉了大多数顶层卡——需连实时 DOM（浏览器 CDP，运行中端口见 AdsPower `browser/active`）比对「页面真有几张顶层 article」vs「scanCards 提取几张」才能最终区分「环境稀疏」与「扫卡器 bug」。**归属**：交叉 memory `fb-feed-never-scrolls-down`（簇 72，settle 判稳的 fix 已 land 但在此 feed 未达成稳定多卡快照）。**未落 change**——下一步＝开 edge change 深挖 `scanCards`/`settleCards` 在真实 FB feed 上的鲁棒性（先 CDP 取证再定是放宽稳定判据 / 修选择器 / 还是环境问题）。
>
> **本次未跑到的部分**：影子档（82.3）——GUI 路径 `fleet.cjs:88` 硬编码 dev-FB→`on`、`shadow` 够不着（需加 toggle，见下）；独立起核心跑 shadow 会与正在跑的 GUI 抢同一分身（CDP 端口漂移致核心掉线，本次已实测）。**要跑纯影子必须先给 `facebookBrowseModeFor` 加「dev-FB 显式降档 shadow/off」toggle**（对 ol/custom 仍强制 off、保 anti-leak），再让 GUI 带 `AIDCP_FB_BROWSE_AUTO=shadow` 重启。但当务之急是先解 82.1 扫卡缺陷——feed 都出不来多卡，影子见证无从谈起。
>
> **✅ 二跑更正 + 修复（2026-07-15，独立受控核心，用户在客户端关掉 Tianxing Bai 移出车队后起独立核心 mode=on）：上面「首跑」把根因扣给「扫卡缺陷/settleCards」是误判。** 只读 CDP 取证定谳（`timeOrigin` 每 ~8s 重置 + `window` 标记被清 + 顶层 `frameNavigated` 无 script 发起标记 = 命令式整页导航）：①**扫卡没坏**——静止态能稳定收 3 张卡、permalink 提取正常；②「上报 1 张」多半是**去重**在正常工作（滚 650px < 帖高 ~900px，重叠大→每滚 ~1 张新卡，如实上报）；③**真根因是 `ensureFeed` 的 `&& !dialogOpen` 守卫**——FB 首页常挂**瞬时良性 `[role=dialog]`**（聊天弹窗/加载态/通知提示），旧判据把它当「不在 feed」→ **每条 scroll 命令都整页 `Page.navigate` 重载**（经 `fbsbx.com/maw_proxy_page` 重定向回首页）→ feed 反复被钉回顶部、永远下不去（＝用户长期看到的「一直刷新」）。**已修（edge `fb8c5b3`，master，change `facebook-feed-dialog-and-lazyload-refresh-fix`）**：去掉 dialog 守卫 + feed_exhausted 改懒加载感知（scrollHeight 增长/接近底部/连续确认）。真机验证修复后 26s：timeOrigin 恒定/零重载、scrollY 持续下滚、scrollHeight 懒加载追加、ensureFeed 整页导航仅启动 1 次、feed_exhausted=0。见 memory `fb-feed-dialog-guard-reload-churn`。
>
> **⚠ 点赞仍 0 = 独立问题（未解，与刷新无关）**：二跑观测到就地读**working**（多次 note_open、view 递增），但云端每次 open_note 后只跑 `concept_extractor`+`content_curator` 就回 scroll、**从不发 like**。链路：`content_curator`（质量粗筛，消费 `note.detail.arrived`）判「不够相关/疑广告」→ `quality.reject` → 深读→评论→`reading.done`→`interaction_appraiser`（点赞判定，消费 `reading.done`）整条链不启动；FB 点赞还额外需 `facebookQualityPassedNoteIds` 门（role-dispatcher `facebookNaturalInteractionEligibility`）。**该号人设其实对口**（读出来是「河内求职者 Minh Anh」，兴趣正是招工帖），故更可能是**粗筛 prompt 对带电话/Zalo 的越南语招工帖偏保守当广告拒**（content-curator-role.ts buildPrompt「纯广告/带货导流→close」）。待办：核 content_curator 真实判定（journalctl grep `[content_curator] LLM 判定`，越南语的即 FB 的）、评估放宽粗筛 / 或换更对口 feed。

- [~] 82.1 **feed 连续性（原簇 66）** — **【2026-07-15 二跑：根因更正 + 已修，见上 ✅】** 首跑「扫卡缺陷」误判已推翻；真根因＝`ensureFeed` 的 dialog 守卫致每条 scroll 整页重载（「一直刷新」），已修 edge `fb8c5b3`（change `facebook-feed-dialog-and-lazyload-refresh-fix`）。真机 CDP 验证「不整页回顶重载 + 一路下滚 + 懒加载追加 + feed_exhausted=0」达标。**剩余待办**：客户端重打包后由运营肉眼复验「浏览器不再刷新」（出包按惯例默认不做，等显式发版）。原验收点仍成立：`page.cards` 只报新顶层卡、深度到阈值受控换批、零新卡有界滚动 `feed_exhausted`、被接管到群组页 `listKey` 不匹配不采纳。交叉 memory `fb-feed-dialog-guard-reload-churn` / `fb-feed-never-scrolls-down`。
- [ ] 82.2 **就地读质量（原簇 68；shadow 即可验）** — 边缘 `=shadow` + 开关已开：统计 `expand_no_effect` 率、正文完整率（就地 textContent 捷径 / 点展开是否拿到全文）、**导航次数是否归零**（不再进详情页读）、view 速率、like-view 比。查 journalctl（cloud dev）关键字 `observedSurface 漂移` / `feed-surface 互动 no_target`。
- [ ] 82.3 **影子点赞见证一致（原簇 66/68；真开的硬前置）** — 边缘 `=shadow` ⇒ 云端下发 `surface:feed`、边缘就地锁卡**不点**、回执带独立见证（page-derived postId / author / 正文头 / reaction / articleIndex）。核：影子见证与云端选中卡是否 **100% 一致**、`no_target(stale)` 率 **<10%**、顺带采 P4 已赞态串。见证不一致或 no_target 高 = 绝不可切真点赞。
- [~] 82.4 **真点赞（原簇 68）** — **【2026-07-15 三根因定位 + 修复 + 真机端到端验证，见下 ✅】** 达标后切 `AIDCP_FB_BROWSE_AUTO=on`：FB feed 就地逐帖真点赞（两步 = 中性按钮点击 → reaction 浮层里点「赞」；单击直翻则跳过第二步）。核：真点成功（`isReactedState` 认「从…移除赞」串）、**MUST NOT 对已赞帖二次 toggle 成撤销**、detail 路径逐位不变。
  > **✅ 两步提交真机根因修复（edge `b4ac517`，master，change `facebook-feed-like-picker-commit-fix`）**：先修云端点赞闸竞态（`56112be`，见上）让 like 真被下发后，暴露出边缘两步提交**从不生效**（恒 `state_unchanged`）。真机 A/B 实证三重根因：① **picker-commit 全文档搜 `/^赞$/`**——feed 每卡 Like 按钮 aria-label 亦「赞」、浮层是 portal 排在所有卡之后 → 目标**非首卡**时点到上方别的帖（点错卡红线 + 目标浮层永不提交）；目标恰为首卡才碰巧撞对（＝之前偶发「首帖成功」的真相）。② **浮层反应项监听真实指针事件**——in-page `element.click()` 只发 `'click'` 被 FB 当 hover 忽略（`clicked=true` 但反应不生效），CDP 坐标 press/release 才真提交（直接「赞」按钮反而吃 click——FB 逐控件事件机制不一致，见 memory `fb-flyout-needs-coordinate-click`）。③ **坐标点击要求元素在可视视口内**——长招工帖只把文章顶滚进视口，按钮/浮层落在折叠线下（cy≈1372>vh≈1002）→ 坐标点空。**修法**：picker-commit 只在打开的浮层 dialog 内定位「赞」项坐标（scoped）→ `dispatchClick` 坐标点击 → `scrollTargetIntoView` 改滚 react 控件 + 视口内守卫。**真机验证**：用真实 `FacebookLikeExecutor` 驱动活页非首位帖（articleIndex=2）→ `✓ 点赞成功`、仅目标帖翻转、别的帖不动。jsdom 坐标落点回归测试 + 两步桩测更新，edge 全量 1348 + acceptance 20 + typecheck 绿。**⚠ 未上运营机**：edge 客户端代码，需重打包（默认不做、等显式发版）。
  > **RETRIABLE 移除 FB like（原硬前置）——证据分析：不再是硬 blocker**。原顾虑「state_unchanged 重试 → 对已赞帖二次 toggle 撤销」。修复后 `state_unchanged` 已是**可靠的「真没赞上」信号**：成功提交后 FB 在 ~300ms 内把按钮翻成「移除赞」，verify 有 2s 轮询窗必然抓到 → 返回 ok（不重试）；只有真没赞上才 `state_unchanged`。且重试路径的 `already_liked` 闸（locate 见「移除赞」即不点）是第二重保险。故 `RETRIABLE_INTERACTION_REASONS` 含 FB like 现**安全**、可保留（有界重试真·transient 失败反而有益）。若仍要 belt-and-suspenders 移除，是**共享路径**（cloud role-dispatcher，like+collect / FB+XHS 共用），须平台感知改、勿一刀切砍 XHS 重试。**灰度 stage 5 前置**：「开真赞」仍须先过 82.1 + 82.3。
- [ ] 82.5 **探针残项（原簇 67）** — 跨入口 / 跨会话 postId 身份一致；群组 `multi_permalinks` 表单形态（首页 feed 上没有）；真实 pointer 序列是否绕过两步 picker。
- [ ] 82.6 **C3 词汇 / 门槛 / 语言 真机核（原簇 69）** — FB 会话跑一轮：① 浏览闭环 prompt 无「小红书 / 笔记 / 收藏」幻影、用「帖子」；② 门槛放宽生效（FB 对 300+ 赞正常热度帖评论、不再只万赞），仍过人审（除非账号 `auto_approve`，见 memory `auto-approve-and-persona-unbind`）；③ **语言规则生效**——当地语言的 FB 群里产出的评论用当地语言、MUST NOT 丢中文评论进去；④ FB 空正文图片帖：撰写诚实（就着评论区语境写 / 没有可写就弃权），MUST NOT 臆造画面内容。
- [ ] 82.7 **冷启动爬坡摘除后浏览额度真机核（change `disable-account-age-coldstart-ramp`；cloud master `2c3d6e5` 已 land + 已部署 dev，登记于 2026-07-15）** — 账号年龄冷启动养号爬坡由「默认开」改「opt-in（默认关，`AIDCP_COLDSTART_RAMP=true` 才启用）」，新号浏览不再被 FB 曲线第 7 天 `view=70` 压低、直接走 `quota_config` 安全限额。dev 启动日志已确认「冷启动配额爬坡 已禁用」。**待真机核**：① FB 号 `61591753702668`（aggressive 档，7 天内新号）**能实际浏览超过 70**、逼近其档位安全日 view（现 `quota_config` aggressive daily=500，小时突发 per_hour=24）；② warned/restricted 账号的互动清零 / 缩放语义不因摘冷启动而放宽。（**已闭**：原提示的 aggressive `per_hour=12` 疑似倒挂，运营 2026-07-15 17:21 自行在后台 `/quotas` 调为 `24`；小时突发仍是 aggressive 号浏览的主约束，如需更宽由运营再调，本 change 不动配额数字。）**回滚**：dev `.env` 加 `AIDCP_COLDSTART_RAMP=true` + restart 即恢复养号爬坡。

- [ ] 82.8 **搜索行程有界化真机核（change `bounded-search-excursion`；cloud master `151462c` 已 land + **已部署 dev** 2026-07-15）** — 修「FB 号在搜索结果页无限打转不回首页」（首跑观测：Tianxing Bai `61591753702668` 在全站 `/search/posts/` 招工帖流里读一篇→pass→滚→换词再搜，几十分钟不回首页）。三段闸：**①首页更耐心**——`SEARCH_THRESHOLD` 5→20，首页连续 20 屏无收获才转搜索（FB ~1–3 卡/屏，20 屏≈20–60 卡、落在 60 卡刷新阈值内 → 搜索仍会触发）；**②页型自指 bug 修好**——真正下发搜索才把页型标 `search`（被限频/预算闸拦下的搜索不误翻转），于是搜索结果页由 `SearchScroller` 正确驱动、搜索卡不再计入 feed 深度；**③搜索行程有界退出**——搜索结果页累计划过 20 张不重复卡（env `AIDCP_SEARCH_HOME_RETURN_AFTER`）→ 回首页（复用 `refresh` 指令、`reason=search_home_return`），空转（一篇都点不开）照样计卡、同样回首页不卡死。**观测法**：dev 云端 journal grep `search_home_return`（应看到「搜索行程累计 N 张卡 ≥ 20 → 回首页」）+ 客户端 `edge.log` 看该号是否不再长时间钉在搜索页、feed↔搜索往复有界。**真机核**：① 首页确实更耐心（20 屏才搜）；② 搜索页读到约 20 张卡就回首页、不再几十分钟打转；③ `sourcePageType` 修好后 `SearchScroller` 真被激活（搜索页翻页/换词由它驱动，不再被当 feed）；④ **XHS 副作用**——XHS ~10 卡/屏，20 屏≈200 卡 > 60 卡刷新阈值 → XHS「首页自动搜索」会变很稀（刷新先触发），核实这是否可接受、要否把阈值做 per-platform。**回滚**：env `AIDCP_FEED_SEARCH_THRESHOLD` / `AIDCP_SEARCH_HOME_RETURN_AFTER` 秒调。**交叉**：memory `bounded-search-excursion`；与 82.4「点赞仍 0」同根的 content_curator 保守问题正交（用户 2026-07-15 已从该号人设移除 Zalo/联系方式判定以放宽互动，另行观测）。

- [ ] 82.9 **FB 评论审批卡「回调失败」修复真机核（热修 cloud master `f5b6fc9` 已 land + **已部署 dev** 2026-07-15；无独立 openspec change，直接热修）** — 修「FB 评论审批卡（待审核评论）点『同意发布』飞书报回调失败、评论发不出」。根因＝Facebook 的 noteId 是**完整帖子 URL**，评论人审 requestId `comment-<noteId>-<ts>` 把 URL 的 `/` 带进 `/tmp/aidcp-publish-approve-<requestId>.json` 落盘路径 → posix.join 造出不存在的子目录 → `writeFile(wx)` 抛 ENOENT → 回调 handler 抛错回「处理审批回调失败」；读侧撞同路径 → 即便点同意也读不到、评论按 `approval_timeout` 丢（XHS noteId 是短码故只 FB 中招；生产日志指纹 `处理卡片回调失败: ENOENT ... /tmp/aidcp-publish-approve-comment-https:/www.facebook.com/thekdaily/...`）。修法＝新增 `buildCommentApprovalRequestId` 单一出口把 noteId 归一到 `[A-Za-z0-9_-]` 再拼（两生成点 `comment-approval-gate.ts`/`compose-approve.ts`；cloud-only，评论信号云端独写独读、边缘不碰）。dev 已用生产真实 URL 跑通：新号 flat、`writeFile(wx)` 不再 ENOENT。**观测法**：dev journal grep `处理卡片回调失败`/`ENOENT`（部署后**新卡**点同意应不再出现）。**真机核**：① 运营对一张**部署后新弹**的 FB 评论审批卡点「同意发布」→ 飞书回成功 toast、不再回调失败；② 评论真发到该 FB 帖（不再 `approval_timeout` 丢）；③ 拒绝/超时语义不变。**⚠ 关键提醒**：部署前已发出的**老卡**（requestId 已烤入 URL）再点仍失败——老 requestId 改不了，只有部署后**新生成**的卡才带安全 requestId，验收须用新卡。交叉 memory `fb-comment-approval-requestid-url-enoent`；与 82.6 人审门槛正交。

- [ ] 82.10 **FB 自动热帖评论迁移在途"上锁" + 慢详情页探测窗放宽真机核（change `fb-comment-migration-hold`；cloud master `865a788` 已 land + **已部署 dev**、edge master `678bdc6` 已 land**待客户端重打包/本地重跑**，登记于 2026-07-16）** — 修「FB 自动 feed-inline 热帖评论时浏览器闪一下群帖地址又秒回首页、已批准评论被静默丢」。真机现场：dev FB 号 `61591753702668`（`ads-k1ei3dbi`）当日 6 次授权丢 1（`groups/1684192411910736`，14:26:35 `open_failed`）。**两正交根因两处修**：①**云端**（`role-dispatcher` 迁移在途以 `pendingMigration` 为闸抑制一切离页 browse/互动命令、只放行本支线自身的迁移 `open_note{navigate}`+`comment`）——去掉"迁移落地前后并发 scroll 经 `ensureFeed` 把浏览器拽回首页"；②**边缘**（`post-reader` 详情探测窗 `surfaceProbeRounds` 14→22，~12s→~18s）——**这才是当日那次掉评论的直接因**：FB 详情正文水合 7–12s > 旧窗 ~12s 上界，慢一拍即误 `open_failed`。**观测法**：dev journal——迁移在途（`pendingMigration` 置位后）不再穿插 `action=scroll`、`评论迁移 navigate 失败 … open_failed` 显著减少；`edge.log`——评论迁移期间不再出现 `ensureFeed 判非目标→整页导航 … surface=group_post` 的中途拽回。**真机核**：① 热帖评论迁移期间浏览器**不再"闪群帖地址又回首页"**（cloud 那半 dev 已生效、单独即可去掉 mid-migration 拽回）；② **慢水合详情页（>12s）评论能发出、不再误 `open_failed` 丢评论**（**须客户端含 edge `678bdc6` 重打包/本地重跑**才有放宽的探测窗，老包仍 ~12s 窗）；③ 评论支线暂停/看门狗终局正常解除、会话不钉死（`pendingMigration` 已在所有终局清空）；④ **XHS 零回归**（读评 surface 相等、迁移结构性不可达，本闸走不到）。**前置**：dev 云端含 `865a788`（已部署）；客户机以 edge master（含 `678bdc6`）重建客户端；用 tom 分组 FB 号（同 82 前置）。**⚠ 分半生效**：cloud 那半已 dev 独立生效；edge 探测窗放宽须重打包（默认不做、等显式发版）。**回滚**：cloud 恢复 `/opt/aidcp/cloud/src/orchestrator/role-dispatcher.ts.bak.20260716-161751` + restart；edge 改回 `surfaceProbeRounds: 14`。交叉 memory `fb-auto-comment-migration-lease-hole` / `fb-feed-dialog-guard-reload-churn`；与 82.6 人审门槛、82.9 审批回调正交。

- [ ] 82.11 **FB 评论链路详情水合窗补齐 + 开帖步超时放宽真机核（change `fb-comment-open-hydration-window`；edge master `ff6c1e1` 已 land + dist 已重建**待运营重启客户端**；cloud master `f4a831e` 已 land + **已部署 dev**（backup `cloud.bak.20260716-202311`，healthcheck 绿：active/8787/飞书长连接/评论调度器就绪/isales 四服务未受影响），登记于 2026-07-16）** — **这是 82.10 那半修复的补齐**。82.10 的 edge `678bdc6` 自述目标是「让慢水合 permalink 不丢已批准评论」，但**只改了 `post-reader.ts`（浏览链路），而评论链路根本不走 post-reader**——`comment-handler.ts:125 → executor.openPost()` 走的是 `comment-executor.ts` 自己的 `openPost`（`:446` 独立产 `open_failed`），其 `surfaceProbeRounds` 是**另一份常量**、值仍为 4（总预算 ≈4.9s < 真机实测水合 7–12s）。dev 取证：`facebook_comment_audit` id 52（2026-07-16 16:54:05，账号 `61591701813509`，`groups/435744902071070`）= `no_strong_candidate/open_failed`，距租约取得仅 14s；且 `dist/facebook/post-reader.js:19`=22 而 `dist/facebook/comment-executor.js:70`=4，坐实「一边修好一边没修」。**两处修**：①**边缘**新增独立的 `postDetailProbeRounds`（默认 22，对齐 post-reader 同源实测依据）只用于 `openPost` 的 article 等待；搜索候选探测与评论框催拉**仍用 `surfaceProbeRounds:4` 逐字节不变**（它们跑在 `editorScrollRounds=6` 循环内，盲改即 6×22×600ms≈79s 炸步超时）；②**云端**新增 `FACEBOOK_OPEN_STEP_TIMEOUT_MS`=45s 让开帖步脱离固定 28s（边端最坏 ≈30s；不放宽只会把诚实的 `open_failed` 改判成 `timeout`——两者塌进同一 `no_strong_candidate`、运营看到的卡片一模一样）；搜索步仍 28s。**观测法**：dev PG `SELECT outcome, reason, count(*) FROM facebook_comment_audit WHERE created_at > <部署时刻> GROUP BY 1,2;` —— `open_failed` 应显著下降；**且 `timeout` 不得同步上升**（若上升说明 45s 仍不够、需复算边端最坏）。**真机核**：① 慢水合（>5s）的群帖评论能发出、不再误 `open_failed`；② 开帖步未被改判成 `timeout`；③ 评论框催拉预算未外溢（开帖步整体耗时不应逼近 45s——桩层已有回归闸，真机再核一次）；④ **XHS 零回归**（走 `edge-steps.ts` 另一条，本 change 未触及）。**前置**：dev 云端含 `f4a831e`（已部署）；**运营机须重启客户端**（dist 已在本机重建含 `ff6c1e1`；`electron:dev` 不含 build，见 memory `standby-restart-loop-stale-build`）；用 tom 分组 FB 号（同簇 82 前置）。**⚠ 分半生效**：cloud 那半已 dev 生效，但**边缘不重启则详情窗仍是 4 轮**、本项无法验收。**回滚**：cloud 恢复 `cloud.bak.20260716-202311.tar.gz` + restart；edge 把 `postDetailProbeRounds` 改回 4（或 revert `ff6c1e1`）。交叉 memory `fb-auto-comment-migration-lease-hole`；**与 82.10 同一现场、必须合并验收**（82.10 只覆盖浏览链路的窗，本项覆盖评论链路的窗）。
- [ ] 82.12 **FB 加群 click 腿复用已确立页、消灭同址整页重载真机核（change `fb-group-join-click-leg-reuse`；edge master `2f726ee` 已 land**待运营重启客户端**（dist 未重建；`electron:dev` 不含 build）；cloud/协议/DB 零改动、无需部署，登记于 2026-07-16）** — 修用户 2026-07-16 报的「跑 `/comment <昵称> --join --contact --force` 访问小组时页面跳两次、进群后又刷新一次」。**非正确性 bug**（群照加、评论照发），代价是白等一整轮就绪渲染 + 对同址连开两次的机器行为特征。根因：加群是**两腿**边缘调用（observe → 云端 LLM 预判 → click），云端在两腿间**故意释放租约**（不在等 LLM 时霸占浏览器，`facebook-group-join-scheduler.ts:303`/`:329` 两次 `withLease`）——但边缘 `joinGroup` 的 `Page.navigate` 原**无条件**排在「本次只观察」守卫之前，于是 click 腿把 observe 腿刚加载好、已水合的同一页**整页重载一遍**。修法：click 腿在位即跳过 navigate；**observe 腿永远 navigate**（承重反死锁闸——若两腿都复用，页面卡在目标 URL 的坏状态时 `not_ready` 重试将永远跳过导航、永远观察同一个坏页，死锁到 attempts 撞上限被永久标 `failed`；桩层已有断言守这条）。在位判据**故意不 canonical 化 current URL**（会把 `m.facebook.com` 移动版 DOM 与 `/groups/<id>/about` 误判成在位），只认 origin + 精确群根路径、容尾斜杠、忽略 query/hash；一切存疑方向 = 导航（退回今日行为）。**桩层验不了、必须真机的点**：**FB 真页在 observe 腿导航后是否把地址改写**（如追加 `?ref=`/`?sorting_setting=` 或跳 vanity → 数字 id），若改写形状超出判据容忍范围，复用会**每次静默回落 navigate**——功能无回归但优化完全不生效（**这是本项唯一的真实风险，且不会以任何错误形态暴露**）。**真机核**：① 跑 `/comment <昵称> --join`，肉眼确认群主页**只完整加载一次**（此前两次）——「跳两次」应变成「跳一次」，随后是群内搜索页那一跳（该跳是必要的、不消除）；② 加群结果与此前一致（joined / pending / questionnaire / already_member 语义不变）；③ 观测法：edge 日志/CDP 看 `Page.navigate` 到群根的次数，click 腿应为 **0** 次；若仍为 1 次即说明判据没命中真实 URL 形状（本项主要风险，须记录 FB 实际改写成什么样再收窄/放宽判据）；④ 慢渲染群（加入按钮 >7s 才出）零回归；⑤ **XHS 零回归**（本 change 只动 FB 加群执行器，XHS 结构性不可达）。**前置**：tom 分组 FB 号 + 一个**未加入**的目标群（已是成员走 `already_member` 早返回、验不到本项）；运营机以 edge master（含 `2f726ee`）重建客户端。**回滚**：把在位谓词 `isOnCanonicalGroupPage` 恒返回 false（或 revert `2f726ee`）即逐字退回今日无条件导航。交叉 memory `fb-join-coordinate-click-fails` / `fb-group-join-observe-i18n`；与 82.10/82.11 的详情水合窗正交（那两项治评论开帖，本项治加群导航）。


## 簇 83

### change `image-postcheck-vision-model` 分阶段真图验收（cloud master `023b5da` + console master `8c27fc2` 已 land + dev 已部署；登记于 2026-07-15）

整组视觉反推、八类专用分析、逐槽主参考绑定、源风格优先和产后视觉审计代码均已落地。dev 首阶段只开 `AIDCP_REFERENCE_VISUAL_ANALYSIS=true`，其余三个行为开关保持 false。已用精选素材 row 342 的 2 张真实参考图做了**不进入发布链**的影子验证：`dashscope/qwen3.7-plus` 两段调用成功，结果为 `analyzed`，两帧均识别为 `ui_document` 并只产 UI/文档专用维度；缓存写回成功，第二次复跑零模型调用。以下项目需要真实生成图和人工视觉判断，桩测与影子分析不能代替。

- [ ] 83.1 **同素材基线 A/B** — 选一组不会对外发布的 3–8 图精选素材，先保留当前 legacy 输出，再仅开启 `AIDCP_REFERENCE_VISUAL_BINDING=true` + `AIDCP_REFERENCE_SOURCE_STYLE=true` 生成第二版；逐槽核对 source i → output i，没有错图参照、张数缩水或图 0 封面位漂移。
- [ ] 83.2 **跨类型反推质量** — 至少覆盖人物摄影、静物/产品摄影、景色/空间摄影、插画/3D、文字卡、UI/文档、图表/信息图、拼贴/混合；摄影类才出现角度/焦段观感/景深/光影/色调/颗粒锐度，非摄影类不得冒充相机参数，也不得输出原图具体文字、数值、账号或水印。
- [ ] 83.3 **源风格优先是否真降低漂移** — 人工对比基线与新版本的画面类型、构图层级、色彩光影、材质和整组一致性；同时确认主体内容仍跟随改写稿，未变成像素复刻或照抄原图文案。未明显优于基线时保持源风格开关关闭并回调反推/合成 prompt。
- [ ] 83.4 **产后审计真图闭环** — 83.1–83.3 达标后开启 `AIDCP_VISUAL_FIDELITY_AUDIT=true`：各跑一例直接通过、首次失败后重生成通过、连续两次失败丢槽、模型不可用保留图但标 `unverified`；后台必须区分 provider `used` 与 audit `passed`。
- [ ] 83.5 **真人与文字风险红线** — 真人样本不得跨槽扩散身份锚或生成可识别名人脸；文字卡/UI/图表样本不得出现乱码、原图逐字复制、画内水印/平台标识。命中硬风险时必须 fail/retry/discard，绝不假 pass。
- [ ] 83.6 **逐阶段开关与回滚** — 先绑定、再源风格、最后产后审计，每阶段至少观察一批真实草稿的成功率、M<N、耗时和 token；任一阶段异常可独立把对应 flag 置 false 并重启，不回滚 schema/缓存列。

## 簇 84

### change `persona-first-post-onboarding` 首次人设→首篇作品真机验收（edge master `43d1e86` 已 land、需从 master 起客户端；cloud master `f4bfc89` 已 land + **已部署 dev**；登记于 2026-07-15）

首次人设完成后，客户端解释“看趋势 → 找匹配 → 开始创作”，CTA 复用既有启动链；Cloud 以账号终身唯一状态下发首轮真实浏览数，在第一条图文/视频精选入池后复用既有参照创作并保留发布确认。桩层与 dev 健康检查已通过，但下列一次性 UI、真实精选和待审稿行为不能由桩测代替。为避免浪费真实账号的终身首次状态，须用明确指定的新测试账号执行。

- [ ] 84.1 **首次只出现一次** — 新测试账号第一次确认人设后出现“人设已成形”引导；关闭后更新人设、重复确认及解绑后重绑均不再出现。旧版庆祝吉祥物、一次弱撒花与一次有界缩放肉眼符合设计；系统减少动画时直接静态展示。
- [ ] 84.2 **CTA 与 0/20 接续** — 点“开始找灵感”后人设浮层关闭，复用该账号既有启动/恢复动作；主界面立刻显示首轮 `0/20`，随后只随真实浏览数增长。普通非首次账号仍显示自己的今日计划，绝不固定为 20。
- [ ] 84.3 **20 不是成功承诺** — 让测试账号真实浏览达到约 20 条但暂不命中精选时，界面仍说继续寻找合适方向，不伪造“已找到 1 条”也不因 20 停止浏览。
- [ ] 84.4 **首条精选自动产待审稿** — 第一条正文非空的图文或视频进入精选池后，界面进入“已找到创作灵感 / 正在生成”，Cloud 只触发一次既有参照创作；最终客户端出现第一篇待发布作品与既有发布确认卡。评论精选、重复入池与并发入池不得多产稿。
- [ ] 84.5 **失败后诚实重试** — 人为制造一次发布容量拒绝或生成失败：不得出现假待审稿，首作状态恢复寻找；后一条真实精选可再次触发。真正发布仍必须由人工确认，本验收默认停在待审、不对外发布。

## 簇 85

### change `lease-strict-preemption` 严格抢占真机验收（**co-deploy 硬前置**：edge `6d87e39` + cloud 批 C 同批部署 dev 后才可跑；登记于 2026-07-15）

高优先级操作（验证码人工协助 / 手动评论 / 手动加群）可**在任意时刻**打断正在跑的低优先级操作，而被打断的一方 MUST NOT 被冤成失败、更不能因此重复发帖/评论。cloud 批 C（BLOCKER command-sequencer 分类 + 7.1/7.2/7.3/7.5/7.6/7.8/9.1 等）单测/typecheck 全绿，但下列行为是「真浏览器 + 真平台副作用」判据，桩测替代不了；且**必须 co-deploy 后跑**（cloud 单独上只会「认而不烧」但 edge 主动抢占未接线，端到端不成立）。

- [ ] 85.1 **A（10 秒，决定可抢占段是否免费）** — 小红书发布页上传一张图后读预览区缩略图地址前缀：指向本机临时对象＝提交前零副作用；指向平台服务器＝抢占会留孤儿图、须在 spec 清场协议 requirement 显式承认（对应 tasks 12.1）。
- [ ] 85.2 **B/F 合验（清场协议 + 端到端，决定抢占是否安全）** — 发布跑到逐字输入中途，运营提交验证码点击：断言①停手 ≤2s；②编辑器被清空（重发正文不拼接）；③发布稿回**待审、未被烧成 failed**（DB status 仍 pending_approval，不进 failed）；④验证码点击落在验证码上、不在发布编辑页；⑤抢占方释放后发布**自动重投整条序列**；⑥脏发布页导航离开若弹「离开此页/保存草稿」框，页面 MUST NOT 被冻住（对应 12.2/12.6）。
- [ ] 85.3 **C（巡视可抢占段是否为空）** — 导航进通知页、不点任何分类栏目、立刻离开再回来，看三个分类角标是否还在。消失＝导航本身已消费未读、可抢占段为空（保守设计已覆盖两种答案；对应 12.3）。
- [ ] 85.4 **D/E（孤儿产物）** — 抢占一次「已填标题正文、已传图」的小红书发布后刷创作首页看草稿箱是否多出一条（12.4）；抢占一次带新建话题的发布后搜该话题看是否已建出实体（12.5）。
- [ ] 85.5 **提交后被抢不重复** — 发布/评论已点提交、未拿到平台确认时被抢占：回执为「已提交，结果未知」，系统 MUST NOT 自动重发/重评；发布 DB 转 submitted（非 failed），评论去重账本因「提交已派发」写入、下次排期不重触发（对应 11.5 真机侧）。
- [ ] 85.6 **G（FB 评论走租约，依赖 7.9 落地）** — 7.9 落地后：租约在跑时下发的 FB 评论命令**不再被静默丢弃**（今天会）。7.9 未落地前此项无法验，随 7.9 一起激活（对应 12.7）。
- [ ] 85.7 **H（逃生梯，控制面故障）** — 人为让一个页面写者收到取消后不停手：断言协调器判为控制面故障（yield_timeout）、整队诚实拒绝，运营看到的是「浏览器不听话，请重启客户端」而非 20 秒后一句神秘租约失败；且**不自动重试/不归还排队额度**（对应 12.8 + 10.4）。

## 簇 86

### change `feishu-legacy-write-direct-queue` 真机验收（旧 slash 写命令直接排队、自然语言仍出确认卡；登记于 2026-07-15；cloud master `821ecef` 已部署 dev）

**前置**：Feishu 管理群（dev，`FEISHU_MANAGEMENT_CHAT_IDS` 已配或放行）+ 一台 headful 在线 edge（tom 分组，工程师大白 / Tmax）用于下游内容人审。**共享环境同簇 3 / 簇 20**，可在同一次真机 session 一并跑。

> 服务层逻辑已单测覆盖（`source==='legacy_command'` 自动确认入队、`approvalMode='review'` 不变、自然语言仍 `awaiting_confirmation`）；下列为「真飞书卡片 + 真路由」判据，桩测替代不了。

- [ ] 86.1 **精确 `/publish <昵称>` 静默排队** — 管理群发 `/publish 工程师大白`：**不再**弹「请确认用户委托任务」确认卡，**也不回队列提示卡**（只有 👀 已读表情，见 `feishu-delegated-suppress-progress-cards`）；随后下游**逐篇内容人审卡照常弹出**，通过后才真发（AC-PUB 不破）。
- [ ] 86.2 **精确 `/comment <昵称>` 静默排队** — 同上，`/comment` 静默排队、评论人审在发前仍触发。
- [ ] 86.3 **自然语言仍先确认** — 发「让工程师大白发布一篇稿件」/「今晚前完成 3 条评论」：**仍**弹结构化确认卡，点「确认并排队」后才入队（不回退）。
- [ ] 86.4 **昵称歧义 fail-closed** — `/publish <重名或不存在昵称>`：诚实拒绝要求澄清，**绝不**直接排队到任意账号。
- [ ] 86.5 **幂等不双发** — 同一 `/publish <昵称>` 因飞书快速重推被触发两次：去重归并到同一任务、不产生双任务 / 双发。

> **补登 `feishu-delegated-suppress-progress-cards`（2026-07-15，cloud master `f654850` 已部署 dev）**：委托层不再推「委托任务 · queued/failed」进度卡，结果由每类任务自己的正常业务结果卡承担；发帖失败委托层补发诚实失败卡兜底。`delegatedPublishOutcomeReceipt` 纯函数已单测；下列为真飞书卡片判据。

- [ ] 86.6 **评论完成不再叠加委托进度卡** — 跑一条 `/comment <昵称>`：只收到**一张**评论链正常结果卡，**不再**同时收到「委托任务 · queued」「委托任务 · failed/completed」。
- [ ] 86.7 **发帖失败仍诚实通知** — 构造一次发帖终态失败（达最大尝试仍 0 成功）：委托层补发**一张红色失败结果卡**（含真实完成 0/N），**绝不静默**。
- [ ] 86.8 **发帖成功不重复报绿** — 一条发帖经人审通过并发布：只有发布人审卡，**不再**额外冒一张绿色「委托任务 · completed」。
- [ ] 86.9 **控制命令/按钮回卡不受影响** — 「查看任务 <id>」「暂停 <id>」「取消 <id>」仍回状态/进度卡；自然语言确认卡点「确认并排队」仍有即时反馈（用户主动请求的回卡未被误删）。

> **补登 `structured-delegated-sources-skip-confirmation`（2026-07-15，cloud `7144be3` + console `9d0d017` 已部署 dev、edge `61b2fc1` 源码合 master 不打包）**：结构化精确入口（console 行级动作 / edge 快捷入口 / api / 旧 slash）不再出「请确认用户委托任务」卡，云端 `createDraft` 对 `source ≠ feishu` 直接确认入队。`createDraft` 分流 + panel 端点 + console 两页 + edge renderer 均有单测/组件测覆盖；下列为真界面判据。

- [ ] 86.10 **管理后台洗稿直接入队** — 精选页对一条图文点「洗稿」→ Popconfirm「洗稿」→ **不弹**「请确认用户委托任务」卡，直接出「已排队洗稿创作（任务…）」toast；稿件仍走下游内容人审后才发。
- [ ] 86.11 **管理后台定向评论 / 候选稿动作直接入队** — 精选页「评论」、内容页候选稿「批准 / 驳回 / 修改 / 删配图」→ 均直接入队 + 成功 toast，无委托确认卡；候选稿动作的 CAS 版本冲突诚实报「内容已被他处修改，请刷新」（不报 `version_conflict` 裸码、不谎报排队成功）。
- [ ] 86.12 **Edge 快捷入口直接入队** — Edge 客户端选中环境后用快捷入口发起委托 → 直接「已排队」+ 刷新任务列表，不弹确认卡（需 edge 跑 electron:dev 或新包）。
- [ ] 86.13 **自然语言仍先确认（回归）** — 飞书「让 <昵称> 发布一篇稿件」仍弹「请确认用户委托任务」卡（唯一保留确认的入口，未被误删）。

> **补登 `restore-delegated-command-card-origin-chat`（2026-07-15，cloud master `f248a1e` 已部署 dev）**：命令触发的委托发帖，其**内容审批卡 + 终态失败卡回下命令的那个会话**（私聊→私聊、群→那个群）；无来源会话的自动 / 排期发帖仍走默认审批群 / 账号团队群。根因＝委托层挡在 `/publish` 前把命令来源会话丢了（原只存进从不读回的 `sourceRef`），致审批卡落默认群、失败卡落账号团队群、两卡分两群且都不在私聊（工程师大白实际踩到）。服务/executor 已单测（`originChatId` 往返 + `manualApprovalChatId` 透传）；下列为真飞书路由判据，桩测替代不了。

- [ ] 86.14 **私聊 `/publish` 审批卡回私聊** — 工程师大白**私聊** Bot 发 `/publish <昵称>`：随后的**内容审批卡出现在该私聊里**，MUST NOT 落默认管理群、MUST NOT 落账号团队群。
- [ ] 86.15 **私聊 `/publish` 终态失败卡回私聊** — 构造该私聊触发的发帖终态失败（达最大尝试仍 0 成功）：**红色失败结果卡出现在同一私聊里**，MUST NOT 落账号团队群。（cloud 日志 `发帖终态失败卡 … sink=origin` 佐证）
- [ ] 86.16 **管理群 `/publish` 回该管理群** — 在**管理群**发 `/publish <昵称>`：审批卡 + 终态卡都回**该群**（来源会话＝群）。
- [ ] 86.17 **自动 / 排期发帖不受影响（回归）** — 自动 / 排期触发的发帖结果卡**仍进账号团队群**（无来源命令会话 → 补集回落既有 per-team 路由）；工程师大白手动命令的改动 MUST NOT 波及自动流量。**⚠️ 本项原文的「审批卡仍走默认审批群」一句已于 2026-07-16 被 `unify-card-routing-origin-then-team` 推翻——自动 / 排期审批卡现在应进账号团队群（见 86.29），按旧口径验收会误判为回归。**
- [ ] 86.18 **后续对齐项 — 已被 `unify-card-routing-origin-then-team` 取代（见 86.26+，勿重复登记）** — 手动 `/comment` 终态结果卡此前仍走账号团队群；该 change 已把 `originChatId` 透传进 `CommentScheduler.postResultCard` 取址，验收判据见 86.27。

> **补登 `delegated-executor-operator-authority-parity` + `delegated-approvalmode-clamp`（2026-07-16，cloud master `b78a27f` / `6413a6a` 已部署 dev，backup `cloud.bak.20260716-162510`，healthcheck 绿）**：委托层重新实现命令语义的两处跑偏 + 一处结构化入口免审信任缺口。服务/executor/helper 已单测（operatorOverride 仅精确类透传、评论起跑前失败→红卡 vs 起跑后→null、approvalMode clamp）；下列为真飞书 + 真调度路由判据，桩测替代不了。设计档 `docs/design/delegated-command-two-layer-split.md`（这是分层设计的阶段 1）。

- [ ] 86.19 **A：精确 `/publish` 在风控受限账号仍出草稿 + 人审卡** — 把一个账号压到风控非 normal（或当天已达发布配额），管理群/私聊发 `/publish <昵称>`：系统**越风控生成草稿并出发布人审卡**，MUST NOT 因风控/配额把命令 blocked→静默判失败。人审 MUST 仍强制（越权只越风控、不越人审）。对照：同账号自然语言「让 <昵称> 发一篇」仍受风控闸（governed），受限时诚实 blocked。
- [ ] 86.20 **B：评论起跑前触发闸失败收诚实红卡（不再静默）** — 对一个**未绑人设**（或联系方式缺 / 非 FB 账号带 `--join`）的账号发 `/comment <昵称>`：运营**收到一张红色「评论任务未触发」卡**，含人类可读原因（如「未绑定人设」），MUST NOT 零反馈静默。（今天此类会静默吞掉）
- [ ] 86.21 **B 负向：评论起跑后失败不双发** — 一个已起跑、跑到最大尝试仍未评上的 `/comment`：只有**评论链自己的结果卡**，委托层 MUST NOT 再叠一张「评论任务未触发」卡（避免双发）。
- [ ] 86.22 **C：结构化 draft 自带 `auto_approve` 被夹成 review** — 用带 `approvalMode:"auto_approve"` 的请求体打后台 `/api/delegated-tasks/draft`（或客户端 `/delegated-tasks/draft`）建发帖/评论草稿：任务以**必审**入队、内容 MUST NOT 免审直发平台，即使该账号未开账号级免审。对照：后台「洗稿」正常入口（服务端传 review）行为不变。

> **补登 `delegated-terminal-failure-reason`（2026-07-16，cloud master `<sha>` 已部署 dev）**：终态失败卡带上真实失败原因（此前只有「已达到最大尝试次数；真实完成 0/1。」这句预算记账，用户实际收到并投诉）。原因一路都在——编排器 `failureReason` → 执行器 → 已持久化到 `delegated_task_attempts.reason` 列——只是 `finishBudget` 从不读它。四支拼接 + humanize 白名单已单测（52 项绿），并已用「真 worker → 真 receipt → 真卡 builder」驱过五支肉眼核对；下列为**真 PG + 真飞书**判据，桩测替代不了。**注意 86.7 是本项的前身**（那时只验「有没有卡」，本批验「卡上说不说得清原因」），可一并跑。

- [ ] 86.23 **失败卡带出真实原因（本投诉的正面验收）** — 构造一次发帖终态失败（最简：让同账号已有一轮发帖编排在跑时再 `/publish <昵称>`；或把账号压到风控非 normal 走自然语言 governed 路径）：红卡正文 MUST 在「已达到最大尝试次数；真实完成 0/1。」之后带出**具体原因**（如「已有一轮发帖编排在运行中」/「账号风控状态为 warned，暂不发帖」），MUST NOT 只有那句记账。
- [ ] 86.24 **「均未真正开始」措辞不误导（红线）** — 上一项若走的是「全程被让开」路径（`failureCount=0`、`skippedCount=attemptCount`）：文案 MUST 为「N 次均未真正开始：<原因>」，MUST NOT 出现「最后一次未成原因」或任何可被读成「已经在平台上动过手」的措辞。
- [ ] 86.25 **PG `listAttempts` 真库验证（本地测不到）** — 本 change 新增的 `listAttempts` **只在 memory 实现上跑过单测**（PG 需真库）。dev 上任一委托任务走到预算终态后，确认卡上真的带出了原因 → 即证 PG 侧 `SELECT … ORDER BY ordinal` 与 `mapAttempt` 正常；若卡上恒无原因尾巴（而 cloud 日志无 `读取 attempt 原因失败`），说明 PG 查询返回空、须回查。
- [ ] 86.26 **平台名出现在失败卡上** — 失败卡 MUST 多一行「**平台**：Facebook / 小红书」（取自 registry displayName，非裸 id）。
- [ ] 86.27 **无原因可取时不补推测（负向）** — 若某次终态确实取不到任何带原因的 attempt：卡文案 MUST 与本 change 前逐字一致（只有记账），MUST NOT 出现「原因未知 / 可能是…」之类推测。

## 簇 87

### change `wechat-channels-interaction-management` dev 真账号与受控写验收（Session 05；登记于 2026-07-15）

**已完成的代码与 dev 基线**：控制仓契约 `3aa51de`（原记 `a678003`，2026-07-17 校正——那个 sha 只活在 `origin/codex/wechat-channels-interaction-management` 分支、**不在 origin/main 上**；`3aa51de` 是主干上 subject 逐字相同的等价提交。工作没丢，只是台账指向了一个别人 clone 下来找不到的提交） 与真实运行闭环变更；Cloud master `42cd5f8` 已部署 dev 并应用 0042；Edge master `4c45e48` 已补齐真实非空评论/DM 读取和客户端详情查询；Console `3a477c1` 已部署 dev。最新 Edge acceptance 22/22、全量 1594/1594、typecheck/build 通过，互动模块 55/55、详情/IPC 22/22 通过。命名账号已完成首次授权、浏览器关闭后的 API-only 恢复和 controls v3 在线收敛；真实只读样本得到 3 条评论与 1 个会话内 3 条 DM，Cloud 持久化 3 个 comment thread/message、1 个 DM thread 与 3 个 DM message，客户端显示 2 条待处理互动且评论/私信列表和详情均可读。Edge/Cloud 3 个 scope 的 last batch 一致，send attempt 仍为 0。真实写与 offboarding 仍不得由本次只读结果替代。

**安全前置**：只用用户明确命名的测试账号；写 capability 初始保持 false，账号级 `write_paused` 保持 true；先完成只读项。评论/私信分别需要用户批准的一条可删除目标。自动模式必须等 87.1–87.6 通过后再次获得明确批准。Edge 本次只验证了 master 源码，**没有构建或发布安装包**。

- [x] 87.1 **真实登录与持续只读同步** — 在 dev 用命名测试账号扫码登录并核对绑定身份；关闭浏览器后，评论和私信仍继续增量同步；Cloud/客户端显示同一账号、同一 cursor，不能把登录请求发出或拿到页面当成同步成功。
- [ ] 87.2 **分页、重启与账号隔离** — 验评论多页、私信多会话、Edge/Cloud 分别重启后的续传恢复；至少两个账号快速切换，列表、详情、游标、草稿、待发送任务和审计不得串账号。
- [ ] 87.3 **一次受控评论回复** — 只对用户批准的可删除测试评论人工发送一次；同时取到平台端可见、Cloud `confirmed`、Edge/Cloud 同一 attempt/idempotency 与 body-free audit 证据；重复点击和重复 command 不得产生第二条平台回复。
- [ ] 87.4 **一次受控私信回复** — 只对用户批准的可删除测试私信人工发送一次；判据同 87.3，并确认私信正文不出现在普通日志/审计中。没有批准目标时必须保持 gated，不能用 mock `confirmed` 代替。
- [ ] 87.5 **真实失败边界** — 分别验会话失效/错误账号、发送中断网形成 `ambiguous` 后只 verify 不盲重发、Edge/Cloud 重启恢复、AI 超时/越界/高风险 fail closed，以及真实 schema missing 时能力熔断；平台不可见且无确认时不得显示「已发送」。
- [ ] 87.6 **真实解绑与延期清理** — 验环境解绑、客户终止、Edge 离线后重连三条路径：Cloud 先撤权/停派发，Edge drain 后清加密 session 并关闭 sidecar，重复/重启只确认一次，Cloud 收到 scope-matching ack 后 tombstone，并在配置期限内完成 scope purge；保留审计不得含正文。需保存真实的凭据删除与 purge 证据。
- [ ] 87.7 **low-risk auto 仍需二次批准** — 只有 87.1–87.6 全部通过且用户再次明确批准，才给该测试账号开启 low-risk auto，用可删除测试消息验一次；否则状态必须写成「已实现、未真机开放验证」，全局开关、账号白名单和账号级暂停继续关闭。
- [x] 87.8 **Edge 真机载体边界** — 已用 Edge master `d321042` 源码连接同一 AdsPower 登录态完成只读真机运行；没有构建或发布安装包，因此本项只证明源码载体，不代表桌面安装包已发布/验收。

<!-- 87.1 partial evidence (2026-07-16): named-account auth became active, the browser closed, controls version 1 converged, and Cloud retained one accepted zero-item batch/cursor for each of comment and DM with no send attempts. Keep 87.1 open until a non-empty incremental sample and the real client-side same-account/cursor presentation are observed; 87.2 remains open for multi-page/restart/two-account isolation. -->

<!-- 87.1 closure evidence (2026-07-17): Edge master 87ee475 parsed the observed non-empty comment-list and global DM-history shapes; 4c45e48 removed the unsupported detail `limit` query. With the browser closed, the named dev account produced three comment messages and three DM messages across one DM session. Cloud stored three comment threads/messages and one DM thread with three messages; the three local/Cloud cursor scopes had matching last batch IDs, send attempts remained zero, and the client rendered two inbound pending items with working comment and DM details. Edge full 1594/1594, acceptance 22/22, interaction 55/55, detail/IPC 22/22, typecheck and build passed. 87.2 remains open for real multi-page, restart recovery and two-account isolation. No platform write or installer build was performed. -->

## 簇 88

### change `facebook-comment-participation-gate` 群参与审批入群闸真机验收（edge master `a6fb282` 已 land、需从 master 起客户端；cloud master `21e44e5` 已 land + **已部署 dev**（backup `cloud.bak.20260716-161340`，healthcheck 绿）；登记于 2026-07-16）

**背景**：Facebook 群「参与者审批 / 参与问题」= 管理员配置的一次性入群闸——账号首次在该群评论时被拦成「申请参与 + 答题 + 同意群规」，提交后待管理员人工批才上墙。桩层已实装：① 止血（确认判据加「待审批徽章」否决，堵住「待批评论误报已发出」假绿）；② 识别（`buildParticipationGateJs` 只认可见 `role=dialog` + 参与审批专属文案，避开侧栏 Join / 问答帖回复框两类旧假阳）→ 新诚实结局 `pending_group_approval`（不上墙、不染绿、不去重、不重试）。**默认不做自动答题**（答了仍等人批 + 暴露自动化痕迹，属另议）。

**前置环境**：tom 分组测试号（工程师大白 / Tmax）+ 一个**开了「参与者审批」的公开 FB 群**（或私密群开「限定成员」）；从 edge master（含 `a6fb282`）起 headful 客户端连 dev（`ws://121.89.85.150:8787`）。**共享环境同簇 82（FB feed / 评论真机批）**，建议同一次真机 session 合验。

- [ ] 88.1 **参与审批闸真机取证** — 用**从未在该群贡献过**的账号，对该群一帖尝试评论；抓弹框 **CDP 截图 + `document.body.innerText` 全量 dump + iframe frameUrls**。核：① URL 停在 `/groups/<id>/...`（**不**跳 `/checkpoint`，据此确认是群作用域入群闸、非账号级反机器人）；② 弹框是不是 `role="dialog"`（决定首版 `buildParticipationGateJs` 只认 dialog 是否够——若为非 dialog 全屏 interstitial，需按取证扩面）；③ 坐实简体中文按钮/徽章原文（`申请参与 / 参与问题 / 同意小组规则 / 待审核`），把 `FB_PARTICIPATION_GATE_RE` / `FB_PENDING_APPROVAL_RE` 从「语义高置信」升到「逐字确认」。
- [ ] 88.2 **诚实结局与卡片** — 命中参与闸时，边缘回执 = `pending_group_approval`（`submitted:false`）、**打字前**不把评论灌进「输入回答」框、确认段**不刷新不重试**；云端出**黄卡**「该群需管理员批准参与后才能评论（评论未上墙，待人工处理）」，**绝不染绿**、不写去重、不记风控、不算委托成功。查 journalctl（cloud dev）关键字 `pending_group_approval` / `参与审批入群闸`。
- [ ] 88.3 **假绿否决回归（止血核心）** — 构造/等到「静默待审批」形态（本人首条评论只对作者可见、带「待审核」徽章、带真 comment_id 或 ≥2 交互控件）：确认判据 MUST NOT 判「已上墙」（`buildAckVerifyJs`/`buildScopedVerifyJs` 待审徽章否决生效）→ 落 `pending_group_approval` 而非 `verification_ambiguous`（更非成功）。
- [ ] 88.4 **不误伤合法回复** — 在**开了参与审批但账号已是 participant** 的群、以及**问答型帖子**（回复框 aria-label「输入回答/Answer」但非参与审批对话框）里正常评论：探针 MUST NOT 误触发，评论照常发出并被确认；参与答题框标签仍被当合法评论框（不回归旧假阳）。

### change `facebook-comment-lifecycle-verify` 评论三态生命周期 + 假绿修复（edge master `d4c081f` 已 land、**需重打安装包**；cloud master `07643ef` 已 land + **已部署 dev**（backup `cloud.bak.20260717-114459`，healthcheck 绿）；登记于 2026-07-17）

**背景**：真机探针（2026-07-17，账号 Tianxing Bai / env `k1ei3dbi`）首次拿到 FB 评论行完整三态，推翻了两条已归档 spec 要求：

```
t=  31ms  '… 发布中...'            按钮=0  opacity=1   ← 在飞（client 占位 id）
t=2807ms  服务器点头（GraphQL 响应）
t=2906ms  '… 1 分钟 赞 回复'        按钮=4  opacity=1   ← 上墙（服务器 base64 id）
（被拒真机样本 comment_id=4134110716722371）
          '… 16小时 已拒绝 查看反馈'  按钮=2  opacity=1   ← 被拒
```

**修掉的活假绿**：旧 ack 判据「服务器 id **或** `role=button` 数 ≥ 2」——被拒行恰好 2 个控件（编辑或删除此项 / 查看反馈）→ **平台拒绝的评论被判成发布成功** → 云端打去重烧掉目标帖 → 运营收到绿卡「服务器已确认」。改为「服务器 base64 id **或** 具名赞 **且** 具名回复」。**删刷新腿**（真机当场制造假阴性：报评论不在、实际两条都在；且其判据只认本人+文本 → 对被拒必假绿；且刷新毁押审证据），其约 9s 预算并入就地窗（32→63 轮），**提交后总预算不变**（云端步超时与 20s 提交保护窗均未动）。

**前置环境**：**与 88.1-88.4 完全同环境同链路**（同一 FB 群 + tom 分组号），建议一次真机 session 合验。⚠️ **edge 必须重打安装包**才生效（运营机跑的是包，不是 master）。

- [ ] 88.6 **🔴 被拒不再假绿（本 change 核心）** — 造/等到一条被 FB 拒绝的评论（真机已知：该状态**发布后即刻出现**，非延迟态）：边缘 MUST NOT 判成功、落 `comment_rejected`、**不打去重**（目标帖仍可留人工）；云端出黄卡「Facebook 已拒绝该评论（未上墙，需人工处理）」，**绝不染绿**、绝不说成「无法确认」。查 journalctl 关键字 `comment_rejected` / `平台已拒绝`。
- [ ] 88.7 **逐字措辞收口（现仅简体中文样本）** — 坐实**越南语**（车队实跑越南群）与英文的「已拒绝 / 查看反馈 / 发布中」真实原文，把 `FB_COMMENT_REJECTED_RE` / `FB_COMMENT_IN_FLIGHT_RE` 从「语义高置信超集」升到「逐字确认」。**漏检安全**（回落既有诚实非成功、不假绿），故不阻塞上线，但不做则越南群里这两态形同虚设。
- [ ] 88.8 **正常评论零回归 + 不误伤** — 正常评论仍在约 3 秒内确认成功（真机实测点头 2.8s），且**全程无任何 reload**；正常行的「查看翻译 / 分享 / 留下心情」控件 MUST NOT 被误判成被拒或在飞。
- [ ] 88.9 **在飞态不误判** — 「发布中」期间不落任何终态；窗口耗尽仍在飞 → 落 `verification_ambiguous` 且**边缘日志**带「观察到在飞」（分诊「压根没提交」vs「提交了没等到结果」）。⚠️ 该证据**只在边缘日志**、未进回执字段（加字段要动 `action.completed` 载荷形状=跨仓契约，超出本 change 范围）——若运营侧要在卡上看到，需另开 change。
- [ ] 88.10 **剥正文防误判（实装期发现的自造洞，已堵）** — 发一条**正文里含「已拒绝」或「发布中」字样**的正常评论：MUST NOT 被误判成被拒/在飞。误判后果不是漏报而是**成功报失败 → 不打去重 → 下轮同帖真重发（平台可见重复评论）**。桩测已覆盖（`stripSubmittedText` 剥完整正文），真机复核一次即可。

## 簇 89

### change `client-created-env-auto-assignment` 客户端本机建号自动归属验收（Cloud `e8b16d6` 已部署 dev；Edge `239c44c` 已 land、未打安装包；登记于 2026-07-16）

客户在已登录桌面客户端内通过官方“创建环境”流程新建 AdsPower 环境后，Cloud 用一次性短时 intent 把**本次新建返回的 envKey**登记到权威环境注册表并唯一分配给当前客户；Electron 主进程重新读取 `/my-environments` 确认后，才把环境加入本地运行花名册。旧 `POST /environments` 任意认领仍固定 403，已登记环境不能借新建 intent 认领，同一 intent 不能换绑第二个 envKey。成功只加入离线行，**不会自动启动**；代理仍可稍后补配。

桩层：Cloud acceptance 54/54、最新 master 全量 2290 通过（5 个显式 gated skip）、一次性 PostgreSQL 真实事务 2/2、typecheck/build 通过；Edge acceptance 22/22、最新 master 全量 1520/1520、typecheck 通过。dev 部署备份 `cloud.bak.20260716-180737.tar.gz`，`8787/8090/8091`、三条 health、PostgreSQL provisioning 表/唯一 owner 索引及飞书长连接均验证正常。**没有运行 `electron:build*`，因此当前已安装的 Windows 客户端仍会显示旧“管理员分配”提示，这是旧包事实，不是新闭环已在真机失败。**

- [ ] 89.1 **Windows 新包载体** — 用户明确授权桌面打包/发布后，从 Edge master（含 `239c44c`）构建 Windows x64 安装包并在 Win11 Intel 真机启动一次；确认 core 能连 dev、AdsPower 调用可达，且无 packaged-only `app.asar`/`spawn ENOTDIR` 回归。未获明确授权前保持本项未执行。
- [ ] 89.2 **视频号新建自动归属与可见性（本 change 直接目的）** — 在新包中以客户账号登录，选择“视频号”创建一个全新环境：回执应为“已分配到当前账号并加入运行环境；需要启动时请在环境栏操作”，左侧环境列表立即出现该视频号环境的**离线行**；Cloud `/my-environments` 与 PostgreSQL active owner 都只归当前账号。MUST NOT 自动启动浏览器/core。
- [ ] 89.3 **代理与重启持久化** — 不填代理创建：提示“未配代理，可稍后在环境行「代理」里补配”，环境仍正常归属；关闭并重开客户端后该环境仍在当前账号花名册，平台保持 `wechat_channels`，补配代理只改该环境且不改变归属。
- [ ] 89.4 **失败诚实性与旧认领红线** — 分别制造 Cloud intent 申请不可达、建号后完成归属失败、权威清单刷新失败和本地 settings 写盘失败：申请失败必须在 AdsPower 建号前停止；其余失败须明确区分“本机已创建 / 已分配 / 未入运行环境”，不得把未确认环境加入花名册。用已登记的另一环境 envKey 与旧 `/environments` 路由尝试认领都必须被拒，且不得改变现有 owner。

## 簇 90

### change `facebook-write-action-visibility` FB 写动作客户端可见性验收（edge master `40aa902` 已 land + 已同步主 checkout；**未打安装包**；登记于 2026-07-16）

**背景**：运营报「触发了多次评论，但客户端记录里一条都没有」。坐实：FB 环境的活动流此前只可能出现 5 类条目（账号就位 / 已连云 / 开始浏览 / 读 / 赞）——评论、加群、搜索**一条不产**。根因是三个独立卡点叠加：① 评论/加群/定向搜索/按链接开帖由会话**委托**给独立处理器，处理器自己回执云端后返回，**走不到**唯一的叙述出口；② 叙述器类型联合封闭 4 值且已用满；③ 壳侧中文兜底表 21/22 条规则是**小红书专属**（`autoBrowse` 按构造排除 FB），唯一命中 FB 的那条还把「就地读」叙述成「顺路去作者主页看看」。**危害不止少显示**：运营分不清「没做」和「做了但没显示」——卡在群参与审批（评论已提交、等管理员批）与评论框没找到的，此前同样隐形。

本批同时修一个**既有 `edge-fleet-console` 规格违反**：FB 验证码/阻断**从不点亮**客户端「需要处理」态（检测行不含兜底正则要的「弹窗」「暂停操作」；清除侧 FB 干脆什么都不打），且该标志会被**任何一次成功互动顺带清掉**——一次正常点赞就把卡在验证码上的机器抹回绿色。已改为两侧走结构化事件 + 清除只认显式解除。

**桩层**：`test:acceptance` 22/22、`npm test` 1559/1559、`typecheck` 干净。新覆盖**压在发射器侧**（既有解析器测试只测解析器、从不执行发射器，改一句措辞照样全绿而条目静默消失）。

**前置环境**：tom 分组测试号（工程师大白 / Tmax）+ 越南招工类 FB 群；从 edge master（含 `40aa902`）起 headful 客户端连 dev（`ws://121.89.85.150:8787`）。**共享环境同簇 82 / 88（FB feed / 评论真机批）**，建议同一次真机 session 合验。

- [ ] 90.1 **计数是否重复（首个要核的点）** — 一条真评论会同时 bump 本地兜底 `comments` 与云端经 `interaction.occurred` 的计数。预期云端 ~60s `dailyUsage` 快照**覆盖**本地兜底（与既有 like / view 同构、非新引入模式）。核：真机跑若干条评论后，客户端「今日进展」的评论数**不虚高**、与 console/云端权威计数一致。若虚高 → 说明覆盖没生效，需查 ui.snapshot 推送。
- [ ] 90.2 **待批准是否为常态（预期反应管理）** — 若群参与审批频繁命中，活动流会出现大量「评论待管理员批准，还没显示出来」。**这是修复在起作用**（把一直存在的现实翻出来），**不是回归**。核：该文案 MUST NOT 计数、MUST NOT 读成已发布；并向运营讲清「现在看着全是待批」≠「现在全失败」——此前它们是静默的假绿。
- [ ] 90.3 **群名读取（越南语真机）** — 加群条目的群名取自现读页面标题，需剥「(3) 」通知计数前缀与「| Facebook」后缀，按 18 字有界截断。核：越南语群名可读、截断不截错、**读不到时回落「一个小组」而非露 URL / group id**。（桩层已覆盖前缀剥除与截断，真机核多语言与通知前缀的真实形状。）
- [ ] 90.4 **FB 验证码点亮与不被顺带清除** — 制造 FB 验证码/阻断：核 ① 该环境客户端「需要处理」**点亮并浮到环境栏最上**（此前从不点亮）；② 其后账号若仍有一次正常点赞/阅读，该态 **MUST NOT 被抹绿**（此前会）；③ 人工处理完、边缘复检发出显式解除后才退出该态。**同时核不回归小红书**：XHS 两侧本有显式 popup/popup_cleared，移除 statsDelta 兜底后其阻断态仍能正常置真与清除。
- [ ] 90.5 **加群成功闸与云端一致** — 加群条目的成功判据镜像云端证据闸（`ok && clicked`）。核：客户端说「加入了小组」时，云端 `interaction.occurred{join_group}` 同时发生；客户端说「申请加入…等待管理员通过」时云端**不**记 join_group。二者 MUST NOT 打架。
- [ ] 90.6 **搜索条目与在场感** — 定向搜索出「在「<真实群名>」搜「<词>」，找到 N 条」/「没有匹配的帖子」（二者可区分）；浏览侧搜索出「搜索「<词>」，找到 N 条」，且在场感为「正在看「<词>」的搜索结果…」而**非**「正在浏览推荐流…」（后者在搜索结果页上是假话）。

> **补登 `unify-card-routing-origin-then-team`（2026-07-16，cloud master `38e3fde`，部署 dev 见 tasks 6.4）**：**一切**出站卡片 / 告警收敛为一条规则——**来源会话 → 账号团队群 → 默认群**。起因＝工程师大白私聊下评论命令，「待审核评论」卡落默认群「AI运营」；同批账号的自动化审批卡也没进已配好的 tom→Tom.A 路由。根因是**一行**：评论审批卡在全仓只有一个发送口（`server.ts` 的 `CommentApprovalPort.request`）写死默认群解析，手里有 `accountId` 也不用、来源会话根本传不进来。解析器三档 + 执行器三分支透传已单测；**下列为真飞书路由判据，桩测替代不了**。
>
> **本批同时推翻了两条既有 spec MUST NOT（运营方 2026-07-16 显式定案）**：审批卡不再硬绑管理群；带账号的运维告警也按账号路由。**已接受的暴露面**：审批回调无任何权限校验（只认 requestId、不校验点按者与来源群）→ **谁看得见卡谁能批准**；`group_route` 无内部 / 外部标记 → 规则对全部已映射团队一视同仁。**若把外部客户群映射成某团队路由，该客户即自动获得批准按钮与运维可见性，系统内无闸可拦**——在引入「路由可信标记」前，映射外部客户群须由人工流程约束。
>
> dev 真值参考：默认群 `oc_144e761f…`＝「AI运营」；`tom`→`oc_1c268549…`「Tom.A」；`ninghao`→`oc_144e761f…`（**即默认群本身**，故其账号看不出变化——别拿 ninghao 验收）。

- [ ] 86.26 **私聊 `/comment` 审批卡回私聊（本投诉的正面验收）** — 工程师大白**私聊** Bot 发 `/comment <昵称>`（tom 组账号，如 Dennis Scott）：「待审核评论」卡 MUST 出现在**该私聊里**，MUST NOT 落默认群「AI运营」、MUST NOT 落 Tom.A。
- [ ] 86.27 **私聊 `/comment` 终态卡与审批卡同投私聊（销 86.18；防「两卡两群」复发）** — 同一条 `/comment` 跑到终态：**结果卡与上面那张审批卡在同一个私聊里**，MUST NOT 一张私聊一张团队群。（此前两卡走两段不同代码、两种兜底，正是分投两群的机制根因）
- [ ] 86.28 **自动化评论审批卡进团队群（本投诉的第二半）** — tom 组账号由**排期 / 自然浏览闭环 / FB 覆盖模式**产出的「待审核评论」卡（无命令来源会话）：MUST 进 **Tom.A**（`oc_1c268549…`），MUST NOT 落默认群。
- [ ] 86.29 **自动 / 排期发帖审批卡进团队群（发帖侧镜像缺口）** — tom 组账号的自动 / 排期发帖走到人审：**发布审批卡进 Tom.A**，MUST NOT 落默认群。（cloud 日志 `审批卡已发 source=account_scope chat=oc_1c268549…` 佐证；`source` 标的是解析路径、落点以 `chat=` 为准）
- [ ] 86.30 **未绑团队账号仍落默认群、绝不丢卡（回落回归 · 最高价值）** — 一个**无 `group_label`** 或团队键未命中 `group_route` 的账号触发评论 / 发帖人审：卡 MUST 仍出现在默认群，MUST NOT 静默消失。cloud 日志应有 config-gap 一行。**这是本 change 回归风险最集中处**——三档全落空时若解析出空串，卡会无声蒸发。
- [ ] 86.31 **群里下命令回该群（来源会话＝群）** — 在**管理群**发 `/comment <昵称>`：审批卡 + 终态卡都回**该群**，MUST NOT 因账号属 tom 而被改投 Tom.A（来源会话优先于团队路由）。
- [ ] 86.32 **带账号的运维告警进团队群（策略变更的直接后果，需运营确认可接受）** — tom 组账号触发验证码告警 / 发布下发段离线回待审 / 熔断开启：这些卡现在**进 Tom.A 而非默认群**。请运营确认这是想要的——**这是本次策略变更影响面最广的一项**，管理群将不再是运维告警的汇总位（无账号的握手 config-error 仍落默认群）。
- [ ] 86.33 **审批可点性（跨会话回调回归）** — 在私聊里点 86.26 那张卡的「通过」：授权 MUST 真生效、评论真发出。（回调只认 requestId、不看会话，理论上零风险；但这是「卡搬家」后唯一会让人审彻底失灵的失败模式，必须实点一次）

## 簇 91

**前置环境**：tom 分组测试号（工程师大白 / Tmax）+ 一个能真实触发 FB 频率限流的场景（连续评论 / 连续发帖直到平台弹限流窗）；从 edge master（含 `26ef2cb`）起 headful 客户端连 dev（`ws://121.89.85.150:8787`，cloud master `8944f75` 已部署）。**共享环境同簇 82 / 88 / 90（FB feed / 评论真机批）**，建议同一次真机 session 合验。

> **`fb-throttle-popup-zh-frequency-copy`（2026-07-17，edge `26ef2cb` + cloud `8944f75`，已部署 dev）**：FB 发帖 / 评论后偶发中文弹窗「为让社群免受垃圾信息打扰，我们限制了你发帖、评论或执行其他操作的频率。你可以稍后再试。」此前**对系统全静默**——账号已被平台限流，云端风控态仍停 `normal` 继续按原节奏发，零告警零 alerts 记录。两处断点已一起修：① 词库只认「封锁 / 不可用」框架、不认「频率」框架；② 证据文本与判据文本不同源（分类读整页 innerText，上报却带遮罩快照某 DOM 元素的 textContent，而 FB 标准限流弹窗必然落空候选筛选 → 证据为空 → 云端「无文案不臆断限流」返否定 → 只降速不刹车）。
>
> **词条字面尚未真机坐实（本簇最高价值项）**：用户文案来自**截图转录**，页面实际 `innerText` 的标点形态（全 / 半角）与用词（社群 / 社区）未验。词条已刻意避开这两处方言面（不含标点、不含「社群/社区」、「你/您」两版并列），但**「发帖」二字是否与页面逐字一致仍未验**——若 FB 实际用「发布」/「发文」，`我们限制了你发帖` 两条会空转，届时只剩 `执行其他操作的频率` 一条兜底。
>
> **失败方向是安全的**：词条不命中 = 回落到今天的静默行为（现状），不会误伤；**真正要防的是反向**——误报一次即 `restricted`、钉住恢复窗且**不自动回滚**、只能人工恢复。故 91.2 的否定验收与 91.1 同等重要。

- [ ] 91.1 **真弹窗逐字取证 + 词条命中（本簇的钉）** — 真机触发限流弹窗后，用 CDP 抓 `document.body.innerText` **逐字记录原文**（存进本条目），比对三条词条 `我们限制了你发帖` / `我们限制了您发帖` / `执行其他操作的频率` 是否真命中。**若「发帖」与页面用词不符，须按真实原文改词条并两仓同步**（两侧单测各锁一份集合，改一侧另一侧必失败）。
- [ ] 91.2 **正常页面不误报（否定验收，与 91.1 同等重要）** — 浏览 FB 群规则页 / 隐私设置页 / 通知中心（这些页面遍布「限制」「频率」字样），账号风控态 MUST 维持 `normal`，MUST NOT 出现 `fb_throttle` 告警。**误报代价 = 该号停摆至恢复窗结束且只能人工恢复。**
- [ ] 91.3 **候选为空假设确认（设计前提验证）** — 限流弹窗弹出时，确认云端收到的 `risk.captcha_detected` 里 `overlay.candidates` 是否真为空、而 `overlay.text` 因回填**非空**。若真机发现候选**并非**为空（弹窗恰好命中某分支），回填降级为无害兜底、change 仍成立，但需在此记录实际命中的分支。
- [ ] 91.4 **账号真进 restricted 而非仅 warned（本 change 的疗效判据）** — 限流命中后查该账号风控态：MUST 为 `restricted`（互动配额清零只留浏览），MUST NOT 停在 `warned`（×0.7 降速）。**这一项直接验证 GAP #2 是否真修好**——只补词库不修证据洞的话，这里会停在 `warned`。
- [ ] 91.5 **告警 P0 + 独立类型 + 路由正确** — 飞书告警 MUST 为 **P0**、标题「Facebook 限流阻断」，MUST NOT 是 P1「未知阻断弹窗」；面板 `GET /api/alerts` 里该条 `type` MUST 为 `fb_throttle`（可过滤）。路由按统一口径：tom 组账号 → Tom.A（`oc_1c268549…`）。
- [ ] 91.6 **冷却不跨类型吞没（真飞书验收）** — 同一 edge 10 分钟内先触发一次验证码告警、再触发限流：限流卡 MUST 照常发出且 `alerts` 表 MUST 落一行。（此前按 edge 不分类型冷却，且落库在冷却闸之后 → 卡与记录一起被吞）
- [ ] 91.7 **评论回执诚实性未回归（红线双向）** — 限流下的评论回执 MUST 仍是「确认不了」（`verification_ambiguous`），MUST NOT 因发了告警就算成功；**也 MUST NOT** 因看到限流弹窗把已被服务器确认的评论改判失败。

## 簇 92

**前置环境**：真实 AdsPower 桌面客户端（**三条均需自出安装包** —— 按 CLAUDE.md §6 打包默认不做，故三者均已 land 但未到运营机）。三条来源不同、可分头跑，聚在一簇是因为共享「本机跑 Electron 客户端 + 真 AdsPower」这一套环境。登记于 2026-07-17（归档 `use-preprovisioned-adspower-group` / `facebook-mandatory-recruitment-interaction` / `wechat-channels-client-self-service` 时解耦）。

> **`use-preprovisioned-adspower-group`（edge master `c86bd94`，纯 Electron 桌面源码、无云端面、未打包）**：客户端不再自建 AdsPower 分组，改用运营预置的固定分组 `aidcp`；写 allowlist 里的 `group/create` 已移除。**运营前置条件（重要）**：每台运营机必须**已经**预置好名为 `aidcp` 的分组——本 change 有意砍掉了客户端自愈，缺分组的机器会**直接失去建环境能力**直到运营补建。桩测覆盖到 46/46，但「真 AdsPower 上分组落对没落对」桩验不了。

- [ ] 92.1 **真机建环境落进预置分组** — 对真实 AdsPower runtime 建一个环境，确认它落进运营预置的、名字逐字为 `aidcp` 的分组。
- [ ] 92.2 **缺分组时硬失败且报得动** — 把 `aidcp` 分组改名 / 删除后建环境：MUST 以可执行的错误文案硬失败（告诉运营去预置分组），**MUST NOT** 自建一个兜底分组把问题掩盖过去。
- [ ] 92.3 **缓存分组 id 失效后只重解析一次** — 分组被删后重建（同名、新 id）：客户端 MUST 重新解析一次拿到新 id，MUST NOT 造一个替代分组、MUST NOT 无界重试。

> **`facebook-mandatory-recruitment-interaction`（cloud `1848506` / `6a609ff` / `dea7cb0`，已部署 dev 三次）**：招工帖强制互动。**本 change 诚实声明：部署后从未触发过一条真实公开评论**（当时账号处于 `user_pause`），即代码路径在真机上一次都没走完过。**共享 FB 真机环境同簇 82 / 88 / 90 / 91**，建议同一次 session 合验。

- [ ] 92.4 **真发出第一条强制互动评论** — 解除账号暂停后跑通一条端到端：招工帖命中 → 强制互动判定 → 评论真的发出且被服务器确认。**这是该 change 迄今零真机证据的唯一补齐路径。**
- [ ] 92.5 **不误伤非招工帖** — 普通帖 MUST NOT 被强制互动逻辑命中（否定验收）。

> **`wechat-channels-client-self-service`（cloud `47e87c2` / edge `5ce88ae` / console `340d93f`，已部署 dev；Edge 侧未打包）**：视频号客户自助互动配置。Edge 的互动设置卡 / 角标 / 通知全未打安装包；Cloud 下发真态与 Console 初始化未经真账号验收。

- [ ] 92.6 **客户端内互动设置三层真态** — 打包后在客户端内改互动读取开关，确认 Cloud 真收到、真下发，且「未开启」与「确实无消息」两种空态在 UI 上可区分（红线：不得混为一谈）。
- [ ] 92.7 **回复配置缺失走显式安全初始化** — Console 上呈现「缺配置」而非静默给默认值；经显式初始化后才可用。

## 簇 93

**前置环境**：真实 AdsPower 桌面客户端（**需自出安装包**——按 CLAUDE.md §6 打包默认不做，故 Edge 侧已 land 未到运营机）+ 一个已归属该客户、且精选池里**有内容**的账号 + 客户登录态。Cloud 侧（`0857d94`）已部署 dev，Edge 侧未打包。登记于 2026-07-17（`client-content-workspace-navigation` 合回主干 + 对抗式评审修复后解耦）。

> **`client-content-workspace-navigation`（cloud `0857d94` 已部署 dev / edge `86aecf7` 未打包 / 控制仓 `f538b55`）**：客户端内灵感库（精选内容回看 + 参考创作）+ 稿件审核从抽屉迁为主窗口全页。本批含一轮多 agent 对抗式评审的 8 项修复（见 change tasks.md §6）。**桩测与 jsdom 覆盖已做到变异验证级别**（逐条改回原样必红），但下列几条**桩验不了**、必须真机。
>
> **已在真机数据上验过、无需重验**：「已成稿」计数修复已用 dev 真库对账——旧口径 34、新口径 28，即修复前有 6 条从未生成的稿被当成成稿报给客户（2026-07-17）。

- [ ] 93.1 **标题栏灵感入口真值** — 打包后在真客户端看标题栏：灵感数与已成稿数 MUST 与该账号真实精选池 / publish_log 对得上；储备条宽度随真实数量变化。
- [ ] 93.2 **未知 ≠ 零（否定验收）** — 断网 / 让 cloud 503 后：入口 MUST 显示「—」+「读取失败」，**MUST NOT** 显示 0、MUST NOT 永远停在「加载中」；储备条 MUST 呈未知虚底纹而非 0% 空槽。恢复后 MUST 能自行读到真值。
- [ ] 93.3 **灵感库分页 / 筛选 / 返回态** — 真账号翻页、切「可创作 / 全部」、进详情再返回：页码与筛选 MUST 保留；跨页 total MUST 一致（含「页码陈旧 / 列表缩短」时 MUST NOT 谎报「精选池还是空的」——本次修的 offset 越界 total 归零）。
- [ ] 93.4 **参考创作端到端** — 从一条可创作图文发起「图文一起参考」与「只参考文字」各一次：MUST 真的排队 → 真的生成稿件 → 真的进审核；回执 MUST 只说排队、MUST NOT 宣称已生成或已发布。
- [ ] 93.5 **重复提交不造重复稿（否定验收）** — 同一条灵感一分钟内连点两次：第二次 MUST 报「已受理 / 已在执行」而非失败（本次修的假失败会把操作员推去再点一次 → 真重复发帖）；一分钟后再点会是**新任务**（既有去重键设计），确认这符合运营预期。
- [ ] 93.6 **切账号零残留** — A 账号灵感库/详情在途时切到 B：MUST 不出现 A 的内容；稿件审核页 MUST 关闭且不带走 A 的删图确认态。
- [ ] 93.7 **首页不再从灵感库底下冒出来** — 开着灵感库 / 稿件审核静置若干个状态心跳周期（非视频号账号）：首页 MUST 始终不可见。这是本次修的高危回归，桩已覆盖但真机需肉眼确认无闪烁。
- [ ] 93.8 **稿件审核全页迁移无回归** — 主窗口全页审核：发布 / 取消 / 逐张删图 / 版本 CAS / 最后一张不可删 MUST 与旧抽屉一致；关闭 MUST 能回到来源页。
- [ ] 93.9 **客户回包不含内部诊断（安全否定验收）** — 抓一次真实 create-post 回包：MUST NOT 出现 formGuess / visualAnalysis / 视觉模型名 / 厂商 id / cacheKey。（桩测已 grep 断言，真机再确认一次线上形状。）
