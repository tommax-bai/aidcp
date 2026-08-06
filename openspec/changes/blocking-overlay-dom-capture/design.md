## Context

### 现状：判为阻断的那一刻，什么都没记下来

生产链路（Facebook）逐段如下：

1. `aidcp-edge/native/page-engine/src/facebook-router/05-session.js` 的 `blockingProbe()` 读整页 `document.body` 文本（≤5000 字）+ iframe src 列表，按词库判出 `captcha` / `login` / `unknown` / `none`，返回 **`{kind, text}` 两个字段**——没有任何 DOM 结构。
2. `90-dispatch.js:42-54` 的 `page_probe` 分支把它压成 `blockingKind` + `blockingText`（截 1000 字）。
3. Rust `native/page-engine/src/probe.rs:120-133` 的 `ProbeResult` 只带 `blocking_kind` / `blocking_text` 两格。
4. `aidcp-edge/src/native-page-engine/browse-session.ts:1529-1532` 的 `observeProbe()` 存成 `lastBlockingEvidence = { url, text }`；`:1656-1670` 的 `reportBlocking()` 组装 `risk.captcha_detected` 时**硬编码 `candidates: []`、从不设 `dom`**。

协议侧载具早已就位：两仓 `src/comm/protocol.ts:1146-1185` 的 `BlockingOverlaySnapshotPayload` 有 `dom` / `candidates`，`BlockingOverlayDomFeaturePayload` 有 tag / id / className / role / ariaModal / selector / rect / style / iframe / hasClose / matchReasons。**载具存在、生产者从未填过。**

云端 `aidcp-automation/src/comm/captcha-coordinator.ts`：`formatDomFeature()`（:319）把结构化特征拍平成一行 Markdown，塞进 `alerts.detail`（TEXT 列，`0006_alerts.sql`）；且冷却闸（:202-209）在**落库动作之前** return，同 edge 同类型 10 分钟内的重复事件连库都不落。

### 一处必须先纠正的落点误判

`aidcp-edge/src/facebook/overlay.ts` 与其中 `backfillOverlayEvidenceText()` 的详细注释、以及 `src/browse/overlay-monitor.ts` 的 `captureBlockingOverlaySnapshot()`（那份**确实在做** DOM 候选筛选的实现），**都不在生产路径上**：

- `facebook/overlay.js` 明列于 `aidcp-edge/scripts/native-engine-inventory.cjs` 的 `RETIRED_DIST_MODULES`，已从生产 dist 剪除；
- `browse/overlay-monitor.ts` 虽不在退役名单，但其消费者全是退役模块（`facebook/*`、`browse/browse-session.ts`）或已改走 Native 的路径——`src/main.ts` 只从 `browse/` 取一个**类型**，会话实体是 `native-page-engine`；验证码协助抓帧也已改为 `captureNativeCaptcha`。

因此 `overlay-monitor.ts` 里那套「带 iframe，或（宽≥60% 视口 且 高≥40% 且 无关闭控件）」的候选筛选，**并不是运营机上跑的那套**——运营机上根本没有筛选，因为根本没有采集。在这两个文件上实装会「写完全绿、发版成功、零生产效果且无任何警告」（CLAUDE.md §2 明列的陷阱）。

### 约束

- Native 引擎的页面规则是**防反编译**资产：新增的 Facebook 页面逻辑必须落在 `facebook-router/` 内嵌片段，不得进明文 dist。
- `probe.rs` 的 `RawPageSignals` 带 `#[serde(deny_unknown_fields)]`：JS 侧多产出一个字段而 Rust 侧不同步声明，**整条探针解码失败**（不是忽略字段，是命令报错）。
- 阻断探针每拍都跑（默认约 1s），命令超时预算 5s。采集必须有界，不能把探针拖爆。
- 红线：MUST NOT 静默假成功 / 假失败。「没采到」与「页面上确实没有可见容器」是两态，不得压成一态。

## Goals / Non-Goals

**Goals:**

- 判为阻断的那一刻，把现场的**可见对话框 / 浮层容器**结构化采下来，随既有上报送到云端。
- 采到的信息必须**足以支撑后续独立开发**：照着记录能写出「认出这类弹窗」「点中其中某个按钮」的代码，不必再等下一次真机复现。
- 云端**每一次带现场的上报都落一条样本**，不受告警冷却影响，可按平台 / URL / 文案指纹查询。
- 采集全程只读，且**绝不改变既有判定与风控行为**。

**Non-Goals:**

- 不做自动关闭、自动点击、任何形态→动作的规则表。
- 不改阻断判定逻辑、词库、风控状态迁移、告警卡片文案与冷却。
- 不新增 Cloud→Edge 浏览器操作命令（因此不触发 `establish-edge-command-grammar` 的命令语法判据流程）。
- 不做 console 展示面（本期样本靠直接查库消费）。
- 不为小红书新增阻断分类器（其「不认未知阻断桶」是已声明的缺席，见 `XIAOHONGSHU_BLOCKING_POLICY`）。

## Decisions

### 决策 1：采集落在 Native 引擎内嵌片段，不在明文 TypeScript

**选择**：新增 `facebook-router/` 片段实现采集函数，由 `05-session.js` 的阻断探针在判出类别后调用；产物经 `90-dispatch.js` 的 `page_probe` 输出。

**理由**：(a) 生产路径就在这里，明文 TS 那两个文件已退役；(b) 防反编译策略要求 FB 页面规则留在引擎内。

**放弃的替代**：在 `browse/overlay-monitor.ts` 上扩展现有 `buildBlockingOverlaySnapshotJs()`——那份实现质量不差，但它跑不到运营机上。**明确记一笔**：本 change MUST NOT 改动那两个退役文件，避免留下「看起来两处都在做同一件事」的第二事实源。

### 决策 2：采集在判定之后触发，与判定完全隔离

**选择**：`blockingProbe()` 判出 `kind !== 'none'` 之后，才跑采集；采集结果**不回喂判定**，判定输入仍只是既有的整页文本 + iframe src。

**理由**：这一条同时解掉 `captcha-incident-handling` 里那条禁令的张力。原禁令写的是「MUST NOT 放宽遮罩快照的 DOM 可信阈」，其理由是「放宽会把良性弹层拖进快照、成倍放大误报面，误报代价是账号停摆」——**该理由只在快照参与判定时成立**。采集通道不参与任何判定，放宽采集面的误报代价恒为零（最坏情况是多存了一条无用样本）。故 spec delta 的写法是：判定通道的可信阈禁令原样保留，为纯采集通道开出具名豁免。

**放弃的替代**：复用判定用的候选筛选阈值。那正是今天什么都采不到的原因——FB 标准弹窗无 iframe、约占视口 35%、带关闭按钮，三个分支全不满足。

### 决策 3：采三层信息，其中 HTML 原文是主交付物

每个入选容器采：

| 层 | 内容 | 为什么 |
| --- | --- | --- |
| 结构特征 | 标签、id、class、role、`aria-*`、`data-testid`、有界层级路径、rect、position/zIndex、是否在 iframe 内 | 后续写「认出这类弹窗」的稳定锚点。FB 的 class 是混淆的，`data-testid` 与 role/aria 才是跨改版稳定的那部分 |
| 可点击子元素清单 | 每个子元素的：文字、`aria-label`、role、tag、**相对视口 rect** | 后续写「点中某个按钮」的直接依据。rect 必须采——FB 上两种点击方式都会用到，且哪种有效是逐部位不同的（加群按钮须元素点击；反应浮层与发帖框须坐标点击），事先不知道新弹窗属于哪种，两种所需信息都得留 |
| 容器 HTML 原文 | `outerHTML`，逐容器截断 | **信息量最大、且不受本次字段设计漏想的限制**。前两层是「我猜你会用到的」，原文是「你实际会用到的」。没有它，每次发现字段设计漏了一样东西就得再等一次真机复现 |

**入选口径**：视口内可见（rect 非零、未 `display:none` / `visibility:hidden` / 近零透明度）的 `[role="dialog"]` / `[aria-modal="true"]` / 定位为 fixed|absolute 且面积超阈值的容器。刻意比判定阈值宽——见决策 2。

### 决策 4：有界性由固定上限保证，不靠自觉

- 容器数上限（建议 5，按面积降序取前 N）；
- 每容器可点击子元素上限（建议 30）；
- 每容器 HTML 原文截断上限（建议 20 KB）、整份采集总字节上限（建议 64 KB）；
- 超限一律**显式标记被截断**，MUST NOT 静默截断后当作完整样本。

**理由**：探针每拍都跑、命令超时 5s。无上限的 `outerHTML` 在 FB 这种页面上能到 MB 级，会把探针拖成超时——而探针超时按 sticky 保持上一状态，等于**阻断监测失明**。这是本 change 唯一可能反向伤害生产的路径，必须用硬上限而非经验值堵死。

### 决策 5：Rust 侧同步扩结构体（非可选）

`RawPageSignals` 带 `deny_unknown_fields`。JS 侧新增字段**必须**在 `probe.rs` 同步声明为 `#[serde(default)]` 的可选字段，否则整条 `page_probe` 解码失败 → 探针失败 → sticky 保持 → 阻断监测失明。

新增字段挂在 `ProbeResult` 顶层（与 `blocking_text` 同级），**不并进 `signals`**——`signals` 全是页型分类用的 u32 计数，塞进去要么污染分类输入、要么把结构压扁（`probe.rs` 对 `notification_unread` 已有同款先例与注释）。

### 决策 6：云端存进独立样本表，不复用 alerts

**选择**：新增表（暂名 `blocking_overlay_samples`），列含：平台、edge_id、account_id、kind、url、文案指纹、采集时间、**结构化 JSONB 载荷原样存**、创建时间。索引覆盖「按平台 + 时间」「按文案指纹」。迁移编号取三仓并集下一号 = `0115`，属主仓 = `aidcp-automation`。

**放弃的替代**：往 `alerts.detail` 里塞。两个理由：(a) 那是 TEXT 列且内容是给人读的 Markdown，结构化数据一进去就再也聚类不了；(b) 更致命的是冷却闸在落库之前 return——攒样本的目标与「10 分钟去重刷屏」的目标直接冲突。

### 决策 7：样本写入与告警冷却解耦，但不需要额外限流

样本写入放在 `handleDetected` 的**冷却判定之前**，与告警投递并列而非串联。

**为什么不需要额外限流**：上报本身已是 episode 级去重——边缘的 `reportedBlockingKind` 保证一个阻断 episode 只发一次 `detected`（`browse-session.ts:1537-1561`），不是每拍发。所以「每次带现场的 detected 落一条样本」天然有界。**不再叠第二道限流**：叠了就等于把冷却的问题原样搬进新表。

### 决策 8：采集失败必须三态诚实

上报载荷 MUST 能区分：

- `captured` — 采到了 N 个容器；
- `none_visible` — 采集跑通了，页面上确实没有符合口径的可见容器；
- `failed` — 采集本身没跑通（求值抛错 / 超时 / 被截断到不可用），并带原因。

MUST NOT 把后两者压成同一态，也 MUST NOT 用空数组同时表示「没有」和「没采到」——那正是本仓红线点名的静默假成功形态。

### 决策 9：采集失败绝不影响既有上报与判定

采集整段包在容错里：抛错 → 记为 `failed` → **照常发既有的 `risk.captcha_detected`**（带 kind + 整页文本证据，与今天完全一致）。采集是加法，不得成为既有阻断上报的新失败点。

### 决策 10：采集 ID 由边缘生成，四处串联，且不依赖落库成功

**问题**：运营收到告警卡后，怎么找到这一次的样本？只靠「同一台机器 + 时间接近」不够——同一台机器短时间内多次阻断就配不上，而冷却窗内被抑制的上报**只有样本、没有告警**，更无从配对。

**选择**：采集时**在边缘生成一个采集 ID**（`captureId`），随上报载荷送出；云端以它为样本表的唯一键；告警正文加一行展示它。

**为什么在边缘生成，而不是云端写库时用自增主键**：

1. **四处串得起来**——同一个 ID 同时出现在边缘诊断行、上报载荷、云端样本行、飞书告警卡。排查时从任何一端都能对上另外三端；自增主键只存在于库里，边缘日志永远对不上号。
2. **不依赖落库成功**——样本写失败时，告警**仍能带上这个 ID 并注明「未存住」**。若用自增主键，写失败就等于什么线索都没有，这正是本仓红线点名的静默假失败形态。
3. **天然幂等**——云端以它建唯一键，重投同一次上报不会写出第二条样本。

**ID 形状**：边缘可读、全局够唯一即可（edge 标识 + 单调时间 + 短随机段）。MUST NOT 使用页面内容做 ID（如文案哈希）——同一形态的弹窗会反复出现，那样会把不同次采集折叠成一条。

**一个告警对应几条样本**：告警正文里的 ID 只指向**触发该告警的那一次上报**（一对一）。冷却窗内被抑制的其余上报各自有样本、没有告警——它们靠「同 edge + 时间窗」在样本表里查得到，卡片上已有机器与 Edge 标识，够用。本期**不做** alerts 表到样本表的外键关联（见递延项）。

### 决策 11：平台范围 —— FB 本期实装，XHS 留缝登记

Facebook 的阻断探针已产出 `unknown` 桶，是本 change 的主场。小红书当前 `reportsUnknownBucket: false`、只认验证码 / 登录墙两桶，且 `probe.rs` 的 XHS `build_result()` 把 `blocking_kind` / `blocking_text` 硬编码为 `None`。

**本期**：FB 全量实装；XHS 侧不接线，作为具名递延项登记（采集片段的形状按平台无关设计，接 XHS 时只需在 `xhs-page-probe.js` 调用同一段）。**MUST NOT** 为本 change 顺手给 XHS 补阻断分类器——那会把「多存点样本」变成「每次识别失败换一次账号降级」。

## Risks / Trade-offs

- **[采集把探针拖超时 → 阻断监测失明]** → 决策 4 的硬上限（容器数 / 子元素数 / 字节数）+ 采集整段自带独立超时；超时即记 `failed` 并照常上报。这是本 change 唯一能反向伤生产的路径，必须在实装时以测试锁住上限而非靠代码评审。
- **[HTML 原文含用户可见的账号信息 / 内容片段]** → 样本表与告警同属云端内部数据面，不外发、不进飞书卡片、不落日志（`captcha-assist` 的图像已有「短命、MUST NOT 落日志」的同类纪律）。采集范围限于**被判为阻断的容器**，不是整页 DOM。
- **[新表无限增长]** → 本期不做自动清理（样本量级由 episode 级去重天然限制，非高频）。留存策略作为具名递延项，不在本期臆造。
- **[Rust / JS 字段不同步 → 探针整条失败]** → 决策 5 已定死同步要求；实装时以「JS 产出字段集 ⊆ Rust 声明字段集」的测试锁住，不靠人记。
- **[样本采到了但没人看 → 本 change 白做]** → 这是可接受的时序：本期的验收标准就是「样本可查、字段够用」，消费方是后续 change。但**验收 MUST 包含一次真机取样**，确认采到的内容确实足以写出选择器——否则可能攒了一堆结构对但没法用的记录。登记为真机验收项。
- **[收到告警却找不到对应样本]** → 决策 10 的边缘生成 ID + 告警正文展示。真机验收 MUST 包含一次「从卡片上的 ID 直接查到样本行」的走通，否则这条链路等于没接。
- **[退役文件与新实装形成两个事实源]** → 决策 1 已明确本 change 不碰退役文件。实装时在退役文件的采集函数处补一行指向新落点的注释，防止下一个人再在那里改。
