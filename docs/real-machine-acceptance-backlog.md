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

## 簇 4 — 浏览闭环行为（真机浏览观察）

**前置**：任一在线账号真机浏览。

- [ ] **return-to-feed-on-follow-block 3.1 / 3.2** — follow 受阻后返回 feed 续刷、不死锁
- [ ] **recency-aware-revisit-pacing 4.4 + 3.2 / 3.3** — 新鲜度重访节奏，上线后校准观察
- [ ] **restore-auto-resume-and-global-safety-config 10.3 / 10.4** — 断点自动续跑 + 全局安全配置生效

## 簇 5 — 后台配置生效（浏览器点后台 UI）

**前置**：管理后台可访问（console `8088`）+ 一个账号有流量出数。

- [ ] **role-model-category-config 5.5** — 「设分类默认 → 同类继承」点测
- [ ] **editable-account-group-label 4.4** — 账号表分组列 inline 编辑落库
- [ ] **session-limits-to-quota-layer 7.4** — 配额层真机校准
- [ ] **llm-token-usage-stats 7.5 + 6.4** — token 用量曲线真机出数 + 视觉/数据核对
- [ ] **dashboard-refresh-clarity 4.4/3.2** — 总览页新鲜度标识随 10s 轮询推进；零边缘在线时「系统未在浏览」提示可见（能一眼区分「无新活动」vs「界面冻结」）（2026-07-03 集成，部署后验）
- [ ] **persona-driven-content-pipeline 3.2** — 人设页：留空保存被拦 + 诚实提示；未绑定账号红标「未绑定」（非「回落默认」）（2026-07-03 集成，部署后验）

## 簇 6 — 精选库（数据自然积累后，机会性验）

**前置**：账号跑一段时间、精选库有沉淀。

- [ ] **curated-admission-eval-roles** — 评论链路 `curated_comment_evaluator` 真机补采样本（单测已覆盖，机会性补）
- [ ] **curated-inspiration-corpus** — Phase 2b：边端逐条评论赞数 / 笔记评论数上报（11.1/11.2 deferred，搭下次评论抽取便车）

## 簇 7 — 桌面打包（需人扫码 / 需 Windows 真机）

**前置**：可出桌面打包产物 + 人在场扫码；Windows 项另需一台真 Windows 机。

- [ ] **edge-desktop-packaging 4.6 / 6.4** — 打包产物启动 + 人工扫码登录闭环
- [ ] **edge-companion-ui 6.3（win 半段）** — Windows 真机装 `AIDCP Setup 0.2.0.exe`（mac 交叉构建，2026-07-03）：验 titleBarOverlay 观感（46px 叠加窗控、最小/最大/关闭可用）、标题带随风控染色时 `setTitleBarOverlay` 同步换色、拖拽区与控件岛不打架（mac 半段已当日真机验过）

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
