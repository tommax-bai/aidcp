# Tasks — pacing-floor-config-min-interval

> 权威设计：`docs/design/pacing-floor-configurable-min-interval.md`。
> **集成完成**：三仓已 land 到各自 master（cloud `93e0eeb` / edge `d8e276b` / console `04b53cf`），两份 `protocol.ts` master 版逐字一致；各仓全量 test:acceptance + test + typecheck 全绿（cloud 1241、edge 577、console 26）。协议层由主 session 单点写死两仓一致。

## 1. aidcp-cloud — 配置存储 + 计算 + 下发 + 面板 API

- [x] 1.1 新建 `src/config/pacing-config-store.ts`：`implements PacingFloorProvider`，内联 `PACING_FLOOR_SCHEMA_SQL` 幂等建表；`reload()` 构建新 Map→原子替换 `this.cache`（防半填竞态）；`floorFor(op)` 现读、逐项回落非零内置默认、并在读出口 `clampFloorRange(v, OP_MIN_FLOOR[op], CAP_MS)`（权威夹点）；`getAll`/`getRow`/`set`(UPSERT+先写库后刷镜像+审计)。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.2 新建 `src/config/pacing-config-facade.ts`：`createPacingConfigPanel`，`buildCatalog()`（生效值+`overridden`+审计）；写校验白名单 op、非负整数、`min≤max`、`max≥min×1.5` 最小展宽、`≤CAP`，整块拒不部分落库。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.3 新建 `migrations/0031_pacing_floor_config.sql`（台账，不被迁移器执行；权威副本内联 store）。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.4 改 `src/risk/pacing.ts`：`CAP_MS=15000`、`OP_MIN_FLOOR`、`BUILTIN_FLOOR`、`PACING_OPS`、`PacingFloorProvider` 接口、`clampFloorRange`（store 与快照共用权威夹逼）；**total 函数** `buildPacingSnapshot(status, provider)`（整体 try/catch，provider 抛错→`undefined` 不 brick 握手）。<!-- aidcp-cloud 93e0eeb 见 §6 偏离① BUILTIN 取任务表 -->
- [x] 1.5 改 `src/comm/protocol.ts`（**热点·与 edge 逐字一致**）：加 `PacingOp` / `PacingFloorPayload` / `PacingSnapshotPayload` + `WelcomePayload.pacing?`。<!-- aidcp-cloud 2ee8461 (protocol layer, 主 session 单点) -->
- [x] 1.6 改 `src/comm/handler.ts` `onHello`：welcome 经 `buildWelcomePacing` 附 `pacing`，纯读该连接风控 status（不写风控态），解析失败回落 normal(tempo=1.0)。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.7 改 `src/panel/panel-server.ts` + `src/panel/types.ts`：`GET /api/pacing`（未注入→503 `pacing_unavailable`）；`PUT /api/pacing`（bad_request→400；`updatedBy=verified.payload.sub`；unknown_operation→404、invalid_value/no_valid_fields→400、成功→200 view）；`PanelPacingConfig` + `PacingConfig{Row,Catalog}View` + `PanelDeps.pacingConfig?`。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.8 改 `src/server.ts`：构造 `PacingConfigStore`→`init()`（失败不致命=空镜像回落默认）→`createPacingConfigPanel`→注入 deps `pacingConfig` + `handler.pacingFloors`（现读=PUT 后下次握手即新值）。<!-- aidcp-cloud 93e0eeb -->
- [x] 1.9 改 `src/risk/resume-limits.ts`：`IDLE_NUDGE_MIN_MS` 注释追加 `CAP_MS < IDLE_NUDGE_MIN_MS` 看门狗 lockstep 不变量。<!-- aidcp-cloud 93e0eeb 见 §6 偏离③ tripwire 断言位置 -->
- [x] 1.10 测试（5 文件 32 用例）：契约 AC-PROTO-06 结构化往返；`buildPacingSnapshot` 抛错不 brick 握手；facade 校验（展宽不足/负数/未知 op 整块拒）；store 三道夹（psql 直插 0/超界/负数）；panel 503/404/400/401。<!-- aidcp-cloud 93e0eeb + 2ee8461(AC-PROTO-06) -->

## 2. aidcp-edge — 最小间隔 gating + 单调时钟 + 采样 + 重连注入

- [x] 2.1 改 `src/comm/protocol.ts`（**热点·与 cloud 逐字一致**）：加同一组 payload 类型 + `WelcomePayload.pacing?`。<!-- aidcp-edge 8e2f15c (protocol layer, 主 session 单点) -->
- [x] 2.2 改 `src/humanize/timing.ts`：新增 `sampleReflect(min,max,sigma)`（三角波反射消硬左壁；**新 helper，未改共享 `sampleDelay`**）。<!-- aidcp-edge 03fb941 -->
- [x] 2.3 改 `src/browse/browse-session.ts`：`monoNow()`（单调、单一注入口、只自身作差、绝不与 Date.now 混算）；`lastActionEndAt`/`opFloorCfg`/`tempo`；`effectiveFloor`（反射采样×tempo÷fatigue、二次夹 `[OP_MIN_FLOOR,CAP]`）；`ensureMinInterval`（compute-only 补差额）；`gateBeforeAction`（think 与间隔取 `max` 非 `+`、单次 sleep）；`sleepInterruptible`（仅 stop/session.end 唤醒、不复活 closing）；`markActionEnd` 放 uplink 之后。<!-- aidcp-edge 03fb941 见 §6 偏离② fatigue 方向 -->
- [x] 2.4 命令入口映射：note.open/profile.open/interaction.* → `action`；note.browse_images → `card_gap`；note.scroll_comments → `scroll`；删 4 处引导性 `humanPause`（executeLikeOrCollect/LikeComment/Comment/Follow 点击前）、保留子步骤微停顿与 captcha 复检；`ensureDetailDwell` floor 源改 welcome `detail_dwell`（复活 `dwellFloorMs`）；`onCdpReconnected` 清 `lastActionEndAt`。notification.* 仍用 thinkBefore（v1 排除、fast-follow）。<!-- aidcp-edge 03fb941 -->
- [x] 2.5 改 `src/client/edge-client.ts`：`connect()` 读 `welcome.payload.pacing` 存 + `getPacing()` getter。<!-- aidcp-edge 03fb941 -->
- [x] 2.6 改 `src/main.ts`：`browseOpts` threading `dwellFloorMs`+`opFloorsMs`+`tempo`；`BrowseSession.applyPacingSnapshot`；**`reestablishIdentity` 在 connect 后 start 前调 `applyPacingSnapshot`**（最严重缺口修复），并重置锚点。<!-- aidcp-edge 03fb941 + d8e276b(applyPacingSnapshot 清锚点) -->
- [x] 2.7 测试（8+1 条红线）：非默认 floor 真到 gate（12000/13000 命中、内置≤6000 对照）；极小配置夹到 800、0/负回落内置；慢回不额外 sleep 不塌零；think 与间隔 `max` 非 `+`（双向）；重连新 floor 生效 + 重连清锚点跳过间隔。注入可控 monoNow。<!-- aidcp-edge 03fb941 + d8e276b -->

## 3. aidcp-console — 面板编辑 UI

- [x] 3.1 改 `src/api/queries.ts` 加 `usePacingConfig()`（照 `useQuotaConfig`，`queryKey ['config','pacing']`）；`src/types/api.ts` 加 `PacingConfigRow/View`（手写镜像 cloud `PacingConfigRowView`、字段逐字对齐）。`client.ts` 不改。<!-- aidcp-console 04b53cf -->
- [x] 3.2 改 `src/pages/QuotasPage.tsx`：并入安全页作「节奏兜底（全局）」Card（免加导航、App/AppShell 免改）：Alert（三条运营预期 + 过低值抬到非零下限说明）+Table（生效值+覆盖 Tag）+Modal（InputNumber min/max）；`savePacing` useMutation→`apiPut('/api/pacing')`→invalidate 重取真态（写非乐观）；本地 canSave(`max≥min×1.5`)+服务端二次校验双闸。<!-- aidcp-console 04b53cf -->

## 4. docs — 协议文档同步

- [x] 4.1 改 `docs/protocol.md`：更新 `welcome` payload（新增 `pacing?` 快照结构 + 三道夹红线说明）；未动 MessageType 计数与 §2 表。<!-- aidcp (随本 change 收口提交) -->

## 5. 集成 / 竞争区登记 / 回归红线

- [x] 5.1 **竞争区串行集成**：三仓经 `scripts/land-change --yes` 逐仓 land（cloud→edge→console），各仓 `fetch`+rebase origin/master 无冲突、ff push、主 checkout 同步、worktree 清理；两份 `protocol.ts` 逐字一致（已验证）。<!-- 无 non-ff、无 force -->
- [x] 5.2 **回归红线全过**：cloud test:acceptance 37/37 + test 1241/1241 + typecheck；edge test:acceptance 12 + test 577/577 + typecheck；console build + test 26/26 + typecheck；`AC-PROTO-*`+AC-PROTO-06、三道夹非零、慢回不累加不塌零、`buildPacingSnapshot` 抛错不 brick 均绿。<!-- land-change 全量套件跑通 -->
- [ ] 5.3 **真机验收项登记** backlog（`docs/real-machine-acceptance-backlog.md`）：非默认 floor 真到边缘生效、慢回不双等、重连重注入、看门狗不误杀 + §6 两条 low 观察。
- [ ] 5.4 **部署**（按需，走安全序列）：cloud 先（具备下发）、edge 后；向后兼容任意组合不 brick；部署前探 ECS 现状、先备份再 rsync/restart/healthcheck、绝不碰 isales。

## 6. 偏离与已知 low 观察（诚实登记）

- **偏离① BUILTIN_FLOOR 取任务表 §5 而非 raw `timing.ts` 预设**（cloud+edge 一致）：edge 现役预设 max 与 §5 不同（action 6000 / card_gap 12000 / scroll {400,2000}），两侧统一取 §5 表（action{1500,4000}/scroll{500,1500}/card_gap{3000,7000}/detail_dwell{2500,5000}=`DWELL_FLOOR_MS`）以保**混版一致**（cloud 下发值=edge 内置回落值）。仅影响「旧云端/缺字段」回落路径；新-新部署由 cloud 下发主导。<!-- cloud 93e0eeb / edge 03fb941 -->
- **偏离② fatigue 方向纠偏**（修设计伪代码笔误）：设计 §3.1 伪码 `raw*(tempo*getSpeedFactor)`，但 `getSpeedFactor>1=更快`、全仓一律 `applySpeedFactor`（除法）落地，照搬乘法会把热身期算成更快。edge 改用 `applySpeedFactor(raw*tempo, fatigue)`（=`raw*tempo/fatigue`），tempo 仍乘法（≥1 放大延迟），与现役节奏层同向。<!-- edge 03fb941 -->
- **偏离③ 看门狗 tripwire 断言位置**：task 1.9 字面要求放 resume-limits 不变量测试，实际放 `test/pacing-snapshot.test.ts`（跨 import `CAP_MS` 与 `IDLE_NUDGE_MIN_MS` 断言关系 + 10× 余量），功能等价、不变量已守。<!-- cloud 93e0eeb -->
- **已修 low**：edge `reestablishIdentity` 重连未清锚点 → `applyPacingSnapshot` 现同清 `lastActionEndAt`（§3.2 不变量2），补红线测试。<!-- edge d8e276b -->
- **未修 low 观察（harmless，登记 backlog 观察、不阻断）**：① edge：gate 因 `session.end` 已排队而 abort 时 `markActionEnd` 仍推进锚点——下条即 session.end 停循环、monoNow 已进 elapsed 大 remaining 0，无害；② cloud：`getAll()` 返回内部 Map 活引用无防御拷贝——当前唯一 catalog 路径经 `getRow`+`floorFor` 不经 getAll，无 caller 变更，无害。
