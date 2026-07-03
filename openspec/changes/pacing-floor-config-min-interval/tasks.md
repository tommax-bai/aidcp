# Tasks — pacing-floor-config-min-interval

> 权威设计：`docs/design/pacing-floor-configurable-min-interval.md`（§ 引用见各任务）。
> 集成纪律：热点/竞争文件（见 §5）**单写者、集成串行**——落地前 `fetch`+rebase 到最新 master，rebase 后再 build，**绝不 force**。两份 `protocol.ts` 逐字一致。改后先 `test:acceptance` 再全量 `test` 再 `typecheck`。

## 1. aidcp-cloud — 配置存储 + 计算 + 下发 + 面板 API

- [ ] 1.1 新建 `src/config/pacing-config-store.ts`：`implements PacingFloorProvider`，内联 `PACING_FLOOR_SCHEMA_SQL` 幂等建表，`init()` 跑 schema→`reload()`；`reload()` 用「构建新 Map→原子替换 `this.cache`」（防半填竞态）；`floorFor(op)` 每次现读、逐项回落非零内置默认、**并在此 `clamp(v, opMinFloor[op], CAP_MS)`**（权威夹点）；`getAll`/`getRow`/`set`(UPSERT+先写库后刷镜像+审计)。（设计 §4.1）
- [ ] 1.2 新建 `src/config/pacing-config-facade.ts`：`createPacingConfigPanel({store})`，`buildCatalog()`（生效值+`overridden`+审计）；写校验：白名单 op、`min/max` 非负整数、`min≤max`、`max≥min×1.5` 最小展宽、`≤CAP`，整块拒不部分落库。（设计 §4.1，spec console-write-operations）
- [ ] 1.3 新建 `migrations/0031_pacing_floor_config.sql`（台账，不被迁移器执行、无逻辑；权威副本内联 store）。（设计 §4.1）
- [ ] 1.4 改 `src/risk/pacing.ts`（**竞争区**，可能撞 category-adaptive-images-and-judgment）：定义 `CAP_MS=15_000`、`opMinFloor`、`BUILTIN_FLOOR`（逐字从现役预设/`DWELL_FLOOR_MS` 提取）；新增 **total 函数** `buildPacingSnapshot(status, provider)`——整体 try/catch，取 status 失败/store 抛错一律返回 `undefined`（绝不 brick 握手）；`tempo=tempoForStatus(status)`、`opFloorsMs` 逐 op clamp。（设计 §4.1）
- [ ] 1.5 改 `src/comm/protocol.ts`（**热点·串行·与 edge 逐字一致**）：加 `PacingOp` / `PacingFloorPayload{minMs,maxMs}` / `PacingSnapshotPayload{tempo,opFloorsMs}` + `WelcomePayload.pacing?`。（设计 §4.2）
- [ ] 1.6 改 `src/comm/handler.ts`（`onHello`，约 :341）：welcome 附 `pacing: buildPacingSnapshot(controllerFor(session).getState().status, pacingConfigStore)`；纯读 status、不写风控态；握手早于风控态则回落 `normal`(tempo=1.0)。（设计 §4.2）
- [ ] 1.7 改 `src/panel/panel-server.ts` + `src/panel/types.ts`（**竞争区**，撞 console-cloud-panel-hardening）：`GET /api/pacing`（deps 未注入→`503 pacing_unavailable`；返 catalog）；`PUT /api/pacing`（`readJsonBody` 失败→400；逐字段类型闸；`updatedBy=verified.payload.sub`；错误映射 unknown_operation→404、invalid_value/no_valid_fields→400、成功→200 view）；`PanelPacingConfig` + `PanelServerDeps.pacingConfig?`。（设计 §4.4，spec console-panel-api / console-write-operations）
- [ ] 1.8 改 `src/server.ts`：构造 `PacingConfigStore`→`init()`→`createPacingConfigPanel`→注入 deps `pacingConfig` + 把 store 交 handler 供 `buildPacingSnapshot` 现读（PUT 后下次握手即新值=热加载）。（设计 §4.4）
- [ ] 1.9 改 `src/config/resume-limits.ts`：MUST 不变量注释追加 `PACING_OP_FLOOR_CAP_MS < IDLE_NUDGE_MIN_MS`；对应不变量测试加常量关系断言 tripwire。（设计 §4.3/§7）
- [ ] 1.10 测试：两份 proto 契约结构化断言（`WelcomePayload`+`PacingSnapshotPayload`、同一份填满全字段样例常量、逐字人工同步、JSON 往返每字段存活）；`buildPacingSnapshot` 注入必抛桩→握手仍成功回退默认；facade 校验用例（展宽不足/非法/未知 op 整块拒）。（设计 §4.2/§7）

## 2. aidcp-edge — 最小间隔 gating + 单调时钟 + 采样 + 重连注入

- [ ] 2.1 改 `src/comm/protocol.ts`（**热点·与 cloud 逐字一致**）：加同一组 payload 类型 + `WelcomePayload.pacing?`。（设计 §4.2）
- [ ] 2.2 改 `src/humanize/timing.ts`：新增 `sampleReflect(min,max,sigma)`（反射采样、越界反弹消硬左壁；**新 helper，不改共享 `sampleDelay`**）；内置 σ 视 §9-Q2 决策略放宽（默认小幅放宽 + 反射双保险）。（设计 §7/§9）
- [ ] 2.3 改 `src/browse/browse-session.ts`（**竞争区**，撞 comment-search-command / fix-interaction-and-comment-capture 的命令入口）：新增状态 `lastActionEndAt`/`opFloorCfg`/`tempo`；`monoNow()`（单一实现·单一注入口·只自身作差·绝不跨基准/持久化）；`ensureMinInterval(op)`（抽 `ensureDetailDwell` 的锚→elapsed→补差额）；`gateBeforeAction(op, thinkMs?)`（think 与间隔取 `max` 非 `+`）；`sleepInterruptible`（可被 stopRequested/命令唤醒、不复活 closing 终态）；`markActionEnd()` 放 uplink 之后。（设计 §3.1/§4.3）
- [ ] 2.4 改 `src/browse/browse-session.ts` 命令入口按 spec §3.3 映射：note.open/profile.open/interaction.* → `gateBeforeAction('action',thinkMs)`；note.browse_images → `card_gap`；note.scroll_comments → `scroll`；**删引导性 `humanPause`**（:1097/1166/1289/1418 等，累加根因）、**保留子步骤微停顿**；`ensureDetailDwell` floor 源改 welcome 下发的 `detail_dwell` 行（复活死参数 `dwellFloorMs`）；`ensureFeedDwell` 原样；`onCdpReconnected` 同处清 `lastActionEndAt=null`。（设计 §3.3/§4.3）
- [ ] 2.5 改 `src/client/edge-client.ts`（**竞争区**，撞 edge-companion-ui；约 :168 connect）：读 `welcome.payload.pacing` 存字段 + 暴露 getter。（设计 §4.3）
- [ ] 2.6 改 `src/main.ts`（**竞争区**，撞 edge-companion-ui；:382/:386 + :366-371）：`browseOpts` threading `dwellFloorMs`(取 `opFloorsMs['detail_dwell']`)+整张 `opFloorsMs`+`tempo`；`BrowseSession` 新增 `applyPacingSnapshot(opFloorsMs,tempo)`；**`reestablishIdentity` 在 connect 后、start 前调 `applyPacingSnapshot`**（最严重缺口修复：重连复用同一对象须重注入）。（设计 §4.3）
- [ ] 2.7 测试（红线）：端到端——云端下发**非默认** floor→边缘 gate 实测间隔命中该值而非内置（把「字段真被读到」变红线）；配 0/负数经三道夹后实测间隔仍 ≥ 防呆下限；云端慢回(`elapsed≥floor`)不额外 sleep 且不塌零、两层用 `max` 非 `+`；重连 `applyPacingSnapshot` 后新值生效。（设计 §6/§7）

## 3. aidcp-console — 面板编辑 UI

- [ ] 3.1 改 `src/api/queries.ts`：加 `usePacingConfig()`（照 `useQuotaConfig`，`queryKey:['config','pacing']`）；`src/types/api.ts` 加 `PacingConfigRow/View`（含 `overridden`+审计）。`client.ts` 不改。（设计 §4.4）
- [ ] 3.2 改 `src/pages/QuotasPage.tsx`（**竞争区**，撞 console-cloud-panel-hardening）：**并入现有安全页作一块 Card**（免加导航项）：`Table`(生效值+已覆盖/系统默认 Tag)+`Modal`(表单 InputNumber min/max)+`useMutation`(`apiPut('/api/pacing')`→invalidate 重取真态、写非乐观)+本地 canSave/服务端二次校验双闸；`Alert` 写清三条运营预期（① 下次重连生效、连接级、rollout 期异构；② `detail_dwell` 仅兜底下限、内容驱动停留由云端算；③ 混版仅对新版边缘生效）。`App.tsx`/`AppShell.tsx` 免改。（设计 §4.4）

## 4. docs — 协议文档同步

- [ ] 4.1 改 `docs/protocol.md`：更新 `welcome` payload（新增 `pacing?` 快照结构）；**不动头部 MessageType 计数与 §2 表**（无新增消息类型）。（设计 §4.2）

## 5. 集成 / 竞争区登记 / 回归红线

- [ ] 5.1 **竞争区串行集成**：`panel-server.ts`/`QuotasPage.tsx`（console-cloud-panel-hardening）、`browse-session.ts` 命令入口（comment-search-command / fix-interaction-and-comment-capture）、`edge-client.ts`/`main.ts`（edge-companion-ui）、`pacing.ts`（category-adaptive-images-and-judgment）——各仓集成前 `fetch`+rebase 到最新 master、rebase 后再 build、**绝不 force**；两份 `protocol.ts` 单写者逐字一致。
- [ ] 5.2 **回归红线全过**：cloud+edge 各 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`；`AC-PROTO-*` + 新增 proto 结构化断言必过；两条最小间隔断言（三道夹非零、慢回不累加不塌零）；`buildPacingSnapshot` 抛错不 brick 握手。
- [ ] 5.3 **真机验收项登记** backlog（`docs/real-machine-acceptance-backlog.md`）：非默认 floor 真到边缘生效、慢回不双等、重连重注入、看门狗不误杀——真机核对项解耦到 backlog、不阻断 archive。
- [ ] 5.4 **部署**（按需，走安全序列）：cloud 先（具备下发）、edge 后；向后兼容任意组合不 brick；部署前探 ECS 现状（并发方也在改同机）、先备份再 rsync/restart/healthcheck、绝不碰 isales。
