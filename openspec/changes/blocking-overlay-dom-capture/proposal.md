## Why

阻断弹窗（验证码 / 安全检查 / 限流）随机出现，每次出现都是一次一次性的现场：处置完就没了，下次是什么形态无人知道。要开发「自动关掉它 / 点它上面某个按钮 / 判定它属于哪一类阻断」，**前置是先拿到页面结构**——今天一条都没有。

现状精确地是：**判定为阻断的那一刻，边缘一个 DOM 节点都没记下来。**

- 生产路径上的阻断探针只产出**两样东西**：类别，和 `document.body` 的整页可见文字（截 1000 字）。见 `aidcp-edge/native/page-engine/src/facebook-router/05-session.js` 的 `blockingProbe()` 与 `90-dispatch.js:42-54`。
- 上报时结构化快照字段被**硬编码为空**：`aidcp-edge/src/native-page-engine/browse-session.ts:1656-1670` 发 `risk.captcha_detected` 时写死 `candidates: []`，`dom` 从不赋值。
- 结果：运营收到的告警卡里「DOM 特征」那一行**永远不出现**，「遮罩文案」实际是整页文字。真实样本（2026-08-06，账号 Maryanne Head，`facebook.com/reel/...`）的文案里混着 Reels 导航、`38.3K 4.1K 1.1K`、`Brady Smith · Follow`，真正的弹窗文字 `Sorry, this feature isn't available right now` 夹在中间。

协议侧的**载具早已存在**（`BlockingOverlaySnapshotPayload` 带 `dom` / `candidates`，两仓 `src/comm/protocol.ts:1146-1185`），只是从来没有生产者去填。云端也**存不下**：结构化载荷在落库前被拍平成一段给人读的 Markdown 塞进 `alerts.detail`（TEXT 列，`0006_alerts.sql`），且同 edge 同类型 10 分钟冷却窗内的重复事件**在落库之前**就被丢弃（`aidcp-automation/src/comm/captcha-coordinator.ts:199-231`）——弹窗越随机，样本越攒不起来。

本 change **只做「拿到信息」**：把现场结构化采下来、原样存住、可查询。判定、自动关闭、规则表一律不做——那些等有了真实样本再各自立项。

## What Changes

- **边缘：新增只读现场采集（Native 引擎侧）**。在阻断探针**已判出阻断类别**的那一刻，额外采集视口内所有可见的对话框 / 浮层容器，每个容器记三层信息：
  - 结构特征：标签、角色、`aria-*`、`data-testid`、有界层级路径、位置尺寸、定位方式、是否位于 iframe 内；
  - **内部可点击子元素清单**：文字、无障碍标签、角色、标签名、相对视口坐标矩形（后续无论做元素点击还是坐标点击都依赖它）；
  - **容器 HTML 原文**（逐容器截断）——信息量最大的一份，后续开发直接照原文写，不受本次字段设计漏想的限制。
- **边缘：填上一直为空的快照字段**。上报时把采集结果放进现有 `overlay.dom` / `overlay.candidates`，并新增承载可点击子元素与 HTML 原文的字段。
- **协议：扩展既有载荷，不新增消息类型**。`risk.captcha_detected` 的 overlay 快照字段扩容；消息类型数不变，无新增 cloud→edge 主动命令，不触碰主动命令路由白名单。
- **云端：新增独立样本表**。每次收到带现场的上报都原样存一条结构化 JSON，**不受告警冷却影响**，可按平台 / URL / 文案指纹查询。
- **明确不做（Non-Goals）**：不改任何阻断判定逻辑；不改风控状态迁移；不改告警卡片文案与冷却行为；不做自动关闭 / 自动点击；不做形态→动作规则表；不新增任何 Cloud→Edge 浏览器操作命令（故不触发命令语法判据流程）。

## Capabilities

### New Capabilities
- `blocking-overlay-sample-capture`: 阻断弹窗现场的结构化采集与留存——采什么、采集与判定的隔离边界、上报载荷形状、云端样本表的存储与可查询性、采集失败时的诚实回报。

### Modified Capabilities
- `captcha-incident-handling`: 既有要求「判为阻断态的遮罩上报必须携带非空证据文案」中含一条禁令——边缘 MUST NOT 放宽遮罩快照的 DOM 可信阈。该禁令的理由是「放宽会把良性弹层拖进快照、放大误报面」，**只在快照参与判定时成立**。本 change 需为「纯采集、不参与任何判定」的通道开出明确豁免，同时把原禁令在判定通道上原样保留。

## Impact

- **aidcp-edge**：
  - `native/page-engine/src/facebook-router/`（新增采集片段 + `05-session.js` 阻断探针产出扩容 + `90-dispatch.js` 的 `page_probe` 输出）——按防反编译策略，页面规则留在引擎内嵌资产，不进明文 dist；
  - `native/page-engine/src/probe.rs`（`RawPageSignals` 带 `deny_unknown_fields`，新增字段必须同步 Rust 侧结构体，否则整条探针解码失败）；
  - `src/native-page-engine/browse-session.ts`（`observeProbe` 承接、`reportBlocking` 停止硬编码空快照）；
  - `src/comm/protocol.ts`（载荷扩容，与 automation 逐字一致）。
- **aidcp-automation**：`src/comm/protocol.ts`（同上）、`src/comm/captcha-coordinator.ts`（落样本，与告警冷却解耦）、新增样本表迁移（三仓并集下一号 = `0115`）、样本写入端口。
- **不涉及**：aidcp-console（本期不做展示面）、aidcp-content、风控状态机、发布链路。
- **平台范围**：Facebook 优先（其阻断探针已产出 `unknown` 桶）。小红书当前**不认未知阻断桶**（`XIAOHONGSHU_BLOCKING_POLICY.reportsUnknownBucket: false`，属已声明的缺席），故 XHS 侧只在验证码 / 登录墙两桶上顺带采集，不为本 change 新增 XHS 阻断分类。
- **风险面**：采集是只读求值，不点击、不改页面；采集失败必须诚实降级为「没采到」，MUST NOT 阻断既有上报或改变判定结果。
