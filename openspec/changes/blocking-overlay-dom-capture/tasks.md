# Tasks — blocking-overlay-dom-capture

> 按 sub-repo 分节。实装后用 HTML 注释标 `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`。
>
> **落点纪律（本 change 最容易走错的一步）**：采集实装 MUST 落在 Native 引擎路径（`aidcp-edge/native/page-engine/`）。
> `aidcp-edge/src/facebook/overlay.ts` 已在 `RETIRED_DIST_MODULES`、`src/browse/overlay-monitor.ts` 的消费方均已退役——
> 在那两处实装会全绿发版且零生产效果。见 design.md「一处必须先纠正的落点误判」。

## 1. aidcp-edge — Native 引擎采集片段（页面规则）

- [ ] 1.1 新增采集片段（`native/page-engine/src/facebook-router/` 下按既有分片命名接一个新片段），实现「入选可见对话框 / 浮层容器」的只读采集：入选口径为具备对话框语义（`role="dialog"` / `aria-modal="true"`）或定位 fixed|absolute 且面积超阈值的可见容器；MUST NOT 要求带 iframe、MUST NOT 要求无关闭控件、MUST NOT 复用判定通道的尺寸阈值
- [ ] 1.2 每个入选容器采「结构特征」层：标签、id、class、role、`aria-*`、`data-testid`、有界层级路径、相对视口 rect、position / zIndex、是否位于 iframe 内
- [ ] 1.3 每个入选容器采「可点击子元素清单」层：文字、`aria-label`、role、tag、**相对视口 rect**（rect 为硬要求，见 spec「必须携带足以复现动作的三层信息」）
- [ ] 1.4 每个入选容器采「HTML 原文」层：`outerHTML`，按字节上限截断
- [ ] 1.5 落硬上限并显式标记截断：容器数上限（建议 5，按面积降序）、每容器子元素上限（建议 30）、每容器原文字节上限（建议 20 KB）、单次总字节上限（建议 64 KB）；任一触及即在结果内置显式截断标记，MUST NOT 静默截断
- [ ] 1.6 采集结果携带三态：`captured` / `none_visible` / `failed`（后者带原因）；MUST NOT 用空数组同时表示后两态
- [ ] 1.7 片段内自带独立超时与容错：抛错 / 超时一律降级为 `failed` 并返回，MUST NOT 让异常逸出到阻断探针
- [ ] 1.8 在 `05-session.js` 的 `blockingProbe()` 中接线：**判出 `kind !== 'none'` 之后**才调用采集；采集结果 MUST NOT 回喂判定输入（判定仍只读既有整页文本 + iframe src）
- [ ] 1.9 在 `90-dispatch.js` 的 `page_probe` 分支输出采集结果（与既有 `blockingKind` / `blockingText` 同级）
- [ ] 1.10 按既有片段纪律登记新片段（`scripts/native-engine-inventory.cjs` 的片段清单 / manifest 对账），确认不进明文 dist、打包后置扫描通过

## 2. aidcp-edge — Rust 引擎结构体同步

- [ ] 2.1 `native/page-engine/src/probe.rs`：`RawPageSignals` 新增采集字段声明（`#[serde(default)]` 可选）。**注意 `deny_unknown_fields`：JS 侧产出而 Rust 未声明会导致整条 `page_probe` 解码失败 → 探针失败 → sticky 保持 → 阻断监测失明**
- [ ] 2.2 `ProbeResult` 新增对应字段，挂**顶层**（与 `blocking_kind` / `blocking_text` 同级），MUST NOT 并进 `signals`（那组是页型分类用的 u32 计数，参照 `notification_unread` 的既有注释与先例）
- [ ] 2.3 补 Rust 单测：锁「JS 产出字段集 ⊆ Rust 声明字段集」，使两侧漂移从「真机探针整条失败」降级为「测试失败」
- [ ] 2.4 补 Rust 单测：采集字段缺席（旧 JS / 非 FB 平台）时解码 MUST 成功并回落为「未采集」，MUST NOT 报错

## 3. aidcp-edge — 宿主侧承接与上报

- [ ] 3.1 `src/native-page-engine/browse-session.ts` 的 `observeProbe()`：从探针输出承接采集结果，与既有 `lastBlockingEvidence` 一并暂存
- [ ] 3.2 `reportBlocking()`：**停止硬编码 `candidates: []`**，把采集结果填进 `overlay.dom` / `overlay.candidates` 与新增字段
- [ ] 3.3 采集为 `failed` / `none_visible` 时，仍 MUST 照常发出既有 `risk.captcha_detected`（kind + 既有证据文案），行为与本 change 引入前逐字一致
- [ ] 3.4 诊断行只记「采到几个 / 三态是哪一态 / 是否截断」，MUST NOT 把 HTML 原文或子元素文字写进日志
- [ ] 3.5 补边缘单测：标准 FB 限流弹窗形态（无 iframe、约 35% 视口、带确认按钮）MUST 被采到——这是今天采不到的那一类，是本 change 的核心回归
- [ ] 3.6 补边缘单测：采集抛错时既有上报的 kind 与证据文案不变（采集失败不影响既有上报）
- [ ] 3.7 补边缘单测：良性浮层（符合较宽采集口径但不命中任何阻断判据）MUST NOT 产生任何上报（采集口径不改变判定）
- [ ] 3.8 在退役的 `src/facebook/overlay.ts` 与 `src/browse/overlay-monitor.ts` 的采集函数处各补一行指向新落点的注释，防止后续在退役实现上改代码

## 4. 协议同步（edge ↔ automation 两份逐字一致）

- [ ] 4.1 `aidcp-edge/src/comm/protocol.ts`：扩展 `BlockingOverlayDomFeaturePayload`（可点击子元素清单、HTML 原文、截断标记）与 `BlockingOverlaySnapshotPayload`（采集三态、总截断标记）
- [ ] 4.2 `aidcp-automation/src/comm/protocol.ts`：同上，**逐字一致**
- [ ] 4.3 确认消息类型数不变、无新增 cloud→edge 主动命令（故不触碰 `edge-client.ts` 主动命令路由白名单，也不触发命令语法判据流程）
- [ ] 4.4 `docs/protocol.md`：同步载荷字段说明；确认头部消息计数无需改动
- [ ] 4.5 跑 `AC-PROTO-*` 验收（在集成仓 `aidcp-cloud` 执行，边云配对为 edge ↔ automation）

## 5. aidcp-automation — 样本表与落库

- [ ] 5.1 新增迁移 `migrations/0115_blocking_overlay_samples.sql`（三仓并集下一号；属主 = automation）：表含平台、edge_id、account_id、kind、url、文案指纹、采集时间、结构化 JSONB 载荷、创建时间
- [ ] 5.2 建索引：按平台 + 创建时间倒序；按文案指纹。满足 spec 的「可按平台 / 来源地址 / 文案指纹查询」
- [ ] 5.3 新增样本写入端口（store），JSONB **原样存**采集结果，MUST NOT 在留存前拍平为供人阅读的文本
- [ ] 5.4 `src/comm/captcha-coordinator.ts`：在 `handleDetected` 的**冷却判定之前**写样本，使冷却窗内被抑制告警的上报同样留样本
- [ ] 5.5 样本写入失败：记录且不静默吞，MUST NOT 阻断风控迁移 / 暂停下发 / 告警投递
- [ ] 5.6 不叠第二道限流：上报本身已是 episode 级去重（边缘 `reportedBlockingKind` 保证一个 episode 只发一次 detected），MUST NOT 在样本侧再加冷却
- [ ] 5.7 组合根接线（`src/server.ts` / 派生入口）：把样本 store 注入 coordinator；未注入时降级为不落样本且**响亮记录**，MUST NOT 静默无声
- [ ] 5.8 补云端单测：冷却窗内被抑制告警的上报仍留下样本
- [ ] 5.9 补云端单测：告警的类型 / 优先级 / 标题 / 正文 / 冷却行为与本 change 引入前逐字一致（告警面貌不变）
- [ ] 5.10 补云端单测：样本写入抛错时风控迁移与告警投递照常完成

## 6. 验证与部署

- [ ] 6.1 edge：`npm run typecheck` + `npm run test:acceptance` + `npm test`
- [ ] 6.2 edge：Rust 侧 `cargo test`（cargo 不在 PATH，须指 rustup toolchain bin）
- [ ] 6.3 automation：`npm run typecheck` + `npm test`
- [ ] 6.4 集成仓 `aidcp-cloud`：跑跨属主 / 整图测试（含 `AC-PROTO-*` 与迁移并集编号断言）
- [ ] 6.5 部署 automation 到 `dev`（按 §5 安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck；迁移须带 `--owner`）
- [ ] 6.6 edge 侧改动收尾到 commit / push（**不出安装包**——打包属用户显式触发的动作，不进自动收尾）

## 7. 真机验收（登记 backlog，不阻塞归档）

- [ ] 7.1 真机取一次样：在 dev 上复现一次 FB 阻断弹窗，确认样本表落到了记录、且三层信息齐全
- [ ] 7.2 **可用性验收（本 change 的实质验收）**：拿真实样本，人工确认「照着它能写出认出该弹窗的锚点 + 点中其中确认按钮的动作参数」。若字段够但写不出，说明采集规格有缺口，须回填而非记成已完成
- [ ] 7.3 确认采集接入后阻断探针的耗时无可观测退化（无超时、无 `observation_probe_failed` 增量）
- [ ] 7.4 按 `docs/real-machine-acceptance-backlog.md` 的簇归并登记以上真机项

## 8. 递延项（本 change 具名不做，留给后续 change）

- [ ] 8.1 小红书侧接线：采集片段按平台无关设计，接 XHS 时在其页面探针调用同一段。**MUST NOT** 为此顺手给 XHS 补阻断分类器（其「不认未知阻断桶」是已声明的缺席，补了等于每次识别失败换一次账号降级）
- [ ] 8.2 样本表留存 / 清理策略（本期不做，样本量级由 episode 级去重天然限制）
- [ ] 8.3 console 展示面（本期靠直接查库消费样本）
- [ ] 8.4 形态→动作规则表与自动关闭 / 自动点击（本 change 的 Non-Goal，须有真实样本后另立 change，且届时新增浏览器操作命令必须先过 `establish-edge-command-grammar` 的命令语法判据）
