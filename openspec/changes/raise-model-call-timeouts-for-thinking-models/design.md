## Context

云端所有文本模型调用都经唯一出口 `QwenClient`（`aidcp-cloud/src/llm/qwen.ts`），构造于 `server.ts:274`，用 `AbortController` 在 `timeoutMs` 到点中止请求。当前构造默认 60s（`qwen.ts:170`），无 env 旋钮。这个值曾从 30s 抬到 60s，理由是非 thinking 模型峰值 25–30s。切到 thinking 模型后单次调用常需 60–150s+。

三处外层时限现在都可能短于模型真实耗时，形成「外层秒表先响 → 静默降级 / 整篇作废」：

1. **发布角色执行超时**：发布角色继承 `publish-agent/roles/base-role.ts` 的 `executeWithTimeout`，用 `Promise.race(execute(), timer)` 包裹。该 race **不取消底层 HTTP**——只是本角色放弃等待、走 fallback。故角色的**有效模型预算 = min(角色闸, 模型调用超时, 60s 默认)**。4 个角色（`ApprovalGatekeeper` 15s / `QualityScorer` 20s / `ContentCleaner` 20s / `ImagePlanner` 30s）角色闸远短于 60s 且调模型时未传 `timeoutMs` → 峰值必被角色闸掐断。对照 `ContentScout`(90s)/`ContentCreator`(120s)/`TitleCreator`(120s) 已把同值既给角色闸又传进 `chat()`，是正确范式。
2. **发布流水线总闸**：`PublishOrchestrator` 顶层一个 `setTimeout` 到 `pipelineTimeoutMs`（`server.ts:487`=180s）就把整条流水线判 failed。而关键路径上 `ContentScout`+`ContentCreator` 串行的角色闸和已达 210s>180s，慢一点总闸会在正文还没写完就先响，丢弃已付费的 LLM 产出。
3. **浏览闭环空转看门狗**：`SessionMonitorRole` 以「wall-clock 距上次 edge 上报/命令活动」判空转，超轻推阈值注入恢复滚动、超结束阈值杀会话（阈值默认在 `risk/resume-limits.ts`：轻推 130s、下限 91s、结束默认 1h，生产经 DB 配到 ~240s）。**一次浏览决策的模型调用期间没有 edge 活动、空转计时在涨**：现在单次 60s < 轻推 130s 安全；一旦单次抬到 150s+ 就会 > 130s，看门狗在模型还没答完时先注入滚动、滚走正要返回决策的页面。

边→云 选元素（v1 兼容路径）：`aidcp-edge/src/client/cloud-selector.ts:36` 边缘等待 15s < 云端模型 60s，边缘先放弃。

约束：不改协议、不改风控状态机；红线「MUST NOT 静默假成功」不动（降级仍须诚实可见）；看门狗结束阈值走 DB 配置，其管线归既有 change `restore-auto-resume-and-global-safety-config`，本 change 只调数值与不变量、不重复其管线。

## Goals / Non-Goals

**Goals:**
- 把单次模型调用天花板抬到能容纳 thinking 模型（180s），并让部署经 env 可调。
- 消除「外层秒表短于模型预算」这一类误超时：发布角色闸 ≥ 其所包裹模型预算且把超时同步传进模型调用；流水线总闸 ≥ 关键路径角色预算之和。
- 把「看门狗轻推阈值 > 单次模型天花板」固化为强制联动不变量，避免抬天花板反而打断合法决策。
- 每处可调值都配 env 旋钮，缺省回落安全默认、绝不 brick。

**Non-Goals:**
- 不改万相生图轮询次数/间隔与生图角色闸数值（现 34×5s=170s 对 wan2.7 够用；仅在换更慢 thinking 生图模型时再等比放大——列入 backlog）。
- 不改边-云协议、不改风控状态机、不改节奏 think/dwell 系数。
- 不接管看门狗结束阈值的 DB 配置管线（归 `restore-auto-resume-and-global-safety-config`）；本 change 只保证代码默认与下限、生产值同步核对。
- 不新增抽象层（YAGNI）：沿用现有 env 旋钮 + 构造注入模式。

## Decisions

**D1. 单次天花板定 180s 而非 150s。** 用户下限是 150s；取 180s 给 thinking 模型留一档余量（≈ 观测峰值的上界再加缓冲），且让下面所有联动值以 180s 为基准推导。经 `AIDCP_LLM_TIMEOUT_MS` 可调，缺省 180000。备选「保持 150s」被否：150s 贴着 thinking 峰值、没余量。

**D2. 发布角色统一以「单一超时常量既做角色闸又传进模型调用」修复。** 复用 `ContentScout` 已验证的范式：一个 env 常量 → 角色 `config.timeoutMs` 与 `chat()/complete()` 的 `opts.timeoutMs` 同取该值。这样角色闸永不短于模型预算，且底层 HTTP 会被真正中止（不再泄漏一个跑满 60s 的悬空请求）。备选「只抬角色闸不传模型超时」被否：底层 HTTP 仍按 60s 默认，角色闸抬到 180s 后反而让一个已注定失败的慢请求空等更久。

**D3. `ContentCleaner` 的模型调用在 `server.ts:469`（经注入的 postProcessor）而非角色文件内。** 故该角色的修复要点是：角色闸抬到 180s **且**在 `server.ts` 注入 postProcessor 处把 `complete()` 的超时同传。设计上把该超时也收在同一个 env 常量下，避免两处漂移。

**D4. 流水线总闸取 600s（10min），并确立「容器 ≥ 内容物」不变量。** 关键路径上模型角色预算之和（scout+content+imgPlan+imageGen+assembler+title+gate+executor，含 180s 级角色与 200s 生图）粗算 ~840s 上界、常态 ~250–400s。发布是人审 gated、不敏感于时延，总闸取 600s 兼顾「装得下常态慢跑」与「真死局不无限拖」。同时天然消解「生图 200s 角色闸 > 180s 总闸而永不可达」的错位。备选「压小角色闸以塞进 180s」被否：与 D1/D2「给 thinking 留足」矛盾。经 `AIDCP_PUBLISH_PIPELINE_TIMEOUT_MS` 可调。

**D5. 看门狗轻推阈值抬到 240s、下限抬到 200s，结束阈值生产值 ≥480s。** 不变量：轻推 > 单次模型天花板（240 > 180）。下限 `IDLE_NUDGE_MIN_MS` 从 91s 抬到 200s（> 180s 天花板），防运营经后台把轻推配到低于一次合法调用。结束默认仍 1h（代码），但生产 DB 值须从 ~240s 抬到 ≥480s（须显著 > 新轻推 240s，给「慢调用+重试」留空间）——此值经既有配置管线在后台改，本 change 负责核对与登记，不改管线。

**D6. 边→云 选元素等待取 200s（> 180s 天花板）。** v1 兼容路径、低频，但同守「等待方须长于被等的模型预算」不变量。硬编码提升即可，无需 env（低频、非热点）。

## Risks / Trade-offs

- **[抬天花板→真死请求失败更慢]** 一个真正卡死的模型请求现在最长空等 180s 才失败 → 缓解：外层仍有角色闸（发布）/看门狗（浏览）/流水线总闸三层有界兜底，且降级路径诚实可见；探活仍用短超时 8s，不受影响。
- **[看门狗轻推抬高→瞬时卡顿自愈变慢]** 轻推从 130s 抬到 240s，页面瞬时卡顿要更久才被推一把 → 缓解：这是为容纳合法 thinking 决策的必要代价；结束阈值仍兜底真死局；瞬时卡顿的其它自愈（返回续刷、坏页兜底）不受影响。
- **[生产 DB 结束阈值漏改]** 若只改代码默认、忘了把生产 DB 的 idle-end 从 240s 抬到 ≥480s，则轻推 240s 与结束 240s 撞车、慢调用可能被直接结束 → 缓解：tasks 内列为部署必做校验项，healthcheck 后核对生效值。
- **[总闸 600s 掩盖真慢]** 总闸放大后，一次真的异常慢发布要 10min 才失败 → 缓解：发布人审 gated、非在线交互，且各角色闸 180s 会先冒泡失败（fallback:'abort' 即时判 failed），总闸只是最后兜底。
- **[env 旋钮非法值]** 部署把 env 配成 0/负数/超大 → 缓解：读 env 时校验并回落安全默认（沿用现有 `Number(process.env.X ?? default)` 模式 + 下限保护），绝不 brick。

## Migration Plan

1. cloud 改码（qwen 默认+env、4 角色+3 标杆角色超时、总闸、看门狗默认+下限）；edge 改 cloud-selector 等待。
2. 两仓 `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`；红线 `AC-PROTO-*`/`AC-PUB-*`/`AC-RISK-*` 必过。
3. 部署 cloud（走 §5 安全序列：备份→rsync→restart→healthcheck）。
4. **部署后必做**：在后台把该生产账号的 idle-end 从 ~240s 改到 ≥480s（或按天花板等比），核对生效值 > 轻推 240s。
5. 回滚：env 旋钮全部留有安全默认，异常时可先用 env 把单次天花板/总闸调回保守值而无需回滚代码；代码级回滚走备份还原。

## Open Questions

- 是否需要把「生图轮询/角色闸随 thinking 生图模型等比放大」也纳入本次？当前设计列为 backlog（换模型时再做）。若近期就要换更慢生图模型，可在 tasks 追加一组等比放大项。
- 单次天花板 180s 是否够所有目标 thinking 模型？留 env 旋钮以便无需改码即调；若某模型常态 >180s，再评估分角色差异化天花板（当前统一，避免过早分化）。
