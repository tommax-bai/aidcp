# Tasks — blocking-overlay-dom-capture

> 按 sub-repo 分节。实装后用 HTML 注释标 `[x]`，写清 commit-sha / 偏离说明。
>
> **落点纪律（本 change 最容易走错的一步）**：采集实装 MUST 落在 Native 引擎路径（`aidcp-edge/native/page-engine/`）。
> `aidcp-edge/src/facebook/overlay.ts` 已在 `RETIRED_DIST_MODULES`、`src/browse/overlay-monitor.ts` 的消费方均已退役——
> 在那两处实装会全绿发版且零生产效果。见 design.md「一处必须先纠正的落点误判」。
>
> **落地状态（2026-08-06）**：三仓代码全部 land + 推送；automation 已部署 dev。
> **迁移 0115 刻意未执行**——执行它会武装一次 OL 停机，判据与两条出路见 §6.5 与 §9。
> 故本 change **未归档**：功能已部署但处于「有采集、无留存」的惰性态。

## 1. aidcp-edge — Native 引擎采集片段（页面规则） <!-- aidcp-edge db0adb9 -->

- [x] 1.1 新增采集片段 `native/page-engine/src/facebook-router/04-blocking-capture.js`，入选口径＝对话框语义（`role=dialog` / `alertdialog` / `aria-modal`）∪ body 近层 fixed|absolute 且面积≥2% 视口且 ≥200×80 的浮层；不要求带 iframe、不要求无关闭控件、不复用判定尺寸阈值 <!-- 编号取 04- 使其在 05-session.js 之前声明，规避 const TDZ -->
- [x] 1.2 结构特征层：tag / id / class / role / aria-modal / aria-label / `data-testid`(+`data-pagelet`) / 有界层级路径(≤5 层) / rect / position+zIndex+opacity / iframe 存在性与 src
- [x] 1.3 可点击子元素清单：tag / role / text / aria-label / testId / **相对视口 rect** / disabled
- [x] 1.4 容器 HTML 原文（`outerHTML`），按字节上限截断
- [x] 1.5 硬上限 + 显式截断标记：容器 5 / 子元素 30 / 每容器原文 20 KB / 单次总量 64 KB / 节点访问预算 4000
- [x] 1.6 三态 `captured` / `none_visible` / `failed`（后者带 reason）
- [x] 1.7 `captureId` 生成：`ovc_<base36 时间>_<crypto 随机>`；**偏离**——未按原文「edge 标识 + …」前缀 edgeId：宿主侧 `edgeId?: string` 可空，前缀会产出 `undefined-…`；edge 归属另有独立列，标识自身已全局唯一
- [x] 1.8 采集入口即生成 captureId + 整段 try/catch，异常降级 `failed` 且不逸出到阻断探针
- [x] 1.9 接线：**偏离**——未放进 `blockingProbe()`，改在 `90-dispatch.js` 的 `page_probe` 分支判出阻断后调用。理由：`blockingProbe()` 在**每条命令**派发前都跑，把 DOM 遍历塞进去等于给每条命令加一次全页扫描，而只有 `page_probe` 的输出会走到阻断上报——纯成本、零收益。语义（判定后才采、不回喂判定）与原文一致
- [x] 1.10 `90-dispatch.js` 的 `page_probe` 输出 `overlayCapture`（与 `blockingKind` / `blockingText` 同级）
- [x] 1.11 片段登记 `manifest.txt`；`artifact-gates` / 明文扫描 / 打包后置扫描全过（inventory 由 manifest 派生，无需另改脚本）

## 2. aidcp-edge — Rust 引擎结构体同步 <!-- aidcp-edge db0adb9 / 0fe518b(fmt) -->

- [x] 2.1 **更正**：`deny_unknown_fields` 不在 `RawPageSignals`（它明确不拒未知字段），而在 **`ProbeResult`**——FB 的 `page_probe` 经 `facebook.rs:921` 直接反序列化成 `ProbeResult`。故新增字段必须在此声明，否则整条探针解码失败 → sticky → 阻断监测失明。design.md 已据实修订
- [x] 2.2 `ProbeResult.overlay_capture` 挂**顶层**（与 `blocking_kind` 同级），未并进 `signals`；新增 `OverlayCapture` / `OverlayContainer` / `OverlayClickable` / `OverlayRect` / `OverlayStyle` / `OverlayViewport`
- [x] 2.3 字段漂移闸落在 **edge TS 侧**（`facebook-blocking-overlay-capture.test.ts` 末例）：jsdom 真跑一次 `page_probe`，递归收集实际产出的键，与从 `probe.rs` 正则读出的 struct 字段（snake→camel）比对。**两侧名单都是读出来的、非手抄**。已做变异验证：往 JS 加一个未声明字段 ⇒ 恰好该例变红，其余 9 例全绿
- [x] 2.4 `probe_result_without_capture_still_decodes`：缺 `overlayCapture` 仍解码成功并回落 None
- [x] 2.5 追加 `overlay_capture_three_states_survive_round_trip` / `overlay_capture_tolerates_undeclared_page_rule_fields`：留证结构**刻意不带** `deny_unknown_fields`——页面规则先行时正确降级是「丢一格」，不是把探针打瞎

## 3. aidcp-edge — 宿主侧承接与上报 <!-- aidcp-edge db0adb9 -->

- [x] 3.1 `observeProbe()` 经 `readOverlayCapture()` 承接，与 `lastBlockingEvidence` 同存
- [x] 3.2 `reportBlocking()` 停止硬编码 `candidates: []`，填 `overlay.dom` / `candidates` / `captureId` / `captureStatus` / `viewport` / `seenCount` / `truncated`
- [x] 3.3 证据文案仍**只**取自判定时的同一份页面文本；采集结果 MUST NOT 用于回填 text（保住证据与判定同源）
- [x] 3.4 诊断行记 `captureId` / 三态 / 容器数，不记 HTML 原文与子元素文字
- [x] 3.5 `readOverlayCapture()` 拒绝残缺载荷：缺 captureId 或状态不认识一律回 undefined，绝不冒充「采到了」
- [x] 3.6 10 条 jsdom 用例全绿（标准限流弹窗被采到 / 子元素带坐标 / HTML 原文 / 标识不重复 / 良性弹层不采不判 / none_visible / failed 不改判定 / 两类截断 / 字段漂移闸）
- [x] 3.7 退役文件注释指向新落点 <!-- 偏离：未加。退役文件 src/facebook/overlay.ts、src/browse/overlay-monitor.ts 本 change 一行未动（design 决策 1 要求不碰）；指路注释留待后续触碰那两个文件时补，已登记 §9.4 -->

## 4. 协议同步（edge ↔ automation 两份逐字一致） <!-- aidcp-edge db0adb9 · aidcp-automation de6430c -->

- [x] 4.1 / 4.2 两份 `src/comm/protocol.ts` 同步扩展：新增 `BlockingOverlayClickablePayload`；`BlockingOverlayDomFeaturePayload` 加 ariaLabel/testId/clickables/clickablesTruncated/html/htmlTruncated；`BlockingOverlaySnapshotPayload` 加 captureId/captureStatus/captureReason/viewport/seenCount/truncated/budgetExhausted。**同一脚本改两份 + `diff` 逐字节校验**
- [x] 4.3 消息类型数不变、无新增 cloud→edge 主动命令 ⇒ 不触碰 `edge-client.ts` 白名单，不触发命令语法判据流程
- [x] 4.4 `docs/protocol.md` <!-- 偏离：未改。本 change 只扩载荷字段、不增删消息类型，文档头部计数与 §2 表均无需变动；载荷字段说明该文档本就未逐字段展开 -->
- [x] 4.5 集成仓 `aidcp-cloud` 全量 2451 例 0 失败（含 acceptance 73 例）<!-- aidcp-cloud b856a24 -->

## 5. aidcp-automation — 样本表与落库 <!-- aidcp-automation de6430c -->

- [x] 5.1 `migrations/0115_blocking_overlay_samples.sql`（三仓并集下一号；`aidcp:owner=automation`）
- [x] 5.2 `capture_id` 唯一索引（幂等）+ 平台/时间、文案指纹两个查询索引
- [x] 5.3 `PgBlockingOverlaySampleStore`：JSONB 原样存，`ON CONFLICT (capture_id) DO NOTHING`，返回真实 `inserted`（重投如实回 false）
- [x] 5.4 写入点在 `onDetected` **最前**（冷却判定之前）
- [x] 5.5 写入失败记录且不阻断风控迁移 / 暂停下发 / 告警投递
- [x] 5.6 不叠第二道限流（上报本身已是 episode 级去重）
- [x] 5.7 组合根接线 `automation-risk-foundation` → `automation-main` → `automation-edge-access` → coordinator；未注入时 warn 响亮记录
- [x] 5.8 告警正文加「现场样本」行；其余正文行逐字不变
- [x] 5.9 写入失败时告警仍展示 captureId 并注明「未存住」
- [x] 5.10–5.13 9 条云端用例全绿（原样存 / 冷却窗内仍留样本 / 正文可回溯 / 失败仍给标识 / 未注入响亮 / 旧边缘不臆造 / 三态透传 / 告警面貌仅差一行 / 指纹归一）。**已做变异验证**：把写入挪到冷却闸之后 ⇒ 「冷却窗内仍留样本」当场变红（第一次变异挪错位置、该例仍绿，已按归因重做）
- [x] 5.14 **计划外必做项**：`schema-contract.ts` 抬 `KNOWN_MAX`→0115（**不抬 REQUIRED**）；store 改用 `requiredObjects` + 空 `ddl`（运行时 DDL 棘轮 AC-SCHEMA-DDL-OWNER 只减不增，新对象一律进 migrations/）；`boundaries/table-ownership.json` + `module-ownership.json` 登记新表与新文件；`automation-risk-foundation` 退化名单加一项

## 6. 验证与部署

- [x] 6.1 edge：typecheck ✓ / test:acceptance 40 例 ✓ / 全量 3203 例 0 失败
- [x] 6.2 edge Native：`cargo test` 210+ 例 0 失败；`cargo fmt` ✓（land 门禁一次红、已修）<!-- toolchain 须指 1.97.1，stable 1.87 装不上 -->
- [x] 6.3 automation：typecheck ✓ / 全量 2327 例 0 失败
- [x] 6.4 集成仓 aidcp-cloud：全量 2451 例 0 失败
- [x] 6.5 部署 automation 到 dev：备份 → rsync（排除 .env/node_modules/.git）→ restart → healthcheck ✓（active / 8787 LISTENING / schema 门 enforce 通过）。**迁移 0115 已随包送达但刻意未执行**，见 §9.1
- [x] 6.6 edge 收尾到 commit / push；**不出安装包**（用户显式触发才打包）

## 7. 真机验收（登记 backlog，不阻塞后续开发；本 change 未归档故一并留此）

- [ ] 7.1 真机取一次样：dev 上复现一次 FB 阻断弹窗，确认样本表落到记录、三层信息齐全 <!-- 前置：§9.1 迁移执行 + edge 出包装机 -->
- [ ] 7.2 **回溯链路走通**：从飞书告警卡上的 `captureId` 直接查到唯一一条样本行
- [ ] 7.3 **可用性验收（实质验收）**：拿真实样本人工确认「照着它能写出认出该弹窗的锚点 + 点中确认按钮的动作参数」。字段够但写不出＝规格有缺口，须回填而非记完成
- [ ] 7.4 确认采集接入后阻断探针耗时无可观测退化（无超时、无 `observation_probe_failed` 增量）
- [ ] 7.5 归并登记 `docs/real-machine-acceptance-backlog.md`

## 8. 递延项（本 change 具名不做）

- [ ] 8.1 小红书侧接线（采集片段按平台无关设计）。**MUST NOT** 为此顺手给 XHS 补阻断分类器
- [ ] 8.2 样本表留存 / 清理策略
- [ ] 8.3 console 展示面（本期靠直接查库）
- [ ] 8.4 形态→动作规则表与自动关闭 / 自动点击（须有真实样本后另立 change，届时新增浏览器操作必须先过命令语法判据）

## 9. 阻塞项与已知缺口（**归档前必须清掉 9.1**）

- [ ] 9.1 **迁移 0115 未执行——执行它会武装一次 OL 停机**。实测：dev 与 ol 的 `.env` 均为 `AIDCP_SCHEMA_GATE=enforce`，OL 在跑的 automation 构建 `KNOWN_MAX=0113`，两环境共用同一 PostgreSQL 与同一迁移账本。一旦在 dev 跑 `migrate up`，账本出现 0115 ⇒ OL 那个构建判 `schema_ahead_of_code` ⇒ enforce 下**下次重启拒绝启动**，且重启前零症状（同 memory `shared-ledger-arms-ol-restart-outage`）。**两条出路**：(a) 先把同一 automation 构建部署到 OL（需用户明确授权 + 走 release 分支），再执行迁移；(b) 维持现状，dev 侧功能保持惰性（现在就是这一态，行为已验证：store 按名退化、风控与告警零影响）。**未选定前不得执行迁移，也不得归档本 change。**
- [ ] 9.2 edge 侧改动需出安装包并装机才在真机生效（打包属用户显式触发动作）
- [ ] 9.3 `openspec/specs/` 里「采集实装必须落在生产路径上」那条要求的机械闸尚缺：现有闸只保证 JS↔Rust 字段一致，不保证有人不去退役模块上重写一份。暂靠 design 决策 1 + 本 tasks 顶部纪律约束
- [ ] 9.4 退役文件（`src/facebook/overlay.ts` / `src/browse/overlay-monitor.ts`）的指路注释未加（见 3.7）
